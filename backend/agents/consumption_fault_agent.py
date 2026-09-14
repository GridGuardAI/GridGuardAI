from agents.llm_client import call_llm
from rag.retriever import retrieve_evidence


SYSTEM_PROMPT = """You are the Consumption/Fault Analysis Agent for GridGuard AI,
an electrical engineering decision-support system. You investigate WHY an
already-detected anomaly likely occurred, using the engineering facts and
technical evidence given to you. You NEVER invent or recalculate numbers -
only the numbers given to you are true.

You must not claim a fault is DEFINITELY the cause without strong supporting
data (spec rule). Use this confidence language exactly, choosing the one
that matches the evidence strength:
- "High confidence" - only if multiple independent facts strongly support it
- "Medium confidence" - if there is some supporting data
- "Low confidence" - if data is insufficient to be sure
- "Cannot determine" - if there is no real evidence either way

Respond in EXACTLY this format, nothing else:
CONFIDENCE: <High confidence|Medium confidence|Low confidence|Cannot determine>
EXPLANATION: <1-3 sentences, plain language, no jargon, reference the actual numbers>
"""


def analyze_anomaly(anomaly: dict, engineering_facts: dict) -> dict:
    """
    anomaly: one item from engine_output["anomalies"]
    engineering_facts: the full engine_output dict (for context - voltage,
        PF, consumption change, etc.)
    Returns: {"confidence": str, "explanation": str, "evidence": [{"text","source"}]}
    """
    query = f"{anomaly['type']} {anomaly['explanation']}"
    evidence = retrieve_evidence(query, top_k=2)
    evidence_text = "\n".join(f"- {e['text']} [{e['source']}]" for e in evidence)

    context_lines = []
    for key in ("consumption_change_percent", "power_factor", "voltage_v",
                "voltage_deviation_percent", "daily_consumption_current_kwh",
                "daily_consumption_previous_kwh"):
        val = engineering_facts.get(key)
        if val is not None:
            context_lines.append(f"{key}: {val}")
    context_text = "\n".join(context_lines)

    prompt = f"""Anomaly detected by the engineering engine:
Type: {anomaly['type']}
Severity: {anomaly['severity']}
Value: {anomaly['value']}  Threshold: {anomaly['threshold']}
Engine's explanation: {anomaly['explanation']}

Other engineering facts for context:
{context_text if context_text else "(none available)"}

Technical evidence retrieved (RAG):
{evidence_text if evidence else "(no matching evidence found)"}

Investigate the likely cause of this anomaly."""

    raw = call_llm(prompt, system=SYSTEM_PROMPT, max_tokens=200).strip()
    confidence, explanation = _parse(raw)

    return {
        "confidence": confidence,
        "explanation": explanation,
        "evidence": evidence,
    }


def _parse(text: str) -> tuple:
    confidence = "Low confidence"
    explanation = text.strip()
    if "EXPLANATION:" in text:
        parts = text.split("EXPLANATION:", 1)
        conf_part = parts[0].replace("CONFIDENCE:", "").strip()
        explanation = parts[1].strip()
        for label in ("High confidence", "Medium confidence", "Low confidence", "Cannot determine"):
            if label.lower() in conf_part.lower():
                confidence = label
                break
    return confidence, explanation
