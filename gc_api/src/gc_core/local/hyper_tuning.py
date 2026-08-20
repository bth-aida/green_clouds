"""Hyperparameter tuning"""

### external imports

import numpy as np
import optuna

from darts.metrics import rmse
from darts import TimeSeries
from darts.models.forecasting.xgboost import XGBModel
from darts.models import LinearRegressionModel
from darts.models.forecasting.rnn_model import RNNModel
from darts.dataprocessing.transformers import Scaler
from optuna.trial import FixedTrial, Trial
from typing import List, cast

### internal imports
from gc_core.shared.data import load_json_df, process_df
from gc_core.shared.model_definitions import (
    ModelName,
    ts_var,
    target_var,
)
# from gc_core.shared.model_definitions import target_var


def get_trial_model(model_name: ModelName, trial: Trial | optuna.trial.FixedTrial):
    if model_name == ModelName.LinearRegression:
        return LinearRegressionModel(lags=trial.suggest_int("lags", 1, 30))
    elif model_name == ModelName.XGBoost:
        return XGBModel(
            lags=trial.suggest_int("lags", 50, 52),
            lags_past_covariates=trial.suggest_int("lags_past_covariates", 32, 37),
            n_estimators=trial.suggest_int("n_estimators", 160, 180),
            learning_rate=trial.suggest_float("learning_rate", 0.04, 0.05),
            max_depth=trial.suggest_int("max_depth", 2, 4),
            random_state=42,
        )
    elif model_name == ModelName.LSTM:
        return RNNModel(
            model="LSTM", input_chunk_length=288, training_length=2400, n_epochs=30
        )
    else:
        raise Exception(
            f"Model {model_name} is not implemented for hyperparameter tuning"
        )


def objective(
    trial: Trial | FixedTrial,
    model_name: ModelName,
    series_list: tuple[TimeSeries] | List[TimeSeries],
    past_cov_list: tuple[TimeSeries] | List[TimeSeries] | None,
    start: float | None,
    scaler_target: Scaler,
):
    model = get_trial_model(model_name, trial)

    hist_f = model.historical_forecasts(
        series=series_list,
        past_covariates=past_cov_list,
        start=start,
        forecast_horizon=1,
        train_length=2500,
        stride=1,
        retrain=100,
        last_points_only=True,
    )

    rmses = rmse(series_list, hist_f)
    return np.mean(rmses)


def print_callback(study, trial):
    print(f"Current value: {trial.value}, Current params: {trial.params}")
    print(f"Best value: {study.best_value}, Best params: {study.best_trial.params}")


def hypertune(
    model_name: ModelName, include_past_cov: bool, cutoff: float, timeout: int
):
    # load data
    # df = load_csv_dir("data_copy")
    df = load_json_df("data_copy")

    if df is None:
        return

    # process the data to correct format
    df_list = process_df(df)
    target_list: list[TimeSeries] = []
    past_covariates_list: list[TimeSeries] | None = []

    # extract data for hypervisor 1, remove last bit
    for idf, dfi in df_list:
        dfi = dfi.iloc[: int(len(dfi) * cutoff)]
        # create target time series
        dfi = dfi.dropna().reset_index(drop=True)
        ts = TimeSeries.from_dataframe(dfi, time_col=ts_var)
        target_list.append(ts[target_var])

        # create past covariates time series
        dfi = dfi.drop(columns=target_var)
        ts = TimeSeries.from_dataframe(dfi, time_col=ts_var)
        past_covariates_list.append(ts)

    # split into validation and test sets
    target_val_set, _ = list(zip(*[s.split_before(cutoff) for s in target_list]))
    past_cov_val_set, _ = list(
        zip(*[s.split_before(cutoff) for s in past_covariates_list])
    )

    # scale the data
    scaler_target = Scaler()
    scaler_pastcov = Scaler()

    target_val_scaled = cast(
        List[TimeSeries], scaler_target.fit_transform(target_val_set)
    )
    past_cov_val_scaled = cast(
        List[TimeSeries], scaler_pastcov.fit_transform(past_cov_val_set)
    )
    target_list_scaled = cast(
        List[TimeSeries], scaler_target.fit_transform(target_list)
    )
    past_cov_list_scaled = cast(
        List[TimeSeries], scaler_pastcov.fit_transform(past_cov_val_set)
    )

    if not include_past_cov:
        past_cov_list_scaled = None
        past_cov_val_scaled = None

    # run hyperparameter tuning
    study = optuna.create_study(direction="minimize")
    study.optimize(
        lambda trial: objective(
            trial, model_name, target_val_scaled, past_cov_val_scaled, None
        ),  # type: ignore
        timeout=timeout,
        callbacks=[print_callback],
    )
    print(f"Best value: {study.best_value}, Best params: {study.best_trial.params}")

    # test the result on the test set
    best_model_val_res = objective(
        optuna.trial.FixedTrial(study.best_params),
        model_name,
        target_list_scaled,
        past_cov_list_scaled,
        cutoff,
        scaler_target,
    )
    print("bmvl", best_model_val_res)


def main():
    hypertune(ModelName.LSTM, False, 0.5, 20)


if __name__ == "__main__":
    main()
