import { useState } from 'react';
import Sidebar from './components/Sidebar';
import MapCard from './components/MapCard';
import ResultsPanel from './components/ResultsPanel';
import './index.css';
import 'leaflet/dist/leaflet.css';

function App() {
  const [routeResult, setRouteResult] = useState(null);
  const [status, setStatus] = useState(null);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="header-title">Smart Logistics and Accessibility Intelligence Platform</h1>
        <p className="header-subtitle">GIS-Based Environmental Risk Assessment and Risk-Aware Route Optimization</p>
      </header>

      <main className="main-content">
        <Sidebar setRouteResult={setRouteResult} setStatus={setStatus} />
        
        <div className="content-area">
          {status && (
            <div className={`status-msg ${status.type === 'error' ? 'status-error' : ''}`}>
              {status.message}
            </div>
          )}
          
          <MapCard routeResult={routeResult} />
          <ResultsPanel routeResult={routeResult} />
        </div>
      </main>
    </div>
  );
}

export default App;
