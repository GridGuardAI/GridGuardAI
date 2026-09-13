"""
GridGuard AI - Deterministic Electrical Engineering Engine
Implements: GridGuard AI Phase 1 Electrical Engineering Specification.

This module is the "technical truth" layer (spec section 14, owned by
Electrical Engineering). It performs validation, normalization, engineering
calculations, and rule-based anomaly screening (EE-01 to EE-07). It returns
ONLY the structured output contract defined in spec section 8.

HARD RULES enforced by this file (do not violate these when editing):
  - No speculative diagnosis here. This module computes; it never explains
    "why" something happened - that's the AI agents' job (spec section 1).
  - Missing data stays missing (None), never silently defaulted
    (e.g. never assume PF=1 - spec section 3, AC-09).
  - No divide-by-zero: zero-baseline / zero-total conditions return None
    with an explicit note, not a crash or a fake number (spec 4.2, 4.7, 11).
  - Tariff is never hard-coded to one universal value (spec 4.8) - it must
    be passed in by the caller (user-provided or from an approved source).
  - Thresholds live in one place (THRESHOLDS / NOMINAL_VOLTAGE below), not
    scattered as magic numbers (spec section 11).
  - When a stronger anomaly threshold is crossed, report only the stronger
    classification, not both (spec section 5 note; see AC-02, AC-06).
"""

import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Configurable thresholds (spec sections 4.4, 4.6, 4.9, 5)
# These are MVP screening thresholds, NOT universal regulatory limits
# (spec section 4.4, 4.9, 15). Swap freely without touching logic below.
# ---------------------------------------------------------------------------

NOMINAL_VOLTAGE_V = 230.0  # single-phase nominal (phase-to-neutral), Pakistan grid assumption
NOMINAL_LINE_VOLTAGE_V = 400.0  # three-phase nominal (phase-to-phase / line voltage)
# Note: 400V is the expected LINE voltage when phase voltage is 230V (230 x sqrt(3)
# ~ 398.4V) - this is NORMAL for a healthy 3-phase system, not a deviation. Comparing
# a 3-phase line voltage against the single-phase nominal would incorrectly flag a
# ~74% "deviation" that is actually just the expected line/phase relationship.

THRESHOLDS = {
    "consumption_change_warning_pct": 20.0,   # EE-01
    "consumption_change_critical_pct": 40.0,  # EE-02
    "pf_warning": 0.90,                        # EE-03 (also 4.6 "Monitor")
    "pf_critical": 0.80,                       # EE-04 (also 4.6 "Poor")
    "pf_good": 0.95,                           # 4.6 classification only
    "voltage_dev_warning_pct": 5.0,            # EE-05
    "voltage_dev_critical_pct": 10.0,          # EE-06
    "load_model_mismatch_pct": 20.0,           # EE-07
}


# ---------------------------------------------------------------------------
# Input model (spec section 2) - every field optional except where noted;
# missing values MUST be passed as None, never guessed.
# ---------------------------------------------------------------------------

@dataclass
class LoadItem:
    """One appliance/load (spec section 2.2)."""
    load_type: str
    power_kw: Optional[float] = None
    hours_per_day: Optional[float] = None
    days_per_month: Optional[float] = None
    quantity: Optional[int] = 1


@dataclass
class EngineInput:
    # Bill inputs (spec 2.1)
    billing_period: Optional[str] = None
    current_consumption_kwh: Optional[float] = None
    previous_consumption_kwh: Optional[float] = None
    billing_days: Optional[float] = None
    electricity_cost_pkr: Optional[float] = None
    peak_offpeak_kwh: Optional[float] = None
    max_demand_kw: Optional[float] = None
    bill_power_factor: Optional[float] = None
    meter_type: Optional[str] = None

    # Electrical / load inputs (spec 2.2)
    supply_voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    power_factor: Optional[float] = None  # instantaneous PF, may differ from bill_power_factor
    num_phases: Optional[int] = None      # 1 or 3
    line_voltage_v: Optional[float] = None  # V_L for three-phase calcs
    line_current_a: Optional[float] = None  # I_L for three-phase calcs
    loads: List[LoadItem] = field(default_factory=list)

    # Tariff - MUST be user-provided (spec 4.8). None => cost fields stay None.
    tariff_pkr_per_kwh: Optional[float] = None

    previous_billing_days: Optional[float] = None
    previous_operating_hours_per_day: Optional[float] = None
    previous_operating_days_per_month: Optional[float] = None


class ValidationError(Exception):
    """Raised for out-of-range inputs (spec section 3)."""
    pass


# ---------------------------------------------------------------------------
# Section 3: Data Validation Rules
# ---------------------------------------------------------------------------

def validate(inp: EngineInput) -> List[str]:
    """Returns a list of validation warning strings. Raises ValidationError
    for hard violations (out-of-range values that make calculation unsafe)."""
    warnings: List[str] = []

    if inp.supply_voltage_v is not None and inp.supply_voltage_v <= 0:
        raise ValidationError("supply_voltage_v must be > 0 when provided")
    if inp.current_a is not None and inp.current_a < 0:
        raise ValidationError("current_a must be >= 0 when provided")
    if inp.current_consumption_kwh is not None and inp.current_consumption_kwh < 0:
        raise ValidationError("current_consumption_kwh must be >= 0")
    if inp.previous_consumption_kwh is not None and inp.previous_consumption_kwh < 0:
        raise ValidationError("previous_consumption_kwh must be >= 0")

    for pf, name in [(inp.power_factor, "power_factor"), (inp.bill_power_factor, "bill_power_factor")]:
        if pf is not None and not (0 <= pf <= 1):
            raise ValidationError(f"{name} must be between 0 and 1")

    if inp.num_phases is not None and inp.num_phases not in (1, 3):
        raise ValidationError("num_phases must be 1 or 3")

    for load in inp.loads:
        if load.hours_per_day is not None and not (0 <= load.hours_per_day <= 24):
            raise ValidationError(f"hours_per_day for '{load.load_type}' must be 0-24")
        if load.days_per_month is not None and not (0 <= load.days_per_month <= 31):
            raise ValidationError(f"days_per_month for '{load.load_type}' must be 0-31")
        if load.power_kw is not None and load.power_kw < 0:
            raise ValidationError(f"power_kw for '{load.load_type}' must be >= 0")

    if inp.power_factor is None and inp.bill_power_factor is None:
        warnings.append("Power factor not provided - PF-dependent analysis unavailable (never assumed as 1).")
    if inp.supply_voltage_v is None:
        warnings.append("Supply voltage not provided - voltage deviation analysis unavailable.")
    if inp.previous_consumption_kwh is None:
        warnings.append("Previous consumption not provided - consumption-change analysis unavailable.")
    if inp.tariff_pkr_per_kwh is None:
        warnings.append("Tariff not provided - cost impact cannot be calculated (tariff must be user-supplied).")

    return warnings


# ---------------------------------------------------------------------------
# Section 4: Core Calculation Rules
# ---------------------------------------------------------------------------

def calc_load_energy_kwh(load: LoadItem) -> Optional[float]:
    """4.1 - E_load = P_load(kW) x hours/day x days/month x quantity."""
    if load.power_kw is None or load.hours_per_day is None or load.days_per_month is None:
        return None
    qty = load.quantity if load.quantity is not None else 1
    return load.power_kw * load.hours_per_day * load.days_per_month * qty


def calc_total_estimated_energy_kwh(loads: List[LoadItem]) -> Optional[float]:
    """4.1 - E_total = sum of all load energies. None if no loads resolvable."""
    values = [calc_load_energy_kwh(l) for l in loads]
    resolvable = [v for v in values if v is not None]
    if not resolvable:
        return None
    return sum(resolvable)


def calc_consumption_change_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """4.2 - returns None for missing data OR zero-baseline (spec: 'return a
    zero-baseline condition instead of dividing by zero')."""
    if current is None or previous is None:
        return None
    if previous == 0:
        return None  # zero-baseline condition - caller should note this explicitly
    return ((current - previous) / previous) * 100


def calc_daily_consumption_kwh(monthly_kwh: Optional[float], billing_days: Optional[float]) -> Optional[float]:
    """4.3 - Daily consumption = Monthly kWh / Billing days."""
    if monthly_kwh is None or billing_days is None or billing_days == 0:
        return None
    return monthly_kwh / billing_days


def calc_real_power_kw(voltage_v: Optional[float], current_a: Optional[float],
                        pf: Optional[float], num_phases: Optional[int],
                        line_voltage_v: Optional[float] = None,
                        line_current_a: Optional[float] = None) -> Optional[float]:
    """4.4 - Single phase: P(W) = V x I x PF. Three phase: P(W) = sqrt(3) x V_L x I_L x PF.
    Phase configuration must be known before applying the formula (returns
    None if num_phases is not specified)."""
    if pf is None:
        return None
    if num_phases == 1:
        if voltage_v is None or current_a is None:
            return None
        return (voltage_v * current_a * pf) / 1000.0
    elif num_phases == 3:
        vl = line_voltage_v if line_voltage_v is not None else voltage_v
        il = line_current_a if line_current_a is not None else current_a
        if vl is None or il is None:
            return None
        return (math.sqrt(3) * vl * il * pf) / 1000.0
    return None  # phase configuration unknown


def calc_apparent_power_kva(voltage_v: Optional[float], current_a: Optional[float],
                             num_phases: Optional[int],
                             line_voltage_v: Optional[float] = None,
                             line_current_a: Optional[float] = None) -> Optional[float]:
    """4.5 - Single phase: S(VA) = V x I. Three phase: S(VA) = sqrt(3) x V_L x I_L."""
    if num_phases == 1:
        if voltage_v is None or current_a is None:
            return None
        return (voltage_v * current_a) / 1000.0
    elif num_phases == 3:
        vl = line_voltage_v if line_voltage_v is not None else voltage_v
        il = line_current_a if line_current_a is not None else current_a
        if vl is None or il is None:
            return None
        return (math.sqrt(3) * vl * il) / 1000.0
    return None


def calc_pf_from_powers(real_power_kw: Optional[float], apparent_power_kva: Optional[float]) -> Optional[float]:
    """4.5 - PF = P/S when both are available."""
    if real_power_kw is None or apparent_power_kva is None or apparent_power_kva == 0:
        return None
    return real_power_kw / apparent_power_kva


def calc_load_contribution_pct(load_energy_kwh: Optional[float], total_energy_kwh: Optional[float]) -> Optional[float]:
    """4.7 - Load contribution (%) = E_load / E_total x 100. None if total is 0/unavailable."""
    if load_energy_kwh is None or total_energy_kwh is None or total_energy_kwh == 0:
        return None
    return (load_energy_kwh / total_energy_kwh) * 100


def calc_cost_pkr(energy_kwh: Optional[float], tariff_pkr_per_kwh: Optional[float]) -> Optional[float]:
    """4.8 - Estimated cost = Energy(kWh) x tariff(PKR/kWh). Tariff must be
    user-provided; this function never substitutes a default tariff."""
    if energy_kwh is None or tariff_pkr_per_kwh is None:
        return None
    return energy_kwh * tariff_pkr_per_kwh


def calc_voltage_deviation_pct(measured_v: Optional[float], nominal_v: float = NOMINAL_VOLTAGE_V) -> Optional[float]:
    """4.9 - Voltage deviation (%) = (Measured - Nominal) / Nominal x 100."""
    if measured_v is None or nominal_v == 0:
        return None
    return ((measured_v - nominal_v) / nominal_v) * 100


def calc_operating_hour_change_pct(current_hours_month: Optional[float],
                                    previous_hours_month: Optional[float]) -> Optional[float]:
    """4.10 - Operating-hour change (%) = (Current - Previous) / Previous x 100."""
    if current_hours_month is None or previous_hours_month is None or previous_hours_month == 0:
        return None
    return ((current_hours_month - previous_hours_month) / previous_hours_month) * 100


# ---------------------------------------------------------------------------
# Section 5: Main Anomaly Rules (EE-01 to EE-07)
# ---------------------------------------------------------------------------

def _anomaly(atype, severity, value, threshold, explanation):
    return {"type": atype, "severity": severity, "value": value, "threshold": threshold, "explanation": explanation}


def evaluate_anomalies(consumption_change_pct: Optional[float],
                        power_factor: Optional[float],
                        voltage_deviation_pct: Optional[float],
                        modeled_vs_billed_mismatch_pct: Optional[float]) -> List[Dict[str, Any]]:
    """Applies EE-01 through EE-07. When a stronger threshold is crossed,
    only the stronger classification is reported (spec section 5 note)."""
    anomalies: List[Dict[str, Any]] = []

    # EE-01 / EE-02 - consumption change (stronger wins)
    if consumption_change_pct is not None:
        abs_change = abs(consumption_change_pct)
        if abs_change > THRESHOLDS["consumption_change_critical_pct"]:
            anomalies.append(_anomaly(
                "major_consumption_anomaly", "critical", consumption_change_pct,
                THRESHOLDS["consumption_change_critical_pct"],
                f"Consumption changed by {consumption_change_pct:.1f}%, exceeding the "
                f"{THRESHOLDS['consumption_change_critical_pct']:.0f}% critical threshold (EE-02).",
            ))
        elif abs_change > THRESHOLDS["consumption_change_warning_pct"]:
            anomalies.append(_anomaly(
                "significant_consumption_increase", "warning", consumption_change_pct,
                THRESHOLDS["consumption_change_warning_pct"],
                f"Consumption changed by {consumption_change_pct:.1f}%, exceeding the "
                f"{THRESHOLDS['consumption_change_warning_pct']:.0f}% warning threshold (EE-01).",
            ))

    # EE-03 / EE-04 - power factor (stronger wins)
    if power_factor is not None:
        if power_factor < THRESHOLDS["pf_critical"]:
            anomalies.append(_anomaly(
                "poor_power_factor", "critical", power_factor, THRESHOLDS["pf_critical"],
                f"Power factor is {power_factor:.2f}, below the {THRESHOLDS['pf_critical']} "
                f"critical threshold (EE-04). High-priority investigation recommended.",
            ))
        elif power_factor < THRESHOLDS["pf_warning"]:
            anomalies.append(_anomaly(
                "low_power_factor", "warning", power_factor, THRESHOLDS["pf_warning"],
                f"Power factor is {power_factor:.2f}, below the {THRESHOLDS['pf_warning']} "
                f"warning threshold (EE-03).",
            ))

    # EE-05 / EE-06 - voltage deviation (stronger wins)
    if voltage_deviation_pct is not None:
        abs_dev = abs(voltage_deviation_pct)
        if abs_dev > THRESHOLDS["voltage_dev_critical_pct"]:
            anomalies.append(_anomaly(
                "significant_voltage_deviation", "critical", voltage_deviation_pct,
                THRESHOLDS["voltage_dev_critical_pct"],
                f"Voltage deviation is {voltage_deviation_pct:.1f}%, exceeding the "
                f"{THRESHOLDS['voltage_dev_critical_pct']:.0f}% critical threshold (EE-06).",
            ))
        elif abs_dev > THRESHOLDS["voltage_dev_warning_pct"]:
            anomalies.append(_anomaly(
                "voltage_deviation_monitor", "warning", voltage_deviation_pct,
                THRESHOLDS["voltage_dev_warning_pct"],
                f"Voltage deviation is {voltage_deviation_pct:.1f}%, exceeding the "
                f"{THRESHOLDS['voltage_dev_warning_pct']:.0f}% monitor threshold (EE-05).",
            ))

    # EE-07 - load model mismatch (independent, can coexist with others)
    if modeled_vs_billed_mismatch_pct is not None:
        if modeled_vs_billed_mismatch_pct > THRESHOLDS["load_model_mismatch_pct"]:
            anomalies.append(_anomaly(
                "load_model_mismatch", "warning", modeled_vs_billed_mismatch_pct,
                THRESHOLDS["load_model_mismatch_pct"],
                f"Modeled load energy differs from billed consumption by "
                f"{modeled_vs_billed_mismatch_pct:.1f}%, exceeding the "
                f"{THRESHOLDS['load_model_mismatch_pct']:.0f}% threshold (EE-07). This may indicate "
                f"missing/incorrect load data or a data/meter mismatch - not necessarily a fault.",
            ))

    return anomalies


# ---------------------------------------------------------------------------
# Orchestration: run the full engine and produce the Section 8 output contract
# ---------------------------------------------------------------------------

def run_engine(inp: EngineInput) -> Dict[str, Any]:
    """Runs validation + all calculations + anomaly rules and returns EXACTLY
    the structure defined in spec section 8, plus a top-level 'warnings' list
    (missing-data notes) and 'major_loads'/'load_contributions_percent' filled
    in from the loads list."""

    warnings = validate(inp)  # raises ValidationError on hard violations

    # --- Consumption change (4.2) ---
    consumption_change_percent = calc_consumption_change_pct(
        inp.current_consumption_kwh, inp.previous_consumption_kwh
    )
    if (inp.previous_consumption_kwh == 0 and inp.current_consumption_kwh is not None):
        warnings.append("Previous consumption is zero - consumption change is a zero-baseline condition, not calculable as a percentage.")

    # --- Daily consumption normalization (4.3) ---
    daily_current = calc_daily_consumption_kwh(inp.current_consumption_kwh, inp.billing_days)
    daily_previous = calc_daily_consumption_kwh(
        inp.previous_consumption_kwh,
        inp.previous_billing_days if inp.previous_billing_days is not None else inp.billing_days,
    )

    # --- Real / apparent power / PF (4.4, 4.5) ---
    pf_for_power_calc = inp.power_factor if inp.power_factor is not None else inp.bill_power_factor
    real_power_kw = calc_real_power_kw(
        inp.supply_voltage_v, inp.current_a, pf_for_power_calc, inp.num_phases,
        inp.line_voltage_v, inp.line_current_a,
    )
    apparent_power_kva = calc_apparent_power_kva(
        inp.supply_voltage_v, inp.current_a, inp.num_phases,
        inp.line_voltage_v, inp.line_current_a,
    )
    derived_pf = calc_pf_from_powers(real_power_kw, apparent_power_kva)
    effective_pf = pf_for_power_calc if pf_for_power_calc is not None else derived_pf

    # --- Load energy / contributions (4.1, 4.7) ---
    total_estimated_load_kw = sum(l.power_kw for l in inp.loads if l.power_kw is not None) or None
    estimated_energy_kwh = calc_total_estimated_energy_kwh(inp.loads)

    major_loads = []
    load_contributions_percent = []
    for load in inp.loads:
        load_energy = calc_load_energy_kwh(load)
        contribution = calc_load_contribution_pct(load_energy, estimated_energy_kwh)
        major_loads.append({
            "load_type": load.load_type,
            "power_kw": load.power_kw,
            "energy_kwh": load_energy,
            "quantity": load.quantity,
        })
        load_contributions_percent.append({
            "load_type": load.load_type,
            "contribution_percent": contribution,
        })

    # --- Cost impact (4.8) ---
    estimated_cost_pkr = calc_cost_pkr(inp.current_consumption_kwh, inp.tariff_pkr_per_kwh)
    additional_kwh = None
    if inp.current_consumption_kwh is not None and inp.previous_consumption_kwh is not None:
        additional_kwh = inp.current_consumption_kwh - inp.previous_consumption_kwh
    additional_cost_pkr = calc_cost_pkr(additional_kwh, inp.tariff_pkr_per_kwh)

    # --- Voltage deviation (4.9) ---
    # For 3-phase systems, the relevant "supply voltage" reading is typically
    # the line voltage, which must be compared against the LINE nominal
    # (400V), not the single-phase nominal (230V) - otherwise a perfectly
    # healthy 3-phase system falsely reads as a huge voltage deviation.
    if inp.num_phases == 3:
        voltage_for_deviation = inp.line_voltage_v if inp.line_voltage_v is not None else inp.supply_voltage_v
        applicable_nominal = NOMINAL_LINE_VOLTAGE_V
    else:
        voltage_for_deviation = inp.supply_voltage_v
        applicable_nominal = NOMINAL_VOLTAGE_V
    voltage_deviation_pct = calc_voltage_deviation_pct(voltage_for_deviation, applicable_nominal)

    # --- Load model mismatch input for EE-07 ---
    modeled_vs_billed_mismatch_pct = None
    if estimated_energy_kwh is not None and inp.current_consumption_kwh not in (None, 0):
        modeled_vs_billed_mismatch_pct = (
            abs(estimated_energy_kwh - inp.current_consumption_kwh) / inp.current_consumption_kwh
        ) * 100

    # --- Anomaly rules (section 5) ---
    anomalies = evaluate_anomalies(
        consumption_change_percent, effective_pf, voltage_deviation_pct, modeled_vs_billed_mismatch_pct
    )

    output = {
        "consumption_change_percent": consumption_change_percent,
        "daily_consumption_previous_kwh": daily_previous,
        "daily_consumption_current_kwh": daily_current,
        "total_estimated_load_kw": total_estimated_load_kw,
        "estimated_energy_kwh": estimated_energy_kwh,
        "voltage_v": inp.supply_voltage_v,
        "current_a": inp.current_a,
        "power_factor": effective_pf,
        "real_power_kw": real_power_kw,
        "apparent_power_kva": apparent_power_kva,
        "major_loads": major_loads,
        "load_contributions_percent": load_contributions_percent,
        "estimated_cost_pkr": estimated_cost_pkr,
        "additional_cost_pkr": additional_cost_pkr,
        "anomalies": anomalies,
        # Extras beyond the strict section-8 contract, useful for the dashboard
        # and for the AI agents; safe additive fields, does not remove anything.
        "voltage_deviation_percent": voltage_deviation_pct,
        "nominal_voltage_v": applicable_nominal,
        "warnings": warnings,
    }
    return output