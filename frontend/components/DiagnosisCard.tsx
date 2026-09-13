"use client";

import { DiagnosisItem } from "@/lib/api";

const severityMeta: Record<string, { color: string; glow: string }> = {
  critical: { color: "var(--critical)", glow: "glow-critical" },
  warning: { color: "var(--warning)", glow: "glow-warning" },
  normal: { color: "var(--muted)", glow: "" },
};

const confidenceColor: Record<string, string> = {
  "High confidence": "var(--good)",
  "Medium confidence": "var(--accent)",
  "Low confidence": "var(--muted)",
  "Cannot determine": "var(--muted)",
};

function formatType(type: string): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function DiagnosisCard({ item }: { item: DiagnosisItem }) {
  const meta = severityMeta[item.severity] || severityMeta.normal;
  const confColor = confidenceColor[item.confidence] || "var(--muted)";

  return (
    <div className={`panel overflow-hidden ${meta.glow}`}>
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: "var(--panel-line)" }}
      >
        <div className="text-[13px] font-semibold">{formatType(item.type)}</div>
        <span
          className="mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-full"
          style={{ color: meta.color, border: `1px solid ${meta.color}` }}
        >
          {item.severity}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3">
        <div className="mono text-[12px] text-[var(--muted)]">
          {item.engine_explanation}
        </div>

        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="mono text-[10px]" style={{ color: "var(--accent)" }}>AI DIAGNOSIS</span>
            <span className="mono text-[10px]" style={{ color: confColor }}>
              · {item.confidence}
            </span>
          </div>
          <p className="text-[13px] leading-relaxed text-[var(--text)]">
            {item.explanation}
          </p>
        </div>

        {item.evidence.length > 0 && (
          <details className="text-[12px] text-[var(--muted)] group">
            <summary className="cursor-pointer mono text-[10px] flex items-center gap-1">
              <span style={{ color: "var(--accent)" }}>▸</span> EVIDENCE ({item.evidence.length})
            </summary>
            <ul className="mt-2 space-y-2">
              {item.evidence.map((e, i) => (
                <li key={i} className="pl-3 border-l" style={{ borderColor: "var(--panel-line-bright)" }}>
                  <p>{e.text}</p>
                  <p className="mono text-[10px] mt-0.5" style={{ color: "var(--accent)" }}>[{e.source}]</p>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
