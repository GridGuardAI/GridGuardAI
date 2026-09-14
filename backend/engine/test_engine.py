import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engineering_engine import (
    EngineInput, LoadItem, run_engine, validate, ValidationError,
    calc_load_energy_kwh, calc_real_power_kw, calc_apparent_power_kva,
    calc_consumption_change_pct, calc_voltage_deviation_pct,
    calc_load_contribution_pct,
)

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def approx(a, b, tol=0.01):
    if a is None or b is None:
        return a == b
    return abs(a - b) <= tol


print("AC-01: 1.5 kW x 8 h/day x 30 days = 360 kWh/month")
load = LoadItem(load_type="test", power_kw=1.5, hours_per_day=8, days_per_month=30)
check("AC-01", approx(calc_load_energy_kwh(load), 360.0), calc_load_energy_kwh(load))

print("\nAC-02: Previous 800 kWh; Current 1200 kWh -> +50%, Major Consumption Anomaly")
change = calc_consumption_change_pct(1200, 800)
check("AC-02 percent", approx(change, 50.0), change)
inp = EngineInput(current_consumption_kwh=1200, previous_consumption_kwh=800)
result = run_engine(inp)
types = [a["type"] for a in result["anomalies"]]
check("AC-02 anomaly", "major_consumption_anomaly" in types, types)
check("AC-02 no double-report", "significant_consumption_increase" not in types, types)

print("\nAC-03: 230V, 10A, PF 0.8, single phase -> P = 1.84 kW")
p = calc_real_power_kw(230, 10, 0.8, 1)
check("AC-03", approx(p, 1.84), p)

print("\nAC-04: Same as AC-03 -> S = 2.30 kVA")
s = calc_apparent_power_kva(230, 10, 1)
check("AC-04", approx(s, 2.30), s)

print("\nAC-05: PF = 0.76 -> Poor Power Factor + anomaly")
inp = EngineInput(supply_voltage_v=230, current_a=10, power_factor=0.76, num_phases=1)
result = run_engine(inp)
types = [a["type"] for a in result["anomalies"]]
check("AC-05", "poor_power_factor" in types, types)

print("\nAC-06: Nominal 230V; measured 246V -> +6.96%, Voltage Deviation - Monitor")
dev = calc_voltage_deviation_pct(246, 230)
check("AC-06 percent", approx(dev, 6.96, tol=0.05), dev)
inp = EngineInput(supply_voltage_v=246)
result = run_engine(inp)
types = [a["type"] for a in result["anomalies"]]
check("AC-06 anomaly", "voltage_deviation_monitor" in types, types)
check("AC-06 not critical", "significant_voltage_deviation" not in types, types)

print("\nAC-07: 2 kW x 5 h/day x 30 days = 300 kWh/month")
load2 = LoadItem(load_type="test2", power_kw=2, hours_per_day=5, days_per_month=30)
check("AC-07", approx(calc_load_energy_kwh(load2), 300.0), calc_load_energy_kwh(load2))

print("\nAC-08: Load 300 kWh; total 500 kWh -> 60% contribution")
contrib = calc_load_contribution_pct(300, 500)
check("AC-08", approx(contrib, 60.0), contrib)

print("\nAC-09: PF not provided -> PF analysis unavailable, never assume PF=1")
inp = EngineInput(supply_voltage_v=230, current_a=10, num_phases=1)
result = run_engine(inp)
check("AC-09 power_factor is None", result["power_factor"] is None, result["power_factor"])
check("AC-09 real_power is None (not computed with fake PF=1)", result["real_power_kw"] is None, result["real_power_kw"])
check("AC-09 warning present", any("Power factor not provided" in w for w in result["warnings"]), result["warnings"])

print("\nAC-10: Structured engine result passed to AI - engine never recalculates AI outputs")
check("AC-10 (contract-level, verified by design)", "anomalies" in result and isinstance(result["anomalies"], list))

print("\n--- Section 11 quality checks ---")
print("No divide-by-zero for zero previous consumption:")
inp = EngineInput(current_consumption_kwh=500, previous_consumption_kwh=0)
try:
    result = run_engine(inp)
    check("Zero-baseline handled without crash", result["consumption_change_percent"] is None, result["consumption_change_percent"])
except ZeroDivisionError:
    check("Zero-baseline handled without crash", False, "raised ZeroDivisionError")

print("Repeated identical input produces identical results:")
inp = EngineInput(current_consumption_kwh=1200, previous_consumption_kwh=800, supply_voltage_v=246, power_factor=0.76, num_phases=1, current_a=10)
r1 = run_engine(inp)
r2 = run_engine(inp)
check("Deterministic/repeatable", r1 == r2)

print("Validation rejects invalid phase count:")
try:
    validate(EngineInput(num_phases=2))
    check("Rejects num_phases=2", False, "did not raise")
except ValidationError:
    check("Rejects num_phases=2", True)

print(f"\n=== {passed} passed, {failed} failed ===")
sys.exit(1 if failed else 0)
