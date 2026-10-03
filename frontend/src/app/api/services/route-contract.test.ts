import { readFileSync } from 'node:fs';
import path from 'node:path';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { applicationService } from './applications';
import { pageService } from './pages';
import { itemService } from './items';
import { regionService } from './regions';
import { lovService } from './lovs';
import { pageProcessService } from './processes';
import { validationService } from './validations';
import { computationService } from './computations';
import { restDataSourceService, getApplicationMetadata } from './rest-data-sources';

/**
 * The URLs the services build are checked against the backend's OpenAPI schema
 * so a rename on either side fails here rather than as a 404 in the browser.
 *
 * Regenerate the schema after backend route changes with:
 *   python backend/dump_openapi.py
 */
// Resolved from the frontend package root, not the test file, so it does not
// depend on where the runner is invoked from.
const SCHEMA_PATH = path.resolve(process.cwd(), '..', 'backend', 'openapi.json');
const schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf-8'));
const backendPaths = schema.paths as Record<string, Record<string, unknown>>;

type Method = 'get' | 'post' | 'put' | 'delete';

/**
 * Replace concrete path segments with the parameter they would match, and
 * normalize the trailing slash. FastAPI issues a 307 redirect when only the
 * trailing slash differs, so both spellings reach the same handler and should
 * not be reported as a contract break.
 */
function toTemplatePath(url: string): string {
  const pathname = url.split('?')[0].replace(/\/+$/, '');
  return pathname
    .split('/')
    .map((segment) => (/^\d+$/.test(segment) || /^[0-9a-f]{8,}$/i.test(segment) ? '{param}' : segment))
    .join('/');
}

function backendAllows(method: Method, url: string): boolean {
  const template = toTemplatePath(url);
  for (const [backendPath, operations] of Object.entries(backendPaths)) {
    if (operations[method] === undefined) continue;

    // Compare segment counts and shapes: a literal segment must match exactly,
    // a {placeholder} in the backend matches any single segment.
    const expected = backendPath.replace(/\/+$/, '').split('/');
    const actual = template.split('/');
    if (expected.length !== actual.length) continue;

    const matches = expected.every((segment, index) =>
      segment.startsWith('{') ? actual[index] !== '' : segment === actual[index],
    );
    if (matches) return true;
  }
  return false;
}

describe('frontend/backend route contract', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  /** Invoke a service call and assert the backend exposes that route. */
  async function expectBackendRoute(call: () => Promise<unknown>) {
    await call();
    const url = fetchMock.mock.calls[0][0] as string;
    const method = (fetchMock.mock.calls[0][1].method as string).toLowerCase() as Method;

    expect(
      backendAllows(method, url),
      `The frontend calls ${method.toUpperCase()} ${url} but the backend has no matching route. Checked against backend/openapi.json.`,
    ).toBe(true);
  }

  describe('applications', () => {
    it('getAll hits a real route', () => expectBackendRoute(() => applicationService.getAll()));
    it('getById hits a real route', () => expectBackendRoute(() => applicationService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() => applicationService.create({ name: 'A', alias: 'A' })));
    it('update hits a real route', () =>
      expectBackendRoute(() => applicationService.update(1, { name: 'A' })));
    it('delete hits a real route', () => expectBackendRoute(() => applicationService.delete(1)));
    it('getApplicationMetadata hits a real route', () =>
      expectBackendRoute(() => getApplicationMetadata(1)));
  });

  describe('pages', () => {
    it('getByAppId hits a real route', () => expectBackendRoute(() => pageService.getByAppId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => pageService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() =>
        pageService.create({ name: 'P', alias: 'P', page_number: 1, application_id: 1 }),
      ));
    it('update hits a real route', () =>
      expectBackendRoute(() => pageService.update(1, { name: 'P' })));
    it('delete hits a real route', () => expectBackendRoute(() => pageService.delete(1)));
  });

  describe('items', () => {
    it('getByPageId hits a real route', () => expectBackendRoute(() => itemService.getByPageId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => itemService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() => itemService.create({ name: 'I', item_type: 'text' })));
    it('update hits a real route', () => expectBackendRoute(() => itemService.update(1, { name: 'I' })));
    it('delete hits a real route', () => expectBackendRoute(() => itemService.delete(1)));
  });

  describe('regions', () => {
    it('getByPageId hits a real route', () => expectBackendRoute(() => regionService.getByPageId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => regionService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() => regionService.create({ name: 'R', region_type: 'form' })));
    it('update hits a real route', () => expectBackendRoute(() => regionService.update(1, { name: 'R' })));
    it('delete hits a real route', () => expectBackendRoute(() => regionService.delete(1)));
  });

  describe('lovs', () => {
    it('getAll hits a real route', () => expectBackendRoute(() => lovService.getAll()));
    it('getById hits a real route', () => expectBackendRoute(() => lovService.getById(1)));
    it('getByName hits a real route', () => expectBackendRoute(() => lovService.getByName('X')));
    it('create hits a real route', () => expectBackendRoute(() => lovService.create({ lov_name: 'X' })));
    it('update hits a real route', () => expectBackendRoute(() => lovService.update(1, { lov_name: 'X' })));
    it('delete hits a real route', () => expectBackendRoute(() => lovService.delete(1)));
  });

  describe('processes', () => {
    it('getByPageId hits a real route', () =>
      expectBackendRoute(() => pageProcessService.getByPageId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => pageProcessService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() =>
        pageProcessService.create({ page_id: 1, name: 'P', process_type: 'sql' }),
      ));
    it('update hits a real route', () => expectBackendRoute(() => pageProcessService.update(1, { name: 'P' })));
    it('delete hits a real route', () => expectBackendRoute(() => pageProcessService.delete(1)));
  });

  describe('validations', () => {
    it('getByPageId hits a real route', () =>
      expectBackendRoute(() => validationService.getByPageId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => validationService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() =>
        validationService.create({ page_id: 1, item_name: 'I', validation_type: 'NOT_NULL' }),
      ));
    it('update hits a real route', () =>
      expectBackendRoute(() => validationService.update(1, { error_message: 'e' })));
    it('delete hits a real route', () => expectBackendRoute(() => validationService.delete(1)));
  });

  describe('computations', () => {
    it('getByPageId hits a real route', () =>
      expectBackendRoute(() => computationService.getByPageId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => computationService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() =>
        computationService.create({
          page_id: 1,
          computation_point: 'ON_LOAD',
          computation_type: 'STATIC_ASSIGNMENT',
          computation_item: 'I',
        }),
      ));
    it('update hits a real route', () =>
      expectBackendRoute(() => computationService.update(1, { computation_value: 'v' })));
    it('delete hits a real route', () => expectBackendRoute(() => computationService.delete(1)));
  });

  describe('rest data sources', () => {
    it('getByAppId hits a real route', () =>
      expectBackendRoute(() => restDataSourceService.getByAppId(1)));
    it('getById hits a real route', () => expectBackendRoute(() => restDataSourceService.getById(1)));
    it('create hits a real route', () =>
      expectBackendRoute(() =>
        restDataSourceService.create({ application_id: 1, name: 'D', url: 'https://x', method: 'GET' }),
      ));
    it('update hits a real route', () =>
      expectBackendRoute(() => restDataSourceService.update(1, { name: 'D' })));
    it('delete hits a real route', () => expectBackendRoute(() => restDataSourceService.delete(1)));
    it('execute hits a real route', () => expectBackendRoute(() => restDataSourceService.execute(1)));
  });
});
