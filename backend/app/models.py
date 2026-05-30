"""SQLAlchemy ORM models for GridResponse."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    # tree / equipment / weather / vehicle / animal / unknown
    cause: Mapped[str] = mapped_column(String(32), nullable=False)
    customers_affected: Mapped[int] = mapped_column(Integer, nullable=False)
    weather_severity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    is_rural: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    near_critical_facility: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # reported / triaged / assigned / restored
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="reported")
    predicted_eta_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_priority: Mapped[str | None] = mapped_column(String(16), nullable=True)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class Crew(Base):
    __tablename__ = "crews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    base_lat: Mapped[float] = mapped_column(Float, nullable=False)
    base_lng: Mapped[float] = mapped_column(Float, nullable=False)
    skill_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-3
    # available / dispatched
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="available")

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="crew", cascade="all, delete-orphan"
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    crew_id: Mapped[int] = mapped_column(ForeignKey("crews.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    incident: Mapped["Incident"] = relationship(back_populates="assignments")
    crew: Mapped["Crew"] = relationship(back_populates="assignments")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    incident: Mapped["Incident"] = relationship(back_populates="reports")
