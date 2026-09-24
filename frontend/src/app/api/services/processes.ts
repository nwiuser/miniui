import { apiClient } from '../client';

export interface PageProcess {
  id?: number;
  page_id: number;
  name: string;
  process_type: string;
  process_code?: string;
  execution_sequence?: number;
  execution_point?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PageProcessCreate {
  page_id: number;
  name: string;
  process_type: string;
  process_code?: string;
  execution_sequence?: number;
  execution_point?: string;
  is_active?: boolean;
}

export interface PageProcessUpdate extends Partial<PageProcessCreate> {}

export const PROCESS_TYPES = [
  { value: 'sql', label: 'SQL' },
  { value: 'plsql', label: 'PL/SQL' },
  { value: 'reset_pagination', label: 'Reset Pagination' },
  { value: 'clear_cache', label: 'Clear Cache' },
];

export const EXECUTION_POINTS = [
  { value: 'ON_LOAD', label: 'On Page Load' },
  { value: 'ON_SUBMIT_BEFORE_VALIDATION', label: 'On Submit (Before Validation)' },
  { value: 'ON_SUBMIT_AFTER_VALIDATION', label: 'On Submit (After Validation)' },
  { value: 'ON_SUBMIT_BEFORE_PROCESSING', label: 'On Submit (Before Processing)' },
];

export const pageProcessService = {
  getByPageId: (pageId: string | number) =>
    apiClient.get<PageProcess[]>(`/processes?page_id=${pageId}`),
  getById: (id: number) =>
    apiClient.get<PageProcess>(`/processes/${id}`),
  create: (data: PageProcessCreate) =>
    apiClient.post<PageProcess>('/processes', data),
  update: (id: number, data: PageProcessUpdate) =>
    apiClient.put<PageProcess>(`/processes/${id}`, data),
  delete: (id: number) =>
    apiClient.delete<void>(`/processes/${id}`),
};
