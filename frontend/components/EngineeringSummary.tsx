"use client";

import { EngineeringFacts } from "@/lib/api";
import ConsumptionChart from "./ConsumptionChart";
import PowerFactorGauge from "./PowerFactorGauge";
import VoltageDeviationMeter from "./VoltageDeviationMeter";

function Stat({ label, value, unit }: { label: string; value: string | number | null; unit?: string }) {
  return (
    <div>
      <div className="mono text-[10px] text-[var(--muted)] mb-1 tracking-wide">{label}</div>
      <div className="mono text-[16px] text-[var(--text)]">
        {value === null || value === undefined ? (
          <span className="text-[var(--muted)]">—</span>
        ) : (
          <>
            {typeof value === "number" ? value.toFixed(2) : value}
            {unit && <span className="text-[12px] text-[var(--muted)]"> {unit}</span>}
          </>
        )}
      </div>
    </div>
  );
}

export default function EngineeringSummary({ facts }: { facts: EngineeringFacts }) {
  return (
    <div className="dial-border rounded-sm bg-[var(--panel-surface)] p-6">
      <div className="mono text-[11px] tracking-widest mb-5" style={{ color: "var(--accent)" }}>
        ENGINEERING FACTS — DETERMINISTIC
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <ConsumptionChart
          currentKwh={facts.daily_consumption_current_kwh}
          previousKwh={facts.daily_consumption_previous_kwh}
          changePercent={facts.consumption_change_percent}
        />
        <PowerFactorGauge powerFactor={facts.power_factor} />
        <div className="dial-border rounded-sm bg-[var(--panel)] p-2">
          <VoltageDeviationMeter
            voltage={facts.voltage_v}
            nominal={facts.nominal_voltage_v}
            deviationPercent={facts.voltage_deviation_percent}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-5 pt-5 border-t" style={{ borderColor: "var(--panel-line)" }}>
        <Stat label="REAL POWER" value={facts.real_power_kw} unit="kW" />
        <Stat label="APPARENT POWER" value={facts.apparent_power_kva} unit="kVA" />
        <Stat label="ESTIMATED COST" value={facts.estimated_cost_pkr} unit="PKR" />
        <Stat label="ADDITIONAL COST" value={facts.additional_cost_pkr} unit="PKR" />
      </div>

      {facts.warnings.length > 0 && (
        <div className="mt-5 pt-4 border-t" style={{ borderColor: "var(--panel-line)" }}>
          <div className="mono text-[10px] mb-2" style={{ color: "var(--warning)" }}>
            DATA LIMITATIONS
          </div>
          <ul className="text-[12px] text-[var(--muted)] space-y-1 list-disc list-inside">
            {facts.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
