import os
import json
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any

import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

EXTRACTION_PROMPT = """
You are reading a Pakistani electricity bill (image or PDF page).
Extract ONLY what is literally printed on the bill. Never guess or infer
a value that is not shown. If a field is not present, return null for it.

Return STRICT JSON with exactly these keys, nothing else, no markdown:

{
  "billing_period": string or null,          // e.g. "Aug26" / bill month
  "current_consumption_kwh": number or null,  // units billed this period
  "previous_consumption_kwh": number or null, // ONLY if explicitly printed as such
  "billing_days": number or null,             // ONLY if explicitly printed as such
  "electricity_cost_pkr": number or null,     // Grand Total / amount payable
  "max_demand_kw": number or null,
  "bill_power_factor": number or null,
  "meter_number": string or null,
  "due_date": string or null,

  // NEW - raw supporting fields used to DERIVE billing_days and
  // previous_consumption_kwh in code (never in the LLM) when the bill
  // doesn't print those two labels directly:
  "previous_meter_reading_date": string or null,  // format DD-MM-YY or DD-MM-YYYY as printed
  "current_meter_reading_date": string or null,
  "bill_history": [
    // rows from the "Bill History" table if present, most recent
    // completed month first (i.e. the row BEFORE the current bill month)
    {"month": string, "units": number}
  ] or null
}
"""


def _call_gemini_vision(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        [
            EXTRACTION_PROMPT,
            {"mime_type": mime_type, "data": image_bytes},
        ]
    )
    text = response.text.strip()
    # strip markdown fences if the model added them despite instructions
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.lower().startswith("json"):
            text = text.split("\n", 1)[1] if "\n" in text else text
    return json.loads(text)


def _parse_bill_date(date_str: Optional[str]) -> Optional[datetime]:
    """Bills print dates in a few common formats - try each in turn."""
    if not date_str:
        return None
    formats = ["%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y", "%d %b %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def compute_billing_days(prev_date_str: Optional[str], curr_date_str: Optional[str]) -> Optional[float]:
    """Derives billing_days from two printed meter-reading dates, never
    from an LLM-computed number (engine owns numerical truth, spec 4.3)."""
    prev = _parse_bill_date(prev_date_str)
    curr = _parse_bill_date(curr_date_str)
    if prev is None or curr is None:
        return None
    days = (curr - prev).days
    return float(days) if days > 0 else None


def get_previous_consumption(bill_history: Optional[List[Dict[str, Any]]]) -> Optional[float]:
    """Derives previous_consumption_kwh from the most recent completed
    month's units in the bill's own history table, if present."""
    if not bill_history:
        return None
    try:
        first_row = bill_history[0]
        return float(first_row["units"])
    except (KeyError, ValueError, TypeError, IndexError):
        return None


def extract_bill_fields(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """Main entry point used by backend/api/main.py's /analyze-bill route.
    Returns a dict with the fields EngineInput needs, plus fields_found /
    fields_missing for the frontend extraction panel."""

    raw = _call_gemini_vision(image_bytes, mime_type)

    result: Dict[str, Any] = {
        "billing_period": raw.get("billing_period"),
        "current_consumption_kwh": raw.get("current_consumption_kwh"),
        "electricity_cost_pkr": raw.get("electricity_cost_pkr"),
        "max_demand_kw": raw.get("max_demand_kw"),
        "bill_power_factor": raw.get("bill_power_factor"),
        "meter_number": raw.get("meter_number"),
        "due_date": raw.get("due_date"),
    }

    # billing_days - prefer an explicitly printed value; otherwise derive
    # from the two meter-reading dates.
    if raw.get("billing_days") is not None:
        result["billing_days"] = raw.get("billing_days")
    else:
        result["billing_days"] = compute_billing_days(
            raw.get("previous_meter_reading_date"),
            raw.get("current_meter_reading_date"),
        )

    # previous_consumption_kwh - prefer an explicitly printed value;
    # otherwise derive from the bill's own history table.
    if raw.get("previous_consumption_kwh") is not None:
        result["previous_consumption_kwh"] = raw.get("previous_consumption_kwh")
    else:
        result["previous_consumption_kwh"] = get_previous_consumption(raw.get("bill_history"))

    fields_found: List[str] = []
    fields_missing: List[str] = []
    for field in (
        "billing_period",
        "current_consumption_kwh",
        "previous_consumption_kwh",
        "billing_days",
        "electricity_cost_pkr",
        "max_demand_kw",
        "bill_power_factor",
        "meter_number",
        "due_date",
    ):
        if result.get(field) is not None:
            fields_found.append(field)
        else:
            fields_missing.append(field)

    result["fields_found"] = fields_found
    result["fields_missing"] = fields_missing
    return result
