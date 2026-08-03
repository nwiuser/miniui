import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './Preview.css';

const Preview = () => {
  const { appId, pageId } = useParams();
  const navigate = useNavigate();
  const [previewContent, setPreviewContent] = useState('Loading...');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [application, setApplication] = useState(null);
  const [page, setPage] = useState(null);

  useEffect(() => {
    const loadApplicationAndPage = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load application data
        if (appId) {
          const appResponse = await fetch(`/api/applications/${appId}/`);
          if (appResponse.ok) {
            const appData = await appResponse.json();
            setApplication(appData);
          } else {
            throw new Error('Failed to load application data');
          }
        }

        // Load page data
        if (pageId) {
          const pageResponse = await fetch(`/api/pages/${pageId}/`);
          if (pageResponse.ok) {
            const pageData = await pageResponse.json();
            setPage(pageData);
          } else {
            throw new Error('Failed to load page data');
          }
        }
      } catch (err) {
        setError(`Failed to load application or page: ${err.message}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (appId !== undefined && pageId !== undefined) {
      loadApplicationAndPage();
    } else {
      setLoading(false);
      setError('Missing application or page ID');
    }
  }, [appId, pageId]);

  useEffect(() => {
    const loadPreview = async () => {
      try {
        setLoading(true);
        setError(null);

        // Construct the preview URL based on the application and page
        // This would typically be something like: /app/{application.alias}/{page.page_number}
        const appAlias = application?.alias || 'app';
        const pageNumber = page?.page_number || 1;

        // Fetch the rendered page from the backend
        const response = await fetch(`/app/${appAlias}/${pageNumber}`);

        if (response.ok) {
          const htmlContent = await response.text();
          setPreviewContent(htmlContent);
        } else {
          throw new Error(`Failed to load preview: ${response.status}`);
        }
      } catch (err) {
        setError(`Error loading preview: ${err.message}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (application && page) {
      loadPreview();
    } else {
      setLoading(false);
      setError('Application or page data not available');
    }
  }, [application, page]);

  if (loading) return <div className="preview-loading">Loading preview...</div>;
  if (error) return <div className="preview-error">{error}</div>;

  return (
    <div className="preview-container">
      <div className="preview-header">
        <h2>Preview: {application?.name} - {page?.name}</h2>
        <div className="preview-actions">
          <button className="btn btn-outline" onClick={() => navigate(`/app/${appId}/${pageId}/builder`)}>
            ← Back to Editor
          </button>
          <button className="btn btn-secondary" onClick={() => window.open(`/app/${application?.alias}/${page?.page_number}`, '_blank')}>
            Open in New Tab
          </button>
        </div>
      </div>

      <div className="preview-content">
        {/* Using dangerouslySetInnerHTML because we're getting actual HTML from the backend */}
        <div
          className="preview-frame"
          dangerouslySetInnerHTML={{ __html: previewContent }}
        />
      </div>
    </div>
  );
};

export default Preview;