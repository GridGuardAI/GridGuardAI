# GridGuard AI

**AI-Powered Electrical Fault Diagnosis & Energy Intelligence Platform**
PakAngel GenAI & Agentic AI Hackathon — Cohort 11

GridGuard AI helps users understand *why* their electricity consumption is
abnormal - not just that it is. It combines deterministic electrical
engineering calculations with a focused multi-agent AI system and
evidence-backed (RAG) recommendations, so every claim is either a
calculated fact or a sourced piece of evidence, never an unsupported guess.

> **Engineering-grade AI, not a chatbot.** Calculations are never delegated
> to an LLM. The engine computes; the AI explains.

---

## How it works (end to end)

```
User uploads bill / enters data
        │
        ▼
Extraction Layer          (reads bill photo/PDF, or accepts manual entry)
        │
        ▼
Validation                (missing data stays missing - never guessed)
        │
        ▼
Engineering Engine        (deterministic: power, PF, consumption change,
                            voltage deviation, cost - see EE-01..EE-07)
        │
        ▼
Orchestrator Agent        (routes the validated case to the right agents)
        │
        ├──► Consumption / Fault Analysis Agent  (investigates likely causes)
        │
        ├──► RAG / Evidence Agent                (retrieves cited technical evidence)
        │
        └──► Recommendation Agent                (prioritized action list)
        │
        ▼
Dashboard                 (facts, diagnosis, confidence, evidence, actions)
```

Full detail: see [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md).

---

## What's in the dashboard

- **Consumption comparison** — current vs. previous month, with % change
- **Power factor gauge** — from bill-reported PF when available
- **Cost impact** — estimated cost & additional cost, using the tariff rate
  in effect for the bill
- **Diagnosis cards** — one per detected anomaly, each with a confidence
  level (High / Medium / Low / Cannot determine) and cited evidence
- **Prioritized recommendations** — a single actionable list, ranked by
  what will move the needle most

### Tariff handling

Consumers pick their **NEPRA tariff category** (A-1 Residential, A-2
Commercial, B-1/B-2/B-3 Industrial, C-1 Agricultural, D-1 Public Lighting,
G-1 Temporary Supply) from a dropdown — this is a labeling aid only, no
rate is hard-coded against it, since NEPRA base rates and monthly Fuel
Price Adjustments change too often to bake into the app (per the
engineering principle below).

For **bill uploads**, the actual PKR/kWh rate used in cost calculations is
**derived automatically** from the bill itself — Grand Total ÷ units
consumed — and shown in a read-only field once the diagnosis completes.
This is an effective/blended rate (energy charge + FPA + taxes combined),
clearly labeled as bill-derived rather than the official NEPRA base
tariff. For manual entry (no bill uploaded), cost figures stay blank
unless a rate is available to derive from.

### A note on electrical readings (voltage / current / instantaneous PF)

The original design accepted manual voltage, current, and instantaneous
power-factor readings to feed the engine's PF (EE-03/EE-04) and voltage
deviation (EE-05/EE-06) anomaly checks directly. These fields have been
removed from the manual-entry form for a simpler, less error-prone user
experience aimed at non-technical consumers. The engine itself is
unchanged and still supports these calculations when the data is present
(see `backend/engine/test_engine.py`, AC-03 through AC-06, AC-09) — they
just aren't currently reachable through the dashboard's manual-entry path.
Bill-reported power factor (`bill_power_factor`, extracted from the bill
itself) still feeds PF screening on the bill-upload path where the bill
states it.

---

## Repository structure

```
gridguard-ai/
├── backend/              # Python/FastAPI - engineering engine + AI agents + API
│   ├── engine/            # Deterministic calculations (EE-01..EE-07) - see spec
│   ├── agents/             # Orchestrator, Fault Analysis, Recommendation agents
│   ├── rag/                 # Knowledge base + retrieval (Evidence Agent)
│   ├── extraction/          # Bill photo/PDF -> structured fields
│   ├── api/                  # FastAPI app (/analyze, /analyze-bill)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md            # Backend-specific setup
├── frontend/              # Next.js dashboard
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── README.md            # Frontend-specific setup
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── ELECTRICAL_ENGINEERING_SPEC.md   # Nadir's Phase 1 spec (source of truth)
│   └── DEMO_SCRIPT.md                     # Qasim's 3-minute demo storyline
├── .gitignore
└── README.md              # (this file)
```

---

## Quick start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY
python -m engine.test_engine  # verify: should print "19 passed, 0 failed"
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
Open http://localhost:3000 - make sure the backend is running at the same time.

---

## Team & ownership

| Member | Role | Owns |
|---|---|---|
| Nadir | Team Lead / Electrical Engineering | Architecture, calculation rules, thresholds, technical review — `docs/ELECTRICAL_ENGINEERING_SPEC.md`,  |
| Anha | AI/ML & Agentic AI | Agent workflow, orchestration, agent I/O — `backend/agents/`, `backend/api/`,`backend/engine/` |
| Asad | RAG / Web & Integration | Retrieval/citation pipeline, dashboard/backend integration — `backend/rag/`, `frontend/`,`integrations/` |
| Qasim | Presentation & Demo | Project narrative, deck, demo video — `docs/DEMO_SCRIPT.md` |

## Engineering principle (non-negotiable)

Per Nadir's spec: **the electrical engine owns numerical truth**; AI agents
interpret and explain but never recalculate or override a computed value.
Missing data stays missing (e.g. power factor is never assumed as 1).
Tariffs are never hard-coded. See `docs/ELECTRICAL_ENGINEERING_SPEC.md` and
`backend/engine/test_engine.py` (automated acceptance tests, AC-01 to AC-10)
for the enforced rules.

## Status

**MVP Complete** — bill upload and manual entry paths are both live, the
engineering engine, orchestrator, RAG evidence layer, and recommendation
agent are all wired end to end, and the dashboard is deployed.

**Known limitations / next steps:**
- Voltage deviation and instantaneous PF anomaly detection are not
  currently reachable from the manual-entry form (see note above) —
  candidate for a "advanced / electrical readings" collapsible section in
  a future pass, if reinstated.
- Tariff rate on bill uploads is a derived blended rate, not the pure
  NEPRA base tariff — sufficient for cost-impact estimates, not for
  official billing reconciliation.
- Phase 2 roadmap (per `docs/SYSTEM_ARCHITECTURE.md`): richer RAG corpus
  (real NEPRA/DISCO documents), embeddings-based retrieval, and automatic
  tariff-category-to-rate lookup once a reliable, regularly-updated source
  is identified.
