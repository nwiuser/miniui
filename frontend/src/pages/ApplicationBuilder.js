import React, { useState, useEffect } from 'react';

const ApplicationBuilder = ({ appId, onAppSelect, onPageSelect }) => {
  // Application form state
  const [appData, setAppData] = useState({
    name: '',
    alias: '',
    description: '',
    logo: '',
    theme: 'default',
    is_active: true
  });

  // Pages state
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const loadAppAndPages = async () => {
      try {
        setLoading(true);

        // Load application data if editing existing app
        if (appId) {
          const appResponse = await fetch(`/api/applications/${appId}/`);
          if (appResponse.ok) {
            const appData = await appResponse.json();
            setAppData(appData);
          }
        }

        // Load pages
        const pagesResponse = await fetch(`/api/pages/?application_id=${appId || ''}`);
        if (pagesResponse.ok) {
          const pagesData = await pagesResponse.json();
          setPages(pagesData);
        } else {
          setPages([]);
        }
      } catch (err) {
        setError('Failed to load application data');
      } finally {
        setLoading(false);
      }
    };

    if (appId !== null || appId === 0) { // Only load if we have an appId or are creating new (0)
      loadAppAndPages();
    } else {
      setLoading(false);
    }
  }, [appId]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setAppData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSaveApp = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      let response;
      if (appId) {
        // Update existing application
        response = await fetch(`/api/applications/${appId}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(appData),
        });
      } else {
        // Create new application
        response = await fetch('/api/applications/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(appData),
        });
      }

      if (response.ok) {
        const data = await response.json();
        // Redirect to show the app builder for the new/updated app
        window.location.href = `/app/${data.id}/builder`;
      } else {
        throw new Error('Failed to save application');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddPage = () => {
    // Navigate to create new page
    window.location.href = `/app/${appId || 'new'}/page/new`;
  };

  if (loading) return <div className="loading">Loading application data...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="application-builder">
      <div className="app-builder-header">
        <h1>{appId ? 'Edit Application' : 'New Application'}</h1>
        <div className="app-builder-actions">
          <button
            className="btn btn-outline"
            onClick={() => onAppSelect('dashboard')}
          >
            ← Back to Dashboard
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSaveApp}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Application'}
          </button>
        </div>
      </div>

      <div className="app-builder-body">
        <form onSubmit={handleSaveApp} className="app-form">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="name">Application Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={appData.name || ''}
                onChange={handleInputChange}
                required
                className="form-input"
                placeholder="Enter application name"
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="alias">Application Alias *</label>
              <input
                type="text"
                id="alias"
                name="alias"
                value={appData.alias || ''}
                onChange={handleInputChange}
                required
                className="form-input"
                placeholder="Enter short alias (e.g., HRAPP)"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={appData.description || ''}
              onChange={handleInputChange}
              className="form-textarea"
              rows="3"
              placeholder="Enter application description"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="theme">Theme</label>
              <select
                id="theme"
                name="theme"
                value={appData.theme || 'default'}
                onChange={handleInputChange}
                className="form-select"
              >
                <option value="default">Default</option>
                <option value="dark">Dark</option>
                <option value="blue">Blue</option>
                <option value="green">Green</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={appData.is_active || false}
                  onChange={handleInputChange}
                  className="form-input"
                />
                Active
              </label>
            </div>
          </div>
        </form>
      </div>

      <div className="app-builder-footer">
        <h2>Pages ({pages.length})</h2>
        {pages.length > 0 ? (
          <div className="pages-list">
            {pages.map(page => (
              <div key={page.id} className="page-item">
                <div className="page-info">
                  <h4>{page.name}</h4>
                  <p className="page-title">{page.alias || 'No alias'}</p>
                  <small>Page {page.page_number}</small>
                </div>
                <div className="page-actions">
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => onPageSelect(page.id)}
                  >
                    Edit Page
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle delete
                      alert('Delete functionality coming soon');
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <h3>No pages yet</h3>
            <p>Add pages to your application using the button below.</p>
          </div>
        )}

        <div className="add-page-section">
          <button
            className="btn btn-success"
            onClick={handleAddPage}
          >
            + New Page
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApplicationBuilder;