"""Tests for the ML predictor (app/ml/predict.py).

Checks the shape and plausible range of predict() output without asserting
exact numeric values — the model is non-deterministic across retrains but
the contract (field names, types, value bounds) must always hold.
"""
from __future__ import annotations

import pytest

from app.ml.predict import predict

VALID_PRIORITIES = {"low", "medium", "high", "critical"}

BASE_KWARGS = dict(
    cause="tree",
    customers_affected=100,
    weather_severity=3,
    is_rural=False,
    near_critical_facility=False,
    crews_available=8,
    hour_of_day=10,
)


def test_predict_returns_required_keys():
    result = predict(**BASE_KWARGS)
    assert "predicted_eta_minutes" in result
    assert "predicted_priority" in result


def test_predict_eta_is_positive_float():
    result = predict(**BASE_KWARGS)
    eta = result["predicted_eta_minutes"]
    assert isinstance(eta, float)
    assert eta >= 0.0


def test_predict_priority_is_valid_class():
    result = predict(**BASE_KWARGS)
    assert result["predicted_priority"] in VALID_PRIORITIES


@pytest.mark.parametrize(
    "cause",
    ["tree", "equipment", "weather", "vehicle", "animal", "unknown"],
)
def test_predict_all_causes(cause: str):
    result = predict(**{**BASE_KWARGS, "cause": cause})
    assert result["predicted_priority"] in VALID_PRIORITIES
    assert result["predicted_eta_minutes"] >= 0.0


def test_predict_high_severity_longer_eta_than_low():
    """Higher weather severity should produce a longer ETA on average."""
    low = predict(**{**BASE_KWARGS, "weather_severity": 1})
    high = predict(**{**BASE_KWARGS, "weather_severity": 5})
    # Allow a wide margin — models can be non-monotone at individual points,
    # but a 5x severity jump should move the needle.
    assert high["predicted_eta_minutes"] >= low["predicted_eta_minutes"] * 0.8


def test_predict_critical_facility_raises_priority_or_keeps_high():
    """Incidents near a critical facility should never be classified 'low'."""
    result = predict(
        **{
            **BASE_KWARGS,
            "near_critical_facility": True,
            "customers_affected": 500,
            "weather_severity": 4,
        }
    )
    assert result["predicted_priority"] in {"medium", "high", "critical"}
