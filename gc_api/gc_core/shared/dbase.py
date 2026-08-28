"""Database logic"""

### external imports
from collections import deque
from datetime import datetime
from enum import Enum
import json
import logging
from fastapi import UploadFile
from pydantic import BaseModel
import secrets
import string
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    create_engine,
    delete,
    select,
    text,
    update,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    Session,
)
from typing import Any, Hashable, List, TypedDict

### internal imports
from gc_core.shared.config import get_config_defaults, parse_config
from gc_core.shared.data import DataEntry, FileItemDB, FileStatus, read_uploaded_file
from gc_core.shared.evalualtion import ModelScores, dbase_eval, dbase_eval_multiple_hz
from gc_core.shared.model import PredictionResult

### logger
lg = logging.getLogger("app_logger")


class AnalysisStatus(str, Enum):
    """Data analysis status"""

    NONE = "none"
    WORKING = "working"
    DONE = "done"
    OUTDATED = "outdated"


def get_key(ksize: int) -> str:
    """Retuns a random key of length ksize"""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(ksize))


class Key(BaseModel):
    """Help class for receiving api key data"""

    key: str


### table classes
class Base(DeclarativeBase, MappedAsDataclass):
    pass


class UserInstance(Base):
    """User instance table"""

    __tablename__ = "user_instance"
    uid: Mapped[int] = mapped_column(primary_key=True, init=False)
    api_key: Mapped[str] = mapped_column()
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    # score: Mapped[dict[str, Any]] = mapped_column(JSON)
    analysis_status: Mapped[str] = mapped_column(default=AnalysisStatus.NONE)


### files table classes
class File(Base):
    """File database"""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    info: Mapped[str] = mapped_column()
    uid: Mapped[int] = mapped_column(ForeignKey("user_instance.uid"), index=True)


class FileItem(TypedDict):
    """Frontend file representation"""

    id: int
    name: str
    status: FileStatus
    info: str


### Results table


class Result(Base):
    """Results table"""

    __tablename__ = "results_table"
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    date: Mapped[str] = mapped_column()
    model: Mapped[str] = mapped_column()
    identifier: Mapped[str] = mapped_column()
    data: Mapped[str] = mapped_column()
    uid: Mapped[int] = mapped_column(ForeignKey("user_instance.uid"))


class ResultSelector(BaseModel):
    dates: list[str]
    models: list[str]
    identifiers: list[str]


class ResultSelect(BaseModel):
    date: str
    model: str
    identifier: str
    horizon: str


class HorizonResult(TypedDict):
    timestamp: str
    cpu_usage: float
    horizon: dict[str, Any]


### datapoints table
class DataPoint(Base):
    """Datapoints table"""

    __tablename__ = "datapoints_table"
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    uid: Mapped[int] = mapped_column(ForeignKey("user_instance.uid"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    data: Mapped[dict[Hashable, Any]] = mapped_column(JSON)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))

    __table_args__ = (Index("datapoint_index", "uid", "timestamp"),)


### dbase class
class DBase:
    """Sqlite database"""

    def __init__(self, name: str):
        engine_name = "sqlite:///./" + name + ".db"
        self.engine = create_engine(engine_name)

        # activate auto vacuum
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA auto_vacuum = FULL"))
            conn.commit()

        # create tables
        Base.metadata.create_all(self.engine)

        # remove removed entries
        self.reset_progress()

    def reset_progress(self):
        """Reset status where status is working for analysis"""
        with Session(self.engine) as session:
            sm = (
                update(UserInstance)
                .where(UserInstance.analysis_status == AnalysisStatus.WORKING)
                .values(analysis_status=AnalysisStatus.NONE)
            )
            session.execute(sm)
            session.commit()

    ### api table
    def add_api_key(self, api_key: str):
        """Add new api key to the database"""
        with Session(self.engine) as session:
            session.add(UserInstance(api_key=api_key, config=get_config_defaults()))
            session.commit()

    def get_uid(self, api_key: str | None) -> int | None:
        """Get uid table-id given the api-key"""
        if api_key is None:
            return None

        with Session(self.engine) as session:
            stmt = select(UserInstance).where(UserInstance.api_key == api_key)
            result = session.scalars(stmt).one_or_none()
            return result.uid if result else None

    ### config
    def get_config(self, api_key: str) -> dict[str, Any] | None:
        """Get the config given an api key"""
        uid = self.get_uid(api_key)

        if uid is None:
            return None

        # return config
        with Session(self.engine) as session:
            api_entry = session.get(UserInstance, uid)
            return api_entry.config if api_entry else None

    def set_config(self, api_key: str, config: dict[str, Any]) -> bool:
        """Save an updated config"""
        uid = self.get_uid(api_key)

        if uid is None:
            return False

        with Session(self.engine) as session:
            api_entry = session.get(UserInstance, uid)
            if api_entry is None:
                return False

            # check for invalid
            num_config = parse_config(config)
            config.update(num_config)

            api_entry.config = config
            session.commit()
            return True

    ### data points
    def get_data_points(self, api_key: str) -> list[DataEntry] | None:
        uid = self.get_uid(api_key)
        if uid is None:
            return None

        data_list: list[DataEntry] = []
        with Session(self.engine) as session:
            sm = select(DataPoint).where(DataPoint.uid == uid)
            result = session.scalars(sm).all()

        for r in result:
            data_list.append(DataEntry(timestamp=r.timestamp, data=r.data))
        return data_list

    def get_data_points_timedelta(
        self, api_key: str, start_time: datetime, end_time: datetime
    ) -> list[DataEntry] | None:
        uid = self.get_uid(api_key)
        if uid is None:
            return None

        data_list: list[DataEntry] = []
        with Session(self.engine) as session:
            sm = select(DataPoint).where(
                DataPoint.uid == uid,
                DataPoint.timestamp >= start_time,
                DataPoint.timestamp < end_time,
            )
            result = session.scalars(sm).all()

        for r in result:
            data_list.append(DataEntry(timestamp=r.timestamp, data=r.data))
        return data_list

    def get_first_data_point(self, api_key: str) -> DataEntry | None:
        uid = self.get_uid(api_key)
        if uid is None:
            return None

        with Session(self.engine) as session:
            sm = (
                select(DataPoint)
                .where(DataPoint.uid == uid)
                .order_by(DataPoint.timestamp.asc())
                .limit(1)
            )
            first_entry = session.scalar(sm)
            if first_entry is None:
                return None
            return DataEntry(timestamp=first_entry.timestamp, data=first_entry.data)

    ### file table
    def add_files(self, api_key: str, files: list[UploadFile]):
        """Add a list of files to the database"""
        uid = self.get_uid(api_key)
        if uid is None:
            return False

        file_list: list[FileItemDB] = []

        for file in files:
            file_list.append(read_uploaded_file(file))

        with Session(self.engine) as session:
            for fi in file_list:
                ### add to File table
                new_file = File(
                    uid=uid,
                    name=fi.get("name"),
                    status=fi.get("status"),
                    info=fi.get("info"),
                )

                # add to get file id
                session.add(new_file)
                session.commit()
                session.refresh(new_file)

                ### add each row to datapoint
                for item in fi.get("items"):
                    new_point = DataPoint(
                        uid=uid,
                        timestamp=item.get("timestamp"),
                        data=item.get("data"),
                        file_id=new_file.id,
                    )
                    session.add(new_point)

            session.commit()

    def get_file_items(self, api_key: str) -> list[FileItem] | None:
        """Returns a list of files given api key"""
        uid = self.get_uid(api_key)
        if uid is None:
            return None

        with Session(self.engine) as session:
            stmt = select(File).where(File.uid == uid)
            result = session.execute(stmt).scalars().all()
            files: list[FileItem] = []
            for file in result:
                files.append(
                    FileItem(
                        id=file.id,
                        name=file.name,
                        status=FileStatus(file.status),
                        info=file.info,
                    )
                )
            return files

    def delete_file(self, api_key: str, file_id: int) -> bool:
        """Delete a file from the database, given file id"""
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            # remove from db
            sm1 = delete(File).where(File.id == file_id, File.uid == uid)
            session.execute(sm1)

            sm2 = delete(DataPoint).where(
                DataPoint.file_id == file_id, DataPoint.uid == uid
            )
            session.execute(sm2)

            session.commit()
            return True

    def delete_all_files(self, api_key: str):
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            # remove all files with matching uid
            session.execute(delete(File).where(File.uid == uid))
            session.execute(delete(DataPoint).where(DataPoint.uid == uid))
            session.commit()

    ### analyse status
    def get_analysis_status(self, api_key: str):
        """Return analysis status given api key"""
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            res = session.get(UserInstance, uid)
            if res is None:
                return None
            return res.analysis_status

    def set_analysis_status(self, api_key: str, new_status: AnalysisStatus) -> bool:
        """Set analysis status for a user instance"""
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            res = session.get(UserInstance, uid)
            if res is None:
                return False
            res.analysis_status = new_status
            session.commit()
            return True

    def set_status_working(self, api_key: str) -> bool:
        """Attempts to set status to working. Returns true if success"""
        uid = self.get_uid(api_key)

        with Session(self.engine) as session:
            res = session.get(UserInstance, uid)
            if res is None:
                return False
            if res.analysis_status == AnalysisStatus.WORKING:
                return False

            res.analysis_status = AnalysisStatus.WORKING
            session.commit()
            return True

    def end_analysis(self, api_key: str) -> bool:
        """Set analysis status to done"""
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            res = session.get(UserInstance, uid)
            if res is None:
                return False
            res.analysis_status = AnalysisStatus.DONE
            session.commit()
            return True

    ### results
    def save_results(self, api_key: str, results: list[PredictionResult]) -> bool:
        """Save model results to db"""
        uid = self.get_uid(api_key)
        if uid is None:
            return False

        # remove old results
        with Session(self.engine) as session:
            sm = delete(Result).where(Result.uid == uid)
            session.execute(sm)
            session.commit()

        # add new results
        with Session(self.engine) as session:
            for pred in results:
                new_result = Result(
                    date=pred.date,
                    model=pred.model,
                    identifier=pred.identifier,
                    uid=uid,
                    data=pred.data,
                )
                session.add(new_result)
            session.commit()

        return True

    def get_selectors(self, api_key: str) -> ResultSelector:
        """Return dates, identifiers and models in the result"""
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            # get dates
            sm = select(Result.date).where(Result.uid == uid).distinct()
            dates = list(session.execute(sm).scalars().all())

            # get identifiers
            sm = select(Result.identifier).where(Result.uid == uid).distinct()
            identifiers = list(session.execute(sm).scalars().all())

            # get models
            sm = select(Result.model).where(Result.uid == uid).distinct()
            models = list(session.execute(sm).scalars().all())

            return ResultSelector(dates=dates, models=models, identifiers=identifiers)

    def get_result(self, api_key: str, resultSelect: ResultSelect) -> str | None:
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            sm = select(Result.data).where(
                Result.uid == uid,
                Result.date == resultSelect.date,
                Result.model == resultSelect.model,
                Result.identifier == resultSelect.identifier,
            )
            return session.execute(sm).scalar_one_or_none()

    def get_horizon(self, api_key: str, resultSelect: ResultSelect) -> str | None:
        uid = self.get_uid(api_key)
        with Session(self.engine) as session:
            sm = select(Result.data).where(
                Result.uid == uid,
                Result.model == resultSelect.model,
                Result.identifier == resultSelect.identifier,
            )
            data = session.execute(sm).scalars()

        added_timestamps: deque[str] = deque(maxlen=25)
        hz_results: list[HorizonResult] = []

        hz_idx = 0
        data_list = [row for row in data]
        for day_json in data_list:
            unpacked = json.loads(day_json)
            for item in unpacked:
                if item["timestamp"] in added_timestamps:
                    continue
                added_timestamps.append(item["timestamp"])

                hz_results.append(
                    HorizonResult(
                        timestamp=item["timestamp"],
                        cpu_usage=item["cpu_usage"],
                        horizon=item["horizons"][hz_idx],
                    )
                )

        return json.dumps(hz_results)

    def get_model_scores_select(
        self, api_key: str, resultSelect: ResultSelect
    ) -> str | None:
        """Get eval scores for specific selected model, hypervisor and day"""
        uid = self.get_uid(api_key)
        if uid is None:
            return None
        with Session(self.engine) as session:
            sm = select(Result.data).where(
                Result.uid == uid,
                Result.identifier == resultSelect.identifier,
                Result.model == resultSelect.model,
                Result.date == resultSelect.date,
            )
            result_set = session.execute(sm).scalar_one_or_none()

        if result_set is None:
            return None
        model_scores = dbase_eval_multiple_hz(result_set)
        return json.dumps(model_scores)

    def get_model_scores(self, api_key: str) -> str | None:
        """Get basic eval scores for models"""
        uid = self.get_uid(api_key)
        if uid is None:
            return None

        # get unique identifiers
        with Session(self.engine) as session:
            sm = select(Result.identifier).where(Result.uid == uid).distinct()
            identifier_list = session.execute(sm).scalars().all()

        # get unique models
        with Session(self.engine) as session:
            sm = select(Result.model).where(Result.uid == uid).distinct()
            model_list = session.execute(sm).scalars().all()

        # gather results for all models
        metrics_list = []
        model_scores = {}

        for model_name in model_list:
            model_result_list: List[List[str]] = []
            for id in identifier_list:
                with Session(self.engine) as session:
                    sm = select(Result.data).where(
                        Result.uid == uid,
                        Result.identifier == id,
                        Result.model == model_name,
                    )
                    result = list(session.execute(sm).scalars().all())
                    model_result_list.append(result)

            # evaluate results
            scores = dbase_eval(model_result_list, 1)
            metrics_list = list(scores.keys())
            model_scores[model_name] = list(scores.values())

        model_scores = ModelScores(metrics=metrics_list, models=model_scores)

        return json.dumps(model_scores)


def main():
    api_key = "H9Qunq2dzsh4vsQYbP0EsMjmEeDJKk"
    db = DBase("database")
    select = ResultSelect(
        date="2025-02-17", model="AutoArima", identifier="Hypervisor 1", horizon="1"
    )
    data = db.get_model_scores_select(api_key, select)
    print(data)


if __name__ == "__main__":
    main()
