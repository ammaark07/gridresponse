"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Cause = Literal["tree", "equipment", "weather", "vehicle", "animal", "unknown"]
Status = Literal["reported", "triaged", "assigned", "restored"]
Priority = Literal["low", "medium", "high", "critical"]
SeveritySignal = Literal["low", "medium", "high"]


# ---------------------------------------------------------------- Incident ---
class IncidentBase(BaseModel):
    lat: float
    lng: float
    cause: Cause
    customers_affected: int = Field(ge=0)
    weather_severity: int = Field(ge=1, le=5)
    is_rural: bool = False
    near_critical_facility: bool = False


class IncidentCreate(IncidentBase):
    reported_at: Optional[datetime] = None
    status: Status = "reported"


class IncidentUpdate(BaseModel):
    cause: Optional[Cause] = None
    customers_affected: Optional[int] = Field(default=None, ge=0)
    weather_severity: Optional[int] = Field(default=None, ge=1, le=5)
    is_rural: Optional[bool] = None
    near_critical_facility: Optional[bool] = None
    status: Optional[Status] = None


class IncidentOut(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reported_at: datetime
    status: Status
    predicted_eta_minutes: Optional[float] = None
    predicted_priority: Optional[Priority] = None


# -------------------------------------------------------------------- Crew ---
class CrewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_lat: float
    base_lng: float
    skill_level: int
    status: Literal["available", "dispatched"]


# -------------------------------------------------------------- Prediction ---
class PredictionOut(BaseModel):
    predicted_eta_minutes: float
    predicted_priority: Priority


# ------------------------------------------------------------------ Report ---
class ReportParseRequest(BaseModel):
    incident_id: int
    raw_text: str


class ParsedReport(BaseModel):
    hazards: list[str]
    est_customers: int
    severity_signal: SeveritySignal
    access_blocked: bool


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    raw_text: str
    parsed: ParsedReport
    created_at: datetime
