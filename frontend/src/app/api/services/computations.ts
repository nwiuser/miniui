import { apiClient } from '../client';

export interface Computation {
  id?: number;
  page_id: number;
  computation_point: string;
  computation_type: string;
  computation_item: string;
  computation_value?: string;
  computation_condition_type?: string;
  computation_condition_expression?: string;
  sequence?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ComputationCreate {
  page_id: number;
  computation_point: string;
  computation_type: string;
  computation_item: string;
  computation_value?: string;
  computation_condition_type?: string;
  computation_condition_expression?: string;
  sequence?: number;
  is_active?: boolean;
}

export interface ComputationUpdate extends Partial<ComputationCreate> {}

export const COMPUTATION_POINTS = [
  { value: 'ON_NEW_INSTANCE', label: 'On New Instance' },
  { value: 'ON_LOAD', label: 'On Page Load' },
  { value: 'BEFORE_HEADER', label: 'Before Header' },
  { value: 'AFTER_HEADER', label: 'After Header' },
  { value: 'BEFORE_BOX_BODY', label: 'Before Box Body' },
  { value: 'AFTER_BOX_BODY', label: 'After Box Body' },
  { value: 'BEFORE_FOOTER', label: 'Before Footer' },
  { value: 'AFTER_FOOTER', label: 'After Footer' },
];

export const COMPUTATION_TYPES = [
  { value: 'STATIC_ASSIGNMENT', label: 'Static Value' },
  { value: 'SQL_QUERY', label: 'SQL Query (Return Single Value)' },
  { value: 'PLSQL_FUNCTION_BODY', label: 'PL/SQL Function Body' },
  { value: 'PLSQL_EXPRESSION', label: 'PL/SQL Expression' },
];

export const computationService = {
  getByPageId: (pageId: string | number) =>
    apiClient.get<Computation[]>(`/computations?page_id=${pageId}`),
  getById: (id: number) =>
    apiClient.get<Computation>(`/computations/${id}`),
  create: (data: ComputationCreate) =>
    apiClient.post<Computation>('/computations', data),
  update: (id: number, data: ComputationUpdate) =>
    apiClient.put<Computation>(`/computations/${id}`, data),
  delete: (id: number) =>
    apiClient.delete<void>(`/computations/${id}`),
};
