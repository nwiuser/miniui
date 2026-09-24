const API_BASE = '/api/v1';

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('miniui_token')
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${path}`;

  const token = getToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('miniui_token')
      localStorage.removeItem('miniui_user')
      window.location.href = '/auth/login'
    }
    throw new Error('Session expired. Please login again.')
  }

  if (!response.ok) {
    let errorMessage = `API Error (${response.status}): ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Response wasn't JSON
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

async function apiFetchForm<T>(endpoint: string, data: Record<string, string>): Promise<T> {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${path}`;

  const token = getToken()
  const formData = new URLSearchParams(data)

  const headers: HeadersInit = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData.toString(),
  });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('miniui_token')
      localStorage.removeItem('miniui_user')
      window.location.href = '/auth/login'
    }
    throw new Error('Session expired. Please login again.')
  }

  if (!response.ok) {
    let errorMessage = `API Error (${response.status}): ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Response wasn't JSON
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, data: unknown) => apiFetch<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) => apiFetch<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: 'DELETE' }),
  postForm: <T>(endpoint: string, data: Record<string, string>) => apiFetchForm<T>(endpoint, data),
};

export default apiClient;
