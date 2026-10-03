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
 * These assert the URL and HTTP verb each service produces, so a change to the
 * service layer that points at a wrong endpoint fails here rather than in the
 * browser.
 */
describe('api services', () => {
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

  const calledUrl = () => fetchMock.mock.calls[0][0] as string;
  const calledMethod = () => fetchMock.mock.calls[0][1].method as string;
  const calledBody = () => fetchMock.mock.calls[0][1].body as string | undefined;

  describe('applicationService', () => {
    it('lists applications', async () => {
      await applicationService.getAll();

      expect(calledUrl()).toBe('/api/v1/applications');
      expect(calledMethod()).toBe('GET');
    });

    it('gets one by id', async () => {
      await applicationService.getById(3);

      expect(calledUrl()).toBe('/api/v1/applications/3');
    });

    it('accepts a string id', async () => {
      await applicationService.getById('abc');

      expect(calledUrl()).toBe('/api/v1/applications/abc');
    });

    it('creates with a JSON body', async () => {
      await applicationService.create({ name: 'App', alias: 'APP' });

      expect(calledUrl()).toBe('/api/v1/applications');
      expect(calledMethod()).toBe('POST');
      expect(JSON.parse(calledBody()!)).toEqual({ name: 'App', alias: 'APP' });
    });

    it('updates by id', async () => {
      await applicationService.update(1, { name: 'Renamed' });

      expect(calledUrl()).toBe('/api/v1/applications/1');
      expect(calledMethod()).toBe('PUT');
    });

    it('deletes by id', async () => {
      await applicationService.delete(1);

      expect(calledUrl()).toBe('/api/v1/applications/1');
      expect(calledMethod()).toBe('DELETE');
    });
  });

  describe('pageService', () => {
    it('unwraps the pages array out of the builder context', async () => {
      fetchMock.mockResolvedValueOnce(
        new Response(JSON.stringify({ application: { id: 5 }, pages: [{ id: 1, name: 'Home' }] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );

      const pages = await pageService.getByAppId(5);

      expect(calledUrl()).toBe('/api/v1/pages/builder/5');
      expect(pages).toEqual([{ id: 1, name: 'Home' }]);
    });

    it('exposes the full builder context', async () => {
      fetchMock.mockResolvedValueOnce(
        new Response(JSON.stringify({ application: { id: 5 }, pages: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );

      const context = await pageService.getBuilderContext(5);

      expect(calledUrl()).toBe('/api/v1/pages/builder/5');
      expect(context.application).toEqual({ id: 5 });
    });

    it('creates a page', async () => {
      await pageService.create({ name: 'Home', alias: 'HOME', page_number: 1, application_id: 5 });

      expect(calledUrl()).toBe('/api/v1/pages/builder/');
      expect(calledMethod()).toBe('POST');
    });

    it('updates a page under the builder prefix', async () => {
      await pageService.update(3, { name: 'Renamed' });

      expect(calledUrl()).toBe('/api/v1/pages/builder/3');
      expect(calledMethod()).toBe('PUT');
    });

    it('deletes a page under the builder prefix', async () => {
      await pageService.delete(3);

      expect(calledUrl()).toBe('/api/v1/pages/builder/3');
      expect(calledMethod()).toBe('DELETE');
    });
  });

  describe('itemService', () => {
    it('lists items filtered by page', async () => {
      await itemService.getByPageId(2);

      expect(calledUrl()).toBe('/api/v1/items?page_id=2');
    });

    it('creates an item', async () => {
      await itemService.create({ name: 'P1_NAME', item_type: 'text' });

      expect(calledUrl()).toBe('/api/v1/items');
      expect(calledMethod()).toBe('POST');
    });

    it('updates an item', async () => {
      await itemService.update(9, { label: 'Name' });

      expect(calledUrl()).toBe('/api/v1/items/9');
      expect(calledMethod()).toBe('PUT');
    });

    it('deletes an item', async () => {
      await itemService.delete(9);

      expect(calledUrl()).toBe('/api/v1/items/9');
      expect(calledMethod()).toBe('DELETE');
    });
  });

  describe('regionService', () => {
    it('lists regions for a page', async () => {
      await regionService.getByPageId(4);

      expect(calledUrl()).toBe('/api/v1/regions?page_id=4');
    });

    it('creates a region', async () => {
      await regionService.create({ name: 'Body', region_type: 'form' });

      expect(calledUrl()).toBe('/api/v1/regions');
    });
  });

  describe('lovService', () => {
    it('lists all LOVs', async () => {
      await lovService.getAll();

      expect(calledUrl()).toBe('/api/v1/lovs/');
    });

    it('gets a LOV by name', async () => {
      await lovService.getByName('STATUSES');

      expect(calledUrl()).toBe('/api/v1/lovs/name/STATUSES');
    });
  });

  describe('pageProcessService', () => {
    it('lists processes for a page', async () => {
      await pageProcessService.getByPageId(6);

      expect(calledUrl()).toBe('/api/v1/processes?page_id=6');
    });
  });

  describe('validationService', () => {
    it('lists validations for a page', async () => {
      await validationService.getByPageId(7);

      expect(calledUrl()).toBe('/api/v1/validations?page_id=7');
    });
  });

  describe('computationService', () => {
    it('lists computations for a page', async () => {
      await computationService.getByPageId(8);

      expect(calledUrl()).toBe('/api/v1/computations?page_id=8');
    });
  });

  describe('restDataSourceService', () => {
    it('lists data sources for an application', async () => {
      await restDataSourceService.getByAppId(2);

      expect(calledUrl()).toBe('/api/v1/rest-data-sources?application_id=2');
    });

    it('executes a data source with no options', async () => {
      await restDataSourceService.execute(3);

      expect(calledUrl()).toBe('/api/v1/rest-data-sources/3/execute');
      expect(calledMethod()).toBe('POST');
      expect(JSON.parse(calledBody()!)).toEqual({});
    });

    it('executes a data source with a payload and page', async () => {
      await restDataSourceService.execute(3, { payload: { id: 1 }, page_id: 4 });

      expect(JSON.parse(calledBody()!)).toEqual({ payload: { id: 1 }, page_id: 4 });
    });

    it('fetches application metadata', async () => {
      await getApplicationMetadata(1);

      expect(calledUrl()).toBe('/api/v1/applications/1/metadata');
    });
  });
});
