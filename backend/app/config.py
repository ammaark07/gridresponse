"""Application configuration loaded from environment / .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend root if present.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT / ".env")

# Filesystem locations.
DB_PATH = BACKEND_ROOT / "gridresponse.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

ML_ARTIFACT_DIR = BACKEND_ROOT / "app" / "ml" / "artifacts"

# LLM settings.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# CORS origins for the Vite dev server.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
