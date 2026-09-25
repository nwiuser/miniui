export interface Application {
  id: number
  name: string
  alias: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ApplicationCreate {
  name: string
  alias: string
  description?: string
  is_active?: boolean
}

export interface ApplicationUpdate extends Partial<ApplicationCreate> {}

export interface Page {
  id: number
  application_id: number
  name: string
  alias?: string
  page_number: number
  title?: string
  description?: string
  is_active: boolean
  is_public?: boolean
  created_at: string
  updated_at: string
}

export interface PageCreate {
  application_id: number
  name: string
  alias?: string
  page_number: number
  title?: string
  description?: string
  is_active?: boolean
  is_public?: boolean
}

export interface PageUpdate extends Partial<PageCreate> {}

export interface RestDataSource {
  id: number
  application_id: number
  name: string
  url: string
  method: string
  headers?: Record<string, string>
  query_params?: Record<string, unknown>
  request_body?: Record<string, unknown>
  response_mapping?: Record<string, string>
  timeout?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface RestDataSourceCreate {
  application_id: number
  name: string
  url: string
  method: string
  headers?: Record<string, string>
  query_params?: Record<string, unknown>
  request_body?: Record<string, unknown>
  response_mapping?: Record<string, string>
  timeout?: number
  is_active?: boolean
}

export interface Region {
  id?: number
  _tempId?: string
  page_id: number
  name: string
  region_type: string
  source?: string
  template_options?: Record<string, any>
  position?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface RegionCreate {
  page_id: number
  name: string
  region_type: string
  source?: string
  template_options?: Record<string, any>
  position?: number
  is_active?: boolean
}

export interface RegionUpdate extends Partial<RegionCreate> {}

export interface PageItem {
  id?: number
  _tempId?: string
  page_id: number
  name: string
  alias?: string
  item_type: string
  label: string
  placeholder?: string
  default_value?: string
  is_required?: boolean
  region_id?: number | null
  lov_id?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface PageItemCreate {
  page_id: number
  name: string
  alias?: string
  item_type: string
  label: string
  placeholder?: string
  default_value?: string
  is_required?: boolean
  region_id?: number | null
  lov_id?: number
  is_active?: boolean
}

export interface PageItemUpdate extends Partial<PageItemCreate> {}

export interface Validation {
  id?: number
  page_id: number
  item_name: string
  validation_type: string
  validation_expression?: string
  error_message?: string
  when_button_pressed?: string
  condition_type?: string
  condition_expression?: string
  sequence?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface ValidationCreate {
  page_id: number
  item_name: string
  validation_type: string
  validation_expression?: string
  error_message?: string
  sequence?: number
  is_active?: boolean
}

export interface PageProcess {
  id?: number
  page_id: number
  name: string
  process_type: string
  process_code?: string
  execution_sequence?: number
  execution_point?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface PageProcessCreate {
  page_id: number
  name: string
  process_type: string
  process_code?: string
  execution_sequence?: number
  execution_point?: string
  is_active?: boolean
}

export interface Computation {
  id?: number
  page_id: number
  computation_point: string
  computation_type: string
  computation_item: string
  computation_value?: string
  computation_condition_type?: string
  computation_condition_expression?: string
  sequence?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface ComputationCreate {
  page_id: number
  computation_point: string
  computation_type: string
  computation_item: string
  computation_value?: string
  sequence?: number
  is_active?: boolean
}

export interface Lov {
  id?: number
  lov_name: string
  lov_definition?: string
  is_static?: boolean
  static_values?: string
  display_extra?: boolean
  is_enterable?: boolean
  show_null_value?: boolean
  null_text?: string
  null_value?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface LovCreate {
  lov_name: string
  lov_definition?: string
  is_static?: boolean
  static_values?: string
  is_active?: boolean
}

export interface WorkspaceUser {
  id: number
  username: string
  first_name?: string
  last_name?: string
  email?: string
  administrator_role?: string
  is_active?: boolean
  created_at: string
  updated_at: string
}

export interface AuthUser {
  user_id: number
  username: string
  email: string
  first_name: string
  last_name: string
  administrator_role: string
}

export interface Token {
  access_token: string
  token_type: string
  user_id: number
  username: string
  email: string
  first_name: string
  last_name: string
  administrator_role: string
}
