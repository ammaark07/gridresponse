"""Report endpoints: parse a free-text field report and attach it to an incident."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.parser import parse_report
from app.ml.predict import predict as ml_predict
from app.models import Crew, Incident, Report
from app.schemas import IncidentOut, ReportOut, ReportParseRequest

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/parse", response_model=ReportOut)
def parse_and_attach(
    payload: ReportParseRequest, db: Session = Depends(get_db)
) -> ReportOut:
    """Parse a field report, persist it, update the incident, and re-predict."""
    incident = db.get(Incident, payload.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    parsed = parse_report(payload.raw_text)

    # Persist the report.
    report = Report(
        incident_id=payload.incident_id,
        raw_text=payload.raw_text,
        parsed_json=parsed.model_dump_json(),
    )
    db.add(report)

    # Update customers_affected from the parsed estimate (only when non-zero).
    if parsed.est_customers > 0:
        incident.customers_affected = parsed.est_customers

    # Re-run ML prediction so ETA and priority reflect the new customer count.
    crews_available = int(
        db.scalar(select(func.count(Crew.id)).where(Crew.status == "available")) or 0
    )
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

    db.commit()
    db.refresh(report)
    db.refresh(incident)

    return ReportOut(
        id=report.id,
        incident_id=report.incident_id,
        raw_text=report.raw_text,
        parsed=parsed,
        created_at=report.created_at,
        incident=IncidentOut.model_validate(incident),
    )
