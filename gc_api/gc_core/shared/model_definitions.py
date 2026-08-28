"""Definitions for models used"""

### external imports
import os
import sys

from darts import TimeSeries
from darts.models import ConformalNaiveModel
from darts.models.forecasting.block_rnn_model import BlockRNNModel
from darts.models.forecasting.catboost_model import CatBoostModel
from darts.models.forecasting.linear_regression_model import LinearRegressionModel
from darts.models.forecasting.random_forest import RandomForestModel
from darts.models.forecasting.sf_auto_arima import AutoARIMA
from darts.models.forecasting.tft_model import TFTModel
from darts.models.forecasting.xgboost import XGBModel
from enum import StrEnum
from typing import Any, List, cast

### internal imports
from gc_core.shared.progress import Progress


### constants
time_interval = 5  # time between samples (minutes)
ts_var = "timestamp"
target_var = "cpu_usage"
horizons = 12


class ModelName(StrEnum):
    """Class containing the names of all allowed models"""

    AutoArima = "AutoArima"
    LinearRegression = "Linear Regression"
    RandomForest = "Random Forest"
    XGBoost = "XGBoost"
    LSTM = "LSTM"
    CatBoost = "CatBoost"
    TFTModel = "TFT Model"


### functions
def get_model_names() -> list[str]:
    return [m.value for m in ModelName]


def historical_forecast(
    model: Any,
    ts_target: TimeSeries,
    ts_features: TimeSeries,
    update_interval: int,
    buffer_size: int,
) -> List[TimeSeries]:
    pred_kwargs = {"predict_likelihood_parameters": True, "verbose": True}

    ts_target_0, ts_target_1 = ts_target.split_after(buffer_size)
    ts_features_0 = ts_features_1 = None
    if ts_features is not None:
        ts_features_0, ts_features_1 = ts_features.split_after(buffer_size)

    model.fit(series=ts_target_0, past_covariates=ts_features_0)

    quantiles = [0.05, 0.50, 0.95]
    cp_model = ConformalNaiveModel(
        model=model, quantiles=quantiles, cal_length=200, cal_stride=1
    )

    hfcs = cp_model.historical_forecasts(
        series=ts_target_1,
        past_covariates=ts_features_1,
        forecast_horizon=horizons,
        retrain=update_interval,
        train_length=buffer_size,
        last_points_only=False,
        random_state=42,
        overlap_end=True,
        **pred_kwargs,
    )

    return cast(List[TimeSeries], hfcs)


def _forecast(
    model: Any,
    ts_target: TimeSeries,
    ts_features: TimeSeries,
    update_interval: int,
    buffer_size: int,
    progress: Progress | None,
) -> List[TimeSeries]:
    # catch verbose stderr output
    if progress is None:
        return historical_forecast(
            model, ts_target, ts_features, update_interval, buffer_size
        )
    else:
        progress.push(100)
        # create a temporary file to write progress output to
        with open(progress.fpath, "w") as f:
            org_stderr = sys.stderr
            sys.stderr = f
            fc = historical_forecast(
                model, ts_target, ts_features, update_interval, buffer_size
            )
            sys.stderr = org_stderr

        # set progress to 100%
        progress.file_fill()
        progress.pop()
        progress.update(update_progress=False)

        # remove temporary file
        if os.path.exists(progress.fpath):
            os.remove(progress.fpath)
        return fc


# darts models
def historical_forecast_darts(
    model_name: str,
    ts_target: TimeSeries,
    ts_features: TimeSeries,
    update_interval: int,
    buffer_size: int,
    progress: Progress | None,
) -> List[TimeSeries]:
    # auto arima
    if model_name == ModelName.AutoArima:
        model = AutoARIMA()
        hf = cast(
            List[TimeSeries],
            model.historical_forecasts(
                series=ts_target,
                forecast_horizon=horizons,
                retrain=update_interval,
                train_length=buffer_size,
                last_points_only=False,
                random_state=42,
                overlap_end=True,
                num_samples=300,
            ),
        )
        quantiles_list = [ts.quantile([0.05, 0.5, 0.95]) for ts in hf]

        return quantiles_list

    # cat boost
    if model_name == ModelName.CatBoost:
        model = CatBoostModel(
            lags=12,
            lags_past_covariates=12,
            output_chunk_length=horizons,
            random_state=42,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    # linear regression
    if model_name == ModelName.LinearRegression:
        model = LinearRegressionModel(
            lags=6,
            lags_past_covariates=6,
            output_chunk_length=horizons,
            random_state=42,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    # lstm
    if model_name == ModelName.LSTM:
        model = BlockRNNModel(
            model="LSTM",
            input_chunk_length=288,
            n_epochs=15,
            output_chunk_length=horizons,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    # random forest
    if model_name == ModelName.RandomForest:
        model = RandomForestModel(
            lags=12,
            lags_past_covariates=6,
            output_chunk_length=horizons,
            random_state=42,
            n_estimators=200,
            max_depth=10,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    if model_name == ModelName.TFTModel:
        model = TFTModel(
            input_chunk_length=288,
            output_chunk_length=horizons,
            add_encoders={"cyclic": {"future": ["hour", "dayofweek"]}},
            n_epochs=15,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    # xgboost
    if model_name == ModelName.XGBoost:
        model = XGBModel(
            lags=50,
            lags_past_covariates=35,
            output_chunk_length=horizons,
            random_state=42,
            n_estimators=175,
            learning_rate=0.04,
            max_depth=4,
        )
        return _forecast(
            model, ts_target, ts_features, update_interval, buffer_size, progress
        )

    raise Exception(f"Model {model_name} not implemented")


def main():
    print(list(ModelName))


if __name__ == "__main__":
    main()
