"""Shared feature definitions for the ML models.

Keeping the feature contract in one place ensures ``train.py`` and
``predict.py`` agree on column names and ordering.
"""
from __future__ import annotations

from pathlib import Path

from app.config import ML_ARTIFACT_DIR

CAUSES = ["tree", "equipment", "weather", "vehicle", "animal", "unknown"]
PRIORITY_CLASSES = ["low", "medium", "high", "critical"]

# Feature columns per model (order matters for the DataFrames we build).
ETA_NUMERIC = ["customers_affected", "weather_severity", "is_rural", "crews_available", "hour_of_day"]
ETA_CATEGORICAL = ["cause"]
ETA_FEATURES = ETA_CATEGORICAL + ETA_NUMERIC

PRIORITY_NUMERIC = ["customers_affected", "weather_severity", "near_critical_facility"]
PRIORITY_CATEGORICAL = ["cause"]
PRIORITY_FEATURES = PRIORITY_CATEGORICAL + PRIORITY_NUMERIC

# Artifact paths.
ETA_MODEL_PATH: Path = ML_ARTIFACT_DIR / "eta_regressor.joblib"
PRIORITY_MODEL_PATH: Path = ML_ARTIFACT_DIR / "priority_classifier.joblib"
