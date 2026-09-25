import { apiClient } from '../client';

export type RestMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export interface RestDataSource {
  id?: number;
  application_id: number;
  name: string;
  url: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, unknown>;
  request_body?: Record<string, unknown>;
  response_mapping?: Record<string, string>;
  timeout?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RestDataSourceCreate {
  application_id: number;
  name: string;
  url: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, unknown>;
  request_body?: Record<string, unknown>;
  response_mapping?: Record<string, string>;
  timeout?: number;
  is_active?: boolean;
}

export interface RestDataSourceUpdate extends Partial<RestDataSourceCreate> {}

export interface RestDataSourceExecuteResponse {
  data_source_id: number;
  name: string;
  method: string;
  url: string;
  status_code: number;
  data: unknown;
  mapped_items?: Record<string, string>;
}

export const restDataSourceService = {
  getByAppId: (appId: number | string) =>
    apiClient.get<RestDataSource[]>(`/rest-data-sources?application_id=${appId}`),
  getById: (id: number | string) => apiClient.get<RestDataSource>(`/rest-data-sources/${id}`),
  create: (data: RestDataSourceCreate) => apiClient.post<RestDataSource>('/rest-data-sources', data),
  update: (id: number | string, data: RestDataSourceUpdate) =>
    apiClient.put<RestDataSource>(`/rest-data-sources/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/rest-data-sources/${id}`),
  execute: (id: number | string, options?: { payload?: Record<string, unknown>; page_id?: number }) =>
    apiClient.post<RestDataSourceExecuteResponse>(`/rest-data-sources/${id}/execute`, options || {}),
};

export const getApplicationMetadata = (appId: number | string) =>
  apiClient.get<{ application: Record<string, unknown>; pages: unknown[] }>(
    `/applications/${appId}/metadata`,
  );