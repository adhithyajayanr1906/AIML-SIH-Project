import { useEffect, useRef } from 'react';
import L from 'leaflet';

const NER_HUBS = {
  "Guwahati": [26.1445, 91.7362], "Shillong": [25.5788, 91.8933],
  "Tezpur": [26.6528, 92.7926], "Silchar": [24.8333, 92.7789],
  "Itanagar": [27.0844, 93.6053], "Imphal": [24.8170, 93.9368],
  "Kohima": [25.6751, 94.1086], "Aizawl": [23.7271, 92.7176],
  "Agartala": [23.8315, 91.2868], "Gangtok": [27.3389, 88.6065],
  "Dibrugarh": [27.4728, 94.9120], "Dimapur": [25.9060, 93.7271],
  "Jorhat": [26.7509, 94.2037], "Tura": [25.5141, 90.2032]
};

function MapCard({ routeResult }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef({ shortest: null, risk: null });

  useEffect(() => {
    if (!mapInstanceRef.current && mapRef.current) {
      const map = L.map(mapRef.current).setView([26.1445, 91.7362], 7);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap'
      }).addTo(map);

      Object.entries(NER_HUBS).forEach(([name, coords]) => {
        L.circleMarker(coords, { radius: 7, fillColor: "#38bdf8", color: "#0f172a", weight: 2, opacity: 1, fillOpacity: 0.9 })
          .bindPopup(`<b>Hub:</b> ${name}`)
          .addTo(map);
      });
      mapInstanceRef.current = map;
    }
  }, []);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (layersRef.current.shortest) map.removeLayer(layersRef.current.shortest);
    if (layersRef.current.risk) map.removeLayer(layersRef.current.risk);

    if (routeResult) {
      if (routeResult.shortest_route?.geometry?.length > 0) {
        layersRef.current.shortest = L.polyline(routeResult.shortest_route.geometry, {
          color: "#38bdf8", weight: 5, opacity: 0.8, dashArray: "6, 6"
        }).addTo(map);
      }
      if (routeResult.risk_aware_route?.geometry?.length > 0) {
        let routeColor = "#4ade80";
        if (routeResult.risk_aware_route.risk_level === "MEDIUM") routeColor = "#fbbf24";
        if (routeResult.risk_aware_route.risk_level === "HIGH") routeColor = "#f87171";

        layersRef.current.risk = L.polyline(routeResult.risk_aware_route.geometry, {
          color: routeColor, weight: 6, opacity: 0.9
        }).addTo(map);
        
        map.fitBounds(layersRef.current.risk.getBounds(), { padding: [40, 40] });
      }
    }
  }, [routeResult]);

  return <div className="map-wrapper" ref={mapRef} />;
}

export default MapCard;
