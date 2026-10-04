'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Icon } from '@iconify/react';
import { applicationService, Application } from '@/app/api/services/applications';
import { pageService, Page } from '@/app/api/services/pages';

export default function PreviewPage() {
  const params = useParams();
  const appId = params.appId as string;
  const pageId = params.pageId as string;

  const [application, setApplication] = useState<Application | null>(null);
  const [page, setPage] = useState<Page | null>(null);
  const [htmlContent, setHtmlContent] = useState<string>('Loading server preview...');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [viewportWidth, setViewportWidth] = useState<'full' | 'tablet' | 'mobile'>('full');

  useEffect(() => {
    const loadMetadataAndPreview = async () => {
      try {
        setLoading(true);
        setError(null);

        const fetchedApp = await applicationService.getById(appId);
        setApplication(fetchedApp);

        const fetchedPage = await pageService.getById(pageId);
        setPage(fetchedPage);

        // Request server-rendered HTML from backend FastAPI rendering engine
        const appAlias = fetchedApp.alias || 'app';
        const pageNumber = fetchedPage.page_number || 1;

        try {
          const sessionToken =
            typeof window !== 'undefined' ? window.localStorage.getItem('miniui_token') : null;
          const sessionParam = sessionToken ? `?session_id=${encodeURIComponent(sessionToken)}` : '';
          const response = await fetch(`/app/${appAlias}/${pageNumber}${sessionParam}`, {
            signal: AbortSignal.timeout(15000),
          });
          setBackendOnline(true);
          if (response.ok) {
            const html = await response.text();
            setHtmlContent(html);
          } else {
            throw new Error(`Rendering engine returned status ${response.status}`);
          }
        } catch (fetchErr: any) {
          setBackendOnline(false);
          setError(
            (fetchErr.name === 'TimeoutError' || fetchErr.name === 'AbortError')
              ? 'The rendering request timed out. Verify the backend server (FastAPI) is running on localhost:8000.'
              : fetchErr.message === 'Failed to fetch'
                ? 'Backend rendering engine is unreachable. Make sure the backend server is running on localhost:8000.'
                : fetchErr.message || 'Failed to render page preview.'
          );
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load page metadata');
      } finally {
        setLoading(false);
      }
    };

    loadMetadataAndPreview();
  }, [appId, pageId]);

  const getViewportClass = () => {
    switch (viewportWidth) {
      case 'mobile': return 'max-w-[375px] mx-auto border-x-4 border-gray-800 rounded-3xl overflow-hidden shadow-2xl';
      case 'tablet': return 'max-w-[768px] mx-auto border-x-4 border-gray-800 rounded-2xl overflow-hidden shadow-xl';
      default: return 'w-full';
    }
  };

  const buildStandaloneUrl = () => {
    if (page?.page_number == null) return null;
    const token = typeof window !== 'undefined' ? window.localStorage.getItem('miniui_token') : null;
    return `/app/${application?.alias}/${page?.page_number}${
      token ? `?session_id=${encodeURIComponent(token)}` : ''
    }`;
  };

  // One standalone tab per application: a named window is reused (and
  // navigated to the latest URL, so it always shows fresh content) instead
  // of opening a new tab on every click.
  const openStandalone = () => {
    const url = buildStandaloneUrl();
    if (!url) return;
    const target = `miniui-standalone-${application?.alias ?? appId}`;
    const win = window.open(url, target);
    if (win) win.focus();
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-gray-500">
        <Icon icon="solar:spinner-linear" className="animate-spin text-4xl mx-auto mb-2 text-blue-600" />
        <p>Loading live application preview from rendering engine...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Top Controls Bar */}
      <div className="bg-white dark:bg-darkgray p-4 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
            <Link href="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <Link href={`/apps/builder/${appId}`} className="hover:underline">{application?.name}</Link>
            <span>/</span>
            <span>Preview</span>
          </div>
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Icon icon="solar:eye-bold" className="text-blue-600" />
            Preview: {application?.name} — {page?.name}
          </h1>
        </div>

        {/* Viewport Width Controls */}
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
          <button
            onClick={() => setViewportWidth('full')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
              viewportWidth === 'full' ? 'bg-white dark:bg-gray-700 shadow text-blue-600' : 'text-gray-500'
            }`}
          >
            <Icon icon="solar:laptop-bold" />
            Desktop
          </button>
          <button
            onClick={() => setViewportWidth('tablet')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
              viewportWidth === 'tablet' ? 'bg-white dark:bg-gray-700 shadow text-blue-600' : 'text-gray-500'
            }`}
          >
            <Icon icon="solar:tablet-bold" />
            Tablet
          </button>
          <button
            onClick={() => setViewportWidth('mobile')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition ${
              viewportWidth === 'mobile' ? 'bg-white dark:bg-gray-700 shadow text-blue-600' : 'text-gray-500'
            }`}
          >
            <Icon icon="solar:smartphone-bold" />
            Mobile
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/apps/builder/${appId}/pages/${pageId}`}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200 text-xs font-semibold rounded-xl flex items-center gap-1 transition"
          >
            ← Back to Page Builder
          </Link>
          {page?.page_number != null ? (
            <button
              onClick={openStandalone}
              title="Opens once per application and always shows the latest saved page"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl flex items-center gap-1 transition"
            >
              Open Standalone
              <Icon icon="solar:export-bold" />
            </button>
          ) : (
            <span
              title="Waiting for page metadata to load"
              className="px-4 py-2 bg-blue-300 text-white text-xs font-semibold rounded-xl flex items-center gap-1 cursor-not-allowed"
            >
              Open Standalone
              <Icon icon="solar:export-bold" />
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-sm rounded-xl border border-red-200 dark:border-red-800">
          <p className="font-semibold flex items-center gap-2">
            <Icon icon="solar:danger-triangle-bold" />
            Preview Unavailable
          </p>
          <p className="mt-1 text-xs">{error}</p>
          {backendOnline === false && (
            <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              The preview renders server-side through the FastAPI rendering engine. Start the backend with{' '}
              <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">uvicorn main:app --reload</code>{' '}
              (port 8000) and refresh this page.
            </p>
          )}
        </div>
      )}

      {/* Frame Container */}
      {/* NOTE: backend returns a FULL HTML document (with its own global
          stylesheet apexos.css). It must be isolated in an iframe — injecting
          it via dangerouslySetInnerHTML would load apexos.css into the
          dashboard page itself, where its global `* { margin: 0; padding: 0 }`
          reset overrides Tailwind utilities and breaks the header/sidebar
          layout. */}
      <div className="bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm min-h-[700px]">
        <div className={getViewportClass()}>
          <iframe
            title={`Preview of ${application?.name ?? 'application'} — ${page?.name ?? 'page'}`}
            srcDoc={htmlContent}
            className="w-full h-[600px] bg-white rounded-xl border border-gray-100 dark:border-gray-700"
          />
        </div>
      </div>
    </div>
  );
}
