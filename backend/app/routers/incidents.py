"""Incident endpoints. Step 1 provides a single list GET; CRUD + predict follow."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident
from app.schemas import IncidentOut

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
