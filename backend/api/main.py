"""
GridGuard AI - Backend API
Implements the two input paths from spec section 2 / board deck slide 4
("Bill uploads or manual entry"):
    POST /analyze        - manual entry (JSON body, any subset of fields)
    POST /analyze-bill    - bill photo/PDF upload (extracted, then analyzed)
    GET  /health          - health check

Run locally:
    pip install -r requirements.txt
    uvicorn api.main:app --reload --port 8000
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.engineering_engine import EngineInput, LoadItem, ValidationError
from agents.orchestrator import run_full_pipeline
from extraction.bill_extraction import extract_bill_fields

app = FastAPI(title="GridGuard AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class LoadItemRequest(BaseModel):
    load_type: str
    power_kw: Optional[float] = None
    hours_per_day: Optional[float] = None
    days_per_month: Optional[float] = None
    quantity: Optional[int] = 1


class AnalyzeRequest(BaseModel):
    billing_period: Optional[str] = None
    current_consumption_kwh: Optional[float] = None
    previous_consumption_kwh: Optional[float] = None
    billing_days: Optional[float] = None
    electricity_cost_pkr: Optional[float] = None
    peak_offpeak_kwh: Optional[float] = None
    max_demand_kw: Optional[float] = None
    bill_power_factor: Optional[float] = None
    meter_type: Optional[str] = None

    supply_voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    power_factor: Optional[float] = None
    num_phases: Optional[int] = None
    line_voltage_v: Optional[float] = None
    line_current_a: Optional[float] = None
    loads: List[LoadItemRequest] = []

    tariff_pkr_per_kwh: Optional[float] = None
    previous_billing_days: Optional[float] = None


def _to_engine_input(req: AnalyzeRequest) -> EngineInput:
    return EngineInput(
        billing_period=req.billing_period,
        current_consumption_kwh=req.current_consumption_kwh,
        previous_consumption_kwh=req.previous_consumption_kwh,
        billing_days=req.billing_days,
        electricity_cost_pkr=req.electricity_cost_pkr,
        peak_offpeak_kwh=req.peak_offpeak_kwh,
        max_demand_kw=req.max_demand_kw,
        bill_power_factor=req.bill_power_factor,
        meter_type=req.meter_type,
        supply_voltage_v=req.supply_voltage_v,
        current_a=req.current_a,
        power_factor=req.power_factor,
        num_phases=req.num_phases,
        line_voltage_v=req.line_voltage_v,
        line_current_a=req.line_current_a,
        loads=[LoadItem(**l.dict()) for l in req.loads],
        tariff_pkr_per_kwh=req.tariff_pkr_per_kwh,
        previous_billing_days=req.previous_billing_days,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """Manual-entry path: any subset of fields, run the full pipeline."""
    try:
        inp = _to_engine_input(request)
        report = run_full_pipeline(inp)
        return report
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze-bill")
async def analyze_bill(
    file: UploadFile = File(...),
    tariff_pkr_per_kwh: Optional[float] = Form(None),
    num_phases: Optional[int] = Form(None),
):

    content = await file.read()
    mime_type = file.content_type or "image/jpeg"

    extracted = extract_bill_fields(content, mime_type)

    derived_tariff_pkr_per_kwh = None
    if tariff_pkr_per_kwh is None:
        bill_total = extracted.get("electricity_cost_pkr")
        units = extracted.get("current_consumption_kwh")
        if bill_total is not None and units not in (None, 0):
            derived_tariff_pkr_per_kwh = round(bill_total / units, 2)

    effective_tariff = (
        tariff_pkr_per_kwh if tariff_pkr_per_kwh is not None else derived_tariff_pkr_per_kwh
    )

    inp = EngineInput(
        billing_period=extracted.get("billing_period"),
        current_consumption_kwh=extracted.get("current_consumption_kwh"),
        previous_consumption_kwh=extracted.get("previous_consumption_kwh"),
        billing_days=extracted.get("billing_days"),
        electricity_cost_pkr=extracted.get("electricity_cost_pkr"),
        max_demand_kw=extracted.get("max_demand_kw"),
        bill_power_factor=extracted.get("bill_power_factor"),
        tariff_pkr_per_kwh=effective_tariff,
        num_phases=num_phases,
    )

    try:
        report = run_full_pipeline(inp)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    report["extraction"] = {
        "fields_found": extracted.get("fields_found", []),
        "fields_missing": extracted.get("fields_missing", []),
        "meter_number": extracted.get("meter_number"),
        "due_date": extracted.get("due_date"),
        "tariff_pkr_per_kwh_used": effective_tariff,
        "tariff_source": "user_provided" if tariff_pkr_per_kwh is not None
                          else ("derived_from_bill" if derived_tariff_pkr_per_kwh is not None else None),
    }
    return report
