function ResultsPanel({ routeResult }) {
  if (!routeResult) {
    return (
      <div style={{position: 'absolute', bottom: '20px', left: '50%', transform:'translateX(-50%)', background: 'rgba(22,27,34,0.8)', padding: '12px 24px', borderRadius: '8px', zIndex: 1000}}>
        Select an origin and destination to compute optimal risk-aware routing.
      </div>
    );
  }

  const { shortest_route, risk_aware_route } = routeResult;

  return (
    <div className="results-overlay">
      {shortest_route && (
        <div className="route-card shortest-card">
          <h3 className="card-title">Shortest Route</h3>
          <div className="card-metric">
            <span className="label">Distance:</span>
            <span className="value">{shortest_route.distance_km} km</span>
          </div>
          <div className="card-metric">
            <span className="label">Est. Time:</span>
            <span className="value">{Math.floor(shortest_route.travel_time_min / 60)}h {shortest_route.travel_time_min % 60}m</span>
          </div>
          <div className="card-metric">
            <span className="label">Risk Score:</span>
            <span className="value">{(shortest_route.risk_score * 100).toFixed(1)}%</span>
          </div>
          <div className="path-text">{shortest_route.path.join(" -> ")}</div>
        </div>
      )}

      {risk_aware_route && (
        <div className="route-card risk-aware-card">
          <h3 className="card-title">Risk-Aware Recommended Route</h3>
          <div className="card-metric">
            <span className="label">Distance:</span>
            <span className="value">{risk_aware_route.distance_km} km</span>
          </div>
          <div className="card-metric">
            <span className="label">Est. Time:</span>
            <span className="value">{Math.floor(risk_aware_route.travel_time_min / 60)}h {risk_aware_route.travel_time_min % 60}m</span>
          </div>
          <div className="card-metric">
            <span className="label">Logistics Risk Level:</span>
            <span className={`badge ${risk_aware_route.risk_level?.toLowerCase() || ''}`}>{risk_aware_route.risk_level}</span>
          </div>
          <div className="path-text">{risk_aware_route.path.join(" -> ")}</div>
        </div>
      )}
    </div>
  );
}

export default ResultsPanel;
