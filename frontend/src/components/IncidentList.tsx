import { priorityColor, type Incident } from "../api";

interface Props {
  incidents: Incident[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function IncidentList({ incidents, selectedId, onSelect }: Props) {
  return (
    <div className="table-wrap">
      <table className="incident-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Cause</th>
            <th>Customers</th>
            <th>Sev</th>
            <th>Priority</th>
            <th>ETA (min)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc) => (
            <tr
              key={inc.id}
              className={inc.id === selectedId ? "selected" : ""}
              onClick={() => onSelect(inc.id)}
            >
              <td>#{inc.id}</td>
              <td>{inc.cause}</td>
              <td>{inc.customers_affected.toLocaleString()}</td>
              <td>{inc.weather_severity}</td>
              <td>
                <span
                  className="priority-pill"
                  style={{ backgroundColor: priorityColor(inc.predicted_priority) }}
                >
                  {inc.predicted_priority ?? "—"}
                </span>
              </td>
              <td>
                {inc.predicted_eta_minutes != null
                  ? Math.round(inc.predicted_eta_minutes)
                  : "—"}
              </td>
              <td>{inc.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
