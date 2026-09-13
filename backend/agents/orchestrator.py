"""
GridGuard AI - Orchestrator Agent
(board-deck agent #1: "directs which analyses run, and in what order")

Coordinates the full pipeline per spec section 13:
    INPUT VALIDATION -> DATA NORMALIZATION -> ENGINEERING CALCULATOR
    -> RULE-BASED ANALYSIS -> ANOMALY DETECTION -> STRUCTURED RESULTS
    -> AI DIAGNOSIS / RAG EVIDENCE / RECOMMENDATIONS -> DASHBOARD

Deliberately implemented as plain Python control flow rather than an LLM
call: orchestration here is "which steps run, in what order, given what
data is available" - a deterministic routing decision, not a creative
task. This keeps the "4 agents" story intact (this IS the Orchestrator
Agent's job per the architecture) while not spending LLM quota on a step
that doesn't need judgment.
"""

from engine.engineering_engine import EngineInput, run_engine, ValidationError
from agents.consumption_fault_agent import analyze_anomaly
from agents.recommendation_agent import generate_recommendations


def run_full_pipeline(inp: EngineInput) -> dict:
    """
    Runs engine -> per-anomaly diagnosis -> recommendations.
    Returns the full report dict for the API layer to serialize.
    Raises ValidationError if inputs are out of range (caller should
    turn this into an HTTP 400).
    """
    engineering = run_engine(inp)  # validation happens inside run_engine

    diagnosed = []
    for anomaly in engineering["anomalies"]:
        analysis = analyze_anomaly(anomaly, engineering)
        diagnosed.append({
            "type": anomaly["type"],
            "severity": anomaly["severity"],
            "value": anomaly["value"],
            "threshold": anomaly["threshold"],
            "engine_explanation": anomaly["explanation"],
            "confidence": analysis["confidence"],
            "explanation": analysis["explanation"],
            "evidence": analysis["evidence"],
        })

    recommendations = generate_recommendations(diagnosed, engineering)

    return {
        "engineering": engineering,
        "diagnosis": diagnosed,
        "recommendations": recommendations,
        "missing_data_notes": engineering.get("warnings", []),
    }
