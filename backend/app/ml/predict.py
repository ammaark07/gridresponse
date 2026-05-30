"""Load trained ML artifacts and expose a ``predict()`` used by the API.

Models are loaded lazily and cached. If artifacts are missing, training is
triggered automatically so the API never fails purely for lack of artifacts.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TypedDict

import pandas as pd

from app.ml.features import (
    ETA_FEATURES,
    ETA_MODEL_PATH,
    PRIORITY_FEATURES,
    PRIORITY_MODEL_PATH,
)


class Prediction(TypedDict):
    predicted_eta_minutes: float
    predicted_priority: str


def _ensure_artifacts() -> None:
    if not ETA_MODEL_PATH.exists() or not PRIORITY_MODEL_PATH.exists():
        # Train on demand (also used in tests / fresh checkouts).
        from app.ml.train import main as train_main

        train_main()


@lru_cache(maxsize=1)
def _load_models() -> tuple[object, object]:
    import joblib

    _ensure_artifacts()
    eta_model = joblib.load(ETA_MODEL_PATH)
    priority_model = joblib.load(PRIORITY_MODEL_PATH)
    return eta_model, priority_model


def predict(
    *,
    cause: str,
    customers_affected: int,
    weather_severity: int,
    is_rural: bool,
    near_critical_facility: bool,
    crews_available: int,
    hour_of_day: int,
) -> Prediction:
    """Predict restoration ETA (minutes) and priority class for an incident."""
    eta_model, priority_model = _load_models()

    feature_row = {
        "cause": cause,
        "customers_affected": customers_affected,
        "weather_severity": weather_severity,
        "is_rural": int(is_rural),
        "near_critical_facility": int(near_critical_facility),
        "crews_available": crews_available,
        "hour_of_day": hour_of_day,
    }

    eta_df = pd.DataFrame([{k: feature_row[k] for k in ETA_FEATURES}])
    priority_df = pd.DataFrame([{k: feature_row[k] for k in PRIORITY_FEATURES}])

    eta = float(eta_model.predict(eta_df)[0])
    priority = str(priority_model.predict(priority_df)[0])

    return Prediction(
        predicted_eta_minutes=round(max(0.0, eta), 1),
        predicted_priority=priority,
    )
