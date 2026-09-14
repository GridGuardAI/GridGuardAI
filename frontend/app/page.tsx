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


const NON_CRITICAL_MISSING_FIELDS = ["max_demand_kw", "bill_power_factor"];

const TARIFF_OPTIONS = [
  { code: "", label: "— Select tariff category —" },
  { code: "a1", label: "A-1 · Residential (protected)" },
  { code: "a1np", label: "A-1 · Residential (non-protected)" },
  { code: "a2", label: "A-2 · Commercial" },
  { code: "b1", label: "B-1 · Industrial (LT)" },
  { code: "b2", label: "B-2 · Industrial (MT)" },
  { code: "b3", label: "B-3 · Industrial (HT/EHT)" },
  { code: "c1", label: "C-1 · Agricultural Tubewell" },
  { code: "d1", label: "D-1 · Public Lighting" },
  { code: "g1", label: "G-1 · Temporary Supply" },
];

export default function Home() {
  const [mode, setMode] = useState<Mode>("bill");
  const [file, setFile] = useState<File | null>(null);
  const [tariffCategory, setTariffCategory] = useState("");
  const [derivedTariff, setDerivedTariff] = useState<string>("");
  const [phases, setPhases] = useState("1");
  const [billPreviousKwh, setBillPreviousKwh] = useState("");

  const [currentKwh, setCurrentKwh] = useState("");
  const [previousKwh, setPreviousKwh] = useState("");
  const [billingDays, setBillingDays] = useState("30");

  const [showExtractionDetails, setShowExtractionDetails] = useState(false);
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
    setDerivedTariff("");
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
          num_phases: num(phases),
          previous_consumption_kwh: num(billPreviousKwh),
        });
      } else {
        data = await analyzeManual({
          current_consumption_kwh: num(currentKwh),
          previous_consumption_kwh: num(previousKwh),
          billing_days: num(billingDays),
          num_phases: num(phases),
        });
      }

      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
      setStages(initialStages.map((s) => ({ ...s, status: "done" })));
      setResult(data);
      const usedRate = data.extraction?.tariff_pkr_per_kwh_used;
      setDerivedTariff(usedRate !== undefined && usedRate !== null ? String(usedRate) : "");
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
          OPTIONAL — CONNECTION &amp; TARIFF (leave blank if unknown)
        </div>
        <div className="grid md:grid-cols-3 gap-3 mb-5">
          <Select
            value={phases}
            onChange={setPhases}
            options={[
              { value: "1", label: "1 Phase" },
              { value: "3", label: "3 Phase" },
            ]}
          />
          <Select
            value={tariffCategory}
            onChange={setTariffCategory}
            options={TARIFF_OPTIONS.map((t) => ({ value: t.code, label: t.label }))}
          />
          <div>
            <input
              value={derivedTariff}
              readOnly
              disabled
              className={inputClass}
              style={{ ...inputStyle, opacity: 0.6, cursor: "not-allowed" }}
              placeholder="Tariff (PKR/kWh) — auto-calculated"
            />
            {derivedTariff && (
              <div className="mono text-[10px] text-[var(--muted)] mt-1">
                Auto-derived from bill total ÷ units — not the official NEPRA base rate.
              </div>
            )}
          </div>
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
              {(() => {
                const relevantMissing = result.extraction.fields_missing.filter(
                  (f) => !NON_CRITICAL_MISSING_FIELDS.includes(f)
                );
                const allGood = relevantMissing.length === 0;
                return (
                  <>
                    <div className="flex items-center justify-between">
                      <div className="text-[13px]" style={{ color: allGood ? "var(--good)" : "var(--warning)" }}>
                        {allGood
                          ? "✓ Bill data extracted successfully."
                          : `⚠ Some fields couldn't be read from this bill (${relevantMissing.length} field${relevantMissing.length === 1 ? "" : "s"}) — using available data only.`}
                      </div>
                      <button
                        onClick={() => setShowExtractionDetails((v) => !v)}
                        className="mono text-[11px] underline"
                        style={{ color: "var(--muted)" }}
                      >
                        {showExtractionDetails ? "Hide details" : "Show details"}
                      </button>
                    </div>
                    {showExtractionDetails && (
                      <div className="mt-3 pt-3 border-t" style={{ borderColor: "var(--panel-line)" }}>
                        <div className="mono text-[10px] text-[var(--muted)] mb-2">BILL EXTRACTION</div>
                        <div className="text-[12px] text-[var(--text)]">
                          Found: {result.extraction.fields_found.join(", ") || "none"}
                        </div>
                        {relevantMissing.length > 0 && (
                          <div className="text-[12px] text-[var(--muted)] mt-1">
                            Missing: {relevantMissing.join(", ")}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                );
              })()}
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
