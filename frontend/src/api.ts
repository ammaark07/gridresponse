// Typed API client for the GridResponse backend.

const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://127.0.0.1:8000";

export type Cause =
  | "tree"
  | "equipment"
  | "weather"
  | "vehicle"
  | "animal"
  | "unknown";

export type Status = "reported" | "triaged" | "assigned" | "restored";
export type Priority = "low" | "medium" | "high" | "critical";
export type SeveritySignal = "low" | "medium" | "high";

export interface Incident {
  id: number;
  lat: number;
  lng: number;
  reported_at: string;
  cause: Cause;
  customers_affected: number;
  weather_severity: number;
  is_rural: boolean;
  near_critical_facility: boolean;
  status: Status;
  predicted_eta_minutes: number | null;
  predicted_priority: Priority | null;
}

export interface Crew {
  id: number;
  name: string;
  base_lat: number;
  base_lng: number;
  skill_level: number;
  status: "available" | "dispatched";
}

export interface CrewAvailability {
  available: number;
  dispatched: number;
  total: number;
}

export interface ParsedReport {
  hazards: string[];
  est_customers: number;
  severity_signal: SeveritySignal;
  access_blocked: boolean;
}

export interface ReportResult {
  id: number;
  incident_id: number;
  raw_text: string;
  parsed: ParsedReport;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listIncidents: () => request<Incident[]>("/incidents?limit=1000"),
  predictAll: () =>
    request<{ updated: number }>("/incidents/predict-all", { method: "POST" }),
  predictIncident: (id: number) =>
    request<{ predicted_eta_minutes: number; predicted_priority: Priority }>(
      `/incidents/${id}/predict`,
      { method: "POST" }
    ),
  listCrews: () => request<Crew[]>("/crews"),
  crewAvailability: () => request<CrewAvailability>("/crews/availability"),
  parseReport: (incident_id: number, raw_text: string) =>
    request<ReportResult>("/reports/parse", {
      method: "POST",
      body: JSON.stringify({ incident_id, raw_text }),
    }),
};

export const PRIORITY_COLORS: Record<Priority, string> = {
  critical: "#d11149",
  high: "#f17105",
  medium: "#f7b801",
  low: "#3a9679",
};

export const PRIORITY_ORDER: Priority[] = ["critical", "high", "medium", "low"];

export function priorityColor(p: Priority | null): string {
  return p ? PRIORITY_COLORS[p] : "#9aa5b1";
}
