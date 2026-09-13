"""
GridGuard AI - AI Output Quality Evaluation
Runs representative anomaly scenarios through the REAL agents (Consumption/
Fault Analysis Agent + Recommendation Agent) and checks the output against
spec rules that are about AI *behavior*, not electrical calculation
correctness (that's covered by engine/test_engine.py).

This is "evaluation of agent behavior" per the team's Phase 1 deliverable
list (Anha's ownership). Needs a real LLM_PROVIDER key configured in .env -
these are not mocked, since the whole point is checking real model output.

Usage:
    python test_ai_output_quality.py
"""

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.engineering_engine import EngineInput
from agents.orchestrator import run_full_pipeline

ALLOWED_CONFIDENCE = {"High confidence", "Medium confidence", "Low confidence", "Cannot determine"}

# Phrases that would violate spec section 4.6 / 6 ("do not automatically
# claim a financial penalty applies", "should not state a fault is
# DEFINITELY X without validated supporting measurements")
OVERCONFIDENT_PHRASES = [
    "definitely caused by", "certainly caused by", "is definitely",
    "guaranteed to", "will certainly", "without a doubt",
]
UNVERIFIED_PENALTY_PHRASES = [
    "will be charged a penalty", "you will be fined", "penalty applies",
    "you will be surcharged",
]

results = []


def record(case_name, check_name, passed, detail=""):
    results.append({"case": case_name, "check": check_name, "passed": passed, "detail": detail})
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {check_name}" + (f" - {detail}" if detail and not passed else ""))


def check_confidence_language(case_name, diagnosis_items):
    for item in diagnosis_items:
        ok = item["confidence"] in ALLOWED_CONFIDENCE
        record(case_name, f"confidence language valid ({item['type']})", ok,
               f"got '{item['confidence']}'")


def check_no_overconfident_claims(case_name, diagnosis_items):
    for item in diagnosis_items:
        text = item["explanation"].lower()
        found = [p for p in OVERCONFIDENT_PHRASES if p in text]
        record(case_name, f"no overconfident phrasing ({item['type']})", len(found) == 0,
               f"found: {found}")


def check_no_unverified_penalty_claims(case_name, recommendations_text):
    text = recommendations_text.lower()
    found = [p for p in UNVERIFIED_PENALTY_PHRASES if p in text]
    record(case_name, "no unverified penalty claims in recommendations", len(found) == 0,
           f"found: {found}")


def check_explanation_length(case_name, diagnosis_items, max_words=60):
    for item in diagnosis_items:
        word_count = len(item["explanation"].split())
        ok = 3 <= word_count <= max_words
        record(case_name, f"explanation length reasonable ({item['type']})", ok,
               f"{word_count} words")


def check_recommendations_nonempty(case_name, recommendations_text):
    ok = len(recommendations_text.strip()) > 10
    record(case_name, "recommendations non-empty", ok)


def check_evidence_present_when_confident(case_name, diagnosis_items):
    """If confidence is High or Medium, there should generally be supporting
    evidence attached (spec 6: confidence should track evidence strength)."""
    for item in diagnosis_items:
        if item["confidence"] in ("High confidence", "Medium confidence"):
            ok = len(item["evidence"]) > 0
            record(case_name, f"evidence backs confidence ({item['type']})", ok,
                   "no evidence retrieved but confidence is Medium/High")


def check_numbers_traceable(case_name, diagnosis_items):
    """Loose check: numbers mentioned in the explanation should roughly
    include the anomaly's own triggering value somewhere (sanity check
    against wholesale invention of unrelated figures). Not exhaustive -
    LLMs may reasonably round or restate; this just flags wildly absent
    grounding for manual review rather than hard-failing."""
    for item in diagnosis_items:
        if item["value"] is None:
            continue
        explanation_numbers = re.findall(r"\d+\.?\d*", item["explanation"])
        explanation_numbers = [float(n) for n in explanation_numbers]
        target = abs(item["value"])
        close_enough = any(abs(n - target) < max(1.0, target * 0.05) for n in explanation_numbers)
        record(case_name, f"triggering value referenced in explanation ({item['type']})",
               close_enough, f"target~{target}, found in text: {explanation_numbers}")


def run_case(case_name, inp: EngineInput):
    print(f"\n=== {case_name} ===")
    report = run_full_pipeline(inp)
    diagnosis = report["diagnosis"]
    recommendations = report["recommendations"]

    if not diagnosis:
        print("  (no anomalies - skipping AI-output checks, nothing to evaluate)")
        return

    check_confidence_language(case_name, diagnosis)
    check_no_overconfident_claims(case_name, diagnosis)
    check_explanation_length(case_name, diagnosis)
    check_evidence_present_when_confident(case_name, diagnosis)
    check_numbers_traceable(case_name, diagnosis)
    check_no_unverified_penalty_claims(case_name, recommendations)
    check_recommendations_nonempty(case_name, recommendations)


if __name__ == "__main__":
    # Case A: critical power factor only
    run_case("Critical Power Factor (PF=0.76)", EngineInput(
        supply_voltage_v=230, current_a=10, power_factor=0.76, num_phases=1,
    ))

    # Case B: critical consumption anomaly only
    run_case("Critical Consumption Anomaly (+70%)", EngineInput(
        current_consumption_kwh=850, previous_consumption_kwh=500, billing_days=30,
    ))

    # Case C: warning-tier voltage deviation only
    run_case("Voltage Deviation Warning (+6.96%)", EngineInput(
        supply_voltage_v=246,
    ))

    # Case D: multiple simultaneous anomalies (the "demo" scenario)
    run_case("Multiple Critical Anomalies (demo scenario)", EngineInput(
        current_consumption_kwh=1250, previous_consumption_kwh=850, billing_days=30,
        supply_voltage_v=246, current_a=10, power_factor=0.76, num_phases=1,
        tariff_pkr_per_kwh=45.0,
    ))

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{passed}/{total} checks passed" + (f", {failed} FAILED" if failed else ""))
    if failed:
        print("\nFailed checks:")
        for r in results:
            if not r["passed"]:
                print(f"  - [{r['case']}] {r['check']}: {r['detail']}")
        print("\nNote: some checks (e.g. 'triggering value referenced') are loose "
              "heuristics meant to flag things for human review, not hard spec "
              "violations - use judgment on whether a failure here is a real problem.")

    sys.exit(1 if failed else 0)
