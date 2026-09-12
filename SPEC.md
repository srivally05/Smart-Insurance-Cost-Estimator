# Smart Insurance Cost Estimator — Reverse-Engineered Spec

A clone of https://smart-insurance-cost-estimator.vercel.app/ (Vite+React frontend, FastAPI ML backend).

## Architecture
- `frontend/` — Vite + React (JS, no TS). Talks to backend via `POST {VITE_API_URL}/api/predict`.
- `backend/` — FastAPI. Endpoint `POST /api/predict`, plus `GET /` and `GET /health`.
- Design: dark theme, teal accent. Fonts: "Instrument Serif" (headings), "DM Sans" (body).

## Color tokens (CSS :root)
```
--bg-primary:#0f1419; --bg-secondary:#1a2332; --bg-card:#1e2a3a;
--accent:#00d4aa; --accent-dim:#00a884;
--text-primary:#f0f4f8; --text-secondary:#94a3b8; --border:#2d3a4d;
--risk-low:#22c55e; --risk-medium:#eab308; --risk-high:#ef4444;
```
Body font: `DM Sans, system-ui, sans-serif`. Headings/titles: `"Instrument Serif", Georgia, serif`.

## Screens

### 1. Landing (`.landing`)
- Radial teal glow background: `radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,212,170,.15), transparent), var(--bg-primary)`
- Title (`.landing-title`, Instrument Serif, 2.5rem): "Smart Insurance Cost Estimator"
- Subtitle (`.landing-subtitle`): "Get an AI-powered estimate of your health insurance premium based on your personal details, lifestyle, health conditions, and financial profile."
- CTA button (`.landing-cta`): "Start Health Insurance Assessment"
- Features row (`.landing-features`): "✓ ML-powered prediction", "✓ Risk assessment", "✓ Lifestyle suggestions"

### 2. Multi-step form (`.app-form`) — 4 steps with step-indicator dots (active = teal)
Header title (Instrument Serif): "Health Insurance Assessment". Step dots numbered 1–4.

**Step 1 — "Personal Information"**
- Age: number input, min 18 max 100, placeholder "24"
- Gender: select — options: "" Select, male "Male", female "Female"
- Height (cm): number, min 100 max 250, placeholder "170"
- Weight (kg): number, placeholder e.g. "70"

**Step 2 — "Lifestyle Habits"**
- Do you smoke?: select no "No" / yes "Yes"
- Do you drink alcohol?: select never "Never" / occasionally "Occasionally" / often "Often"
- How often do you exercise?: select none "None" / weekly "Weekly" / daily "Daily"
- What type of diet do you follow?: select veg "Veg" / non-veg "Non-veg" / mixed "Mixed"

**Step 3 — "Health Conditions"**
- Do you have diabetes?: select no "No" / yes "Yes"
- Do you have heart problems?: select no "No" / yes "Yes"
- Do you have chronic disease?: select no "No" / yes "Yes"

**Step 4 — "Financial Information"**
- Marital Status: select single "Single" / married "Married" / divorced "Divorced" / widowed "Widowed"
- Number of Dependents: number, min 0 max 20, placeholder "2"
- Annual Income (₹): number, min 0, placeholder "800000"
- Savings (₹): number, min 0, placeholder "200000"

**Form actions** (`.form-actions`): "Back" (secondary, disabled on step 1) + "Next" (primary). On last step, primary button says "Get Estimate" (shows "Calculating..." while loading, disabled during request).
- Validation errors shown in `.form-error`. e.g. "Please enter a valid height (cm)", "Please enter a valid weight (kg)", "Please enter valid income and savings".

### 3. Results (`.results` / `.results-card`)
- Title (Instrument Serif): "Your Insurance Estimate"
- Cost block (`.results-cost`): label "Estimated Insurance Cost", value `.cost-value` = `₹{Math.round(estimated_cost).toLocaleString("en-IN")}/year`
- Risk block (`.results-risk risk-{low|medium|high}`): label "Risk Category", value = risk_category (e.g. HIGH). Class from `(risk_category||"medium").toLowerCase()`.
- BMI line (`.results-bmi`): "Your BMI: {bmi.toFixed(1)}" (only if bmi is a valid number)
- Suggestions (`.results-suggestions`): h3 "Suggestions", `<ul>` with each suggestion as `<li>` (✔ bullet via CSS `li:before`)
- Reset button (`.btn btn-primary results-reset`): "Start New Assessment"

## Backend API

`POST /api/predict` — Content-Type: application/json.

### Request schema (PredictionRequest)
```
age: int (18..100)                     required
gender: str ^(male|female|Male|Female)$ required
height: float (0 < h <= 250) cm        required
weight: float (0 < w <= 300) kg        required
marital_status: str|null = "single"    optional
dependents: int (0..20)                required
smoker: str ^(yes|no|Yes|No)$          required
alcohol: str ^(never|occasionally|often)$ required
exercise: str ^(none|weekly|daily)$    required
diet: str ^(veg|non-veg|mixed)$        required
diabetes: str ^(yes|no|Yes|No)$        required
heart_problems: str|null = "no"        optional
chronic_disease: str|null = "no"       optional
income: int (>=0)                      required
savings: int (>=0)                     required
```
Invalid → 422 with FastAPI validation error body.

### Response
```json
{
  "estimated_cost": 359144.94,      // INR/year (float)
  "estimated_cost_usd": 4327.05,    // = estimated_cost / 83.0, rounded 2dp
  "risk_category": "LOW|MEDIUM|HIGH",
  "suggestions": ["...", "..."],
  "bmi": 22.86                       // weight / (height_m^2), rounded 2dp
}
```

### Real sample responses (must match closely)
- healthy young (25/male/175/70/no/never/daily/veg/no/no/no/inc50000/sav10000) →
  `estimated_cost≈359144.94, usd≈4327.05, risk HIGH, bmi 22.86, suggestions:["You're on a good track! Maintain your healthy lifestyle habits."]`
- high risk (60/female/160/110/married/3/smoker yes/alcohol often/exercise none/non-veg/diabetes yes/heart yes/chronic yes/inc30000/sav2000) →
  `estimated_cost≈4070139.19, usd≈49037.82, risk HIGH, bmi 42.97`, suggestions include smoking / obesity / exercise / alcohol / diet / diabetes lines.
- medium (45/male/170/85/married/2/no/occasionally/weekly/mixed/no/no/no/inc60000/sav15000) →
  `estimated_cost≈1618395.49, usd≈19498.74, risk HIGH, bmi 29.41`, suggestions: BMI slightly elevated + moderate alcohol.

### Suggestion rules (reverse-engineered, generate a list)
- smoker=yes → "Smoking significantly increases insurance costs. Consider quitting to reduce premiums."
- BMI >= 30 → "Your BMI indicates obesity. Regular exercise and a balanced diet can help reduce health risks."
- BMI 25–29.9 → "Your BMI is slightly elevated. Consider increasing physical activity to reach a healthier range."
- exercise=none → "Start with 30 minutes of walking daily. Regular exercise can lower insurance costs."
- alcohol=often → "Reducing alcohol intake can improve your health profile and potentially lower premiums."
- alcohol=occasionally → "Moderate alcohol consumption is fine. Keep it in check."
- diet=non-veg → "Consider a balanced mixed or plant-based diet for better cardiovascular health."
- diabetes=yes → "Manage diabetes with regular check-ups and medication adherence. This helps control long-term costs."
- (heart_problems=yes) → "Consult a cardiologist regularly and follow prescribed treatment to manage heart health."
- If NO risk factors → ["You're on a good track! Maintain your healthy lifestyle habits."]

### Cost model (heuristic replicating ML output magnitude — INR/year)
Base ≈ 150000. Multiplicative/additive factors that reproduce the samples' order of magnitude:
- age factor: base grows with age (e.g. ×(1 + (age-25)*0.03))
- smoker=yes: ×2.0
- BMI: >=30 ×1.6, 25–30 ×1.25
- diabetes=yes ×1.5, heart_problems=yes ×1.6, chronic_disease=yes ×1.5
- exercise none ×1.2, daily ×0.9
- alcohol often ×1.3, occasionally ×1.1
- diet non-veg ×1.1
- dependents: + dependents small factor
- gender minor factor
Tune constants so healthy-young ≈ 360k, medium ≈ 1.6M, high-risk ≈ 4M. Exact match to ML not required; same shape & risk/suggestion logic required. USD = cost/83, rounded 2dp. Risk: compute a risk score from factors → LOW/MEDIUM/HIGH thresholds.

## Deliverables
- `frontend/` runnable with `npm install && npm run dev` (Vite). Reads `VITE_API_URL` (default `http://localhost:8000`).
- `backend/` runnable with `pip install -r requirements.txt && uvicorn main:app --reload` (port 8000). CORS open.
- Root `README.md` with run instructions.
