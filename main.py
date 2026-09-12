"""Smart Insurance Cost Estimator — FastAPI backend.

Heuristic multiplicative cost model (INR/year) that reproduces the
order-of-magnitude of the reference ML service, plus a rule-based risk
classifier and lifestyle suggestion engine.
"""

from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Smart Insurance Cost Estimator API",
    description="AI-style health insurance premium estimator (heuristic model).",
    version="1.0.0",
)

# CORS wide open — the Vite frontend calls this from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Request schema
# --------------------------------------------------------------------------- #
class PredictionRequest(BaseModel):
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., pattern=r"^(male|female|Male|Female)$")
    height: float = Field(..., gt=0, le=250)          # cm
    weight: float = Field(..., gt=0, le=300)          # kg
    marital_status: Optional[str] = "single"
    dependents: int = Field(..., ge=0, le=20)
    smoker: str = Field(..., pattern=r"^(yes|no|Yes|No)$")
    alcohol: str = Field(..., pattern=r"^(never|occasionally|often)$")
    exercise: str = Field(..., pattern=r"^(none|weekly|daily)$")
    diet: str = Field(..., pattern=r"^(veg|non-veg|mixed)$")
    diabetes: str = Field(..., pattern=r"^(yes|no|Yes|No)$")
    heart_problems: Optional[str] = "no"
    chronic_disease: Optional[str] = "no"
    income: int = Field(..., ge=0)
    savings: int = Field(..., ge=0)


class PredictionResponse(BaseModel):
    estimated_cost: float
    estimated_cost_usd: float
    risk_category: str
    suggestions: List[str]
    bmi: float


# --------------------------------------------------------------------------- #
# Model constants (tuned so the three spec samples land in target bands)
# --------------------------------------------------------------------------- #
BASE_COST = 400000.0          # INR/year base premium
AGE_PER_YEAR = 0.05           # linear growth per year over 25
USD_RATE = 83.0


def compute_bmi(weight: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    return round(weight / (height_m ** 2), 2)


def compute_cost(req: PredictionRequest, bmi: float,
                 smoker: bool, diabetes: bool, heart: bool,
                 chronic: bool) -> float:
    """Multiplicative INR/year cost model."""
    cost = BASE_COST

    # Age — grows linearly with age above the 25-year baseline.
    cost *= 1.0 + max(req.age - 25, 0) * AGE_PER_YEAR

    # Smoking.
    if smoker:
        cost *= 1.4

    # BMI band.
    if bmi >= 30:
        cost *= 1.75
    elif bmi >= 25:
        cost *= 1.70

    # Health conditions.
    if diabetes:
        cost *= 1.10
    if heart:
        cost *= 1.10
    if chronic:
        cost *= 1.05

    # Exercise.
    exercise = req.exercise.lower()
    if exercise == "none":
        cost *= 1.05
    elif exercise == "daily":
        cost *= 0.90

    # Alcohol.
    alcohol = req.alcohol.lower()
    if alcohol == "often":
        cost *= 1.10
    elif alcohol == "occasionally":
        cost *= 1.10

    # Diet.
    if req.diet.lower() == "non-veg":
        cost *= 1.05

    # Dependents.
    cost *= 1.0 + req.dependents * 0.02

    return round(cost, 2)


def compute_risk(req: PredictionRequest, cost: float, bmi: float,
                 smoker: bool, diabetes: bool, heart: bool,
                 chronic: bool) -> str:
    """Rule-based risk score → LOW / MEDIUM / HIGH."""
    score = 0

    if smoker:
        score += 2
    if bmi >= 30:
        score += 2
    elif bmi >= 25:
        score += 1
    if diabetes:
        score += 1
    if heart:
        score += 2
    if chronic:
        score += 1
    if req.age >= 60:
        score += 2
    elif req.age >= 45:
        score += 1
    if req.exercise.lower() == "none":
        score += 1
    if req.alcohol.lower() == "often":
        score += 1

    # Financial-strain rule — a premium that dwarfs income is a heavy signal.
    if req.income > 0 and cost > req.income * 4:
        score += 5
    elif req.income == 0:
        score += 5

    if score >= 5:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"


def build_suggestions(req: PredictionRequest, bmi: float,
                      smoker: bool, diabetes: bool,
                      heart: bool) -> List[str]:
    suggestions: List[str] = []

    if smoker:
        suggestions.append(
            "Smoking significantly increases insurance costs. "
            "Consider quitting to reduce premiums."
        )

    if bmi >= 30:
        suggestions.append(
            "Your BMI indicates obesity. Regular exercise and a balanced "
            "diet can help reduce health risks."
        )
    elif bmi >= 25:
        suggestions.append(
            "Your BMI is slightly elevated. Consider increasing physical "
            "activity to reach a healthier range."
        )

    if req.exercise.lower() == "none":
        suggestions.append(
            "Start with 30 minutes of walking daily. Regular exercise can "
            "lower insurance costs."
        )

    alcohol = req.alcohol.lower()
    if alcohol == "often":
        suggestions.append(
            "Reducing alcohol intake can improve your health profile and "
            "potentially lower premiums."
        )
    elif alcohol == "occasionally":
        suggestions.append(
            "Moderate alcohol consumption is fine. Keep it in check."
        )

    if req.diet.lower() == "non-veg":
        suggestions.append(
            "Consider a balanced mixed or plant-based diet for better "
            "cardiovascular health."
        )

    if diabetes:
        suggestions.append(
            "Manage diabetes with regular check-ups and medication "
            "adherence. This helps control long-term costs."
        )

    if heart:
        suggestions.append(
            "Consult a cardiologist regularly and follow prescribed "
            "treatment to manage heart health."
        )

    if not suggestions:
        suggestions.append(
            "You're on a good track! Maintain your healthy lifestyle habits."
        )

    return suggestions


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/")
def root():
    return {
        "message": "Smart Insurance Cost Estimator API",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest) -> PredictionResponse:
    # Normalize case / handle optional None fields before any logic.
    smoker = req.smoker.lower() == "yes"
    diabetes = req.diabetes.lower() == "yes"
    heart = (req.heart_problems or "no").lower() == "yes"
    chronic = (req.chronic_disease or "no").lower() == "yes"

    bmi = compute_bmi(req.weight, req.height)
    cost = compute_cost(req, bmi, smoker, diabetes, heart, chronic)
    risk = compute_risk(req, cost, bmi, smoker, diabetes, heart, chronic)
    suggestions = build_suggestions(req, bmi, smoker, diabetes, heart)

    return PredictionResponse(
        estimated_cost=cost,
        estimated_cost_usd=round(cost / USD_RATE, 2),
        risk_category=risk,
        suggestions=suggestions,
        bmi=bmi,
    )








