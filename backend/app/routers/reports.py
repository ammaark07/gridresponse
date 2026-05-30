"""Report endpoints: parse a free-text field report and attach it to an incident."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.llm.parser import parse_report
from app.models import Incident, Report
from app.schemas import ReportOut, ReportParseRequest

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/parse", response_model=ReportOut)
def parse_and_attach(
    payload: ReportParseRequest, db: Session = Depends(get_db)
) -> ReportOut:
    """Run the LLM parser on the report text and store it against an incident."""
    incident = db.get(Incident, payload.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    parsed = parse_report(payload.raw_text)

    report = Report(
        incident_id=payload.incident_id,
        raw_text=payload.raw_text,
        parsed_json=parsed.model_dump_json(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportOut(
        id=report.id,
        incident_id=report.incident_id,
        raw_text=report.raw_text,
        parsed=parsed,
        created_at=report.created_at,
    )
