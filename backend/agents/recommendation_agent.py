from agents.llm_client import call_llm

SYSTEM_PROMPT = """You are the Recommendation Agent for GridGuard AI. Given a
list of diagnosed electrical anomalies (with severity and confidence),
produce prioritized, actionable recommendations for the user.

Rules:
- Order by severity (critical first), then by confidence.
- Each recommendation: one short action line (under 20 words).
- Do NOT state that a financial penalty definitely applies unless the input
  explicitly confirms tariff/customer applicability - use cautious language
  like "may be subject to" if uncertain.
- Do not invent numbers - only reference values given to you.

Respond as a plain bullet list, one recommendation per line, starting with "- ".
Maximum 5 bullets total."""


def generate_recommendations(diagnosed_anomalies: list, engineering_facts: dict) -> str:
    """
    diagnosed_anomalies: list of dicts, each merging an anomaly with its
        analysis, e.g. {"type", "severity", "confidence", "explanation"}
    engineering_facts: full engine output (for cost figures etc.)
    Returns a plain-text bullet list (string).
    """
    if not diagnosed_anomalies:
        return "- No anomalies detected under current MVP screening rules. No action needed at this time."

    lines = []
    for a in diagnosed_anomalies:
        lines.append(f"- [{a['severity'].upper()}] {a['type']}: {a.get('explanation', '')} "
                      f"(confidence: {a.get('confidence', 'Low confidence')})")
    findings_text = "\n".join(lines)

    cost_line = ""
    if engineering_facts.get("estimated_cost_pkr") is not None:
        cost_line = f"Estimated cost: {engineering_facts['estimated_cost_pkr']:.0f} PKR"
        if engineering_facts.get("additional_cost_pkr") is not None:
            cost_line += f" (additional vs previous: {engineering_facts['additional_cost_pkr']:.0f} PKR)"

    prompt = f"""Diagnosed anomalies for this report:
{findings_text}

{cost_line}

Produce the prioritized recommendation list."""

    return call_llm(prompt, system=SYSTEM_PROMPT, max_tokens=300).strip()
