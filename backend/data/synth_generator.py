"""Synthetic data generator for GridResponse.

Produces plausible storm-outage incidents and crews around the Greater Toronto
Area, with realistic correlations:

* Severe weather and downed equipment drive longer restoration times.
* Rural incidents and high customer counts raise priority.

Each generated incident also carries *latent* ground-truth labels
(``restoration_minutes`` and ``priority``) that are used only for ML training.
``seed.py`` persists just the observable columns; ``train.py`` consumes the
labels.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import TypedDict

# Greater Toronto Area bounding box (rough).
GTA_LAT_MIN, GTA_LAT_MAX = 43.45, 44.05
GTA_LNG_MIN, GTA_LNG_MAX = -79.85, -79.10

CAUSES = ["tree", "equipment", "weather", "vehicle", "animal", "unknown"]

# Base restoration minutes by cause (downed equipment is the slowest).
CAUSE_BASE_MINUTES = {
    "equipment": 220,
    "weather": 180,
    "tree": 150,
    "vehicle": 110,
    "animal": 75,
    "unknown": 130,
}

# Crew base depots scattered across the GTA.
CREW_DEPOTS = [
    ("Downtown", 43.6532, -79.3832),
    ("Scarborough", 43.7731, -79.2578),
    ("North York", 43.7615, -79.4111),
    ("Etobicoke", 43.6205, -79.5132),
    ("Mississauga", 43.5890, -79.6441),
    ("Brampton", 43.7315, -79.7624),
    ("Markham", 43.8561, -79.3370),
    ("Vaughan", 43.8361, -79.4983),
    ("Richmond Hill", 43.8828, -79.4403),
    ("Pickering", 43.8384, -79.0868),
]


class IncidentRecord(TypedDict):
    lat: float
    lng: float
    reported_at: datetime
    cause: str
    customers_affected: int
    weather_severity: int
    is_rural: bool
    near_critical_facility: bool
    status: str
    # Latent labels (training only).
    crews_available: int
    restoration_minutes: float
    priority: str


class CrewRecord(TypedDict):
    name: str
    base_lat: float
    base_lng: float
    skill_level: int
    status: str


def _priority_from(customers: int, severity: int, near_critical: bool, is_rural: bool) -> str:
    """Derive a latent priority label from incident features."""
    score = 0.0
    score += customers / 400.0  # customer weight
    score += (severity - 1) * 0.45  # weather weight
    if near_critical:
        score += 1.2
    if is_rural:
        score += 0.6
    if score >= 2.6:
        return "critical"
    if score >= 1.6:
        return "high"
    if score >= 0.8:
        return "medium"
    return "low"


def generate_crews(seed: int = 7, n_crews: int = 15) -> list[CrewRecord]:
    rng = random.Random(seed)
    crews: list[CrewRecord] = []
    for i in range(n_crews):
        depot_name, lat, lng = CREW_DEPOTS[i % len(CREW_DEPOTS)]
        # Jitter the base location slightly around the depot.
        crews.append(
            CrewRecord(
                name=f"{depot_name} Crew {i // len(CREW_DEPOTS) + 1}",
                base_lat=round(lat + rng.uniform(-0.02, 0.02), 5),
                base_lng=round(lng + rng.uniform(-0.02, 0.02), 5),
                skill_level=rng.choice([1, 2, 2, 3]),
                status=rng.choice(["available", "available", "dispatched"]),
            )
        )
    return crews


def generate_incidents(seed: int = 42, n_incidents: int = 300) -> list[IncidentRecord]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    n_crews = 15
    available_crews = sum(
        1 for c in generate_crews() if c["status"] == "available"
    )

    incidents: list[IncidentRecord] = []
    for _ in range(n_incidents):
        cause = rng.choices(
            CAUSES, weights=[0.30, 0.22, 0.18, 0.12, 0.10, 0.08], k=1
        )[0]

        # Weather severity skews higher for weather/tree causes.
        if cause in ("weather", "tree"):
            weather_severity = rng.choices([2, 3, 4, 5], weights=[0.2, 0.3, 0.3, 0.2])[0]
        else:
            weather_severity = rng.choices([1, 2, 3, 4], weights=[0.35, 0.3, 0.2, 0.15])[0]

        is_rural = rng.random() < 0.28
        # Rural incidents tend to affect fewer customers; urban more.
        base_customers = rng.lognormvariate(4.0, 0.9)
        if is_rural:
            base_customers *= 0.5
        # Higher severity correlates with more customers affected.
        base_customers *= 1.0 + 0.18 * (weather_severity - 1)
        customers_affected = max(1, int(base_customers))

        near_critical_facility = rng.random() < 0.15

        lat = round(rng.uniform(GTA_LAT_MIN, GTA_LAT_MAX), 5)
        lng = round(rng.uniform(GTA_LNG_MIN, GTA_LNG_MAX), 5)

        reported_at = now - timedelta(minutes=rng.randint(0, 60 * 36))
        hour_of_day = reported_at.hour

        # Latent restoration time (minutes) with realistic correlations + noise.
        minutes = CAUSE_BASE_MINUTES[cause]
        minutes += (weather_severity - 1) * 35  # severe weather slows restoration
        minutes += (customers_affected / 50.0) * 4  # bigger outages take longer
        if is_rural:
            minutes += 45  # travel time
        # More available crews -> faster restoration.
        minutes -= available_crews * 4
        # Overnight work is slower.
        if hour_of_day < 6 or hour_of_day >= 22:
            minutes += 25
        minutes *= rng.uniform(0.85, 1.15)  # noise
        restoration_minutes = round(max(20.0, minutes), 1)

        priority = _priority_from(
            customers_affected, weather_severity, near_critical_facility, is_rural
        )

        incidents.append(
            IncidentRecord(
                lat=lat,
                lng=lng,
                reported_at=reported_at,
                cause=cause,
                customers_affected=customers_affected,
                weather_severity=weather_severity,
                is_rural=is_rural,
                near_critical_facility=near_critical_facility,
                status=rng.choices(
                    ["reported", "triaged", "assigned", "restored"],
                    weights=[0.5, 0.2, 0.15, 0.15],
                )[0],
                crews_available=available_crews,
                restoration_minutes=restoration_minutes,
                priority=priority,
            )
        )
    return incidents


if __name__ == "__main__":
    incs = generate_incidents()
    crews = generate_crews()
    print(f"Generated {len(incs)} incidents and {len(crews)} crews.")
    print("Sample incident:", incs[0])
    print("Sample crew:", crews[0])
