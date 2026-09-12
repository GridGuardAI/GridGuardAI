# GridGuard AI — Phase 1 Electrical Engineering Specification

**Owner: Nadir (Team Lead / Electrical Engineering).** This is the source of
truth for the deterministic engineering layer. If anything in the code
(`backend/engine/engineering_engine.py`) ever appears to contradict this
document, this document wins — flag it to Nadir rather than silently
"fixing" the code to something else.

> Purpose: Define the deterministic electrical-engineering layer for Phase 1.
> The electrical engine validates inputs, performs engineering calculations,
> applies predefined screening rules, and returns structured engineering
> facts and anomalies. AI agents interpret those facts; RAG supplies
> supporting technical evidence.

## 1. System Boundary

| Layer | Responsibility | Boundary |
|---|---|---|
| Python / Electrical Engine | Validation, normalization, calculations, thresholds, anomaly rules | No speculative diagnosis |
| AI Agents | Interpret facts, investigate hypotheses, explain and prioritize | Do not replace deterministic calculations |
| RAG / Evidence | Retrieve authoritative technical evidence and citations | Does not alter calculated values |
| Dashboard | Present inputs, calculations, anomalies, evidence and recommendations | Must show missing-data limitations |

## 2. Required / Optional Inputs

### 2.1 Electricity Bill Inputs
| Parameter | Unit | Requirement / validation |
|---|---|---|
| Billing period | month/date range | Required |
| Current consumption | kWh | Required; >=0 |
| Previous consumption | kWh | Preferred; >=0 |
| Billing days | days | Preferred; 1–31 |
| Electricity cost | PKR | Preferred; >=0 |
| Peak/off-peak consumption | kWh | Optional |
| Maximum demand | kW | Optional; >=0 |
| Power factor | 0–1 | Optional; do not assume 1 if missing |
| Meter type | text | Optional |

### 2.2 Electrical / Load Inputs
| Parameter | Unit | Requirement / validation |
|---|---|---|
| Supply voltage | V RMS | >0 when supplied |
| Current | A RMS | >=0 when supplied |
| Power factor | 0–1 | 0 to 1 inclusive |
| Number of phases | 1 / 3 | Only 1 or 3 |
| Load power | W/kW | >=0 |
| Operating hours/day | h/day | 0–24 |
| Operating days/month | days | 0–31 |
| Load type | text | AC, motor, heater, pump, etc. |
| Quantity | count | >=0 integer |

## 3. Data Validation Rules
- Voltage must be >0 when provided; current must be >=0; energy must be >=0.
- Power factor must be between 0 and 1.
- Operating hours must be 0–24 h/day and operating days 0–31 days/month.
- Number of phases must be 1 or 3; load power must be >=0.
- **Missing data must remain explicitly missing.** Do not silently
  substitute PF=1 or another engineering value.
- Inconsistent load/bill data should generate a data/model mismatch flag,
  not an automatic claim that the bill or meter is faulty.

## 4. Core Calculation Rules

**4.1 Energy Consumption**
- Individual load: `E_load (kWh) = P_load (kW) × hours/day × days/month`
- Multiple loads: `E_total (kWh) = Σ[P_i × hours_i/day × days_i/month × quantity_i]`
- Example: 1.5 kW × 8 h/day × 30 days = 360 kWh/month.

**4.2 Consumption Change**
- `Consumption change (%) = [(Current − Previous) / Previous] × 100`
- If Previous = 0, percentage change is undefined; return a zero-baseline
  condition instead of dividing by zero.

**4.3 Daily Consumption Normalization**
- `Daily consumption = Monthly kWh / Billing days`
- Use daily consumption when billing periods have different lengths.
- Example: 900/30 = 30 kWh/day; 1,000/20 = 50 kWh/day; increase = 66.7%.

**4.4 Real Power**
- Single phase: `P(W) = V × I × PF`
- Three phase: `P(W) = √3 × V_L × I_L × PF`
- The phase configuration must be known before applying the formula.
- MVP consumption-change classification: ≤±10% Normal variation; >10-20%
  Moderate change; >20-40% Significant change/Warning; >40% Major
  consumption anomaly/high-priority investigation. These are GridGuard MVP
  screening thresholds, not regulatory limits.

**4.5 Apparent Power and PF**
- Single phase: `S(VA) = V × I`
- Three phase: `S(VA) = √3 × V_L × I_L`
- `PF = P/S` when P and S are available.

**4.6 Power Factor Screening**
| PF | Classification | MVP action |
|---|---|---|
| ≥0.95 | Good | — |
| 0.90–<0.95 | Acceptable | No PF warning |
| 0.80–<0.90 | Monitor | Low Warning |
| <0.80 | Poor | High-priority investigation |

PF <0.90 generates a low-PF engineering warning. Do not automatically claim
that a financial penalty applies; tariff/customer applicability must be
separately verified.

**4.7 Load Energy / Contribution**
- `Load energy = P(kW) × hours/day × days/month`
- `Load contribution (%) = E_load / E_total × 100`
- Example: 300 kWh / 500 kWh = 60%. If total energy is zero, contribution
  is unavailable.

**4.8 Cost Impact**
- `Estimated cost (PKR) = Energy(kWh) × applicable tariff(PKR/kWh)`
- `Additional cost = additional kWh × applicable tariff`
- **Do not hard-code one universal Pakistani tariff.** Tariff must be
  user-provided or supplied by an approved current data source, because
  applicability varies by customer category, utility, slab, TOU structure
  and adjustments.

**4.9 Voltage Deviation**
- `Voltage deviation (%) = [(Measured − Nominal) / Nominal] × 100`
| Condition | MVP classification |
|---|---|
| Within ±5% | Normal |
| >±5% to ±10% | Voltage deviation – Monitor |
| >±10% | Significant voltage deviation |

For 230V nominal: ±5% = 218.5–241.5V; ±10% = 207–253V. These are MVP
screening thresholds, not universal statutory limits.

**4.10 Operating-Hour Analysis**
- `Monthly hours = hours/day × operating days/month`
- `Operating-hour change (%) = [(Current − Previous) / Previous] × 100`
- Increased hours are evidence that may explain increased energy use; they
  are not automatically a fault.

## 5. Main Anomaly Rules

| ID | Condition | Output | Severity |
|---|---|---|---|
| EE-01 | Consumption change >20% | Significant Consumption Increase | Warning |
| EE-02 | Consumption change >40% | Major Consumption Anomaly | Critical / high-priority |
| EE-03 | PF <0.90 | Low Power Factor | Warning |
| EE-04 | PF <0.80 | Poor Power Factor | Critical / high-priority |
| EE-05 | \|Voltage deviation\| >5% | Voltage Deviation – Monitor | Warning |
| EE-06 | \|Voltage deviation\| >10% | Significant Voltage Deviation | Critical / high-priority |
| EE-07 | \|Modeled−billed\|/billed >20% | Load Model Mismatch | Warning / investigation |

When a stronger threshold is crossed, use the stronger classification
rather than reporting the same condition twice. Independent anomalies may
coexist.

## 6. Diagnosis Logic and Confidence

The deterministic engine supplies evidence; AI agents rank hypotheses.

| Evidence strength | Allowed language |
|---|---|
| Strong supporting data | High confidence / likely contributor |
| Some supporting data | Medium confidence / plausible contributor |
| Insufficient data | Low confidence / requires more information |
| No evidence | Cannot determine |

AI should not state that a fault is definitely X without validated
supporting measurements.

## 7. RAG Boundary
- Calculated facts come from the electrical engine.
- AI interpretation is labeled as interpretation/diagnosis.
- RAG supplies technical evidence and citations.
- RAG does not change the engine's numerical results.
- Potential Pakistan-focused evidence includes applicable NEPRA documents,
  electrical safety guidance and other authoritative technical documents
  permitted for use.

## 8. Engineering Output Contract
```json
{
  "consumption_change_percent": "number | null",
  "daily_consumption_previous_kwh": "number | null",
  "daily_consumption_current_kwh": "number | null",
  "total_estimated_load_kw": "number | null",
  "estimated_energy_kwh": "number | null",
  "voltage_v": "number | null",
  "current_a": "number | null",
  "power_factor": "number | null",
  "real_power_kw": "number | null",
  "apparent_power_kva": "number | null",
  "major_loads": [],
  "load_contributions_percent": [],
  "estimated_cost_pkr": "number | null",
  "additional_cost_pkr": "number | null",
  "anomalies": [
    {"type": "string", "severity": "normal|warning|critical",
     "value": "number|null", "threshold": "number|null", "explanation": "string"}
  ]
}
```

## 9. Severity Definitions
| Severity | Meaning |
|---|---|
| Normal | No significant abnormality detected by implemented rules |
| Warning | Potential issue requiring investigation |
| Critical | Large deviation or high-priority engineering condition under MVP rules |

Critical does not automatically mean an electrical safety emergency. Safety
conclusions require appropriate measurements and applicable standards.

## 10. Acceptance Criteria

| ID | Test case | Expected result |
|---|---|---|
| AC-01 | 1.5 kW × 8 h/day × 30 days | 360 kWh/month |
| AC-02 | Previous 800 kWh; Current 1,200 kWh | +50%; Major Consumption Anomaly |
| AC-03 | 230V, 10A, PF 0.8, single phase | P = 1.84 kW |
| AC-04 | Same as AC-03 | S = 2.30 kVA |
| AC-05 | PF = 0.76 | Poor Power Factor + anomaly |
| AC-06 | Nominal 230V; measured 246V | +6.96%; Voltage Deviation – Monitor |
| AC-07 | 2 kW × 5 h/day × 30 days | 300 kWh/month |
| AC-08 | Load 300 kWh; total 500 kWh | 60% contribution |
| AC-09 | PF not provided | PF analysis unavailable; never assume PF=1 |
| AC-10 | Structured engine result passed to AI | AI receives engineering facts and does not recalculate them |

**Verified automatically** — see `backend/engine/test_engine.py`, currently
19/19 passing.

## 11. Additional Acceptance / Quality Criteria
- No divide-by-zero errors for zero previous consumption or zero billed energy.
- Single-phase and three-phase formulas are tested separately.
- Units are explicit in returned data.
- Voltage threshold uses absolute deviation; consumption threshold uses the
  defined signed percentage change.
- Every anomaly includes the triggering value, threshold and explanation.
- The engine distinguishes 'not available' from 'normal'.
- Repeated identical input produces identical numerical results.
- Thresholds are configurable parameters, not scattered hard-coded constants.
- AI agents cannot overwrite deterministic electrical results.

## 12. Phase 1 Out of Scope
Harmonic analysis without waveform/THD data · Motor-fault diagnosis without
motor measurements · Insulation resistance diagnosis · Earth-leakage
diagnosis · Short-circuit diagnosis · Arc-fault diagnosis · Detailed
protection coordination · Cable sizing · Full load-flow analysis ·
Transformer thermal analysis · Automatic capacitor-bank sizing · Real-time
IoT monitoring · Automatic tariff determination for every Pakistani
customer category.

## 13. Final Electrical Logic Pipeline
```
USER / BILL → INPUT VALIDATION → DATA NORMALIZATION → ENGINEERING CALCULATOR
→ RULE-BASED ANALYSIS → ANOMALY DETECTION → STRUCTURED ENGINEERING RESULTS
→ AI DIAGNOSIS / RAG EVIDENCE / RECOMMENDATIONS → DASHBOARD
```

## 14. Team Handoff / Ownership
Electrical Engineering owns the technical truth of the deterministic layer:
inputs, formulas, validation, thresholds, anomaly rules and acceptance
tests. The AI/backend team owns orchestration, agent reasoning, RAG
retrieval, API implementation and dashboard presentation. Integration
occurs through the structured engineering output contract (section 8).

## 15. Engineering Note
This specification separates engineering calculations from AI reasoning.
MVP thresholds identified as screening thresholds are project detection
criteria, not universal regulatory limits. Where a regulatory or utility
limit is required, implementation must use the applicable current standard,
regulation, tariff or utility requirement and preserve the source/citation.
