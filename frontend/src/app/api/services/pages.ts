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

/** Shape returned by GET /pages/builder/{application_id}. */
export interface PageBuilderContext {
  application: Record<string, unknown>;
  pages: Page[];
}

export const pageService = {
  // The backend exposes the builder's pages under /pages/builder. The
  // /pages/{alias}/{number} routes render HTML for end users, not metadata.
  getBuilderContext: (appId: number | string) =>
    apiClient.get<PageBuilderContext>(`/pages/builder/${appId}`),

  getByAppId: (appId: number | string) =>
    apiClient
      .get<PageBuilderContext>(`/pages/builder/${appId}`)
      .then((context) => context.pages),
  getById: (id: number | string) => apiClient.get<Page>(`/pages/builder/${id}`),
  create: (data: PageCreate) => apiClient.post<Page>('/pages/builder/', data),
  update: (id: number | string, data: PageUpdate) =>
    apiClient.put<Page>(`/pages/builder/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/pages/builder/${id}`),
};
