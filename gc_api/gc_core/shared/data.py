"""Data loading and processing"""

### external imports
from datetime import datetime
from enum import Enum
from fastapi import UploadFile
import glob
import logging
import pandas as pd
from typing import Any, BinaryIO, Hashable, TypedDict

### internal imports
from gc_core.shared.model_definitions import time_interval, ts_var

### config log
lg = logging.getLogger("app_logger")


class FileStatus(str, Enum):
    """File approval status"""

    OK = "ok"
    WARNING = "warning"
    LOADING = "loading"


class DataEntry(TypedDict):
    timestamp: datetime
    data: dict[Hashable, Any]


class FileItemDB(TypedDict):
    """Db file representation"""

    name: str
    status: FileStatus
    info: str
    items: list[DataEntry]


def load_csv_df(dir_path: str) -> pd.DataFrame | None:
    """Read all csv files in a directory. Return a dataframe with its contents"""
    csv_files = glob.glob(dir_path + "/*.csv")
    csv_dfs: list[pd.DataFrame] = []

    for csv_file in csv_files:
        df = pd.read_csv(
            csv_file,
            header=None,
            names=["timestamp", "identifier", "resource_type", "resource_usage"],
        )

        # convert to datetime object
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)

        # group by hypervisor and time to same row
        df = df.pivot(
            index=["timestamp", "identifier"],
            columns="resource_type",
            values="resource_usage",
        )
        csv_dfs.append(df)

    # Concat, rename instances to num_instances
    df = pd.concat(csv_dfs)
    df = df.rename(
        columns={"instances": "num_instances", "total_cpu_usage": "cpu_usage"}
    )

    # Remove multiindex
    df = df.reset_index(drop=False)

    # Remove instances with missing measurements
    df = df[df["qemu_processes"].isna()]
    df = df.drop(columns="qemu_processes")

    # Float to int for selected columns
    df["memory_total"] = df["memory_total"].astype(int)
    df["memory_usage"] = df["memory_usage"].astype(int)
    df["num_instances"] = df["num_instances"].astype(int)

    df = df[
        [
            "timestamp",
            "identifier",
            "cpu_usage",
            "memory_total",
            "memory_usage",
            "num_instances",
        ]
    ]

    return df.reset_index(drop=True)


def load_json_df(dir_path: str) -> pd.DataFrame | None:
    """Read all json files in a directory. Return a dataframe with its contents"""

    db_files = glob.glob(dir_path + "/*.db")
    db_dfs: list[pd.DataFrame] = []

    # read each file
    for db_file in db_files:
        try:
            df = pd.read_json(db_file, lines=True)
            db_dfs.append(df)
        except ValueError:
            lg.error(f"Failed to read file {db_file} as json")
            return None

    # concat data all data frames
    if len(db_dfs) == 0:
        return None
    return pd.concat(db_dfs)


def load_json_bin(file: BinaryIO) -> pd.DataFrame | None:
    """Read a binary json file"""

    try:
        df = pd.read_json(file, lines=True)
        return df
    except ValueError:
        lg.debug("failed to read as json")
        return None


def read_uploaded_file(
    file: UploadFile,
) -> FileItemDB:
    """Read uploaded json file, return format to save in db"""
    df_json = load_json_bin(file.file)
    file_name = file.filename if file.filename else ""
    file_item = FileItemDB(name=file_name, status=FileStatus.WARNING, info="", items=[])

    if df_json is None:
        file_item["info"] = "Invalid file format"
        return file_item

    if ts_var not in df_json.columns:
        file_item["info"] = "Failed to locate timestamp column"
        return file_item

    # convert to datetime
    try:
        df_json[ts_var] = pd.to_datetime(df_json[ts_var])
    except Exception:
        file_item["info"] = "Invalid timestamp format found"
        return file_item

    timestamp_list = df_json[ts_var].dt.to_pydatetime().tolist()
    df_json = df_json.drop(columns=["timestamp"])
    df_dict = df_json.to_dict(orient="records")

    # return file item
    try:
        file_item["items"] = [
            DataEntry(timestamp=ts, data=df) for ts, df in zip(timestamp_list, df_dict)
        ]
        file_item["status"] = FileStatus.OK
    except Exception:
        file_item["info"] = "Invalid file content"

    return file_item


def add_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    """Add features to dataframe"""
    df = df.copy()

    # mem usage ratio
    df["mem_usage_ratio"] = df["memory_usage"] / df["memory_total"]

    # numerical time features
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek

    # rolling features
    df["cpu_usage_rolling_mean"] = df["cpu_usage"].rolling(6).mean().shift(1)
    df["cpu_usage_rolling_std"] = df["cpu_usage"].rolling(6).std().shift(1)
    df["mem_usage_ratio_rolling_mean"] = (
        df["mem_usage_ratio"].rolling(6).mean().shift(1)
    )
    df["mem_usage_ratio_rolling_std"] = df["mem_usage_ratio"].rolling(6).std().shift(1)

    return df


def add_missing_instances(df: pd.DataFrame, identifier: str) -> pd.DataFrame:
    """Add missing instances to dataframe, and interpolate.
    Return a modified dataframe"""

    df = df.copy()

    # add missing instances. move all timestamps to even 5 min
    df = df.set_index("timestamp").resample(f"{time_interval}min").mean()

    # interpolate
    df_new = df.interpolate(limit=2, limit_area="inside").round(2)

    # add index column
    df_new = df_new.reset_index()

    return df_new


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    # 0. remove attributes
    if "num_instances" in df.columns:
        df = df.drop("num_instances", axis=1)
    if "instances" in df.columns:
        df = df.drop("instances", axis=1)
    if "_id" in df.columns:
        df = df.drop("_id", axis=1)

    # 1. convert timestamps to timestamp objects
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)

    # 2. sort by timestamps
    df = df.sort_values(["timestamp"]).reset_index(drop=True)

    return df


def process_df(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    """Process a loaded json/csv dataframe. Returns a list with each entry being an identifier and dataframe.
    Convert time to timestamp, sort, group by identifier,
    add missing instances, feature engineering, drop features
    """
    df = preprocess_df(df)

    # group by identifier, split into different time seriei
    ts_list: list[tuple[str, pd.DataFrame]] = []
    for id, dfi in df.groupby("identifier"):
        # remove identifier column
        dfi = dfi.drop("identifier", axis=1)

        # 4. add missing timestamps and interpolate
        dfi = add_missing_instances(dfi, str(id))

        # 5. feature engineering
        dfi = add_feature_set(dfi)

        # 6. drop features
        dfi = dfi.drop(columns=["memory_total", "memory_usage"])

        # append to list
        ts_list.append((str(id), dfi))

    return ts_list
