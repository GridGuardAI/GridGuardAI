"use client";

import { useState } from "react";
import { analyzeManual, analyzeBill, AnalyzeResponse } from "@/lib/api";
import Header from "@/components/Header";
import AgentTracker, { Stage } from "@/components/AgentTracker";
import EngineeringSummary from "@/components/EngineeringSummary";
import DiagnosisCard from "@/components/DiagnosisCard";
import Select from "@/components/Select";

type Mode = "bill" | "manual";

const initialStages: Stage[] = [
  { id: "orchestrator", label: "ORCHESTRATOR AGENT", detail: "Routing input through the analysis pipeline.", status: "pending" },
  { id: "engine", label: "ENGINEERING ENGINE", detail: "Running deterministic calculations and EE-01..EE-07 screening.", status: "pending" },
  { id: "fault", label: "CONSUMPTION / FAULT ANALYSIS AGENT", detail: "Investigating likely causes, grounded in retrieved evidence.", status: "pending" },
  { id: "recommend", label: "RECOMMENDATION AGENT", detail: "Prioritizing actionable guidance.", status: "pending" },
];

export default function Home() {
  const [mode, setMode] = useState<Mode>("bill");
  const [file, setFile] = useState<File | null>(null);
  const [tariff, setTariff] = useState("");
  const [voltage, setVoltage] = useState("");
  const [current, setCurrent] = useState("");
  const [pf, setPf] = useState("");
  const [phases, setPhases] = useState("1");
  const [billPreviousKwh, setBillPreviousKwh] = useState("");

  const [currentKwh, setCurrentKwh] = useState("");
  const [previousKwh, setPreviousKwh] = useState("");
  const [billingDays, setBillingDays] = useState("30");

  const [stages, setStages] = useState<Stage[]>(initialStages);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function num(s: string): number | undefined {
    if (s.trim() === "") return undefined;
    const n = parseFloat(s);
    return Number.isNaN(n) ? undefined : n;
  }

  async function runAnalysis() {
    setRunning(true);
    setError(null);
    setResult(null);
    setStages(initialStages.map((s, i) => ({ ...s, status: i === 0 ? "active" : "pending" })));

    const t1 = setTimeout(() => {
      setStages((prev) => prev.map((s, i) => (i === 0 ? { ...s, status: "done" } : i === 1 ? { ...s, status: "active" } : s)));
    }, 500);
    const t2 = setTimeout(() => {
      setStages((prev) => prev.map((s, i) => (i <= 1 ? { ...s, status: "done" } : i === 2 ? { ...s, status: "active" } : s)));
    }, 1100);
    const t3 = setTimeout(() => {
      setStages((prev) => prev.map((s, i) => (i <= 2 ? { ...s, status: "done" } : i === 3 ? { ...s, status: "active" } : s)));
    }, 1900);

    try {
      let data: AnalyzeResponse;
      if (mode === "bill") {
        if (!file) throw new Error("Please choose a bill image/PDF first.");
        data = await analyzeBill(file, {
          tariff_pkr_per_kwh: num(tariff),
          supply_voltage_v: num(voltage),
          current_a: num(current),
          power_factor: num(pf),
          num_phases: num(phases),
          previous_consumption_kwh: num(billPreviousKwh),
        });
      } else {
        data = await analyzeManual({
          current_consumption_kwh: num(currentKwh),
          previous_consumption_kwh: num(previousKwh),
          billing_days: num(billingDays),
          tariff_pkr_per_kwh: num(tariff),
          supply_voltage_v: num(voltage),
          current_a: num(current),
          power_factor: num(pf),
          num_phases: num(phases),
        });
      }

      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
      setStages(initialStages.map((s) => ({ ...s, status: "done" })));
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setStages(initialStages);
    } finally {
      setRunning(false);
    }
  }

  const inputClass =
    "w-full bg-transparent border rounded-sm px-3 py-2 text-[13px] mono outline-none transition-shadow focus:shadow-[0_0_0_1px_var(--accent),0_0_14px_-4px_rgba(0,232,255,0.6)]";
  const inputStyle = { borderColor: "var(--panel-line)" };

  return (
    <main className="min-h-screen px-6 py-10 md:px-14 md:py-16 max-w-6xl mx-auto">
      <Header />

      <section className="panel p-6 mb-10 relative scanline">
        <div
          className="inline-flex p-1 rounded-full mb-6"
          style={{ background: "var(--panel-bg)", border: "1px solid var(--panel-line)" }}
        >
          <button
            onClick={() => setMode("bill")}
            className="flex items-center gap-2 mono text-[12px] px-4 py-2 rounded-full transition-all"
            style={{
              background: mode === "bill" ? "var(--accent)" : "transparent",
              color: mode === "bill" ? "var(--panel-bg)" : "var(--muted)",
              fontWeight: mode === "bill" ? 600 : 400,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 17v2a2 2 0 002 2h10a2 2 0 002-2v-2"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Upload Bill
          </button>
          <button
            onClick={() => setMode("manual")}
            className="flex items-center gap-2 mono text-[12px] px-4 py-2 rounded-full transition-all"
            style={{
              background: mode === "manual" ? "var(--accent)" : "transparent",
              color: mode === "manual" ? "var(--panel-bg)" : "var(--muted)",
              fontWeight: mode === "manual" ? 600 : 400,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M11 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Manual Entry
          </button>
        </div>

        {mode === "bill" ? (
          <div className="mb-4">
            <div className="mono text-[11px] text-[var(--muted)] mb-1">BILL PHOTO / PDF</div>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="text-[13px] text-[var(--muted)] mb-3"
            />
            <div>
              <div className="mono text-[11px] text-[var(--muted)] mb-1">
                PREVIOUS MONTH CONSUMPTION (kWh) — optional, if bill doesn&apos;t show it
              </div>
              <input
                value={billPreviousKwh}
                onChange={(e) => setBillPreviousKwh(e.target.value)}
                className={inputClass}
                style={{ ...inputStyle, maxWidth: 220 }}
                placeholder="e.g. 850"
              />
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div>
              <div className="mono text-[11px] text-[var(--muted)] mb-1">CURRENT CONSUMPTION (kWh)</div>
              <input value={currentKwh} onChange={(e) => setCurrentKwh(e.target.value)} className={inputClass} style={inputStyle} placeholder="1250" />
            </div>
            <div>
              <div className="mono text-[11px] text-[var(--muted)] mb-1">PREVIOUS CONSUMPTION (kWh)</div>
              <input value={previousKwh} onChange={(e) => setPreviousKwh(e.target.value)} className={inputClass} style={inputStyle} placeholder="850" />
            </div>
            <div>
              <div className="mono text-[11px] text-[var(--muted)] mb-1">BILLING DAYS</div>
              <input value={billingDays} onChange={(e) => setBillingDays(e.target.value)} className={inputClass} style={inputStyle} placeholder="30" />
            </div>
          </div>
        )}

        <div className="mono text-[11px] text-[var(--muted)] mb-2 mt-2">
          OPTIONAL — ELECTRICAL READINGS &amp; TARIFF (leave blank if unknown)
        </div>
        <div className="grid md:grid-cols-5 gap-3 mb-5">
          <input value={voltage} onChange={(e) => setVoltage(e.target.value)} className={inputClass} style={inputStyle} placeholder="Voltage (V)" />
          <input value={current} onChange={(e) => setCurrent(e.target.value)} className={inputClass} style={inputStyle} placeholder="Current (A)" />
          <input value={pf} onChange={(e) => setPf(e.target.value)} className={inputClass} style={inputStyle} placeholder="Power Factor" />
         <Select
  value={phases}
  onChange={setPhases}
  options={[
    { value: "1", label: "1 Phase" },
    { value: "3", label: "3 Phase" },
  ]}
/>
          <input value={tariff} onChange={(e) => setTariff(e.target.value)} className={inputClass} style={inputStyle} placeholder="Tariff (PKR/kWh)" />
        </div>

        <button
          onClick={runAnalysis}
          disabled={running}
          className="mono text-[12px] tracking-widest px-5 py-2.5 rounded-sm border transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            borderColor: "var(--accent)",
            color: running ? "var(--panel-bg)" : "var(--accent)",
            background: running ? "var(--accent)" : "transparent",
            boxShadow: running ? "0 0 24px -4px rgba(0,232,255,0.8)" : "0 0 16px -6px rgba(0,232,255,0.4)",
          }}
        >
          {running ? "ANALYZING…" : "▶ RUN DIAGNOSTIC"}
        </button>

        {error && (
          <p className="mt-4 text-[13px] mono" style={{ color: "var(--red)" }}>
            ✕ ERROR: {error}
          </p>
        )}
      </section>

      {(running || result) && (
        <section className="mb-10">
          <AgentTracker stages={stages} />
        </section>
      )}

      {result && (
        <>
          <section className="mb-8">
            <EngineeringSummary facts={result.engineering} />
          </section>

          {result.extraction && (
            <section className="mb-8 panel p-4">
              <div className="mono text-[10px] text-[var(--muted)] mb-2">BILL EXTRACTION</div>
              <div className="text-[12px] text-[var(--text)]">
                Found: {result.extraction.fields_found.join(", ") || "none"}
              </div>
              {result.extraction.fields_missing.length > 0 && (
                <div className="text-[12px] text-[var(--muted)] mt-1">
                  Missing: {result.extraction.fields_missing.join(", ")}
                </div>
              )}
            </section>
          )}

          <section className="mb-8">
            <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
              <h2 className="text-[18px] font-semibold" style={{ color: "var(--text)" }}>Diagnosis</h2>
              <div className="mono text-[12px] text-[var(--muted)]">
                {result.diagnosis.length} anomal{result.diagnosis.length === 1 ? "y" : "ies"} found
              </div>
            </div>
            {result.diagnosis.length === 0 ? (
              <div className="panel p-8 text-center text-[var(--muted)] text-[14px] glow-good">
                ✓ No anomalies detected under current MVP screening rules.
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {result.diagnosis.map((d, i) => (
                  <DiagnosisCard key={i} item={d} />
                ))}
              </div>
            )}
          </section>

          <section className="mb-10 panel p-5 glow-accent">
            <div className="mono text-[11px] tracking-widest mb-3" style={{ color: "var(--accent)" }}>
              RECOMMENDATIONS
            </div>
            <div className="text-[13px] leading-relaxed whitespace-pre-line text-[var(--text)]">
              {result.recommendations}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
