"""Incident endpoints. Step 1 list GET + Step 2 prediction; full CRUD follows."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.predict import predict as ml_predict
from app.models import Crew, Incident
from app.schemas import IncidentOut, PredictionOut

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    db: Session = Depends(get_db),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[Incident]:
    """Return incidents ordered by most recently reported."""
    stmt = (
        select(Incident)
        .order_by(Incident.reported_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/predict", response_model=PredictionOut)
def predict_incident(incident_id: int, db: Session = Depends(get_db)) -> PredictionOut:
    """Run the ML models and persist predicted ETA + priority on the incident."""
    incident = _get_incident_or_404(db, incident_id)

    crews_available = db.scalar(
        select(func.count(Crew.id)).where(Crew.status == "available")
    ) or 0

    result = ml_predict(
        cause=incident.cause,
        customers_affected=incident.customers_affected,
        weather_severity=incident.weather_severity,
        is_rural=incident.is_rural,
        near_critical_facility=incident.near_critical_facility,
        crews_available=int(crews_available),
        hour_of_day=incident.reported_at.hour,
    )

    incident.predicted_eta_minutes = result["predicted_eta_minutes"]
    incident.predicted_priority = result["predicted_priority"]
    db.commit()

    return PredictionOut(
        predicted_eta_minutes=result["predicted_eta_minutes"],
        predicted_priority=result["predicted_priority"],
    )
