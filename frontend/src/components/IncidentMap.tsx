import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { priorityColor, type Incident } from "../api";

interface Props {
  incidents: Incident[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

// Centered on the Greater Toronto Area.
const GTA_CENTER: [number, number] = [43.72, -79.42];

export function IncidentMap({ incidents, selectedId, onSelect }: Props) {
  return (
    <MapContainer
      center={GTA_CENTER}
      zoom={10}
      style={{ height: "100%", width: "100%" }}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {incidents.map((inc) => {
        const selected = inc.id === selectedId;
        return (
          <CircleMarker
            key={inc.id}
            center={[inc.lat, inc.lng]}
            radius={selected ? 10 : 6}
            pathOptions={{
              color: selected ? "#1f2933" : priorityColor(inc.predicted_priority),
              weight: selected ? 3 : 1,
              fillColor: priorityColor(inc.predicted_priority),
              fillOpacity: 0.8,
            }}
            eventHandlers={{ click: () => onSelect(inc.id) }}
          >
            <Tooltip>
              <strong>#{inc.id}</strong> · {inc.cause}
              <br />
              {inc.customers_affected} customers · sev {inc.weather_severity}
              <br />
              priority: {inc.predicted_priority ?? "—"}
              <br />
              ETA:{" "}
              {inc.predicted_eta_minutes != null
                ? `${Math.round(inc.predicted_eta_minutes)} min`
                : "—"}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
