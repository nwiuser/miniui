import { apiClient } from '../client';

export interface PageItem {
  id?: number;
  _tempId?: string;
  name: string;
  alias?: string;
  item_type: 'text' | 'textarea' | 'select' | 'checkbox' | 'date_picker' | 'hidden' | 'display_only' | string;
  label?: string;
  placeholder?: string;
  default_value?: string;
  is_required?: boolean;
  region_id?: number | null;
  page_id?: number;
  is_active?: boolean;
}

export interface ItemCreate extends Omit<PageItem, 'id' | '_tempId'> {}
export interface ItemUpdate extends Partial<ItemCreate> {}

export const itemService = {
  getByPageId: (pageId: number | string) => apiClient.get<PageItem[]>(`/items?page_id=${pageId}`),
  getById: (id: number | string) => apiClient.get<PageItem>(`/items/${id}`),
  create: (data: ItemCreate) => apiClient.post<PageItem>('/items', data),
  update: (id: number | string, data: ItemUpdate) => apiClient.put<PageItem>(`/items/${id}`, data),
  delete: (id: number | string) => apiClient.delete<void>(`/items/${id}`),
};
