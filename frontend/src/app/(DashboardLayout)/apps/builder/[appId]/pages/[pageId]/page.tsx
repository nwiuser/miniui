'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Icon } from '@iconify/react';
import { pageService, Page } from '@/app/api/services/pages';
import { regionService, Region } from '@/app/api/services/regions';
import { itemService, PageItem } from '@/app/api/services/items';
import { validationService, Validation, VALIDATION_TYPES } from '@/app/api/services/validations';
import { pageProcessService, PageProcess, PROCESS_TYPES, EXECUTION_POINTS } from '@/app/api/services/processes';
import { computationService, Computation, COMPUTATION_POINTS, COMPUTATION_TYPES } from '@/app/api/services/computations';

export default function VisualPageBuilder() {
  const params = useParams();
  const router = useRouter();
  const appId = params.appId as string;
  const pageId = params.pageId as string;
  const isNew = pageId === 'new';

  const [pageData, setPageData] = useState<Partial<Page>>({
    name: '',
    alias: '',
    title: '',
    page_number: 1,
    is_active: true,
    application_id: parseInt(appId, 10),
  });

  const [regions, setRegions] = useState<Region[]>([]);
  const [items, setItems] = useState<PageItem[]>([]);
  const [validations, setValidations] = useState<Validation[]>([]);
  const [processes, setProcesses] = useState<PageProcess[]>([]);
  const [computations, setComputations] = useState<Computation[]>([]);
  const [showProcesses, setShowProcesses] = useState(false);
  const [showComputations, setShowComputations] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Drag and drop / Property Inspector state
  const [dragPayload, setDragPayload] = useState<{ kind: 'region' | 'item'; data: any } | null>(null);
  const [selectedElement, setSelectedElement] = useState<{ kind: 'region' | 'item'; id?: number; tempId?: string } | null>(null);

  useEffect(() => {
    if (isNew) return;

    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        const fetchedPage = await pageService.getById(pageId);
        setPageData(fetchedPage);

        try {
          const fetchedRegions = await regionService.getByPageId(pageId);
          setRegions(fetchedRegions || []);
        } catch {
          setRegions([]);
        }

        try {
          const fetchedItems = await itemService.getByPageId(pageId);
          setItems(fetchedItems || []);
        } catch {
          setItems([]);
        }

        try {
          const fetchedValidations = await validationService.getByPageId(pageId);
          setValidations(fetchedValidations || []);
        } catch {
          setValidations([]);
        }

        try {
          const fetchedProcesses = await pageProcessService.getByPageId(pageId);
          setProcesses(fetchedProcesses || []);
        } catch {
          setProcesses([]);
        }

        try {
          const fetchedComputations = await computationService.getByPageId(pageId);
          setComputations(fetchedComputations || []);
        } catch {
          setComputations([]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load page data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [pageId, isNew]);

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setPageData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleDragStart = (kind: 'region' | 'item', data: any) => {
    setDragPayload({ kind, data });
  };

  const handleDropRegion = (data: any) => {
    const tempId = `temp_reg_${Date.now()}`;
    const newRegion: Region = {
      _tempId: tempId,
      name: data.name || 'New Region',
      region_type: data.type || 'static_content',
      source: data.type === 'report' ? 'SELECT id, name FROM sample_table' : '',
      position: regions.length + 1,
      page_id: pageData.id,
      is_active: true,
    };
    setRegions(prev => [...prev, newRegion]);
    setSelectedElement({ kind: 'region', tempId });
  };

  const handleDropItem = (data: any, regionId?: number) => {
    const tempId = `temp_item_${Date.now()}`;
    const newItem: PageItem = {
      _tempId: tempId,
      name: (data.name || 'new_item').toLowerCase().replace(/\s+/g, '_'),
      alias: (data.name || 'NEW_ITEM').toUpperCase().replace(/\s+/g, '_'),
      item_type: data.type || 'text',
      label: data.name || 'New Item',
      placeholder: data.placeholder || '',
      default_value: '',
      is_required: false,
      region_id: regionId || null,
      page_id: pageData.id,
      is_active: true,
    };
    setItems(prev => [...prev, newItem]);
    setSelectedElement({ kind: 'item', tempId });
  };

  const handleDeleteRegion = async (e: React.MouseEvent, region: Region) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete region "${region.name}"?`)) {
      try {
        if (region.id) {
          await regionService.delete(region.id);
        }
        setRegions(prev => prev.filter(r => (r.id ? r.id !== region.id : r._tempId !== region._tempId)));
        if (selectedElement?.kind === 'region' && (selectedElement.id === region.id || selectedElement.tempId === region._tempId)) {
          setSelectedElement(null);
        }
      } catch (err: any) {
        alert(`Failed to delete region: ${err.message}`);
      }
    }
  };

  const handleDeleteItem = async (e: React.MouseEvent, item: PageItem) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete item "${item.label || item.name}"?`)) {
      try {
        if (item.id) {
          await itemService.delete(item.id);
        }
        setItems(prev => prev.filter(i => (i.id ? i.id !== item.id : i._tempId !== item._tempId)));
        if (selectedElement?.kind === 'item' && (selectedElement.id === item.id || selectedElement.tempId === item._tempId)) {
          setSelectedElement(null);
        }
      } catch (err: any) {
        alert(`Failed to delete item: ${err.message}`);
      }
    }
  };

  const handleMoveRegion = (index: number, dir: -1 | 1) => {
    setRegions(prev => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return prev;
      const [moved] = next.splice(index, 1);
      next.splice(target, 0, moved);
      return next.map((r, i) => ({ ...r, position: i + 1 }));
    });
    setSelectedElement({ kind: 'region', id: regions[index]?.id, tempId: regions[index]?._tempId });
  };

  const handleMoveItem = (index: number, dir: -1 | 1) => {
    setItems(prev => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return prev;
      const [moved] = next.splice(index, 1);
      next.splice(target, 0, moved);
      return next;
    });
    setSelectedElement({ kind: 'item', id: items[index]?.id, tempId: items[index]?._tempId });
  };

  const handleAddValidation = (itemName: string) => {
    const newValidation: Validation = {
      page_id: parseInt(pageId, 10),
      item_name: itemName,
      validation_type: 'NOT_NULL',
      error_message: '',
      sequence: validations.filter(v => v.item_name === itemName).length + 1,
      is_active: true,
    };
    setValidations(prev => [...prev, newValidation]);
  };

  const handleUpdateValidation = (index: number, field: string, value: any) => {
    setValidations(prev => prev.map((v, i) => i === index ? { ...v, [field]: value } : v));
  };

  const handleDeleteValidation = (index: number) => {
    setValidations(prev => prev.filter((_, i) => i !== index));
  };

  const getValidationsForItem = (itemName: string) => {
    return validations
      .map((v, i) => ({ ...v, _index: i }))
      .filter(v => v.item_name === itemName);
  };

  const handleAddProcess = () => {
    const newProcess: PageProcess = {
      page_id: parseInt(pageId, 10),
      name: 'New Process',
      process_type: 'sql',
      process_code: '',
      execution_sequence: (processes.length + 1) * 10,
      execution_point: 'ON_SUBMIT_BEFORE_PROCESSING',
      is_active: true,
    };
    setProcesses(prev => [...prev, newProcess]);
  };

  const handleUpdateProcess = (index: number, field: string, value: any) => {
    setProcesses(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
  };

  const handleDeleteProcess = (index: number) => {
    setProcesses(prev => prev.filter((_, i) => i !== index));
  };

  const handleAddComputation = () => {
    const newComputation: Computation = {
      page_id: parseInt(pageId, 10),
      computation_point: 'ON_LOAD',
      computation_type: 'STATIC_ASSIGNMENT',
      computation_item: '',
      computation_value: '',
      sequence: (computations.length + 1) * 10,
      is_active: true,
    };
    setComputations(prev => [...prev, newComputation]);
  };

  const handleUpdateComputation = (index: number, field: string, value: any) => {
    setComputations(prev => prev.map((c, i) => i === index ? { ...c, [field]: value } : c));
  };

  const handleDeleteComputation = (index: number) => {
    setComputations(prev => prev.filter((_, i) => i !== index));
  };

  const handleSavePage = async () => {
    setSaving(true);
    setError(null);

    try {
      let savedPage: Page;
      const numericAppId = parseInt(appId, 10);

      const payload = {
        name: pageData.name || 'Untitled Page',
        alias: pageData.alias || 'PAGE',
        title: pageData.title || pageData.name || 'Untitled Page',
        page_number: parseInt(String(pageData.page_number || 1), 10),
        is_active: pageData.is_active ?? true,
        application_id: numericAppId,
      };

      if (pageData.id) {
        savedPage = await pageService.update(pageData.id, payload);
      } else {
        savedPage = await pageService.create(payload);
      }

      setPageData(savedPage);

      // Save Regions
      const savedRegions = await Promise.all(
        regions.map(async reg => {
          const regPayload = {
            name: reg.name,
            region_type: reg.region_type,
            source: reg.source || '',
            position: reg.position || 1,
            page_id: savedPage.id,
            is_active: reg.is_active ?? true,
          };
          if (reg.id) {
            return await regionService.update(reg.id, regPayload);
          } else {
            return await regionService.create(regPayload);
          }
        })
      );
      setRegions(savedRegions);

      // Save Items
      const savedItems = await Promise.all(
        items.map(async item => {
          const itemPayload = {
            name: item.name,
            alias: item.alias || item.name.toUpperCase(),
            item_type: item.item_type,
            label: item.label,
            placeholder: item.placeholder || '',
            default_value: item.default_value || '',
            is_required: item.is_required ?? false,
            page_id: savedPage.id,
            is_active: item.is_active ?? true,
          };
          if (item.id) {
            return await itemService.update(item.id, itemPayload);
          } else {
            return await itemService.create(itemPayload);
          }
        })
      );
      setItems(savedItems);

      // Save Validations
      const savedValidations = await Promise.all(
        validations.map(async val => {
          const valPayload = {
            page_id: savedPage.id,
            item_name: val.item_name,
            validation_type: val.validation_type,
            validation_expression: val.validation_expression || '',
            error_message: val.error_message || '',
            when_button_pressed: val.when_button_pressed || '',
            condition_type: val.condition_type || '',
            condition_expression: val.condition_expression || '',
            is_active: val.is_active ?? true,
            sequence: val.sequence || 1,
          };
          if (val.id) {
            return await validationService.update(val.id, valPayload);
          } else {
            return await validationService.create(valPayload);
          }
        })
      );
      setValidations(savedValidations);

      // Save Processes
      const savedProcesses = await Promise.all(
        processes.map(async proc => {
          const procPayload = {
            page_id: savedPage.id,
            name: proc.name,
            process_type: proc.process_type,
            process_code: proc.process_code || '',
            execution_sequence: proc.execution_sequence || 10,
            execution_point: proc.execution_point || 'ON_SUBMIT_BEFORE_PROCESSING',
            is_active: proc.is_active ?? true,
          };
          if (proc.id) {
            return await pageProcessService.update(proc.id, procPayload);
          } else {
            return await pageProcessService.create(procPayload);
          }
        })
      );
      setProcesses(savedProcesses);

      // Save Computations
      const savedComputations = await Promise.all(
        computations.map(async comp => {
          const compPayload = {
            page_id: savedPage.id,
            computation_point: comp.computation_point,
            computation_type: comp.computation_type,
            computation_item: comp.computation_item,
            computation_value: comp.computation_value || '',
            computation_condition_type: comp.computation_condition_type || '',
            computation_condition_expression: comp.computation_condition_expression || '',
            sequence: comp.sequence || 1,
            is_active: comp.is_active ?? true,
          };
          if (comp.id) {
            return await computationService.update(comp.id, compPayload);
          } else {
            return await computationService.create(compPayload);
          }
        })
      );
      setComputations(savedComputations);

      alert('Page saved successfully!');

      if (isNew) {
        router.push(`/apps/builder/${appId}/pages/${savedPage.id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save page');
    } finally {
      setSaving(false);
    }
  };

  const selectedObj = selectedElement?.kind === 'region'
    ? regions.find(r => (selectedElement.id ? r.id === selectedElement.id : r._tempId === selectedElement.tempId))
    : selectedElement?.kind === 'item'
    ? items.find(i => (selectedElement.id ? i.id === selectedElement.id : i._tempId === selectedElement.tempId))
    : null;

  const selectedRegion = selectedElement?.kind === 'region' ? (selectedObj as Region | undefined) : undefined;
  const selectedItem = selectedElement?.kind === 'item' ? (selectedObj as PageItem | undefined) : undefined;

  const updateSelectedProperty = (field: string, value: any) => {
    if (!selectedElement) return;

    if (selectedElement.kind === 'region') {
      setRegions(prev => prev.map(r => {
        const matches = selectedElement.id ? r.id === selectedElement.id : r._tempId === selectedElement.tempId;
        return matches ? { ...r, [field]: value } : r;
      }));
    } else if (selectedElement.kind === 'item') {
      setItems(prev => prev.map(i => {
        const matches = selectedElement.id ? i.id === selectedElement.id : i._tempId === selectedElement.tempId;
        return matches ? { ...i, [field]: value } : i;
      }));
    }
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-gray-500">
        <Icon icon="solar:spinner-linear" className="animate-spin text-4xl mx-auto mb-2 text-blue-600" />
        <p>Loading visual builder workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Builder Toolbar */}
      <div className="flex items-center justify-between bg-white dark:bg-dark-card p-4 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div className="flex items-center gap-3">
          <Link
            href={`/apps/builder/${appId}`}
            className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800"
            title="Back to Application Settings"
          >
            <Icon icon="solar:arrow-left-bold" className="text-xl" />
          </Link>
          <div>
            <h1 className="text-lg font-bold">
              {isNew ? 'New Page Builder' : `Page Builder: ${pageData.name}`}
            </h1>
            <span className="text-xs text-gray-500 font-mono">App ID: #{appId} | Page #{pageData.page_number}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isNew && (
            <Link
              href={`/apps/builder/${appId}/pages/${pageId}/preview`}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200 text-sm font-semibold rounded-xl flex items-center gap-1.5 transition"
            >
              <Icon icon="solar:eye-bold" className="text-base" />
              Preview Page
            </Link>
          )}
          <button
            onClick={handleSavePage}
            disabled={saving}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl shadow transition flex items-center gap-1.5"
          >
            <Icon icon="solar:diskette-bold" className="text-base" />
            {saving ? 'Saving...' : 'Save Page'}
          </button>
        </div>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded-xl border border-red-200">Error: {error}</div>}

      {/* 3-Column Visual Builder Workspace */}
      <div className="grid grid-cols-12 gap-4 items-start">
        {/* Left Column: Page Settings & Component Palette */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <div className="bg-white dark:bg-dark-card p-4 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
            <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
              <Icon icon="solar:document-bold" className="text-blue-600" />
              Page Metadata
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Page Name</label>
                <input
                  type="text"
                  name="name"
                  value={pageData.name || ''}
                  onChange={handlePageInputChange}
                  className="w-full px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Page Alias</label>
                <input
                  type="text"
                  name="alias"
                  value={pageData.alias || ''}
                  onChange={handlePageInputChange}
                  className="w-full px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Page Number</label>
                <input
                  type="number"
                  name="page_number"
                  value={pageData.page_number || 1}
                  onChange={handlePageInputChange}
                  min={1}
                  className="w-full px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-xs"
                />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-dark-card p-4 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm">
            <h3 className="font-bold text-sm mb-1 flex items-center gap-2">
              <Icon icon="solar:widget-add-bold" className="text-blue-600" />
              Component Palette
            </h3>
            <p className="text-xs text-gray-400 mb-3">Drag items into the center canvas zone.</p>

            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Regions</p>
              <div
                draggable
                onDragStart={() => handleDragStart('region', { type: 'static_content', name: 'Static Content Region' })}
                className="p-2.5 bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-blue-100 transition"
              >
                <Icon icon="solar:file-text-bold" className="text-base" />
                Static Content Region
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('region', { type: 'form', name: 'Form Region' })}
                className="p-2.5 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-800 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-800 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-indigo-100 transition"
              >
                <Icon icon="solar:pen-new-square-bold" className="text-base" />
                Form Region
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('region', { type: 'report', name: 'SQL Report Region' })}
                className="p-2.5 bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-200 border border-purple-200 dark:border-purple-800 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-purple-100 transition"
              >
                <Icon icon="solar:table-bold" className="text-base" />
                SQL Report Region
              </div>

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider pt-2">Page Items</p>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'text', name: 'Text Input' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:text-square-bold" className="text-base text-gray-600" />
                Text Input
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'textarea', name: 'Text Area' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:document-text-bold" className="text-base text-gray-600" />
                Text Area
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'select', name: 'Select Dropdown' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:list-arrow-down-minimalistic-bold" className="text-base text-gray-600" />
                Select Dropdown
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'checkbox', name: 'Checkbox' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:check-square-bold" className="text-base text-gray-600" />
                Checkbox
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'date_picker', name: 'Date Picker' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:calendar-bold" className="text-base text-gray-600" />
                Date Picker
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'radio', name: 'Radio Group' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:radio-minimalistic-bold" className="text-base text-gray-600" />
                Radio Group
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'display_only', name: 'Display Only' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:text-bold" className="text-base text-gray-600" />
                Display Only
              </div>
              <div
                draggable
                onDragStart={() => handleDragStart('item', { type: 'hidden', name: 'Hidden Item' })}
                className="p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium cursor-grab flex items-center gap-2 hover:bg-gray-100 transition"
              >
                <Icon icon="solar:eye-closed-bold" className="text-base text-gray-600" />
                Hidden Item
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-dark-card rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden">
            <button
              onClick={() => setShowProcesses(!showProcesses)}
              className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition"
            >
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Icon icon="solar:code-bold" className="text-purple-600" />
                Page Processes ({processes.length})
              </h3>
              <Icon
                icon={showProcesses ? 'solar:alt-arrow-up-bold' : 'solar:alt-arrow-down-bold'}
                className="text-gray-400"
              />
            </button>
            {showProcesses && (
              <div className="px-4 pb-4 space-y-2">
                <button
                  onClick={handleAddProcess}
                  className="w-full p-2 border border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-xs text-gray-500 hover:border-purple-400 hover:text-purple-600 transition"
                >
                  + Add Process
                </button>
                {processes.map((proc, index) => (
                  <div key={proc.id || index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        value={proc.name}
                        onChange={(e) => handleUpdateProcess(index, 'name', e.target.value)}
                        className="flex-1 px-2 py-1 border rounded text-xs font-medium"
                      />
                      <button
                        onClick={() => handleDeleteProcess(index)}
                        className="ml-2 text-gray-400 hover:text-red-600 p-1"
                      >
                        <Icon icon="solar:trash-bin-trash-bold" className="text-sm" />
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={proc.process_type}
                        onChange={(e) => handleUpdateProcess(index, 'process_type', e.target.value)}
                        className="px-2 py-1 border rounded text-xs"
                      >
                        {PROCESS_TYPES.map(t => (
                          <option key={t.value} value={t.value}>{t.label}</option>
                        ))}
                      </select>
                      <select
                        value={proc.execution_point}
                        onChange={(e) => handleUpdateProcess(index, 'execution_point', e.target.value)}
                        className="px-2 py-1 border rounded text-xs"
                      >
                        {EXECUTION_POINTS.map(p => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                    </div>
                    {(proc.process_type === 'sql' || proc.process_type === 'plsql') && (
                      <textarea
                        value={proc.process_code || ''}
                        onChange={(e) => handleUpdateProcess(index, 'process_code', e.target.value)}
                        placeholder={proc.process_type === 'sql' ? 'SELECT * FROM ...' : 'BEGIN ... END;'}
                        rows={3}
                        className="w-full px-2 py-1 border rounded text-xs font-mono"
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white dark:bg-dark-card rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm overflow-hidden">
            <button
              onClick={() => setShowComputations(!showComputations)}
              className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition"
            >
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Icon icon="solar:calculator-bold" className="text-emerald-600" />
                Computations ({computations.length})
              </h3>
              <Icon
                icon={showComputations ? 'solar:alt-arrow-up-bold' : 'solar:alt-arrow-down-bold'}
                className="text-gray-400"
              />
            </button>
            {showComputations && (
              <div className="px-4 pb-4 space-y-2">
                <button
                  onClick={handleAddComputation}
                  className="w-full p-2 border border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-xs text-gray-500 hover:border-emerald-400 hover:text-emerald-600 transition"
                >
                  + Add Computation
                </button>
                {computations.map((comp, index) => (
                  <div key={comp.id || index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2">
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        value={comp.computation_item}
                        onChange={(e) => handleUpdateComputation(index, 'computation_item', e.target.value)}
                        placeholder="Item name (e.g. P1_TOTAL)"
                        className="flex-1 px-2 py-1 border rounded text-xs font-mono"
                      />
                      <button
                        onClick={() => handleDeleteComputation(index)}
                        className="ml-2 text-gray-400 hover:text-red-600 p-1"
                      >
                        <Icon icon="solar:trash-bin-trash-bold" className="text-sm" />
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={comp.computation_point}
                        onChange={(e) => handleUpdateComputation(index, 'computation_point', e.target.value)}
                        className="px-2 py-1 border rounded text-xs"
                      >
                        {COMPUTATION_POINTS.map(p => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                      <select
                        value={comp.computation_type}
                        onChange={(e) => handleUpdateComputation(index, 'computation_type', e.target.value)}
                        className="px-2 py-1 border rounded text-xs"
                      >
                        {COMPUTATION_TYPES.map(t => (
                          <option key={t.value} value={t.value}>{t.label}</option>
                        ))}
                      </select>
                    </div>
                    <textarea
                      value={comp.computation_value || ''}
                      onChange={(e) => handleUpdateComputation(index, 'computation_value', e.target.value)}
                      placeholder="Value / Expression / Query"
                      rows={2}
                      className="w-full px-2 py-1 border rounded text-xs font-mono"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center Column: Interactive Canvas Drop Zone */}
        <div className="col-span-12 lg:col-span-6 min-h-[600px]">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (dragPayload) {
                if (dragPayload.kind === 'region') handleDropRegion(dragPayload.data);
                else if (dragPayload.kind === 'item') handleDropItem(dragPayload.data);
                setDragPayload(null);
              }
            }}
            className="bg-white dark:bg-dark-card p-6 rounded-2xl border-2 border-dashed border-gray-200 dark:border-gray-800 min-h-[600px] space-y-4"
          >
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
              <h2 className="font-bold text-sm text-gray-700 dark:text-gray-300">Layout Canvas</h2>
              <span className="text-xs text-gray-400">Click elements to inspect & modify properties</span>
            </div>

            {regions.length === 0 && items.length === 0 && (
              <div className="py-24 text-center">
                <Icon icon="solar:widget-5-bold-duotone" className="text-5xl text-gray-300 mx-auto mb-2 animate-pulse" />
                <p className="text-sm font-semibold text-gray-600 dark:text-gray-400">Canvas is empty</p>
                <p className="text-xs text-gray-400 mt-1">Drag regions or items from the left palette onto this zone.</p>
              </div>
            )}

            {/* Regions List */}
            {regions.map((region, regionIndex) => {
              const isSelected = selectedElement?.kind === 'region' &&
                (selectedElement.id ? selectedElement.id === region.id : selectedElement.tempId === region._tempId);

              const regionItems = items.filter(item =>
                item.region_id != null
                  ? (region.id ? item.region_id === region.id : item.region_id === region.id)
                  : false
              );

              return (
                <div
                  key={region.id || region._tempId}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedElement({ kind: 'region', id: region.id, tempId: region._tempId });
                  }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (dragPayload && dragPayload.kind === 'item') {
                      handleDropItem(dragPayload.data, region.id);
                      setDragPayload(null);
                    }
                  }}
                  className={`p-4 rounded-xl border transition cursor-pointer ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/30 ring-2 ring-blue-500/20'
                      : 'border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Icon icon="solar:folder-bold" className="text-blue-600" />
                      <h4 className="font-bold text-sm">{region.name}</h4>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="flex items-center gap-0.5 mr-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleMoveRegion(regionIndex, -1); }}
                          disabled={regionIndex === 0}
                          className="text-gray-400 hover:text-blue-600 disabled:opacity-30 p-0.5"
                          title="Move up"
                        >
                          <Icon icon="solar:alt-arrow-up-bold" className="text-sm" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleMoveRegion(regionIndex, 1); }}
                          disabled={regionIndex === regions.length - 1}
                          className="text-gray-400 hover:text-blue-600 disabled:opacity-30 p-0.5"
                          title="Move down"
                        >
                          <Icon icon="solar:alt-arrow-down-bold" className="text-sm" />
                        </button>
                      </div>
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 text-[10px] font-semibold rounded">
                        {region.region_type}
                      </span>
                      <button
                        onClick={(e) => handleDeleteRegion(e, region)}
                        className="text-gray-400 hover:text-red-600 p-1"
                      >
                        <Icon icon="solar:trash-bin-trash-bold" />
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 font-mono">
                    {region.region_type === 'report' ? `Query: ${region.source || 'SELECT ...'}` : 'Region Container'}
                  </p>

                  {/* Items nested inside this region */}
                  {regionItems.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {regionItems.map((item, itemIndex) => (
                        <RegionItemCard
                          key={item.id || item._tempId}
                          item={item}
                          selected={selectedElement?.kind === 'item' &&
                            (selectedElement.id ? selectedElement.id === item.id : selectedElement.tempId === item._tempId)}
                          onSelect={() => setSelectedElement({ kind: 'item', id: item.id, tempId: item._tempId })}
                          onDelete={(e) => handleDeleteItem(e, item)}
                          onMoveUp={(e) => { e.stopPropagation(); handleMoveItem(itemIndex, -1); }}
                          onMoveDown={(e) => { e.stopPropagation(); handleMoveItem(itemIndex + 1, 1); }}
                        />
                      ))}
                    </div>
                  )}

                  <div className="mt-3 pt-2 border-t border-dashed border-gray-200 dark:border-gray-700 text-center">
                    <p className="text-[10px] text-gray-400 uppercase tracking-wider">Drag page items here</p>
                  </div>
                </div>
              );
            })}

            {/* Unassigned Items List */}
            {items.filter(item => item.region_id == null).map((item, itemIndex) => {
              const isSelected = selectedElement?.kind === 'item' &&
                (selectedElement.id ? selectedElement.id === item.id : selectedElement.tempId === item._tempId);

              return (
                <RegionItemCard
                  key={item.id || item._tempId}
                  item={item}
                  selected={isSelected}
                  onSelect={() => setSelectedElement({ kind: 'item', id: item.id, tempId: item._tempId })}
                  onDelete={(e) => handleDeleteItem(e, item)}
                  onMoveUp={(e) => { e.stopPropagation(); handleMoveItem(itemIndex, -1); }}
                  onMoveDown={(e) => { e.stopPropagation(); handleMoveItem(itemIndex + 1, 1); }}
                />
              );
            })}

          </div>
        </div>

        {/* Right Column: Property Inspector */}
        <div className="col-span-12 lg:col-span-3">
          <div className="bg-white dark:bg-dark-card p-4 rounded-2xl border border-gray-100 dark:border-gray-800 shadow-sm sticky top-4">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-100 dark:border-gray-800">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Icon icon="solar:tuning-bold" className="text-blue-600" />
                Property Inspector
              </h3>
              {selectedElement && (
                <button
                  onClick={() => setSelectedElement(null)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Clear
                </button>
              )}
            </div>

            {!selectedObj ? (
              <p className="text-xs text-gray-400 py-8 text-center">
                Click any region or item on the canvas to edit its properties.
              </p>
            ) : selectedRegion ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Region Title</label>
                  <input
                    type="text"
                    value={selectedRegion.name || ''}
                    onChange={(e) => updateSelectedProperty('name', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Region Type</label>
                  <select
                    value={selectedRegion.region_type || 'static_content'}
                    onChange={(e) => updateSelectedProperty('region_type', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  >
                    <option value="static_content">Static Content</option>
                    <option value="form">Form Region</option>
                    <option value="report">SQL Report Region</option>
                  </select>
                </div>

                {selectedRegion.region_type === 'report' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">SQL Query Source</label>
                    <textarea
                      rows={4}
                      value={selectedRegion.source || ''}
                      onChange={(e) => updateSelectedProperty('source', e.target.value)}
                      placeholder="SELECT * FROM my_table"
                      className="w-full px-3 py-1.5 border rounded-lg text-xs font-mono"
                    />
                  </div>
                )}
              </div>
            ) : selectedItem ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Item Label</label>
                  <input
                    type="text"
                    value={selectedItem.label || ''}
                    onChange={(e) => updateSelectedProperty('label', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Item Name (Code ID)</label>
                  <input
                    type="text"
                    value={selectedItem.name || ''}
                    onChange={(e) => updateSelectedProperty('name', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Item Type</label>
                  <select
                    value={selectedItem.item_type || 'text'}
                    onChange={(e) => updateSelectedProperty('item_type', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  >
                    <option value="text">Text Field</option>
                    <option value="textarea">Text Area</option>
                    <option value="select">Select Dropdown</option>
                    <option value="checkbox">Checkbox</option>
                    <option value="radio">Radio Group</option>
                    <option value="date_picker">Date Picker</option>
                    <option value="display_only">Display Only</option>
                    <option value="hidden">Hidden Item</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Placeholder</label>
                  <input
                    type="text"
                    value={selectedItem.placeholder || ''}
                    onChange={(e) => updateSelectedProperty('placeholder', e.target.value)}
                    className="w-full px-3 py-1.5 border rounded-lg text-xs"
                  />
                </div>

                <div className="pt-3 border-t border-gray-100 dark:border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Validations</label>
                    <button
                      onClick={() => handleAddValidation(selectedItem.name)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      + Add
                    </button>
                  </div>
                  {getValidationsForItem(selectedItem.name).length === 0 ? (
                    <p className="text-xs text-gray-400 py-2">No validations for this item.</p>
                  ) : (
                    <div className="space-y-3">
                      {getValidationsForItem(selectedItem.name).map((val) => (
                        <div key={val._index} className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-2">
                          <div className="flex items-center justify-between">
                            <select
                              value={val.validation_type}
                              onChange={(e) => handleUpdateValidation(val._index, 'validation_type', e.target.value)}
                              className="flex-1 px-2 py-1 border rounded text-xs"
                            >
                              {VALIDATION_TYPES.map(t => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                              ))}
                            </select>
                            <button
                              onClick={() => handleDeleteValidation(val._index)}
                              className="ml-2 text-gray-400 hover:text-red-600 p-1"
                            >
                              <Icon icon="solar:trash-bin-trash-bold" className="text-sm" />
                            </button>
                          </div>
                          {val.validation_type !== 'NOT_NULL' && val.validation_type !== 'VALUE_REQUIRED' && (
                            <input
                              type="text"
                              value={val.validation_expression || ''}
                              onChange={(e) => handleUpdateValidation(val._index, 'validation_expression', e.target.value)}
                              placeholder="Expression / Value"
                              className="w-full px-2 py-1 border rounded text-xs"
                            />
                          )}
                          <input
                            type="text"
                            value={val.error_message || ''}
                            onChange={(e) => handleUpdateValidation(val._index, 'error_message', e.target.value)}
                            placeholder="Error message"
                            className="w-full px-2 py-1 border rounded text-xs"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

interface RegionItemCardProps {
  item: PageItem;
  selected: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onMoveUp: (e: React.MouseEvent) => void;
  onMoveDown: (e: React.MouseEvent) => void;
}

function RegionItemCard({ item, selected, onSelect, onDelete, onMoveUp, onMoveDown }: RegionItemCardProps) {
  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
      className={`p-3 rounded-xl border transition cursor-pointer ${
        selected
          ? 'border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/30 ring-2 ring-emerald-500/20'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-700 dark:text-gray-200">
          {item.label || item.name} <span className="text-gray-400">({item.item_type})</span>
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={onMoveUp}
            className="text-gray-400 hover:text-blue-600 p-0.5"
            title="Move up"
          >
            <Icon icon="solar:alt-arrow-up-bold" className="text-sm" />
          </button>
          <button
            onClick={onMoveDown}
            className="text-gray-400 hover:text-blue-600 p-0.5"
            title="Move down"
          >
            <Icon icon="solar:alt-arrow-down-bold" className="text-sm" />
          </button>
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-600 p-1"
          >
            <Icon icon="solar:trash-bin-trash-bold" />
          </button>
        </div>
      </div>
      <div className="pointer-events-none">
        {item.item_type === 'text' && (
          <input type="text" placeholder={item.placeholder || 'Text field preview'} readOnly className="w-full px-3 py-1.5 border rounded-lg text-xs bg-gray-50" />
        )}
        {item.item_type === 'textarea' && (
          <textarea placeholder={item.placeholder || 'Text area preview'} readOnly rows={2} className="w-full px-3 py-1.5 border rounded-lg text-xs bg-gray-50" />
        )}
        {item.item_type === 'select' && (
          <select disabled className="w-full px-3 py-1.5 border rounded-lg text-xs bg-gray-50">
            <option>Sample Option</option>
          </select>
        )}
        {item.item_type === 'checkbox' && (
          <label className="flex items-center gap-2 text-xs">
            <input type="checkbox" disabled />
            {item.label}
          </label>
        )}
        {item.item_type === 'radio' && (
          <div className="flex items-center gap-3 text-xs">
            <label className="flex items-center gap-1"><input type="radio" disabled /> Option 1</label>
            <label className="flex items-center gap-1"><input type="radio" disabled /> Option 2</label>
          </div>
        )}
        {item.item_type === 'date_picker' && (
          <input type="date" readOnly className="w-full px-3 py-1.5 border rounded-lg text-xs bg-gray-50" />
        )}
        {item.item_type === 'display_only' && (
          <div className="px-3 py-1.5 rounded-lg text-xs bg-gray-50 border border-gray-200 text-gray-600">
            {item.default_value || 'Display value preview'}
          </div>
        )}
        {item.item_type === 'hidden' && (
          <div className="px-3 py-1.5 rounded-lg text-xs bg-gray-50 border border-dashed border-gray-300 text-gray-400">
            Hidden item: {item.name}
          </div>
        )}
      </div>
    </div>
  );
}
