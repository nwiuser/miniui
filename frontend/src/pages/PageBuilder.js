import React, { useState, useEffect } from 'react';

const PageBuilder = ({ pageId, onAppSelect, onPageSelect }) => {
  // Page form state
  const [pageData, setPageData] = useState({
    id: '',
    name: '',
    alias: '',
    title: '',
    page_number: 1,
    is_active: true,
    application_id: null
  });

  // Region state
  const [regions, setRegions] = useState([]);
  // Item state
  const [items, setItems] = useState([]);

  // Component state for drag and drop
  const [dragItem, setDragItem] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  // Load page data, regions, and items
  useEffect(() => {
    const loadPageAndData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load page data if editing existing page
        if (pageId) {
          const pageResponse = await fetch(`/api/pages/${pageId}/`);
          if (pageResponse.ok) {
            const pageData = await pageResponse.json();
            setPageData(pageData);
          } else {
            throw new Error('Failed to load page data');
          }
        }

        // Load regions for this page
        if (pageId) {
          const regionsResponse = await fetch(`/api/regions/?page_id=${pageId}`);
          if (regionsResponse.ok) {
            const regionsData = await regionsResponse.json();
            setRegions(regionsData);
          } else {
            console.warn('Failed to load regions');
          }
        }

        // Load items for this page
        if (pageId) {
          const itemsResponse = await fetch(`/api/items/?page_id=${pageId}`);
          if (itemsResponse.ok) {
            const itemsData = await itemsResponse.json();
            setItems(itemsData);
          } else {
            console.warn('Failed to load items');
          }
        }
      } catch (err) {
        setError('Failed to load page data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (pageId !== null && pageId !== undefined) {
      loadPageAndData();
    } else {
      setLoading(false);
    }
  }, [pageId]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setPageData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleDragStart = (type, data) => {
    setDragItem({ type, data });
  };

  const handleDragEnd = () => {
    setDragItem(null);
  };

  const handleDropRegion = (regionData) => {
    // Create a new region based on the dropped data
    const newRegion = {
      name: regionData.name || 'New Region',
      region_type: regionData.type || 'static_content',
      template_options: {}, // Initialize empty options
      position: Date.now(), // Temporary position, will be sorted later
      page_id: pageData.id || null, // Will be set when saving
      is_active: true
    };
    // Add to regions state
    setRegions(prev => [...prev, newRegion]);
  };

  const handleDropItem = (itemData) => {
    // Create a new item based on the dropped data
    const newItem = {
      name: itemData.name || 'New Item',
      alias: itemData.alias || '',
      item_type: itemData.type || 'text',
      label: itemData.label || itemData.name,
      placeholder: itemData.placeholder || '',
      default_value: itemData.default_value || '',
      is_required: itemData.is_required || false,
      page_id: pageData.id || null, // Will be set when saving
      is_active: true
    };
    // Add to items state
    setItems(prev => [...prev, newItem]);
  };

  const handleDeleteRegion = async (regionId) => {
    if (window.confirm('Are you sure you want to delete this region?')) {
      try {
        if (regionId) {
          await fetch(`/api/regions/${regionId}/`, {
            method: 'DELETE',
          });
        }
        setRegions(prev => prev.filter(r => r.id !== regionId));
      } catch (err) {
        setError('Failed to delete region');
        console.error(err);
      }
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        if (itemId) {
          await fetch(`/api/items/${itemId}/`, {
            method: 'DELETE',
          });
        }
        setItems(prev => prev.filter(i => i.id !== itemId));
      } catch (err) {
        setError('Failed to delete item');
        console.error(err);
      }
    }
  };

  const handleSavePage = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      let pageResponse;
      if (pageData.id) {
        // Update existing page
        pageResponse = await fetch(`/api/pages/${pageData.id}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...pageData,
            application_id: pageData.application_id || (window.location.pathname.match(/\/app\/(\d+)\//) || [])[1]
          }),
        });
      } else {
        // Create new page
        const appIdMatch = window.location.pathname.match(/\/app\/(\d+)\//);
        const appId = appIdMatch ? appIdMatch[1] : null;

        pageResponse = await fetch('/api/api/pages/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...pageData,
            application_id: appId
          }),
        });
      }

      if (!pageResponse.ok) {
        throw new Error('Failed to save page');
      }

      const savedPage = await pageResponse.json();
      // Update pageData with the new ID if it was created
      if (!pageData.id) {
        setPageData(prev => ({ ...prev, id: savedPage.id }));
      }

      // Now save regions and items
      const regionPromises = regions.map(async (region) => {
        const regionData = { ...region, page_id: savedPage.id };
        if (region.id) {
          // Update existing region
          const res = await fetch(`/api/regions/${region.id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(regionData)
          });
          if (!res.ok) throw new Error(`Failed to update region ${region.name}`);
          return res.json();
        } else {
          // Create new region
          const res = await fetch(`/api/regions/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(regionData)
          });
          if (!res.ok) throw new Error(`Failed to create region ${region.name}`);
          return res.json();
        }
      });

      const itemPromises = items.map(async (item) => {
        const itemData = { ...item, page_id: savedPage.id };
        if (item.id) {
          // Update existing item
          const res = await fetch(`/api/items/${item.id}/`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(itemData)
          });
          if (!res.ok) throw new Error(`Failed to update item ${item.name}`);
          return res.json();
        } else {
          // Create new item
          const res = await fetch(`/api/items/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(itemData)
          });
          if (!res.ok) throw new Error(`Failed to create item ${item.name}`);
          return res.json();
        }
      });

      // Wait for all requests
      const savedRegions = await Promise.all(regionPromises);
      const savedItems = await Promise.all(itemPromises);

      // Update state with saved regions and items (which now have IDs and other server-generated fields)
      setRegions(savedRegions);
      setItems(savedItems);

      // Show success message
      alert('Page saved successfully!');
      // Optionally redirect to show the saved page
      // window.location.href = `/app/${savedPage.application_id}/page/${savedPage.id}`;
    } catch (err) {
      setError(err.message);
      console.error('Save error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddPage = () => {
    // Navigate to create new page
    const appIdMatch = window.location.pathname.match(/\/app\/(\d+)\//);
    const appId = appIdMatch ? appIdMatch[1] : 'new';
    window.location.href = `/app/${appId}/page/new`;
  };

  if (loading) return <div className="loading">Loading page data...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-builder">
      <div className="page-builder-header">
        <h1>{pageData.id ? 'Edit Page' : 'New Page'}</h1>
        <div className="page-builder-actions">
          <button
            className="btn btn-outline"
            onClick={() => onAppSelect('dashboard')}
          >
            ← Back to Dashboard
          </button>
          {pageData.id && (
            <button
              className="btn btn-outline"
              onClick={() => onPageSelect(null)} // Back to app builder
            >
              ← Back to Application
            </button>
          )}
          <button
            className="btn btn-primary"
            onClick={handleSavePage}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Page'}
          </button>
        </div>
      </div>

      <div className="page-builder-body">
        <div className="page-builder-sidebar">
          <div className="sidebar-section">
            <h3>Page Properties</h3>
            <form onSubmit={handleSavePage} className="page-form">
              <div className="form-group">
                <label className="form-label" htmlFor="page-name">Page Name *</label>
                <input
                  type="text"
                  id="page-name"
                  name="name"
                  value={pageData.name || ''}
                  onChange={handleInputChange}
                  required
                  className="form-input"
                  placeholder="Enter page name"
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="page-alias">Page Alias *</label>
                <input
                  type="text"
                  id="page-alias"
                  name="alias"
                  value={pageData.alias || ''}
                  onChange={handleInputChange}
                  required
                  className="form-input"
                  placeholder="Enter page alias (e.g., HOME)"
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="page-title">Page Title</label>
                <input
                  type="text"
                  id="page-title"
                  name="title"
                  value={pageData.title || ''}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Browser tab title"
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="page-number">Page Number *</label>
                <input
                  type="number"
                  id="page-number"
                  name="page_number"
                  value={pageData.page_number || 1}
                  onChange={handleInputChange}
                  required
                  min="1"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={pageData.is_active || true}
                    onChange={handleInputChange}
                    className="form-input"
                  />
                  Active
                </label>
              </div>
            </form>
          </div>

          <div className="sidebar-section">
            <h3>Components</h3>
            <div className="components-panel">
              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('region', { type: 'static_content', name: 'Static Content' })}
              >
                <div className="component-icon">📄</div>
                <div className="component-label">Static Content</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('region', { type: 'form', name: 'Form' })}
              >
                <div className="component-icon">📝</div>
                <div className="component-label">Form</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('region', { type: 'report', name: 'Report' })}
              >
                <div className="component-icon">📊</div>
                <div className="component-label">Report</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('item', { type: 'text', name: 'Text Field' })}
              >
                <div className="component-icon">🔤</div>
                <div className="component-label">Text Field</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('item', { type: 'textarea', name: 'Text Area' })}
              >
                <div className="component-icon">📝</div>
                <div className="component-label">Text Area</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('item', { type: 'select', name: 'Select List' })}
              >
                <div className="component-icon">📋</div>
                <div className="component-label">Select List</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('item', { type: 'checkbox', name: 'Checkbox' })}
              >
                <div className="component-icon">☑️</div>
                <div className="component-label">Checkbox</div>
              </div>

              <div
                className="component-item"
                draggable
                onDragStart={(e) => handleDragStart('item', { type: 'date_picker', name: 'Date Picker' })}
              >
                <div className="component-icon">📅</div>
                <div className="component-label">Date Picker</div>
              </div>
            </div>
          </div>
        </div>

        <div className="page-builder-main">
          <div className="page-editor">
            <div className="page-editor-header">
              <h2>Page Layout</h2>
              <div className="editor-actions">
                <button className="btn btn-sm btn-outline" onClick={() => alert('Grid settings coming soon')}>
                  Grid Settings
                </button>
                <button className="btn btn-sm btn-outline" onClick={() => alert('Page properties')}>
                  Page Properties
                </button>
              </div>
            </div>

            <div className="page-canvas"
              onDragOver={(e) => e.preventDefault()}
              onDragLeave={() => setDragItem(null)}
              onDrop={(e) => {
                e.preventDefault();
                setDragItem(null);
                // Handle drop logic here - we'll determine what was dropped based on dragItem state
                if (dragItem) {
                  if (dragItem.type === 'region') {
                    handleDropRegion(dragItem.data);
                  } else if (dragItem.type === 'item') {
                    handleDropItem(dragItem.data);
                  }
                }
              }}
            >
              {/* Drag and drop area for regions and items */}
              <div className="drop-zone">
                <div className="drop-zone-content">
                  {dragItem && (
                    <div className="drag-preview">
                      Dropping: {dragItem.data.name}
                    </div>
                  )}
                  <div className="drop-zone-instructions">
                    Drag components here to build your page
                  </div>
                </div>
              </div>

              {/* Render regions */}
              <div className="regions-container">
                {regions.map(region => (
                  <div
                    key={region.id || region.name} // Use temporary key if no ID
                    className={`region region-${region.region_type}`}
                    data-region-id={region.id}
                  >
                    <div className="region-header">
                      <h3>{region.name}</h3>
                      <span className="region-type">{region.region_type}</span>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteRegion(region.id)}
                        title="Delete Region"
                      >
                        ×
                      </button>
                    </div>
                    <div className="region-body">
                      <div className="region-placeholder">
                        Drop items here to build this region
                      </div>
                    </div>
                    <div className="region-footer">
                      <div className="region-actions">
                        <button className="btn btn-sm btn-outline" onClick={() => alert(`Configure ${region.name}`)}>
                          Configure
                        </button>
                        <button className="btn btn-sm btn-outline" onClick={() => alert(`Add content to ${region.name}`)}>
                          Add Content
                        </button>
                      </div>
                    </div>
                  >
                ))}
              </div>

              {/* Render items */}
              <div className="items-container">
                {items.map(item => (
                  <div
                    key={item.id || item.name}
                    className={`item item-${item.item_type}`}
                    data-item-id={item.id}
                  >
                    <div className="item-header">
                      <h4>{item.label || item.name}</h4>
                      <span className="item-type">{item.item_type}</span>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteItem(item.id)}
                        title="Delete Item"
                      >
                        ×
                      </button>
                    </div>
                    <div className="item-body">
                      <div className="item-preview">
                        {/* Simple preview based on item type */}
                        {item.item_type === 'text' && (
                          <input type="text" placeholder={item.placeholder} readOnly className="item-preview-input" />
                        )}
                        {item.item_type === 'textarea' && (
                          <textarea placeholder={item.placeholder} readOnly className="item-preview-textarea" />
                        )}
                        {item.item_type === 'select' && (
                          <select className="item-preview-select" disabled>
                            <option>Select an option</option>
                          </select>
                        )}
                        {item.item_type === 'checkbox' && (
                          <div className="item-preview-checkbox">
                            <input type="checkbox" readOnly />
                            <span>{item.label}</span>
                          </div>
                        )}
                        {item.item_type === 'date_picker' && (
                          <input type="date" readOnly className="item-preview-date" />
                        )}
                        {/* Add more previews as needed */}
                      </div>
                    </div>
                    <div className="item-footer">
                      <div className="item-actions">
                        <button className="btn btn-sm btn-outline" onClick={() => alert(`Configure ${item.label}`)}>
                          Configure
                        </button>
                      </div>
                    </div>
                  >
                ))}
              </div>
            </div>
          </div>

          {/* Property panel (appears when clicking on an element) */}
          {selectedElement && (
            <div className="property-panel">
              <div className="property-panel-header">
                <h3>Properties</h>
                <button className="btn btn-sm btn-outline" onClick={() => setSelectedElement(null)}>
                  ×
                </button>
              </div>
              <div className="panel-body">
                {/* Property fields would go here based on selected element type */}
                <div className="property-group">
                  <label className="property-label">Name</label>
                  <input type="text" className="property-input" placeholder="Enter name" />
                </div>
                <div className="property-group">
                  <label className="property-label">Type</label>
                  <input type="text" className="property-input" readOnly value={selectedElement?.type || ''} />
                </div>
                {/* More properties based on element type */}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PageBuilder;