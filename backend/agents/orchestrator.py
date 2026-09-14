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
