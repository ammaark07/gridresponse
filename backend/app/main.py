"""GridResponse FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routers import crews, incidents, reports
from seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Populate the database with synthetic data on startup if it is empty.
    seed_if_empty()
    yield


app = FastAPI(
    title="GridResponse API",
    description="AI-powered storm outage triage and crew-dispatch dashboard.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(crews.router)
app.include_router(reports.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
