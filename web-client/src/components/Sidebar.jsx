import { useState } from 'react';
import { routeRecommend, predictEnvironmentalRisk } from '../services/api';

const HUBS = [
  "Guwahati", "Shillong", "Tezpur", "Silchar", "Itanagar", 
  "Imphal", "Kohima", "Aizawl", "Agartala", "Gangtok", 
  "Dibrugarh", "Dimapur", "Jorhat", "Tura"
];

function Sidebar({ setRouteResult, setStatus }) {
  const [origin, setOrigin] = useState("Guwahati");
  const [destination, setDestination] = useState("Shillong");
  const [preference, setPreference] = useState("risk_aware");
  const [riskData, setRiskData] = useState(null);

  const [envInputs, setEnvInputs] = useState({
    rainfall: 180, waterLevel: 6.2, discharge: 3200, 
    elevation: 1200, landCover: 'Water Body', soilType: 'Clay'
  });

  const handleRoute = async () => {
    if (origin === destination) {
      setStatus({ type: 'error', message: 'Origin and Destination must differ.' });
      setTimeout(() => setStatus(null), 3000);
      return;
    }

    try {
      const data = await routeRecommend(origin, destination, preference);
      if (data.status === 'unavailable' || data.error) {
        setStatus({ type: 'error', message: data.message || 'Route unavailable' });
        setRouteResult(null);
      } else {
        setRouteResult(data);
        setStatus(null);
      }
    } catch (err) {
      setStatus({ type: 'error', message: 'API Error' });
    }
  };

  const handleRisk = async () => {
    try {
      const payload = {
        rainfall_mm: envInputs.rainfall,
        water_level_m: envInputs.waterLevel,
        river_discharge_m3s: envInputs.discharge,
        elevation_m: envInputs.elevation,
        land_cover: envInputs.landCover,
        soil_type: envInputs.soilType
      };
      const data = await predictEnvironmentalRisk(payload);
      setRiskData(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <aside className="sidebar">
      <section className="card-section">
        <h2 className="section-title">Route Optimization</h2>
        
        <div className="form-group">
          <label>Origin Hub</label>
          <select className="form-control" value={origin} onChange={(e) => setOrigin(e.target.value)}>
            {HUBS.map(h => <option key={h} value={h}>{h}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Destination Hub</label>
          <select className="form-control" value={destination} onChange={(e) => setDestination(e.target.value)}>
            {HUBS.map(h => <option key={h} value={h}>{h}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Routing Preference</label>
          <select className="form-control" value={preference} onChange={(e) => setPreference(e.target.value)}>
            <option value="risk_aware">Risk-Aware Path</option>
            <option value="shortest">Shortest Path</option>
          </select>
        </div>

        <button className="btn btn-primary" onClick={handleRoute}>Calculate Routes</button>
      </section>

      <section className="card-section">
        <h2 className="section-title">Environmental Risk Predictor</h2>
        
        <div className="form-row">
          <div className="form-group half">
            <label>Rainfall (mm)</label>
            <input type="number" className="form-control" value={envInputs.rainfall} onChange={e => setEnvInputs({...envInputs, rainfall: parseFloat(e.target.value)})} />
          </div>
          <div className="form-group half">
            <label>Water Level (m)</label>
            <input type="number" className="form-control" value={envInputs.waterLevel} onChange={e => setEnvInputs({...envInputs, waterLevel: parseFloat(e.target.value)})} />
          </div>
        </div>

        <button className="btn btn-secondary" onClick={handleRisk} style={{marginTop: '10px'}}>Evaluate Risk</button>

        {riskData && (
          <div style={{ marginTop: '16px', background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px' }}>
            <div style={{display:'flex', justifyContent:'space-between', marginBottom:'8px'}}>
              <span>Probability:</span>
              <strong>{(riskData.probability * 100).toFixed(1)}%</strong>
            </div>
            <div style={{display:'flex', justifyContent:'space-between'}}>
              <span>Level:</span>
              <span className={`badge ${riskData.risk_level?.toLowerCase() || ''}`}>{riskData.risk_level}</span>
            </div>
          </div>
        )}
      </section>
    </aside>
  );
}

export default Sidebar;
