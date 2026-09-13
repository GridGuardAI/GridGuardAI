"use client";

export default function VoltageDeviationMeter({
  voltage,
  nominal,
  deviationPercent,
}: {
  voltage: number | null;
  nominal: number;
  deviationPercent: number | null;
}) {
  if (voltage === null || deviationPercent === null) {
    return (
      <div className="h-[140px] flex items-center justify-center">
        <span className="mono text-[13px] text-[var(--muted)]">NO VOLTAGE DATA</span>
      </div>
    );
  }

  // Map deviation % onto a -15% to +15% visual scale, clamped
  const clamped = Math.max(-15, Math.min(15, deviationPercent));
  const posPercent = ((clamped + 15) / 30) * 100;

  const absDev = Math.abs(deviationPercent);
  const color = absDev > 10 ? "var(--critical)" : absDev > 5 ? "var(--warning)" : "var(--good)";

  return (
    <div className="h-[140px] flex flex-col items-center justify-center gap-4">
      <div className="mono text-[22px] font-bold" style={{ color }}>
        {voltage.toFixed(1)}V
        <span className="text-[13px] text-[var(--muted)] ml-2">
          ({deviationPercent > 0 ? "+" : ""}{deviationPercent.toFixed(1)}%)
        </span>
      </div>
      <div className="w-full max-w-[220px] relative h-2 rounded-full" style={{ background: "var(--panel-line-bright)" }}>
        {/* normal band ±5% */}
        <div
          className="absolute h-full rounded-full"
          style={{ left: "33.3%", width: "33.3%", background: "rgba(57,255,136,0.25)" }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 h-3.5 w-3.5 rounded-full border-2"
          style={{
            left: `calc(${posPercent}% - 7px)`,
            background: color,
            borderColor: "var(--void)",
            boxShadow: `0 0 10px ${color}`,
          }}
        />
      </div>
      <div className="mono text-[9px] text-[var(--muted)]">NOMINAL {nominal}V</div>
    </div>
  );
}
