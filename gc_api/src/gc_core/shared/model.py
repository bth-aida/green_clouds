"""Model running logic"""

### external imports
import logging
import pandas as pd

from darts import TimeSeries, to_group_dataframe  # type: ignore
from darts.dataprocessing.transformers import Scaler
from pydantic import BaseModel
from typing import Any, List, TypedDict, cast


### internal imports
from gc_core.shared.config import NumConfig, Option, parse_config
from gc_core.shared.model_definitions import (
    historical_forecast_darts,
    target_var,
    horizons,
)
from gc_core.shared.progress import Progress

### config logger
lg = logging.getLogger("app_logger")


class PredictionResult(BaseModel):
    date: str
    model: str
    identifier: str
    data: str


class PointPrediction(TypedDict):
    timestamp: pd.Timestamp
    pred: float
    low: float | None
    high: float | None


def forecast_to_df_quick(forecast: List[TimeSeries]):
    """Convert TimeSeries forecast to dataframe"""


def forecast_to_df(forecast: List[TimeSeries]):
    """Convert TimeSeries result list to dataframe"""
    df_fc = to_group_dataframe(forecast, add_group_col=True).reset_index()

    df_data = []
    for index, dg in df_fc.groupby("group"):
        # find prediction, lower and upper bounds
        low_list = dg.iloc(axis=1)[1]
        pred_list = dg.iloc(axis=1)[2]
        high_list = dg.iloc(axis=1)[3]

        time_start = dg.iloc[0]["timestamp"] - pd.Timedelta(minutes=5)
        row_dict = {"timestamp": time_start}

        hz = 1
        for low, pred, high in zip(low_list, pred_list, high_list):
            row_dict[f"h{hz}_l"] = low
            row_dict[f"h{hz}_p"] = pred
            row_dict[f"h{hz}_h"] = high
            hz += 1

        df_data.append(row_dict)

    df_res = pd.DataFrame(df_data)
    value_cols = df_res.columns.difference(["timestamp"])

    df_res[value_cols] = df_res[value_cols].round(2)
    return df_res


def run_model(
    df: pd.DataFrame,
    model_name: str,
    config: dict[str, Any],
    horizons: int,
    progress: Progress | None,
) -> pd.DataFrame | None:
    """Run a model for specified horizons"""

    # dataframe for results
    df_res = df[["timestamp", "cpu_usage"]].copy()
    df = df.dropna().reset_index(drop=True)

    df_nolag = _run_prediction_darts(df, config, model_name, progress)
    df_res = df_res.merge(df_nolag, on="timestamp", how="left")

    return df_res


def _run_prediction_darts(
    df: pd.DataFrame, config: dict[str, Any], model_name: str, progress: Progress | None
) -> pd.DataFrame:
    # config parameters
    num_config = parse_config(config)
    buffer_size = num_config[NumConfig.BufferSize]
    update_interval = num_config[NumConfig.UpdateInterval]

    # stream/not stream
    if not config[Option.Stream]:
        buffer_size = int(len(df) * 0.8)
        update_interval = len(df)

    # create target and features df
    ts_target = TimeSeries.from_dataframe(df, time_col="timestamp")[target_var]
    df_features = df.drop(columns=target_var)
    ts_features = TimeSeries.from_dataframe(df_features, time_col="timestamp")

    # scaling
    scaler_target = Scaler(global_fit=True)
    scaler_features = Scaler()
    ts_target = cast(TimeSeries, scaler_target.fit_transform(ts_target))
    ts_features = cast(TimeSeries, scaler_features.fit_transform(ts_features))

    # historical forecasts
    forecast = historical_forecast_darts(
        model_name,
        ts_target,
        ts_features,
        update_interval,
        buffer_size,
        progress,
    )

    # reverse scaling
    forecast = cast(List[TimeSeries], scaler_target.inverse_transform(forecast))

    # convert to dataframe
    df_res = forecast_to_df(forecast)

    return df_res


def format_prediction_results(
    df: pd.DataFrame,
    idf: str,
    model_name: str,
    horizons: int,
) -> list[PredictionResult]:
    pred_results: list[PredictionResult] = []

    df["date"] = df["timestamp"].dt.date
    dates = df["date"].unique()

    for date in dates:
        # find day index
        df_date_filter: pd.DataFrame = cast(pd.DataFrame, df[df["date"] == date])
        day_idx = cast(pd.RangeIndex, df_date_filter.index)

        first_idx = day_idx[0]
        last_idx = day_idx[-1]

        # include n before day
        start_idx = max(0, first_idx - horizons)
        end_idx = min(last_idx + horizons, len(df))

        # extract df day
        dfd = df.iloc[start_idx:end_idx]
        dfd["horizons"] = dfd.apply(create_horizons, axis=1)

        jsond = dfd[["timestamp", "cpu_usage", "horizons"]].to_json(  # type: ignore
            orient="records", date_format="iso"
        )
        date_str = str(date)
        pred_results.append(
            PredictionResult(
                date=date_str,
                model=model_name,
                data=jsond,
                identifier=idf,
            )
        )

    return pred_results


def create_horizons(row: pd.Series):
    """Create horizon list from dataframe row"""
    hlist: list[dict[Any, Any]] = []

    for hz in range(1, horizons + 1):
        h_str = f"h{hz}"
        if f"{h_str}_p" not in row:
            break

        hlist.append(
            {
                "h_timestamp": (
                    row["timestamp"] + pd.Timedelta(minutes=5 * hz)
                ).isoformat(),
                "pred": row[f"{h_str}_p"],
                "low": row.get(f"{h_str}_l", None),
                "high": row.get(f"{h_str}_h", None),
            }
        )
    return hlist
