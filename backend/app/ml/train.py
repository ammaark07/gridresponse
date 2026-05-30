"""Train the GridResponse ML models on synthetic data.

Run as a module from the ``backend`` directory:

    python -m app.ml.train

Trains and persists two joblib artifacts:

* Model 1 — restoration-ETA regressor (GradientBoostingRegressor)
* Model 2 — priority classifier (GradientBoostingClassifier)

Prints held-out evaluation metrics (MAE / R2 and accuracy / macro F1).
"""
from __future__ import annotations

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.config import ML_ARTIFACT_DIR
from app.ml.features import (
    CAUSES,
    ETA_CATEGORICAL,
    ETA_FEATURES,
    ETA_MODEL_PATH,
    ETA_NUMERIC,
    PRIORITY_CATEGORICAL,
    PRIORITY_FEATURES,
    PRIORITY_MODEL_PATH,
    PRIORITY_NUMERIC,
)
from data.synth_generator import generate_incidents

RANDOM_STATE = 42


def _build_dataframe() -> pd.DataFrame:
    """Generate labeled synthetic incidents and return a tidy DataFrame."""
    records = generate_incidents(seed=RANDOM_STATE, n_incidents=1500)
    rows = []
    for r in records:
        rows.append(
            {
                "cause": r["cause"],
                "customers_affected": r["customers_affected"],
                "weather_severity": r["weather_severity"],
                "is_rural": int(r["is_rural"]),
                "near_critical_facility": int(r["near_critical_facility"]),
                "crews_available": r["crews_available"],
                "hour_of_day": r["reported_at"].hour,
                "restoration_minutes": r["restoration_minutes"],
                "priority": r["priority"],
            }
        )
    return pd.DataFrame(rows)


def _make_preprocessor(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "cause",
                OneHotEncoder(categories=[CAUSES], handle_unknown="ignore"),
                categorical,
            ),
            ("num", "passthrough", numeric),
        ]
    )


def train_eta_regressor(df: pd.DataFrame) -> Pipeline:
    X = df[ETA_FEATURES]
    y = df["restoration_minutes"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    pipeline = Pipeline(
        steps=[
            ("pre", _make_preprocessor(ETA_CATEGORICAL, ETA_NUMERIC)),
            (
                "model",
                GradientBoostingRegressor(random_state=RANDOM_STATE),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print("=== Model 1: Restoration-ETA Regressor ===")
    print(f"  Held-out MAE: {mae:.2f} minutes")
    print(f"  Held-out R2 : {r2:.3f}")
    return pipeline


def train_priority_classifier(df: pd.DataFrame) -> Pipeline:
    X = df[PRIORITY_FEATURES]
    y = df["priority"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("pre", _make_preprocessor(PRIORITY_CATEGORICAL, PRIORITY_NUMERIC)),
            (
                "model",
                GradientBoostingClassifier(random_state=RANDOM_STATE),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average="macro")
    print("=== Model 2: Priority Classifier ===")
    print(f"  Held-out accuracy: {acc:.3f}")
    print(f"  Held-out macro F1: {macro_f1:.3f}")
    return pipeline


def main() -> None:
    ML_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    df = _build_dataframe()
    print(f"Training on {len(df)} synthetic incidents.\n")

    eta_model = train_eta_regressor(df)
    print()
    priority_model = train_priority_classifier(df)

    joblib.dump(eta_model, ETA_MODEL_PATH)
    joblib.dump(priority_model, PRIORITY_MODEL_PATH)
    print(f"\nSaved artifacts to {ML_ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
