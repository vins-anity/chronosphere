import React, { useState, useEffect } from 'react';
import About from './pages/About';

// Define types for our data
interface FeatureData {
  [key: string]: number | string;
}

interface WebSocketMessage {
  type: string;
  timestamp: string | number;
  win_probability: number;
  features: FeatureData;
}

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'about'>('dashboard');
  const [winProb, setWinProb] = useState<number | null>(null);
  const [features, setFeatures] = useState<FeatureData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');

  useEffect(() => {
    const connectWs = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/live');

      ws.onopen = () => {
        setConnectionStatus('connected');
        console.log('Connected to WebSocket');
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          if (data.type === 'update') {
            setWinProb(data.win_probability);
            setFeatures(data.features);
          }
        } catch (e) {
          console.error('Error parsing WS message', e);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        console.log('Disconnected from WebSocket');
        // Reconnect after 3 seconds
        setTimeout(connectWs, 3000);
      };

      return ws;
    };

    const ws = connectWs();

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-base-100 text-base-content font-sans">
      {/* Navbar */}
      <div className="navbar bg-base-300 shadow-lg">
        <div className="flex-1">
          <a className="btn btn-ghost normal-case text-xl text-primary font-bold" onClick={() => setCurrentPage('dashboard')}>
            Chronosphere
          </a>
        </div>
        <div className="flex-none">
          <ul className="menu menu-horizontal px-1">
            <li><a className={currentPage === 'dashboard' ? 'active' : ''} onClick={() => setCurrentPage('dashboard')}>Dashboard</a></li>
            <li><a className={currentPage === 'about' ? 'active' : ''} onClick={() => setCurrentPage('about')}>About</a></li>
          </ul>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto p-4">
        {currentPage === 'about' ? (
          <About />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Win Probability Card */}
            <div className="card bg-base-200 shadow-xl">
              <div className="card-body items-center text-center">
                <h2 className="card-title text-2xl">Win Probability</h2>
                {winProb !== null ? (
                  <div className="radial-progress text-primary" style={{ "--value": winProb * 100, "--size": "12rem" } as React.CSSProperties}>
                    {(winProb * 100).toFixed(1)}%
                  </div>
                ) : (
                  <span className="loading loading-spinner loading-lg text-primary"></span>
                )}
                <p className="text-sm opacity-70">Radiant Victory Chance</p>
              </div>
            </div>

            {/* Status Card */}
            <div className="card bg-base-200 shadow-xl">
              <div className="card-body">
                <h2 className="card-title">System Status</h2>
                <div className="flex items-center gap-2">
                  <div className={`badge ${connectionStatus === 'connected' ? 'badge-success' : 'badge-error'} badge-lg`}></div>
                  <span className="capitalize">{connectionStatus}</span>
                </div>
                <div className="divider"></div>
                <h3 className="font-bold">Live Features</h3>
                {features ? (
                  <div className="overflow-x-auto">
                    <table className="table table-xs">
                      <thead>
                        <tr>
                          <th>Feature</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(features).map(([key, value]) => (
                          <tr key={key}>
                            <td>{key}</td>
                            <td>{typeof value === 'number' ? value.toFixed(2) : value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm opacity-50">Waiting for game data...</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
