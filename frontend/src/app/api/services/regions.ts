import { apiClient } from '../client';

export interface Region {
  id?: number;
  _tempId?: string;
  name: string;
  region_type: 'static_content' | 'form' | 'report' | 'cards' | string;
  source?: string;
  template_options?: Record<string, unknown> | null;
  position?: number;
  page_id?: number;
  is_active?: boolean;
}

export interface RegionCreate extends Omit<Region, 'id' | '_tempId'> {}
export interface RegionUpdate extends Partial<RegionCreate> {}

export const regionService = {
  getByPageId: (pageId: number | string) => apiClient.get<Region[]>(`/regions?page_id=${pageId}`),
  getById: (id: number | string) => apiClient.get<Region>(`/regions/${id}`),
  create: (data: RegionCreate) => apiClient.post<Region>('/regions', data),
  update: (id: number | string, data: RegionUpdate) => apiClient.put<Region>(`/regions/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/regions/${id}`),
};
