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
| Nadir | Team Lead / Electrical Engineering | Architecture, calculation rules, thresholds, technical review — `docs/ELECTRICAL_ENGINEERING_SPEC.md`, `backend/engine/` |
| Anha | AI/ML & Agentic AI | Agent workflow, orchestration, agent I/O — `backend/agents/`, `backend/api/` |
| Asad | RAG / Web & Integration | Retrieval/citation pipeline, dashboard/backend integration — `backend/rag/`, `frontend/` |
| Qasim | Presentation & Demo | Project narrative, deck, demo video — `docs/DEMO_SCRIPT.md` |

## Engineering principle (non-negotiable)

Per Nadir's spec: **the electrical engine owns numerical truth**; AI agents
interpret and explain but never recalculate or override a computed value.
Missing data stays missing (e.g. power factor is never assumed as 1).
Tariffs are never hard-coded. See `docs/ELECTRICAL_ENGINEERING_SPEC.md` and
`backend/engine/test_engine.py` (automated acceptance tests, AC-01 to AC-10)
for the enforced rules.

## Status
(IN Progess)
