### external imports
import json
import logging
from typing import List, TypedDict
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

### internal imports
from gc_core.shared.model_definitions import horizons

### logging config
log = logging.getLogger("app_logger")


### model scores
class ModelScores(TypedDict):
    metrics: List[str]
    models: dict[str, List[str]]


def mae(real: pd.Series, pred: pd.Series):
    """Calculates mean absolute error"""
    return mean_absolute_error(real, pred)


def rmse(real: pd.Series, pred: pd.Series):
    """Calculates root mean squared error"""
    return np.sqrt(mean_squared_error(real, pred))


def mue(pred: pd.Series, real: pd.Series):
    """Calculated mean under error"""
    under_errors = real - pred
    return np.mean(np.abs(under_errors[under_errors > 0]))


def mcu(pred: pd.Series, real: pd.Series):
    """Calculates mean conditional underestimation"""
    diff = real - pred
    diff[diff < 0] = 0
    return np.mean(diff)


def upf(pred: pd.Series, real: pd.Series):
    """Calculates under prediction frequency"""
    real_arr = np.array(real)
    pred_arr = np.array(pred)
    return np.mean(pred_arr < real_arr)


def rcs(pred: pd.Series, real: pd.Series, low: pd.Series, high: pd.Series):
    """Calculates the regression coverage score"""
    in_interval = (real >= low) & (real <= high)
    return float(in_interval.mean())


def rmws(pred: pd.Series, real: pd.Series, low: pd.Series, high: pd.Series):
    """Calculates the regression mean width score"""
    return (high - low).mean()


def dbase_eval_multiple_hz(data: str) -> ModelScores:
    metrics_list = []
    hz_scores = {}

    for hz in range(1, horizons + 1):
        df_list = []
        json_day = json.loads(data)
        daily_list = []
        for pred_batch in json_day:
            row = {
                "timestamp": pred_batch["timestamp"],
                "cpu_usage": pred_batch["cpu_usage"],
            }

            row[f"h{hz}_p"] = pred_batch["horizons"][hz - 1]["pred"]
            row[f"h{hz}_l"] = pred_batch["horizons"][hz - 1]["low"]
            row[f"h{hz}_h"] = pred_batch["horizons"][hz - 1]["high"]
            daily_list.append(row)

        df_d = pd.DataFrame(daily_list)
        df_d["timestamp"] = pd.to_datetime(df_d["timestamp"]).dt.tz_localize(None)
        df_d = df_d.drop_duplicates()
        df_d = df_d.dropna().reset_index(drop=True)

        # shift
        df_d[f"h{hz}_p"] = df_d[f"h{hz}_p"].shift(hz)
        df_d[f"h{hz}_l"] = df_d[f"h{hz}_l"].shift(hz)
        df_d[f"h{hz}_h"] = df_d[f"h{hz}_h"].shift(hz)
        df_list.append(df_d)

        # combine the hypervisors
        df = pd.concat(df_list, ignore_index=True)
        df.columns = ["timestamp", "real", "pred", "low", "high"]
        df = df.dropna()

        # eval errros
        res = eval_errors(df)
        metrics_list = list(res.keys())
        hz_scores[f"h{hz}"] = list(res.values())

    model_scores = ModelScores(metrics=metrics_list, models=hz_scores)
    return model_scores


def dbase_eval(data_list: List[List[str]], hz: int) -> dict[str, float]:
    """Evaluate json format results"""

    df_list = []
    # unpack json data
    for i, hypervisor_data in enumerate(data_list):
        hv_list = []
        for day_data in hypervisor_data:
            json_day = json.loads(day_data)
            for pred_batch in json_day:
                row = {
                    "timestamp": pred_batch["timestamp"],
                    "cpu_usage": pred_batch["cpu_usage"],
                }

                row[f"h{hz}_p"] = pred_batch["horizons"][hz - 1]["pred"]
                row[f"h{hz}_l"] = pred_batch["horizons"][hz - 1]["low"]
                row[f"h{hz}_h"] = pred_batch["horizons"][hz - 1]["high"]
                hv_list.append(row)

        df_hv = pd.DataFrame(hv_list)
        df_hv["timestamp"] = pd.to_datetime(df_hv["timestamp"]).dt.tz_localize(None)
        df_hv = df_hv.drop_duplicates()
        df_hv = df_hv.dropna().reset_index(drop=True)

        # shift
        df_hv[f"h{hz}_p"] = df_hv[f"h{hz}_p"].shift(hz)
        df_hv[f"h{hz}_l"] = df_hv[f"h{hz}_l"].shift(hz)
        df_hv[f"h{hz}_h"] = df_hv[f"h{hz}_h"].shift(hz)
        df_list.append(df_hv)

    # combine the hypervisors
    df = pd.concat(df_list, ignore_index=True)
    df.columns = ["timestamp", "real", "pred", "low", "high"]
    df = df.dropna()

    # eval errros
    res = eval_errors(df)
    return res


def eval_errors(df: pd.DataFrame) -> dict[str, float]:
    if len(df) == 0:
        return {}

    pred = df["pred"]
    real = df["real"]
    low = df["low"]
    high = df["high"]

    results: dict[str, float] = {}
    results["rmse"] = float(round(rmse(pred, real), 3))
    results["mae"] = float(round(mae(pred, real), 3))
    results["mue"] = float(round(mue(pred, real), 3))
    results["mcu"] = float(round(mcu(pred, real), 3))
    results["rcs"] = float(round(rcs(pred, real, low, high), 3))
    results["rmws"] = float(round(rmws(pred, real, low, high), 3))

    return results
