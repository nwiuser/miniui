'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Icon } from '@iconify/react';
import { applicationService, Application } from '@/app/api/services/applications';
import { pageService, Page } from '@/app/api/services/pages';
import { regionService, Region } from '@/app/api/services/regions';

interface AppWithStats extends Application {
  pageCount: number;
  regionCount: number;
}

export default function ApplicationsPage() {
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
          try {
            const pages: Page[] = await pageService.getByAppId(app.id);
            pageCount = pages.length;
            const regionPromises = pages.map(p => regionService.getByPageId(p.id).catch(() => [] as Region[]));
            const regionResults = await Promise.all(regionPromises);
            regionCount = regionResults.reduce((acc, r) => acc + r.length, 0);
          } catch {
            // Stats are best-effort; leave as 0
          }
          return { ...app, pageCount, regionCount };
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

  const filteredApps = apps.filter(app =>
    app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.alias.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (app.description && app.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Applications</h1>
          <p className="text-sm text-gray-500 mt-1">Browse all applications, or launch the visual builder to edit one.</p>
        </div>
        <Link
          href="/apps/new"
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2.5 rounded-xl shadow transition"
        >
          <Icon icon="solar:add-circle-bold" className="text-xl" />
          New Application
        </Link>
      </div>

      <div className="bg-white dark:bg-dark-card rounded-2xl border border-gray-100 dark:border-gray-800 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h2 className="font-bold">All Applications ({apps.length})</h2>
            <p className="text-sm text-gray-500">Select an application to open its builder.</p>
          </div>
          <div className="relative w-full md:w-64">
            <Icon icon="solar:magnifer-linear" className="absolute left-3 top-3 text-gray-400 text-lg" />
            <input
              type="text"
              placeholder="Search applications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-500">
            <Icon icon="solar:spinner-linear" className="animate-spin text-3xl mx-auto mb-2 text-blue-600" />
            <p>Loading applications...</p>
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
                className="group bg-gray-50 dark:bg-gray-800/40 hover:bg-white dark:hover:bg-gray-800/80 border border-gray-200/80 dark:border-gray-700/80 hover:border-blue-500 dark:hover:border-blue-500 rounded-2xl p-5 transition duration-200 cursor-pointer shadow-sm hover:shadow-md flex flex-col justify-between"
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

                <div className="pt-4 border-t border-gray-200/60 dark:border-gray-700/60">
                  <div className="flex items-center justify-around text-center mb-4">
                    <div>
                      <p className="text-lg font-bold text-blue-600">{app.pageCount}</p>
                      <p className="text-[11px] text-gray-400">Pages</p>
                    </div>
                    <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
                    <div>
                      <p className="text-lg font-bold text-indigo-600">{app.regionCount}</p>
                      <p className="text-[11px] text-gray-400">Regions</p>
                    </div>
                    <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
                    <div>
                      <p className="text-lg font-bold text-gray-500">#{app.id}</p>
                      <p className="text-[11px] text-gray-400">App ID</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
                    <Link
                      href={`/apps/builder/${app.id}`}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1 transition"
                    >
                      <Icon icon="solar:pen-bold" />
                      Builder
                    </Link>
                    <Link
                      href={`/apps/builder/${app.id}`}
                      className="text-xs text-gray-400 hover:text-blue-600 transition flex items-center gap-1"
                    >
                      Open
                      <Icon icon="solar:arrow-right-bold" />
                    </Link>
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
