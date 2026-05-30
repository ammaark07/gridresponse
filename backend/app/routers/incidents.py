"""Incident endpoints: CRUD plus ML prediction."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.predict import predict as ml_predict
from app.models import Crew, Incident
from app.schemas import IncidentCreate, IncidentOut, IncidentUpdate, PredictionOut

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


def _available_crew_count(db: Session) -> int:
    return int(
        db.scalar(select(func.count(Crew.id)).where(Crew.status == "available")) or 0
    )


def _run_prediction(db: Session, incident: Incident, crews_available: int) -> None:
    result = ml_predict(
        cause=incident.cause,
        customers_affected=incident.customers_affected,
        weather_severity=incident.weather_severity,
        is_rural=incident.is_rural,
        near_critical_facility=incident.near_critical_facility,
        crews_available=crews_available,
        hour_of_day=incident.reported_at.hour,
    )
    incident.predicted_eta_minutes = result["predicted_eta_minutes"]
    incident.predicted_priority = result["predicted_priority"]


# ---------------------------------------------------------------------- CRUD ---
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


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    return _get_incident_or_404(db, incident_id)


@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> Incident:
    data = payload.model_dump(exclude_none=True)
    incident = Incident(**data)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db)
) -> Incident:
    incident = _get_incident_or_404(db, incident_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=204, response_class=Response)
def delete_incident(incident_id: int, db: Session = Depends(get_db)) -> Response:
    incident = _get_incident_or_404(db, incident_id)
    db.delete(incident)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------- prediction ---
@router.post("/{incident_id}/predict", response_model=PredictionOut)
def predict_incident(incident_id: int, db: Session = Depends(get_db)) -> PredictionOut:
    """Run the ML models and persist predicted ETA + priority on the incident."""
    incident = _get_incident_or_404(db, incident_id)
    _run_prediction(db, incident, _available_crew_count(db))
    db.commit()
    return PredictionOut(
        predicted_eta_minutes=incident.predicted_eta_minutes,
        predicted_priority=incident.predicted_priority,
    )


@router.post("/predict-all")
def predict_all(
    db: Session = Depends(get_db), only_missing: bool = Query(default=True)
) -> dict[str, int]:
    """Run predictions across incidents (by default only those lacking one)."""
    stmt = select(Incident)
    if only_missing:
        stmt = stmt.where(Incident.predicted_priority.is_(None))
    incidents = list(db.scalars(stmt).all())

    crews_available = _available_crew_count(db)
    for incident in incidents:
        _run_prediction(db, incident, crews_available)
    db.commit()
    return {"updated": len(incidents)}
