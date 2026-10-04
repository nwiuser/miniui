'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Icon } from '@iconify/react';
import { applicationService, Application } from '@/app/api/services/applications';
import { pageService, Page } from '@/app/api/services/pages';
import { regionService, Region } from '@/app/api/services/regions';
import { itemService, PageItem } from '@/app/api/services/items';

interface AppWithStats extends Application {
  pageCount: number;
  regionCount: number;
  itemCount: number;
}

export default function MiniUIDashboard() {
  const router = useRouter();
  const [apps, setApps] = useState<AppWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await applicationService.getAll();

      const withStats = await Promise.all(
        (data || []).map(async (app): Promise<AppWithStats> => {
          let pageCount = 0;
          let regionCount = 0;
          let itemCount = 0;
          try {
            const pages: Page[] = await pageService.getByAppId(app.id);
            pageCount = pages.length;
            for (const p of pages) {
              const regions: Region[] = await regionService.getByPageId(p.id).catch(() => [] as Region[]);
              regionCount += regions.length;
              const items: PageItem[] = await itemService.getByPageId(p.id).catch(() => [] as PageItem[]);
              itemCount += items.length;
            }
          } catch {
            // Stats are best-effort; leave as 0
          }
          return { ...app, pageCount, regionCount, itemCount };
        })
      );

      setApps(withStats);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleDeleteApp = async (e: React.MouseEvent, appId: number, appName: string) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete application "${appName}"?`)) {
      try {
        await applicationService.delete(appId);
        setApps(prev => prev.filter(app => app.id !== appId));
      } catch (err: any) {
        alert(`Failed to delete application: ${err.message}`);
      }
    }
  };

  const filteredApps = apps.filter(app =>
    app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.alias.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (app.description && app.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const activeAppsCount = apps.filter(app => app.is_active).length;
  const totalPages = apps.reduce((acc, app) => acc + (app.pageCount || 0), 0);
  const totalItems = apps.reduce((acc, app) => acc + (app.itemCount || 0), 0);
  const totalRegions = apps.reduce((acc, app) => acc + (app.regionCount || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">MiniUI Platform Dashboard</h1>
          <p className="text-blue-100 mt-1">Manage and build your metadata-driven low-code web applications.</p>
        </div>
        <Link
          href="/apps/new"
          className="inline-flex items-center gap-2 bg-white text-blue-700 hover:bg-blue-50 font-semibold px-4 py-2.5 rounded-xl shadow transition duration-200"
        >
          <Icon icon="solar:add-circle-bold" className="text-xl" />
          New Application
        </Link>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-darkgray p-5 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Applications</p>
              <h3 className="text-2xl font-bold mt-1">{apps.length}</h3>
            </div>
            <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 text-blue-600 rounded-xl flex items-center justify-center">
              <Icon icon="solar:layers-line-duotone" className="text-2xl" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-darkgray p-5 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Active Applications</p>
              <h3 className="text-2xl font-bold mt-1 text-emerald-600">{activeAppsCount}</h3>
            </div>
            <div className="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 rounded-xl flex items-center justify-center">
              <Icon icon="solar:check-circle-bold-duotone" className="text-2xl" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-darkgray p-5 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Pages</p>
              <h3 className="text-2xl font-bold mt-1 text-indigo-600">{totalPages}</h3>
            </div>
            <div className="w-12 h-12 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 rounded-xl flex items-center justify-center">
              <Icon icon="solar:document-bold-duotone" className="text-2xl" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-darkgray p-5 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Items</p>
              <h3 className="text-2xl font-bold mt-1 text-purple-600">{totalItems}</h3>
            </div>
            <div className="w-12 h-12 bg-purple-50 dark:bg-purple-900/30 text-purple-600 rounded-xl flex items-center justify-center">
              <Icon icon="solar:text-square-bold-duotone" className="text-2xl" />
            </div>
          </div>
        </div>
      </div>

      {/* Applications Section */}
      <div className="bg-white dark:bg-darkgray rounded-2xl border border-gray-100 dark:border-gray-800 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold">Your Applications</h2>
            <p className="text-sm text-gray-500">Select an application to launch the visual builder or edit metadata.</p>
          </div>
          <div className="relative w-full md:w-64">
            <Icon icon="solar:magnifer-linear" className="absolute left-3 top-3 text-gray-400 text-lg" />
            <input
              type="text"
              placeholder="Search applications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-dark dark:text-gray-200 placeholder:text-gray-400"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-500">
            <Icon icon="solar:spinner-linear" className="animate-spin text-3xl mx-auto mb-2 text-blue-600" />
            <p>Loading applications from backend...</p>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 dark:bg-red-950/40 text-red-600 rounded-xl border border-red-200 dark:border-red-800 flex items-center justify-between">
            <span>Error: {error}</span>
            <button
              onClick={fetchApplications}
              className="px-3 py-1 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
            <Icon icon="solar:folder-open-bold-duotone" className="text-5xl text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">No Applications Found</h3>
            <p className="text-sm text-gray-500 mb-4">Create your first application to start building forms and reports.</p>
            <Link
              href="/apps/new"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-xl"
            >
              + Create Application
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredApps.map(app => (
              <div
                key={app.id}
                onClick={() => router.push(`/apps/builder/${app.id}`)}
                className="group bg-gray-50 dark:bg-dark hover:bg-white dark:hover:bg-gray-800 border border-gray-200/80 dark:border-gray-700/80 hover:border-blue-500 dark:hover:border-blue-500 rounded-2xl p-5 transition duration-200 cursor-pointer shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-600 text-white rounded-xl flex items-center justify-center font-bold text-lg">
                        {app.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900 dark:text-white group-hover:text-blue-600 transition">
                          {app.name}
                        </h3>
                        <span className="text-xs text-gray-500 font-mono">Alias: {app.alias}</span>
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                      app.is_active
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {app.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-4">
                    {app.description || 'No description provided.'}
                  </p>
                </div>

                <div className="flex items-center gap-4 mb-4 px-3 py-2 bg-white dark:bg-darkgray rounded-xl border border-gray-100 dark:border-gray-700 text-center" onClick={(e) => e.stopPropagation()}>
                  <div className="flex-1">
                    <p className="text-base font-bold text-blue-600">{app.pageCount}</p>
                    <p className="text-[10px] text-gray-400">Pages</p>
                  </div>
                  <div className="w-px h-6 bg-gray-200 dark:bg-gray-700" />
                  <div className="flex-1">
                    <p className="text-base font-bold text-indigo-600">{app.regionCount}</p>
                    <p className="text-[10px] text-gray-400">Regions</p>
                  </div>
                  <div className="w-px h-6 bg-gray-200 dark:bg-gray-700" />
                  <div className="flex-1">
                    <p className="text-base font-bold text-purple-600">{app.itemCount}</p>
                    <p className="text-[10px] text-gray-400">Items</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200/60 dark:border-gray-700/60 flex items-center justify-between">
                  <span className="text-xs text-gray-400 font-mono">ID: #{app.id}</span>
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <Link
                      href={`/apps/builder/${app.id}`}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1 transition"
                    >
                      <Icon icon="solar:pen-bold" />
                      Builder
                    </Link>
                    <button
                      onClick={(e) => handleDeleteApp(e, app.id, app.name)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg transition"
                      title="Delete Application"
                    >
                      <Icon icon="solar:trash-bin-trash-bold" className="text-base" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
