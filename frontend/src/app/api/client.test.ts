import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from './client';

const TOKEN_KEY = 'miniui_token';
const USER_KEY = 'miniui_user';

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

describe('apiClient', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  describe('request construction', () => {
    it('prefixes endpoints with /api/v1', async () => {
      fetchMock.mockResolvedValue(jsonResponse([]));

      await apiClient.get('/applications');

      expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/applications');
    });

    it('adds a leading slash when one is missing', async () => {
      fetchMock.mockResolvedValue(jsonResponse([]));

      await apiClient.get('applications');

      expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/applications');
    });

    it('sends JSON content type and the XHR marker', async () => {
      fetchMock.mockResolvedValue(jsonResponse({}));

      await apiClient.get('/applications');

      const headers = fetchMock.mock.calls[0][1].headers;
      expect(headers['Content-Type']).toBe('application/json');
      expect(headers['X-Requested-With']).toBe('XMLHttpRequest');
    });

    it('sends the bearer token when one is stored', async () => {
      localStorage.setItem(TOKEN_KEY, 'token-123');
      fetchMock.mockResolvedValue(jsonResponse([]));

      await apiClient.get('/applications');

      expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer token-123');
    });

    it('omits the Authorization header when no token is stored', async () => {
      fetchMock.mockResolvedValue(jsonResponse([]));

      await apiClient.get('/applications');

      expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
    });

    it('serializes the body as JSON on post', async () => {
      fetchMock.mockResolvedValue(jsonResponse({ id: 1 }));

      await apiClient.post('/pages', { name: 'Home', page_number: 1 });

      const options = fetchMock.mock.calls[0][1];
      expect(options.method).toBe('POST');
      expect(options.body).toBe('{"name":"Home","page_number":1}');
    });

    it('url-encodes the body on postForm', async () => {
      fetchMock.mockResolvedValue(jsonResponse({ access_token: 't' }));

      await apiClient.postForm('/auth/login', {
        username: 'admin',
        password: 'p&ss word',
      });

      const options = fetchMock.mock.calls[0][1];
      expect(options.headers['Content-Type']).toBe('application/x-www-form-urlencoded');
      expect(options.body).toBe('username=admin&password=p%26ss+word');
    });

    it('sends no body on delete', async () => {
      fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

      await apiClient.delete('/items/5');

      expect(fetchMock.mock.calls[0][1].method).toBe('DELETE');
    });

    it('exposes no way to pass custom headers on a GET', async () => {
      // get(endpoint) takes only the path, so the default header set is fixed.
      // A caller needing a custom header cannot add one without changing this
      // signature.
      expect(apiClient.get.length).toBe(1);
    });
  });

  describe('responses', () => {
    it('parses a JSON body', async () => {
      fetchMock.mockResolvedValue(jsonResponse({ id: 7, name: 'Home' }));

      await expect(apiClient.get('/items/7')).resolves.toEqual({ id: 7, name: 'Home' });
    });

    it('returns an empty object for 204 No Content', async () => {
      fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

      await expect(apiClient.delete<void>('/items/7')).resolves.toEqual({});
    });

    it('preserves query strings when prefixing', async () => {
      fetchMock.mockResolvedValue(jsonResponse([]));

      await apiClient.get('/items?page_id=3');

      expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/items?page_id=3');
    });
  });

  describe('error handling', () => {
    it('surfaces a string detail from the error body', async () => {
      fetchMock.mockResolvedValue(
        jsonResponse({ detail: 'Page not found' }, { status: 404, statusText: 'Not Found' }),
      );

      await expect(apiClient.get('/pages/1')).rejects.toThrow('Page not found');
    });

    it('serializes a structured detail', async () => {
      fetchMock.mockResolvedValue(
        jsonResponse({ detail: [{ loc: ['body', 'name'] }] }, { status: 422 }),
      );

      await expect(apiClient.post('/pages', {})).rejects.toThrow('[{"loc":["body","name"]}]');
    });

    it('falls back to status and statusText when the body is not JSON', async () => {
      fetchMock.mockResolvedValue(
        new Response('<html>Gateway Timeout</html>', {
          status: 504,
          statusText: 'Gateway Timeout',
        }),
      );

      await expect(apiClient.get('/applications')).rejects.toThrow('API Error (504): Gateway Timeout');
    });

    it('rejects on 401 and clears the stored session', async () => {
      localStorage.setItem(TOKEN_KEY, 'stale');
      localStorage.setItem(USER_KEY, '{"username":"admin"}');
      fetchMock.mockResolvedValue(jsonResponse({ detail: 'Not authenticated' }, { status: 401 }));

      await expect(apiClient.get('/applications')).rejects.toThrow('Session expired');

      expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
      expect(localStorage.getItem(USER_KEY)).toBeNull();
    });

    it('rejects on 403 without clearing the stored session', async () => {
      localStorage.setItem(TOKEN_KEY, 'valid');
      fetchMock.mockResolvedValue(jsonResponse({ detail: 'Forbidden' }, { status: 403 }));

      await expect(apiClient.get('/applications')).rejects.toThrow('Forbidden');

      expect(localStorage.getItem(TOKEN_KEY)).toBe('valid');
    });
  });
});
