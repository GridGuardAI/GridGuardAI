# GridGuard AI — System Architecture

This document describes the implemented architecture. It follows Nadir's
initial architecture brief and Phase 1 Electrical Engineering Specification
exactly; those two documents remain the source of truth for scope and rules.

---

## 1. Layered architecture

| Layer | Responsibility | Location in repo |
|---|---|---|
| **Dashboard (Presentation)** | Bill upload, manual entry form, results display | `frontend/` |
| **API / Application Layer** | Request handling, validation entry point, orchestration trigger | `backend/api/main.py` |
| **Extraction & Normalization** | Bill OCR/vision parsing, field normalization | `backend/extraction/bill_extraction.py` |
| **Engineering Calculation Engine** | Deterministic energy/power/PF/voltage/cost calculations + EE-01..EE-07 anomaly screening | `backend/engine/engineering_engine.py` |
| **AI Orchestrator + Agents** | Routes validated data to specialist agents, combines outputs | `backend/agents/` |
| **RAG Knowledge Layer** | Retrieval + citation of technical evidence | `backend/rag/` |
| **Report Generator** | Assembles engine facts + agent diagnosis + evidence + recommendations into the API response | `backend/agents/orchestrator.py` (`run_full_pipeline`) |

**Hard boundary (never crossed):** the AI layer does not perform electrical
calculations, and the engineering engine does not generate explanatory text.
Every number in a dashboard card traces back to either the deterministic
engine (labeled "Engineering Facts") or a cited RAG source (labeled
"Evidence") — never an unattributed AI claim.

---

## 2. Data flow (implemented)

```
1. User uploads bill (image/PDF) OR fills manual entry form
        │
2. [Bill path only] extraction/bill_extraction.py reads the image via
   Gemini Vision -> raw fields (current/previous kWh, billing days, cost...)
   Fields not found on the bill are returned as null - never guessed.
        │
3. engine/engineering_engine.py: validate()
   - Range checks (PF 0-1, phases 1 or 3, hours 0-24, etc.)
   - Raises ValidationError -> API returns 400 with a clear message
   - Missing optional fields are recorded as warnings, not defaulted
        │
4. engine/engineering_engine.py: run_engine()
   - Calculates: energy (4.1), consumption change % (4.2), daily
     normalization (4.3), real/apparent power + PF (4.4/4.5), load
     contribution (4.7), cost impact (4.8), voltage deviation (4.9)
   - Applies EE-01..EE-07 anomaly rules (section 5) - stronger threshold
     wins, independent anomalies coexist
   - Returns the exact Section 8 output contract (+ a few additive fields)
        │
5. agents/orchestrator.py: run_full_pipeline()
   - For each anomaly the engine found, calls
     agents/consumption_fault_agent.py -> analyze_anomaly()
       - Retrieves RAG evidence (rag/retriever.py) relevant to that anomaly
       - Asks the LLM to explain the likely cause, constrained to the
         4-level confidence language from spec section 6
   - Calls agents/recommendation_agent.py -> generate_recommendations()
     with all diagnosed anomalies, to produce one prioritized action list
        │
6. api/main.py serializes the full report:
   { engineering, diagnosis[], recommendations, missing_data_notes,
     extraction? }
        │
7. frontend/ renders: Agent Pipeline tracker -> Engineering Facts panel
   -> Diagnosis cards (per anomaly, with confidence + evidence) ->
   Recommendations panel
```

---

## 3. Agent architecture

Matches the 4-agent design from the board roadmap and Nadir's brief (some
responsibilities consolidated for the MVP - see note below).

| Agent | Responsibility | Implementation |
|---|---|---|
| **Orchestrator Agent** | Decides which analyses run, in what order; combines structured outputs | `agents/orchestrator.py` — implemented as deterministic Python control flow, not an LLM call (routing here is a fixed sequence, not a judgment call; this saves LLM quota for steps that need it) |
| **Consumption / Fault Analysis Agent** | Investigates likely causes of each flagged anomaly, ranked by confidence | `agents/consumption_fault_agent.py` |
| **RAG / Evidence Agent** | Retrieves technical evidence + citation for each claim | `rag/retriever.py` + `rag/knowledge_base.py` |
| **Recommendation Agent** | Converts diagnosed findings into a prioritized action list | `agents/recommendation_agent.py` |

**Note on Cost & Impact:** per the Phase 1 Electrical Engineering
Specification (section 4.8), cost/impact calculation is **deterministic**
(`estimated_cost_pkr`, `additional_cost_pkr` in the engine output), not a
separate AI agent — this supersedes the earlier brief's "Cost & Impact
Agent" as a distinct AI component. The AI layer may *reference* these
numbers in recommendations but never recalculates them.

---

## 4. Engineering Engine (the "technical truth" layer)

Implements the Phase 1 Electrical Engineering Specification exactly:

- **Inputs** (spec section 2): bill fields (current/previous kWh, billing
  days, cost, PF, max demand) and/or electrical readings (voltage, current,
  PF, phases) and/or a load list (appliance power, hours/day, days/month).
  All fields optional except where the spec marks them required; missing
  fields are `null`, never defaulted.
- **Calculations** (section 4): energy, consumption change %, daily
  normalization, real/apparent power, PF, load contribution %, cost impact,
  voltage deviation %, operating-hour change %.
- **Anomaly rules EE-01 to EE-07** (section 5): consumption change,
  power factor, voltage deviation, load-model mismatch - each with a
  Warning/Critical tier; the stronger tier suppresses the weaker one.
- **Output contract** (section 8): a fixed JSON shape the AI layer consumes
  and never mutates.
- **Verified by** `backend/engine/test_engine.py` — automated tests for
  every acceptance criterion (AC-01 to AC-10) plus quality rules (no
  divide-by-zero, deterministic/repeatable output, PF never assumed as 1).

---

## 5. RAG / Evidence Layer

- Current MVP knowledge base (`rag/knowledge_base.py`) holds curated
  technical reference entries (power factor, voltage regulation,
  consumption screening, NEPRA reference) each tagged with a source label.
- Retrieval (`rag/retriever.py`) uses TF-IDF + cosine similarity - no
  external embedding API needed, works instantly, zero marginal cost.
- **Phase 2 upgrade path** (per roadmap): replace/extend with real NEPRA
  and DISCO documents, move to embeddings + a vector store for larger
  corpora, and retain page/section metadata for stronger citations.
- If no relevant evidence is found for a claim, the agent must say
  confidence is "Low" or "Cannot determine" rather than asserting anyway
  (spec section 6).

---

## 6. What's explicitly out of scope for Phase 1

Per the Electrical Engineering Specification section 12 and the MVP brief
section 14:
- Harmonic analysis, motor-fault/insulation/earth-leakage/short-circuit/
  arc-fault diagnosis, protection coordination, cable sizing, full
  load-flow analysis, transformer thermal analysis, automatic
  capacitor-bank sizing.
- Real-time IoT monitoring.
- Automatic tariff determination for every Pakistani customer category
  (tariff must be user-provided).
- A full utility billing platform.
- Diagnosing every possible electrical fault with certainty from limited
  data — confidence language must reflect actual evidence strength.

---

## 7. Traceability principle (for the dashboard)

Every piece of information shown to the user must be visibly one of:
1. **Calculated fact** (from the engine — deterministic, reproducible)
2. **AI interpretation** (labeled with a confidence level)
3. **Retrieved evidence** (labeled with its source)
4. **Assumption / limitation** (e.g. "tariff not provided", "PF unavailable")

This is enforced in the API response shape (`engineering` vs `diagnosis`
vs `missing_data_notes`) and mirrored in the frontend's card layout.
