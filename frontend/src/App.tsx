import { useCallback, useEffect, useState } from "react";
import "./App.css";
import {
  api,
  type Crew,
  type CrewAvailability,
  type Incident,
} from "./api";
import { Dashboard } from "./components/Dashboard";
import { IncidentList } from "./components/IncidentList";
import { IncidentMap } from "./components/IncidentMap";
import { ReportForm } from "./components/ReportForm";

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [crews, setCrews] = useState<Crew[]>([]);
  const [availability, setAvailability] = useState<CrewAvailability | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Ensure predictions exist so the map/list render with colors.
      await api.predictAll();
      const [inc, crw, avail] = await Promise.all([
        api.listIncidents(),
        api.listCrews(),
        api.crewAvailability(),
      ]);
      setIncidents(inc);
      setCrews(crw);
      setAvailability(avail);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>⚡ GridResponse</h1>
        <span className="subtitle">
          Storm outage triage &amp; crew-dispatch dashboard
        </span>
        <button className="refresh" onClick={() => void load()} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {error && (
        <div className="error banner">
          {error}
          <div className="hint">Is the backend running on http://127.0.0.1:8000?</div>
        </div>
      )}

      <Dashboard incidents={incidents} crews={crews} availability={availability} />

      <div className="main-grid">
        <section className="panel map-panel">
          <h3>Incident map</h3>
          <div className="map-box">
            <IncidentMap
              incidents={incidents}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>
        </section>

        <section className="panel report-panel">
          <h3>Field report parser</h3>
          <ReportForm incidents={incidents} selectedId={selectedId} />
        </section>
      </div>

      <section className="panel list-panel">
        <h3>Incidents ({incidents.length})</h3>
        <IncidentList
          incidents={incidents}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </section>
    </div>
  );
}
