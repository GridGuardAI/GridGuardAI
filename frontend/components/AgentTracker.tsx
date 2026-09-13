"use client";

export type StageStatus = "pending" | "active" | "done";

export interface Stage {
  id: string;
  label: string;
  detail: string;
  status: StageStatus;
}

const ICONS: Record<string, React.ReactNode> = {
  orchestrator: (
    <path d="M12 3v3M12 18v3M3 12h3M18 12h3M6 6l2 2M16 16l2 2M6 18l2-2M16 8l2-2"
      stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" fill="none" />
  ),
  engine: (
    <>
      <rect x="5" y="4" width="14" height="16" rx="1.5" stroke="currentColor" strokeWidth="1.6" fill="none" />
      <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </>
  ),
  fault: (
    <>
      <circle cx="10.5" cy="10.5" r="6" stroke="currentColor" strokeWidth="1.6" fill="none" />
      <path d="M15 15l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </>
  ),
  recommend: (
    <path d="M5 12l4 4L19 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
  ),
};

function statusText(status: StageStatus): string {
  if (status === "done") return "Complete";
  if (status === "active") return "Processing…";
  return "Waiting";
}

export default function AgentTracker({ stages }: { stages: Stage[] }) {
  return (
    <div className="panel p-5">
      <div className="mono text-[11px] tracking-widest mb-5" style={{ color: "var(--accent)" }}>
        AGENT PIPELINE
      </div>
      <div className="flex flex-col gap-0">
        {stages.map((stage, i) => {
          const iconKey = stage.id in ICONS ? stage.id : Object.keys(ICONS)[i] || "engine";
          const color =
            stage.status === "pending" ? "var(--muted)" : "var(--accent)";
          return (
            <div key={stage.id} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div
                  className={[
                    "h-8 w-8 rounded-full flex items-center justify-center shrink-0 transition-all",
                    stage.status === "active" ? "ring-pulse" : "",
                  ].join(" ")}
                  style={{
                    background: stage.status === "pending" ? "transparent" : "var(--panel-surface)",
                    border: `1.5px solid ${stage.status === "pending" ? "var(--panel-line-bright)" : "var(--accent)"}`,
                    color,
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24">
                    {ICONS[iconKey]}
                  </svg>
                </div>
                {i < stages.length - 1 && (
                  <svg width="2" height="32" className="my-0.5">
                    <line
                      x1="1" y1="0" x2="1" y2="32"
                      stroke={stage.status === "done" ? "var(--accent)" : "var(--panel-line)"}
                      strokeWidth="2"
                      className={stage.status === "active" ? "flow-line" : ""}
                    />
                  </svg>
                )}
              </div>
              <div className="pb-6 pt-1">
                <div className="flex items-center gap-2">
                  <span
                    className="mono text-[13px]"
                    style={{ color: stage.status === "pending" ? "var(--muted)" : "var(--text)" }}
                  >
                    {stage.label}
                  </span>
                  <span
                    className="mono text-[10px] tracking-wide"
                    style={{ color: stage.status === "done" ? "var(--good)" : stage.status === "active" ? "var(--accent)" : "var(--muted)" }}
                  >
                    {statusText(stage.status)}
                  </span>
                </div>
                <div className="text-[12px] text-[var(--muted)] mt-0.5">
                  {stage.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
