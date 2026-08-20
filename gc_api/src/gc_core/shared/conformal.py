"""Conformal prediction logic"""

# external imports
from collections import deque
from mapie.regression import SplitConformalRegressor
import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from typing import Any


class DummyModel(RegressorMixin):
    def __init__(self):
        self.fitted_ = True

    def fit(self, X: Any, y: Any):
        return self

    def predict(self, X: pd.DataFrame):
        return np.zeros(len(X))


class SplitConformalPredictor:
    def __init__(self, buffer_size: int = 100) -> None:
        self.residual_buffer: deque[float] = deque(maxlen=buffer_size)
        self.q = None
        self.buffer_size = buffer_size

    def get_q(self):
        return self.q

    def update(self, new_residuals: list[np.float64]):
        self.residual_buffer.extend(new_residuals)

        if len(self.residual_buffer) < 100:
            return

        mapie = SplitConformalRegressor(
            DummyModel(), prefit=True, confidence_level=0.95
        )
        mapie.conformalize(
            np.zeros((len(self.residual_buffer), 1)),
            np.array(self.residual_buffer),
        )

        _, y_pis = mapie.predict_interval(np.zeros((1, 1)))
        self.q = y_pis[0, 1, 0]
