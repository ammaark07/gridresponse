# GridResponse

AI-powered storm outage triage and crew-dispatch dashboard — runs entirely on your local machine.

---

## Architecture

```
gridresponse/
├── backend/                   FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── main.py            App entrypoint, CORS, startup seed
│   │   ├── models.py          SQLAlchemy ORM: Incident, Crew, Assignment, Report
│   │   ├── schemas.py         Pydantic request/response schemas
│   │   ├── database.py        Engine, session factory, get_db dependency
│   │   ├── config.py          Env-var loading (.env)
│   │   ├── routers/
│   │   │   ├── incidents.py   CRUD + POST /{id}/predict + POST /predict-all
│   │   │   ├── crews.py       GET /crews, GET /crews/availability
│   │   │   └── reports.py     POST /reports/parse (LLM → update incident → re-predict)
│   │   ├── ml/
│   │   │   ├── train.py       GradientBoosting ETA regressor + priority classifier
│   │   │   ├── predict.py     Lazy-loads joblib artifacts, exposes predict()
│   │   │   └── features.py    Shared feature contract (column names, artifact paths)
│   │   └── llm/
│   │       └── parser.py      OpenAI strict-JSON parser with offline keyword fallback
│   ├── data/
│   │   └── synth_generator.py 300 GTA incidents + 15 crews with realistic correlations
│   ├── seed.py                Populates DB on startup if empty
│   └── tests/
│       ├── test_predict.py    Shape/range/contract tests for predict()
│       └── test_parser.py     Offline fallback tests for parse_report()
└── frontend/                  React + TypeScript + Vite
    └── src/
        ├── api.ts             Typed fetch client for all endpoints
        ├── App.tsx            Root: data fetch, selection state, layout
        └── components/
            ├── IncidentMap.tsx   Leaflet map, CircleMarkers colour-coded by priority
            ├── IncidentList.tsx  Sortable table with priority pills and ETA
            ├── Dashboard.tsx     Stat cards, Recharts pie (priority) + bar (cause)
            └── ReportForm.tsx    Free-text field report → parsed JSON → incident update
```

**Data flow for a field report:**
1. Crew submits free-text via `ReportForm`
2. `POST /reports/parse` runs the LLM parser (OpenAI or offline fallback)
3. `Report` is persisted; incident `customers_affected` updated to parsed estimate
4. ML `predict()` re-runs → new `predicted_eta_minutes` + `predicted_priority` persisted
5. Response carries both the parsed JSON and the updated incident
6. Frontend splices the updated incident into state — map marker recolours, table row and dashboard counts update instantly

---

## Local run

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1 — Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Add your OpenAI key — without it the parser uses offline fallback
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# Train the ML models (creates app/ml/artifacts/*.joblib)
python -m app.ml.train

# Start the API — seeds the DB automatically on first boot
uvicorn app.main:app --reload --port 8000
# Swagger UI → http://127.0.0.1:8000/docs
```

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
# App → http://localhost:5173
```

### 3 — Tests

```bash
cd backend
pytest tests/ -v
```

---

## ML evaluation metrics

Printed by `python -m app.ml.train` on a held-out 20 % split of 1 500 synthetic incidents:

<!-- Replace the placeholders below with the output from your own training run -->

```
=== Model 1: Restoration-ETA Regressor ===
  Held-out MAE: ___ minutes
  Held-out R2 : ___

=== Model 2: Priority Classifier ===
  Held-out accuracy: ___
  Held-out macro F1: ___
```

---

## Screenshots

<!-- Add screenshots here after running the app -->
