import { apiClient } from '../client';

export interface Page {
  id: number;
  name: string;
  alias: string;
  title?: string;
  page_number: number;
  is_active: boolean;
  is_public?: boolean;
  application_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface PageCreate {
  name: string;
  alias: string;
  title?: string;
  page_number: number;
  is_active?: boolean;
  is_public?: boolean;
  application_id: number;
}

export interface PageUpdate extends Partial<PageCreate> {}

export const pageService = {
  getByAppId: (appId: number | string) => apiClient.get<Page[]>(`/pages?application_id=${appId}`),
  getById: (id: number | string) => apiClient.get<Page>(`/pages/${id}`),
  create: (data: PageCreate) => apiClient.post<Page>('/pages', data),
  update: (id: number | string, data: PageUpdate) => apiClient.put<Page>(`/pages/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/pages/${id}`),
};
