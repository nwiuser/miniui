'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Icon } from '@iconify/react';
import { applicationService, Application } from '@/app/api/services/applications';
import { pageService, Page } from '@/app/api/services/pages';
import { lovService, Lov } from '@/app/api/services/lovs';
import { restDataSourceService, RestDataSource } from '@/app/api/services/rest-data-sources';

export default function ApplicationBuilderPage() {
  const params = useParams();
  const router = useRouter();
  const appId = params.appId as string;
  // '/apps/new' reuses this component without an appId route param, so a
  // missing appId must behave as create-mode instead of fetching id
  // 'undefined' from the API.
  const isNew = !appId || appId === 'new';

  const [appData, setAppData] = useState<Partial<Application>>({
    name: '',
    alias: '',
    description: '',
    theme: 'default',
    is_active: true,
  });

  const [pages, setPages] = useState<Page[]>([]);
  const [lovs, setLovs] = useState<Lov[]>([]);
  const [restSources, setRestSources] = useState<RestDataSource[]>([]);
  const [showLovs, setShowLovs] = useState(false);
  const [showRestSources, setShowRestSources] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;

    const loadAppAndPages = async () => {
      try {
        setLoading(true);
        setError(null);

        const fetchedApp = await applicationService.getById(appId);
        setAppData(fetchedApp);

        try {
          const fetchedPages = await pageService.getByAppId(appId);
          setPages(fetchedPages || []);
        } catch {
          setPages([]);
        }

        try {
          const fetchedLovs = await lovService.getAll();
          setLovs(fetchedLovs || []);
        } catch {
          setLovs([]);
        }

        try {
          const fetchedRestSources = await restDataSourceService.getByAppId(appId);
          setRestSources(fetchedRestSources || []);
        } catch {
          setRestSources([]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load application');
      } finally {
        setLoading(false);
      }
    };

    loadAppAndPages();
  }, [appId, isNew]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setAppData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSaveApp = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (isNew) {
        const created = await applicationService.create({
          name: appData.name || '',
          alias: appData.alias || '',
          description: appData.description || '',
          theme: appData.theme || 'default',
          is_active: appData.is_active ?? true,
        });
        router.push(`/apps/builder/${created.id}`);
      } else {
        await applicationService.update(appId, {
          name: appData.name,
          alias: appData.alias,
          description: appData.description,
          theme: appData.theme,
          is_active: appData.is_active,
        });
        alert('Application settings saved successfully!');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save application');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePage = async (pageId: number, pageName: string) => {
    if (confirm(`Are you sure you want to delete page "${pageName}"?`)) {
      try {
        await pageService.delete(pageId);
        setPages(prev => prev.filter(p => p.id !== pageId));
      } catch (err: any) {
        alert(`Failed to delete page: ${err.message}`);
      }
    }
  };

  const handleAddLov = () => {
    const newLov: Lov = {
      lov_name: `LOV_${Date.now()}`,
      lov_definition: '',
      is_static: true,
      static_values: '',
      is_active: true,
    };
    setLovs(prev => [...prev, newLov]);
  };

  const handleUpdateLov = async (index: number, field: string, value: any) => {
    const lov = lovs[index];
    const updated = { ...lov, [field]: value };
    setLovs(prev => prev.map((l, i) => i === index ? updated : l));

    if (lov.id) {
      try {
        await lovService.update(lov.id, { [field]: value });
      } catch (err: any) {
        alert(`Failed to update LOV: ${err.message}`);
      }
    }
  };

  const handleSaveLov = async (index: number) => {
    const lov = lovs[index];
    try {
      if (lov.id) {
        await lovService.update(lov.id, lov);
      } else {
        const created = await lovService.create({
          lov_name: lov.lov_name,
          lov_definition: lov.lov_definition,
          is_static: lov.is_static,
          static_values: lov.static_values,
          is_active: lov.is_active,
        });
        setLovs(prev => prev.map((l, i) => i === index ? created : l));
      }
    } catch (err: any) {
      alert(`Failed to save LOV: ${err.message}`);
    }
  };

  const handleDeleteLov = async (index: number) => {
    const lov = lovs[index];
    if (confirm(`Delete LOV "${lov.lov_name}"?`)) {
      if (lov.id) {
        try {
          await lovService.delete(lov.id);
        } catch (err: any) {
          alert(`Failed to delete LOV: ${err.message}`);
        }
      }
      setLovs(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleAddRestSource = () => {
    const newSource: RestDataSource = {
      application_id: parseInt(appId, 10),
      name: `REST_${Date.now()}`,
      url: 'https://',
      method: 'GET',
      timeout: 30,
      is_active: true,
    };
    setRestSources(prev => [...prev, newSource]);
  };

  const handleUpdateRestSource = async (index: number, field: string, value: any) => {
    const source = restSources[index];
    const updated = { ...source, [field]: value };
    setRestSources(prev => prev.map((s, i) => i === index ? updated : s));

    if (source.id) {
      try {
        await restDataSourceService.update(source.id, { [field]: value });
      } catch (err: any) {
        alert(`Failed to update REST data source: ${err.message}`);
      }
    }
  };

  const handleSaveRestSource = async (index: number) => {
    const source = restSources[index];
    try {
      if (source.id) {
        await restDataSourceService.update(source.id, {
          name: source.name,
          url: source.url,
          method: source.method,
          timeout: source.timeout,
          is_active: source.is_active,
          query_params: source.query_params,
          response_mapping: source.response_mapping,
        });
        alert('REST data source saved successfully!');
      } else {
        const created = await restDataSourceService.create({
          application_id: parseInt(appId, 10),
          name: source.name,
          url: source.url,
          method: source.method,
          timeout: source.timeout,
          is_active: source.is_active,
          query_params: source.query_params,
          response_mapping: source.response_mapping,
        });
        setRestSources(prev => prev.map((s, i) => i === index ? created : s));
        alert('REST data source created successfully!');
      }
    } catch (err: any) {
      alert(`Failed to save REST data source: ${err.message}`);
    }
  };

  const handleTestRestSource = async (index: number) => {
    const source = restSources[index];
    if (!source.id) {
      alert('Save the REST data source before testing it.');
      return;
    }
    try {
      const result = await restDataSourceService.execute(source.id);
      alert(`OK (${result.status_code})\nData: ${JSON.stringify(result.data).slice(0, 300)}`);
    } catch (err: any) {
      alert(`Test failed: ${err.message}`);
    }
  };

  const handleDeleteRestSource = async (index: number) => {
    const source = restSources[index];
    if (confirm(`Delete REST data source "${source.name}"?`)) {
      if (source.id) {
        try {
          await restDataSourceService.delete(source.id);
        } catch (err: any) {
          alert(`Failed to delete REST data source: ${err.message}`);
        }
      }
      setRestSources(prev => prev.filter((_, i) => i !== index));
    }
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-gray-500">
        <Icon icon="solar:spinner-linear" className="animate-spin text-4xl mx-auto mb-2 text-blue-600" />
        <p>Loading application details...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Link href="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <span>{isNew ? 'New Application' : appData.name}</span>
          </div>
          <h1 className="text-2xl font-bold">
            {isNew ? 'Create New Application' : `Application Builder: ${appData.name}`}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            ← Back to Dashboard
          </Link>
          <button
            onClick={handleSaveApp}
            disabled={saving}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl shadow transition disabled:opacity-50 flex items-center gap-2"
          >
            <Icon icon="solar:diskette-bold" />
            {saving ? 'Saving...' : 'Save Application'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200 text-sm">
          Error: {error}
        </div>
      )}

      {/* Application Properties Form */}
      <div className="bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Icon icon="solar:settings-bold" className="text-blue-600" />
          Application Settings
        </h2>

        <form onSubmit={handleSaveApp} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Application Name *
              </label>
              <input
                type="text"
                name="name"
                value={appData.name || ''}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. Employee HR Portal"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Application Alias *
              </label>
              <input
                type="text"
                name="alias"
                value={appData.alias || ''}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. HRAPP"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              name="description"
              rows={3}
              value={appData.description || ''}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Describe the application scope and utility..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Theme Palette
              </label>
              <select
                name="theme"
                value={appData.theme || 'default'}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="default">Default Blue</option>
                <option value="dark">Sleek Dark</option>
                <option value="emerald">Emerald Green</option>
                <option value="purple">Royal Purple</option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={appData.is_active ?? true}
                onChange={handleInputChange}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium cursor-pointer">
                Active Application Status
              </label>
            </div>
          </div>
        </form>
      </div>

      {/* Pages List Section */}
      {!isNew && (
        <div className="bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Icon icon="solar:document-bold" className="text-blue-600" />
                Application Pages ({pages.length})
              </h2>
              <p className="text-sm text-gray-500">Design forms, data tables, and dashboard pages.</p>
            </div>

            <Link
              href={`/apps/builder/${appId}/pages/new`}
              className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold px-4 py-2 rounded-xl shadow transition"
            >
              <Icon icon="solar:add-circle-bold" />
              + New Page
            </Link>
          </div>

          {pages.length === 0 ? (
            <div className="py-8 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
              <Icon icon="solar:document-text-bold-duotone" className="text-4xl text-gray-300 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">No pages created yet.</p>
              <Link
                href={`/apps/builder/${appId}/pages/new`}
                className="inline-block mt-3 text-sm text-blue-600 font-semibold hover:underline"
              >
                + Add your first page
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {pages.map(page => (
                <div key={page.id} className="py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/40 px-3 rounded-xl transition">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 bg-blue-100 text-blue-800 text-xs font-bold rounded-md flex items-center justify-center">
                        #{page.page_number}
                      </span>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{page.name}</h4>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 font-mono">
                      Alias: {page.alias} | Title: {page.title || page.name}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/apps/builder/${appId}/pages/${page.id}`}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1"
                    >
                      <Icon icon="solar:pen-bold" />
                      Visual Builder
                    </Link>
                    <Link
                      href={`/apps/builder/${appId}/pages/${page.id}/preview`}
                      className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-xs font-semibold rounded-lg flex items-center gap-1"
                    >
                      <Icon icon="solar:eye-bold" />
                      Preview
                    </Link>
                    <button
                      onClick={() => handleDeletePage(page.id, page.name)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                      title="Delete Page"
                    >
                      <Icon icon="solar:trash-bin-trash-bold" className="text-base" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* LOV Management Section */}
      {!isNew && (
        <div className="bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <button
            onClick={() => setShowLovs(!showLovs)}
            className="w-full flex justify-between items-center"
          >
            <div className="flex items-center gap-2">
              <Icon icon="solar:list-check-bold" className="text-purple-600" />
              <h2 className="text-lg font-bold">Lists of Values ({lovs.length})</h2>
            </div>
            <Icon
              icon={showLovs ? 'solar:alt-arrow-up-bold' : 'solar:alt-arrow-down-bold'}
              className="text-gray-400"
            />
          </button>

          {showLovs && (
            <div className="mt-4 space-y-4">
              <p className="text-sm text-gray-500">Manage dropdown/select options used across your application.</p>

              <button
                onClick={handleAddLov}
                className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold px-4 py-2 rounded-xl shadow transition"
              >
                <Icon icon="solar:add-circle-bold" />
                + New LOV
              </button>

              {lovs.length === 0 ? (
                <div className="py-8 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
                  <Icon icon="solar:list-check-bold" className="text-4xl text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">No LOVs created yet.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {lovs.map((lov, index) => (
                    <div key={lov.id || index} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="text"
                          value={lov.lov_name}
                          onChange={(e) => handleUpdateLov(index, 'lov_name', e.target.value)}
                          className="flex-1 px-3 py-1.5 border rounded-lg text-sm font-medium"
                          placeholder="LOV Name"
                        />
                        <label className="flex items-center gap-2 text-xs">
                          <input
                            type="checkbox"
                            checked={lov.is_static ?? true}
                            onChange={(e) => handleUpdateLov(index, 'is_static', e.target.checked)}
                            className="w-4 h-4"
                          />
                          Static
                        </label>
                        <button
                          onClick={() => handleSaveLov(index)}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => handleDeleteLov(index)}
                          className="p-1.5 text-gray-400 hover:text-red-600"
                        >
                          <Icon icon="solar:trash-bin-trash-bold" />
                        </button>
                      </div>
                      {lov.is_static ? (
                        <textarea
                          value={lov.static_values || ''}
                          onChange={(e) => handleUpdateLov(index, 'static_values', e.target.value)}
                          placeholder="STATIC:Display1:Value1,Display2:Value2"
                          rows={2}
                          className="w-full px-3 py-1.5 border rounded-lg text-xs font-mono"
                        />
                      ) : (
                        <textarea
                          value={lov.lov_definition || ''}
                          onChange={(e) => handleUpdateLov(index, 'lov_definition', e.target.value)}
                          placeholder="SELECT display_value, return_value FROM my_table ORDER BY 1"
                          rows={2}
                          className="w-full px-3 py-1.5 border rounded-lg text-xs font-mono"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    {/* REST Data Sources Section */}
      {!isNew && (
        <div className="bg-white dark:bg-darkgray p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <button
            onClick={() => setShowRestSources(!showRestSources)}
            className="w-full flex justify-between items-center"
          >
            <div className="flex items-center gap-2">
              <Icon icon="solar:global-bold" className="text-sky-600" />
              <h2 className="text-lg font-bold">REST Data Sources ({restSources.length})</h2>
            </div>
            <Icon
              icon={showRestSources ? 'solar:alt-arrow-up-bold' : 'solar:alt-arrow-down-bold'}
              className="text-gray-400"
            />
          </button>

          {showRestSources && (
            <div className="mt-4 space-y-4">
              <p className="text-sm text-gray-500">
                Connect pages to external REST services. Define a source here, then reference it from a
                &quot;rest&quot; region in the page builder.
              </p>

              <button
                onClick={handleAddRestSource}
                className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-sm font-semibold px-4 py-2 rounded-xl shadow transition"
              >
                <Icon icon="solar:add-circle-bold" />
                + New REST Data Source
              </button>

              {restSources.length === 0 ? (
                <div className="py-8 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
                  <Icon icon="solar:global-bold" className="text-4xl text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">No REST data sources configured yet.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {restSources.map((source, index) => (
                    <div key={source.id || index} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="text"
                          value={source.name}
                          onChange={(e) => handleUpdateRestSource(index, 'name', e.target.value)}
                          className="flex-1 px-3 py-1.5 border rounded-lg text-sm font-medium"
                          placeholder="Source Name"
                        />
                        <select
                          value={source.method || 'GET'}
                          onChange={(e) => handleUpdateRestSource(index, 'method', e.target.value)}
                          className="px-2 py-1.5 border rounded-lg text-xs font-semibold"
                        >
                          <option value="GET">GET</option>
                          <option value="POST">POST</option>
                          <option value="PUT">PUT</option>
                          <option value="DELETE">DELETE</option>
                        </select>
                        <label className="flex items-center gap-2 text-xs">
                          <input
                            type="checkbox"
                            checked={source.is_active ?? true}
                            onChange={(e) => handleUpdateRestSource(index, 'is_active', e.target.checked)}
                            className="w-4 h-4"
                          />
                          Active
                        </label>
                        <button
                          onClick={() => handleSaveRestSource(index)}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => handleTestRestSource(index)}
                          className="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-semibold rounded-lg"
                          title="Execute and preview the response"
                        >
                          Test
                        </button>
                        <button
                          onClick={() => handleDeleteRestSource(index)}
                          className="p-1.5 text-gray-400 hover:text-red-600"
                          title="Delete Source"
                        >
                          <Icon icon="solar:trash-bin-trash-bold" />
                        </button>
                      </div>
                      <input
                        type="url"
                        value={source.url || ''}
                        onChange={(e) => handleUpdateRestSource(index, 'url', e.target.value)}
                        placeholder="https://api.example.com/v1/endpoint"
                        className="w-full px-3 py-1.5 border rounded-lg text-xs font-mono"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
