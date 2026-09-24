import { apiClient } from '../client';

export interface Validation {
  id?: number;
  page_id: number;
  item_name: string;
  validation_type: string;
  validation_expression?: string;
  error_message?: string;
  when_button_pressed?: string;
  condition_type?: string;
  condition_expression?: string;
  is_active?: boolean;
  sequence?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ValidationCreate {
  page_id: number;
  item_name: string;
  validation_type: string;
  validation_expression?: string;
  error_message?: string;
  when_button_pressed?: string;
  condition_type?: string;
  condition_expression?: string;
  is_active?: boolean;
  sequence?: number;
}

export interface ValidationUpdate extends Partial<ValidationCreate> {}

export const VALIDATION_TYPES = [
  { value: 'NOT_NULL', label: 'Not Null' },
  { value: 'VALUE_REQUIRED', label: 'Value Required' },
  { value: 'EQUALS', label: 'Equals' },
  { value: 'NOT_EQUALS', label: 'Not Equals' },
  { value: 'GREATER_THAN', label: 'Greater Than' },
  { value: 'LESS_THAN', label: 'Less Than' },
  { value: 'REGEXP', label: 'Regular Expression' },
  { value: 'MAX_LENGTH', label: 'Max Length' },
  { value: 'MIN_LENGTH', label: 'Min Length' },
  { value: 'EXACT_LENGTH', label: 'Exact Length' },
  { value: 'IN_LIST', label: 'In List (comma-separated)' },
];

export const validationService = {
  getByPageId: (pageId: string | number) =>
    apiClient.get<Validation[]>(`/validations?page_id=${pageId}`),
  getById: (id: number) =>
    apiClient.get<Validation>(`/validations/${id}`),
  create: (data: ValidationCreate) =>
    apiClient.post<Validation>('/validations', data),
  update: (id: number, data: ValidationUpdate) =>
    apiClient.put<Validation>(`/validations/${id}`, data),
  delete: (id: number) =>
    apiClient.delete<void>(`/validations/${id}`),
};
