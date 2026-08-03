import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Dashboard = ({ onAppSelect }) => {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchApps = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/applications/');
        if (response.ok) {
          const data = await response.json();
          setApps(data);
        } else {
          throw new Error('Failed to fetch applications');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchApps();
  }, []);

  if (loading) return <div className="dashboard-loading">Loading applications...</div>;
  if (error) return <div className="dashboard-error">Error: {error}</div>;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Applications</h1>
        <button className="btn btn-primary" onClick={() => window.location.href = '/app/new'}>
          + New Application
        </button>
      </div>

      {apps.length === 0 ? (
        <div className="empty-state">
          <h2>No applications yet</h2>
          <p>Create your first application to get started.</p>
          <button className="btn btn-primary" onClick={() => window.location.href = '/app/new'}>
            Create Application
          </button>
        </div>
      ) : (
        <div className="apps-grid">
          {apps.map(app => (
            <div key={app.id} className="app-card">
              <div className="app-card-header">
                <h3>{app.name}</h3>
                <span className={app.is_active ? 'status-active' : 'status-inactive'}>
                  {app.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="app-card-body">
                <p className="app-description">{app.description || 'No description provided'}</p>
                <div className="app-meta">
                  <span>ID: {app.id}</span>
                  <span>Alias: {app.alias}</span>
                </div>
              </div>
              <div className="app-card-footer">
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => onAppSelect(app.id)}
                >
                  Open Builder
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;