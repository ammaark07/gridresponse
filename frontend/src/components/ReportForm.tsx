import { useState } from "react";
import { api, type Incident, type ReportResult } from "../api";

interface Props {
  incidents: Incident[];
  selectedId: number | null;
  onParsed: (updated: Incident) => void;
}

const SAMPLE =
  "Large tree down across Maple Ave, taking power lines with it. Road is " +
  "impassable and crews can't get through. Roughly 200 homes are dark.";

export function ReportForm({ incidents, selectedId, onParsed }: Props) {
  const [incidentId, setIncidentId] = useState<number | "">(selectedId ?? "");
  const [text, setText] = useState(SAMPLE);
  const [result, setResult] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Keep the dropdown in sync when the user selects on the map/list.
  const effectiveId = incidentId === "" ? selectedId : incidentId;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (effectiveId == null) {
      setError("Select an incident first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const r = await api.parseReport(Number(effectiveId), text);
      setResult(r);
      onParsed(r.incident);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="report-form" onSubmit={submit}>
      <label>
        Incident
        <select
          value={effectiveId ?? ""}
          onChange={(e) =>
            setIncidentId(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">— select —</option>
          {incidents.map((inc) => (
            <option key={inc.id} value={inc.id}>
              #{inc.id} · {inc.cause} · {inc.customers_affected} cust
            </option>
          ))}
        </select>
      </label>

      <label>
        Field report
        <textarea
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe what the crew is seeing on the ground…"
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Parsing…" : "Parse report"}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="parsed-result">
          <h4>Parsed JSON</h4>
          <pre>{JSON.stringify(result.parsed, null, 2)}</pre>
        </div>
      )}
    </form>
  );
}
