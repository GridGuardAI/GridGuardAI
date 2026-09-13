
import json
import re
from agents.llm_client import call_llm_vision

SYSTEM_PROMPT = """You are a precise document-extraction assistant reading an
electricity bill (Pakistani utility bill, e.g. K-Electric, LESCO, IESCO, or
similar). Extract ONLY fields that are actually visible on the bill. If a
field is not present or not legible, use null - never guess or estimate.

IMPORTANT - do not confuse these two different things:
1. METER READINGS ("Present Reading" / "Previous Reading" on the meter) -
   these are large CUMULATIVE totals (e.g. 15420, 16400) that only ever go
   up over the meter's lifetime. They are NOT the monthly consumption.
2. UNITS CONSUMED / CONSUMPTION - this is the actual usage for the billing
   period, usually a much smaller number (e.g. 200-2000 kWh for a typical
   residential/small commercial bill), often explicitly labeled "Units
   Consumed" or shown in a monthly history table.

If the bill explicitly states "Units Consumed" (or equivalent) for the
current and/or previous period, use those numbers directly for
current_consumption_kwh / previous_consumption_kwh.

If the bill ONLY shows meter readings (present + previous reading) and does
NOT separately state units consumed, then CALCULATE:
    current_consumption_kwh = present_meter_reading - previous_meter_reading
and put that calculated (smaller) number in current_consumption_kwh - do
NOT put the raw meter reading there. Also report the raw readings in
present_meter_reading / previous_meter_reading so nothing is lost.

Respond with ONLY a JSON object (no markdown fences, no commentary) in
exactly this shape:
{
  "current_consumption_kwh": number or null,
  "previous_consumption_kwh": number or null,
  "present_meter_reading": number or null,
  "previous_meter_reading": number or null,
  "billing_days": number or null,
  "electricity_cost_pkr": number or null,
  "billing_period": string or null,
  "meter_number": string or null,
  "due_date": string or null,
  "max_demand_kw": number or null,
  "bill_power_factor": number or null
}"""


def extract_bill_fields(image_bytes: bytes, mime_type: str) -> dict:
    """Returns the raw extracted fields dict (see SYSTEM_PROMPT shape).
    Also includes 'fields_found' and 'fields_missing' lists for transparency
    on the dashboard (spec: 'Dashboard must show missing-data limitations')."""

    raw = call_llm_vision(
        prompt="Extract the billing fields from this electricity bill image.",
        image_bytes=image_bytes,
        mime_type=mime_type,
        system=SYSTEM_PROMPT,
        max_tokens=400,
    )

    data = _safe_parse_json(raw)
    data = _reconcile_meter_readings_vs_consumption(data)

    expected_fields = [
        "current_consumption_kwh", "previous_consumption_kwh", "billing_days",
        "electricity_cost_pkr", "billing_period", "meter_number", "due_date",
        "max_demand_kw", "bill_power_factor",
    ]
    fields_found = [f for f in expected_fields if data.get(f) is not None]
    fields_missing = [f for f in expected_fields if data.get(f) is None]

    return {
        **{f: data.get(f) for f in expected_fields},
        "fields_found": fields_found,
        "fields_missing": fields_missing,
    }


def _reconcile_meter_readings_vs_consumption(data: dict) -> dict:
    """Safety net: even with explicit prompt instructions, a vision model can
    still put a raw cumulative meter reading into current_consumption_kwh
    instead of the actual usage. If we have both meter readings AND a
    current_consumption_kwh that looks suspiciously close to the raw
    reading (rather than the reading difference), recompute it deterministically.
    This never invents data - it only corrects an internally-inconsistent
    extraction using numbers the model itself already reported."""
    present = data.get("present_meter_reading")
    previous = data.get("previous_meter_reading")
    current_consumption = data.get("current_consumption_kwh")

    if present is not None and previous is not None and present >= previous:
        computed_consumption = present - previous
        # If current_consumption_kwh is missing, or looks like it's actually
        # the raw meter reading (within 1% of `present`) rather than the
        # reading difference, use the computed value instead.
        looks_like_raw_reading = (
            current_consumption is None
            or (present != 0 and abs(current_consumption - present) / present < 0.01)
        )
        if looks_like_raw_reading:
            data["current_consumption_kwh"] = computed_consumption

        
        previous_consumption = data.get("previous_consumption_kwh")
        if (previous_consumption is not None and previous != 0
                and abs(previous_consumption - previous) / previous < 0.01):
            data["previous_consumption_kwh"] = None

    return data


def _safe_parse_json(raw: str) -> dict:
    """Gemini sometimes wraps JSON in markdown fences despite instructions -
    strip those before parsing. Returns {} on any parse failure (caller
    treats all fields as missing rather than crashing)."""
    text = raw.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}