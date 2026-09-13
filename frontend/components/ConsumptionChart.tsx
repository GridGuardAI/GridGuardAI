"use client";

import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  currentKwh: number | null;
  previousKwh: number | null;
  changePercent: number | null;
}

export default function ConsumptionChart({ currentKwh, previousKwh, changePercent }: Props) {
  if (currentKwh === null && previousKwh === null) return null;

  const data = [
    { label: "Previous", value: previousKwh ?? 0, key: "previous" },
    { label: "Current", value: currentKwh ?? 0, key: "current" },
  ];

  const isUp = (changePercent ?? 0) > 0;
  const barColor = changePercent === null
    ? "var(--accent)"
    : Math.abs(changePercent) > 40
    ? "var(--critical)"
    : Math.abs(changePercent) > 20
    ? "var(--warning)"
    : "var(--good)";

  return (
    <div className="dial-border rounded-sm bg-[var(--panel-surface)] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="mono text-[10px] tracking-wide" style={{ color: "var(--muted)" }}>
          CONSUMPTION COMPARISON
        </div>
        {changePercent !== null && (
          <div className="mono text-[12px]" style={{ color: barColor }}>
            {isUp ? "▲" : "▼"} {Math.abs(changePercent).toFixed(1)}%
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--muted)", fontSize: 11, fontFamily: "var(--font-mono)" }}
            axisLine={{ stroke: "var(--panel-line)" }}
            tickLine={false}
          />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--panel-line-bright)",
              borderRadius: 2,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
            }}
            labelStyle={{ color: "var(--text)" }}
            formatter={(v) => [`${Number(v).toFixed(1)} kWh`, ""]}
          />
          <Bar dataKey="value" radius={[2, 2, 0, 0]} maxBarSize={64}>
            {data.map((entry) => (
              <Cell
                key={entry.key}
                fill={entry.key === "current" ? barColor : "var(--panel-line-bright)"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
