"""API stream time series analysis module"""

### external imports
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel

from gc_core.api.web_socket import WebSocketManager

### internal imports
from gc_core.shared.data import process_df
from gc_core.shared.dbase import AnalysisStatus, DBase, PredictionResult
from gc_core.shared.model import format_prediction_results, run_model
from gc_core.shared.model_definitions import get_model_names, horizons
from gc_core.shared.progress import Progress

### config logger
lg = logging.getLogger("app_logger")

### constants
result_dir = "result"
os.makedirs(result_dir, exist_ok=True)


def save_df(df: pd.DataFrame, config: dict[str, Any], model_name: str, idf: str):
    timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M_%S_%f")
    idf = idf.lower().replace(" ", "-")
    filepath = f"{result_dir}/{timestamp}.csv"

    with open(filepath, "w", newline="") as file:
        file.write(f"# {json.dumps(config).replace(',', ';')}\n")
        file.write(f"# {model_name}\n")
        file.write(f"# {idf}\n")
        df.to_csv(file)


class AnalysisResponse(BaseModel):
    status: AnalysisStatus
    progress: int


class StreamManager:
    """Class making calculations on the time series data. For all users"""

    def __init__(self):
        self.active_jobs: dict[str, Progress] = {}

    def get_progress(self, api_key: str) -> int:
        active = self.active_jobs.get(api_key)
        if active:
            return active.get_progress()
        return 0

    def _get_data_points(self, api_key: str, db: DBase) -> pd.DataFrame | None:
        """Return full dataset uploaded"""
        # get all data from db
        data_list = db.get_data_points(api_key)
        if data_list is None:
            return None

        # create the df
        df = pd.DataFrame(d["data"] for d in data_list)
        df.insert(0, "timestamp", [d["timestamp"] for d in data_list])  # type: ignore
        return df

    def start_analysis(self, api_key: str, db: DBase, wsm: WebSocketManager):
        """Start analysis of full dataset"""
        if not db.get_uid(api_key):
            return

        # check if analysis is in progress already
        analysis_started = db.set_status_working(api_key)
        if not analysis_started:
            return False

        # load data and process
        df_full = self._get_data_points(api_key, db)

        if df_full is None or len(df_full) == 0:
            lg.debug("No data to analyse")
            asyncio.run(
                wsm.send_long_message(api_key, "Analysis stopped", "No data to analyse")
            )
            db.set_analysis_status(api_key, AnalysisStatus.NONE)
            return

        config = db.get_config(api_key)
        if config is None:
            lg.debug("Config is None")
            return

        results = self.analyse_df(df_full, api_key, config)
        db.save_results(api_key, results)
        db.end_analysis(api_key)

    def analyse_df(
        self, df: pd.DataFrame, api_key: str, config: dict[str, Any]
    ) -> list[PredictionResult]:
        df_list = process_df(df)

        # start progress
        progress = None
        if api_key != "":
            progress = Progress()
            self.active_jobs[api_key] = progress

        # analysis
        results: list[PredictionResult] = []

        if progress:
            progress.push(len(df_list))
        for idf, dfi in df_list:
            # get models that are included in the config
            run_models = [m for m in get_model_names() if config.get(m)]

            if progress:
                progress.push(len(run_models))
            for model_name in run_models:
                df_res = run_model(dfi, model_name, config, horizons, progress)

                if df_res is not None:
                    # save locally
                    # save_df(df_res, config, model_name, idf)

                    res_format = format_prediction_results(
                        df_res, idf, model_name, horizons
                    )
                    results.extend(res_format)

        return results
