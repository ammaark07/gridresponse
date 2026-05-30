"""Crew endpoints: list crews and report availability."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crew
from app.schemas import CrewOut

router = APIRouter(prefix="/crews", tags=["crews"])


@router.get("", response_model=list[CrewOut])
def list_crews(db: Session = Depends(get_db)) -> list[Crew]:
    return list(db.scalars(select(Crew).order_by(Crew.name)).all())


@router.get("/availability")
def crew_availability(db: Session = Depends(get_db)) -> dict[str, int]:
    """Return counts of available vs dispatched crews."""
    rows = db.execute(
        select(Crew.status, func.count(Crew.id)).group_by(Crew.status)
    ).all()
    counts = {status: count for status, count in rows}
    available = counts.get("available", 0)
    dispatched = counts.get("dispatched", 0)
    return {
        "available": available,
        "dispatched": dispatched,
        "total": available + dispatched,
    }
