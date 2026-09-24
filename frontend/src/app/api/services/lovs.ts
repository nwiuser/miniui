import { apiClient } from '../client';

export interface Lov {
  id?: number;
  lov_name: string;
  lov_definition?: string;
  is_static?: boolean;
  static_values?: string;
  display_extra?: boolean;
  is_enterable?: boolean;
  show_null_value?: boolean;
  null_text?: string;
  null_value?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LovCreate {
  lov_name: string;
  lov_definition?: string;
  is_static?: boolean;
  static_values?: string;
  display_extra?: boolean;
  is_enterable?: boolean;
  show_null_value?: boolean;
  null_text?: string;
  null_value?: string;
  is_active?: boolean;
}

export interface LovUpdate extends Partial<LovCreate> {}

export const lovService = {
  getAll: () => apiClient.get<Lov[]>('/lovs/'),
  getById: (id: number) => apiClient.get<Lov>(`/lovs/${id}`),
  getByName: (name: string) => apiClient.get<Lov>(`/lovs/name/${name}`),
  create: (data: LovCreate) => apiClient.post<Lov>('/lovs/', data),
  update: (id: number, data: LovUpdate) => apiClient.put<Lov>(`/lovs/${id}`, data),
  delete: (id: number) => apiClient.delete<void>(`/lovs/${id}`),
};
