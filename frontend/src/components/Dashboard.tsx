import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  PRIORITY_COLORS,
  PRIORITY_ORDER,
  priorityColor,
  type Crew,
  type CrewAvailability,
  type Incident,
} from "../api";

interface Props {
  incidents: Incident[];
  crews: Crew[];
  availability: CrewAvailability | null;
}

const CAUSE_COLOR = "#3b6ea5";

export function Dashboard({ incidents, crews, availability }: Props) {
  const byPriority = PRIORITY_ORDER.map((p) => ({
    priority: p,
    count: incidents.filter((i) => i.predicted_priority === p).length,
  })).filter((d) => d.count > 0);

  const causeCounts = new Map<string, number>();
  for (const inc of incidents) {
    causeCounts.set(inc.cause, (causeCounts.get(inc.cause) ?? 0) + 1);
  }
  const byCause = Array.from(causeCounts.entries())
    .map(([cause, count]) => ({ cause, count }))
    .sort((a, b) => b.count - a.count);

  const totalCustomers = incidents.reduce(
    (sum, i) => sum + i.customers_affected,
    0
  );

  return (
    <div className="dashboard">
      <div className="stat-row">
        <Stat label="Incidents" value={incidents.length} />
        <Stat label="Customers affected" value={totalCustomers.toLocaleString()} />
        <Stat label="Crews available" value={availability?.available ?? crews.length} />
        <Stat label="Crews dispatched" value={availability?.dispatched ?? 0} />
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h4>Incidents by predicted priority</h4>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={byPriority}
                dataKey="count"
                nameKey="priority"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, value }: { name?: string; value?: number }) =>
                  `${name} (${value})`
                }
              >
                {byPriority.map((d) => (
                  <Cell key={d.priority} fill={priorityColor(d.priority)} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h4>Incidents by cause</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byCause} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="cause" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill={CAUSE_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="legend">
        {PRIORITY_ORDER.map((p) => (
          <span key={p} className="legend-item">
            <span
              className="legend-dot"
              style={{ backgroundColor: PRIORITY_COLORS[p] }}
            />
            {p}
          </span>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
