# Smart Insurance Cost Estimator

A clone of the [Smart Insurance Cost Estimator](https://smart-insurance-cost-estimator.vercel.app/) —
an AI-style health insurance premium estimator. A **Vite + React** frontend collects your personal,
lifestyle, health, and financial details through a multi-step form, and a **FastAPI** backend returns
an estimated annual premium (INR + USD), a risk category, your BMI, and tailored lifestyle suggestions.

## Project structure

```
.
├── backend/     FastAPI service (POST /api/predict, GET /, GET /health)
├── frontend/    Vite + React app (multi-step form + results)
└── README.md
```

## Backend

Requirements: Python 3.9+.

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs on <http://localhost:8000>. Interactive docs are at <http://localhost:8000/docs>.

Endpoints:

- `GET /` — service metadata.
- `GET /health` — health check (`{"status":"ok"}`).
- `POST /api/predict` — accepts a JSON body (see `PredictionRequest` in `main.py`) and returns:

```json
{
  "estimated_cost": 360000.0,
  "estimated_cost_usd": 4337.35,
  "risk_category": "HIGH",
  "suggestions": ["You're on a good track! Maintain your healthy lifestyle habits."],
  "bmi": 22.86
}
```

CORS is open (`allow_origins=["*"]`) so the frontend can call it directly from the browser.

## Frontend

Requirements: Node 18+.

```bash
cd frontend
npm install
npm run dev
```

The dev server prints a local URL (default <http://localhost:5173>).

By default the frontend talks to `http://localhost:8000`. To point it elsewhere, create a
`frontend/.env` file:

```
VITE_API_URL=http://localhost:8000
```

The frontend calls `POST ${VITE_API_URL}/api/predict`.

## Running both together

Start the backend in one terminal (`uvicorn main:app --reload`) and the frontend in another
(`npm run dev`), then open the frontend URL and complete the assessment.
