'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Icon } from '@iconify/react';
import { applicationService, Application } from '@/app/api/services/applications';
import { pageService } from '@/app/api/services/pages';

export default function NewPageForm() {
  const params = useParams();
  const router = useRouter();
  const appId = params.appId as string;

  const [app, setApp] = useState<Application | null>(null);
  const [form, setForm] = useState({
    name: '',
    alias: '',
    title: '',
    page_number: 1,
    is_active: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadApp = async () => {
      try {
        setLoading(true);
        const fetched = await applicationService.getById(appId);
        setApp(fetched);

        const pages = await pageService.getByAppId(appId).catch(() => []);
        const nextNumber = pages.length + 1;
        setForm(prev => ({
          ...prev,
          name: `Page ${nextNumber}`,
          alias: `PAGE${nextNumber}`,
          page_number: nextNumber,
        }));
      } catch (err: any) {
        setError(err.message || 'Failed to load application');
      } finally {
        setLoading(false);
      }
    };
    loadApp();
  }, [appId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await pageService.create({
        name: form.name || 'Untitled Page',
        alias: form.alias || 'PAGE',
        title: form.title || form.name || 'Untitled Page',
        page_number: parseInt(String(form.page_number || 1), 10),
        is_active: form.is_active,
        application_id: parseInt(appId, 10),
      });
      router.push(`/apps/builder/${appId}/pages/${created.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create page');
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-gray-500">
        <Icon icon="solar:spinner-linear" className="animate-spin text-4xl mx-auto mb-2 text-blue-600" />
        <p>Loading application...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between bg-white dark:bg-dark-card p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
            <Link href="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <Link href={`/apps/builder/${appId}`} className="hover:underline">{app?.name}</Link>
            <span>/</span>
            <span>New Page</span>
          </div>
          <h1 className="text-2xl font-bold">Create New Page</h1>
        </div>
        <Link
          href={`/apps/builder/${appId}`}
          className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          ← Back
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200 text-sm">
          Error: {error}
        </div>
      )}

      <div className="bg-white dark:bg-dark-card p-6 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Icon icon="solar:document-bold" className="text-blue-600" />
          Page Details
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Page Name *
              </label>
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. Employee List"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Page Alias *
              </label>
              <input
                type="text"
                name="alias"
                value={form.alias}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="e.g. EMP_LIST"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Page Title
            </label>
            <input
              type="text"
              name="title"
              value={form.title}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Page title shown in browser (defaults to page name)"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Page Number
              </label>
              <input
                type="number"
                name="page_number"
                value={form.page_number}
                onChange={handleChange}
                min={1}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={form.is_active}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium cursor-pointer">
                Active Page
              </label>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl shadow transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Icon icon="solar:save-bold" />
              {saving ? 'Creating...' : 'Create Page & Open Builder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
