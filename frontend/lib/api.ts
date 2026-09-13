// GridGuard AI - API client (Phase 1 spec-compliant contract)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoadItem {
  load_type: string;
  power_kw?: number | null;
  hours_per_day?: number | null;
  days_per_month?: number | null;
  quantity?: number | null;
}

export interface AnalyzeRequest {
  billing_period?: string | null;
  current_consumption_kwh?: number | null;
  previous_consumption_kwh?: number | null;
  billing_days?: number | null;
  electricity_cost_pkr?: number | null;
  supply_voltage_v?: number | null;
  current_a?: number | null;
  power_factor?: number | null;
  num_phases?: number | null;
  tariff_pkr_per_kwh?: number | null;
  loads?: LoadItem[];
}

export interface Anomaly {
  type: string;
  severity: "normal" | "warning" | "critical" | string;
  value: number | null;
  threshold: number | null;
  explanation: string;
}

export interface Evidence {
  text: string;
  source: string;
}

export interface DiagnosisItem {
  type: string;
  severity: string;
  value: number | null;
  threshold: number | null;
  engine_explanation: string;
  confidence: "High confidence" | "Medium confidence" | "Low confidence" | "Cannot determine" | string;
  explanation: string;
  evidence: Evidence[];
}

export interface EngineeringFacts {
  consumption_change_percent: number | null;
  daily_consumption_previous_kwh: number | null;
  daily_consumption_current_kwh: number | null;
  total_estimated_load_kw: number | null;
  estimated_energy_kwh: number | null;
  voltage_v: number | null;
  current_a: number | null;
  power_factor: number | null;
  real_power_kw: number | null;
  apparent_power_kva: number | null;
  major_loads: Array<{ load_type: string; power_kw: number | null; energy_kwh: number | null; quantity: number | null }>;
  load_contributions_percent: Array<{ load_type: string; contribution_percent: number | null }>;
  estimated_cost_pkr: number | null;
  additional_cost_pkr: number | null;
  anomalies: Anomaly[];
  voltage_deviation_percent: number | null;
  nominal_voltage_v: number;
  warnings: string[];
}

export interface AnalyzeResponse {
  engineering: EngineeringFacts;
  diagnosis: DiagnosisItem[];
  recommendations: string;
  missing_data_notes: string[];
  extraction?: {
    fields_found: string[];
    fields_missing: string[];
    meter_number: string | null;
    due_date: string | null;
    tariff_pkr_per_kwh_used?: number | null;
    tariff_source?: "user_provided" | "derived_from_bill" | null;
  };
}

export async function analyzeManual(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Analysis failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function analyzeBill(
  file: File,
  extras: {
    tariff_pkr_per_kwh?: number;
    num_phases?: number;
    previous_consumption_kwh?: number;
  } = {}
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  Object.entries(extras).forEach(([k, v]) => {
    if (v !== undefined && v !== null && !Number.isNaN(v)) formData.append(k, String(v));
  });

  const res = await fetch(`${API_URL}/analyze-bill`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Bill analysis failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
