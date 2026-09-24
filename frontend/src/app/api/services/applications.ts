import { apiClient } from '../client';

export interface Application {
  id: number;
  name: string;
  alias: string;
  description?: string;
  logo?: string;
  theme?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ApplicationCreate {
  name: string;
  alias: string;
  description?: string;
  theme?: string;
  is_active?: boolean;
}

export interface ApplicationUpdate extends Partial<ApplicationCreate> {}

export const applicationService = {
  getAll: () => apiClient.get<Application[]>('/applications'),
  getById: (id: number | string) => apiClient.get<Application>(`/applications/${id}`),
  create: (data: ApplicationCreate) => apiClient.post<Application>('/applications', data),
  update: (id: number | string, data: ApplicationUpdate) => apiClient.put<Application>(`/applications/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/applications/${id}`),
};
