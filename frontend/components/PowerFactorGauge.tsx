"use client";

interface Props {
  powerFactor: number | null;
}

// Semicircle gauge, 0 (left) to 1 (right). Zones follow spec 4.6 classification.
export default function PowerFactorGauge({ powerFactor }: Props) {
  const cx = 90;
  const cy = 82;
  const r = 70;

  const angleFor = (v: number) => Math.PI - v * Math.PI; // 0 -> 180deg(left), 1 -> 0deg(right)
  const pt = (v: number, radius: number) => {
    const a = angleFor(v);
    return { x: cx + radius * Math.cos(a), y: cy - radius * Math.sin(a) };
  };

  const zones = [
    { from: 0, to: 0.8, color: "var(--critical)" },
    { from: 0.8, to: 0.9, color: "var(--warning)" },
    { from: 0.9, to: 0.95, color: "var(--accent)" },
    { from: 0.95, to: 1, color: "var(--good)" },
  ];

  const arcPath = (from: number, to: number, radius: number) => {
    const p1 = pt(from, radius);
    const p2 = pt(to, radius);
    return `M ${p1.x} ${p1.y} A ${radius} ${radius} 0 0 1 ${p2.x} ${p2.y}`;
  };

  const needleColor =
    powerFactor === null
      ? "var(--muted)"
      : powerFactor >= 0.95
      ? "var(--good)"
      : powerFactor >= 0.9
      ? "var(--accent)"
      : powerFactor >= 0.8
      ? "var(--warning)"
      : "var(--critical)";

  const needleAngle = powerFactor !== null ? angleFor(Math.min(Math.max(powerFactor, 0), 1)) : Math.PI / 2;
  const needleTip = {
    x: cx + (r - 12) * Math.cos(needleAngle),
    y: cy - (r - 12) * Math.sin(needleAngle),
  };

  return (
    <div className="dial-border rounded-sm bg-[var(--panel-surface)] p-4 flex flex-col items-center">
      <div className="mono text-[10px] tracking-wide self-start mb-1" style={{ color: "var(--muted)" }}>
        POWER FACTOR
      </div>
      <svg width="180" height="100" viewBox="0 0 180 100">
        {zones.map((z, i) => (
          <path
            key={i}
            d={arcPath(z.from, z.to, r)}
            stroke={z.color}
            strokeWidth={10}
            strokeOpacity={0.85}
            fill="none"
            strokeLinecap="butt"
          />
        ))}
        {powerFactor !== null && (
          <>
            <line
              x1={cx}
              y1={cy}
              x2={needleTip.x}
              y2={needleTip.y}
              stroke={needleColor}
              strokeWidth={2}
              style={{ filter: `drop-shadow(0 0 6px ${needleColor})` }}
            />
            <circle cx={cx} cy={cy} r={4} fill={needleColor} />
          </>
        )}
        <text x={cx} y={cy - 20} textAnchor="middle" fontFamily="var(--font-mono)" fontSize="20" fill="var(--text)">
          {powerFactor !== null ? powerFactor.toFixed(2) : "—"}
        </text>
      </svg>
      <div className="mono text-[9px] flex gap-3 mt-1" style={{ color: "var(--muted)" }}>
        <span>0.0</span>
        <span className="flex-1" />
        <span>1.0</span>
      </div>
    </div>
  );
}
