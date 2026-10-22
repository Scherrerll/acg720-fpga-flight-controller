import test from 'node:test';
import assert from 'node:assert/strict';
import { BlobBucket } from '../platform/blob-bucket.mjs';

const key = n => `logs/flight_${String(n).padStart(3, '0')}.json`;
function store(pageSize = 2) {
  const data = new Map();
  const calls = [];
  return { data, calls,
    async set(k, v) { calls.push(['set', k]); data.set(k, v); },
    async get(k, options) { calls.push(['get', k, options]); return data.get(k) ?? null; },
    async delete(k) { calls.push(['delete', k]); data.delete(k); },
    async list(options) {
      calls.push(['list', options]);
      const keys = [...data.keys()].filter(k => k.startsWith(options.prefix)).sort();
      const start = Number(options.cursor || 0);
      return { blobs: keys.slice(start, start + pageSize).map(key => ({ key, etag: 'etag' })),
        ...(start + pageSize < keys.length ? { cursor: String(start + pageSize) } : {}) };
    },
  };
}

test('restart preserves atomic payload and metadata; overwrite replaces metadata', async () => {
  const shared = store();
  await new BlobBucket(shared).put(key(1), '{"n":1}', {
    customMetadata: { id: 'flight_001', old: 'yes' }, httpMetadata: { contentType: 'application/json' },
  });
  const bucket = new BlobBucket(shared);
  const first = await bucket.get(key(1));
  assert.deepEqual(await first.json(), { n: 1 });
  assert.equal(await first.text(), '{"n":1}');
  assert.equal(first.httpMetadata.contentType, 'application/json');
  await bucket.put(key(1), '{"n":2}', { customMetadata: { id: 'flight_001' } });
  const object = await bucket.get(key(1));
  assert.deepEqual(object.customMetadata, { id: 'flight_001' });
  assert.deepEqual(object.httpMetadata, {});
  assert.deepEqual(await object.json(), { n: 2 });
  assert.equal(shared.data.size, 1);
  await bucket.delete(key(1));
  await bucket.delete(key(1));
  assert.equal(await bucket.get(key(1)), null);
});

test('keys, prefixes, limits and metadata reject invalid input before SDK access', async () => {
  const shared = store();
  const bucket = new BlobBucket(shared);
  for (const invalid of ['logs/short.json', 'logs/../secret.json', 'logs/abcdefgh.json/x',
    'telemetry/other.json', '/logs/abcdefgh.json', 'logs/' + 'a'.repeat(91) + '.json', null]) {
    await assert.rejects(bucket.get(invalid), TypeError);
    await assert.rejects(bucket.put(invalid, '{}'), TypeError);
    await assert.rejects(bucket.delete(invalid), TypeError);
  }
  await assert.rejects(bucket.list({ prefix: '' }), TypeError);
  await assert.rejects(bucket.list({ limit: 0 }), TypeError);
  await assert.rejects(bucket.put(key(1), '{}', { customMetadata: { bad: 1 } }), TypeError);
  assert.equal(shared.calls.length, 0);
});

test('bounded manual pagination reports exact truncation and uses strong reads', async () => {
  const shared = store(2);
  const bucket = new BlobBucket(shared);
  for (let n = 0; n < 10; n++) await bucket.put(key(n), '{}', { customMetadata: { id: `flight_${n}` } });
  shared.calls.length = 0;
  const page = await bucket.list({ prefix: 'logs/', limit: 3, include: ['customMetadata'] });
  assert.equal(page.objects.length, 3);
  assert.equal(page.truncated, true);
  assert.equal(page.objects[0].customMetadata.id, 'flight_0');
  assert.equal(shared.calls.filter(c => c[0] === 'get').length, 4);
  assert.equal(shared.calls.filter(c => c[0] === 'list').length, 2);
  for (const call of shared.calls) {
    const options = call[0] === 'get' ? call[2] : call[1];
    assert.equal(options.consistency, 'strong');
    if (call[0] === 'list') assert.equal(options.paginate, false);
  }
  const all = await bucket.list({ limit: 10 });
  assert.equal(all.truncated, false);
  assert.equal(all.objects.length, 10);
});

test('corrupted and foreign entries are hidden; corruption does not falsely truncate', async () => {
  const shared = store();
  const bucket = new BlobBucket(shared);
  shared.data.set(key(1), 'secret plain text');
  shared.data.set(key(2), JSON.stringify({ version: 1, payload: 'secret', customMetadata: null, httpMetadata: {} }));
  shared.data.set('logs/../secret.json', 'secret');
  await bucket.put(key(3), '{}', { customMetadata: { id: 'flight_003' } });
  assert.equal(await bucket.get(key(1)), null);
  assert.deepEqual(await bucket.list({ limit: 1, include: ['customMetadata'] }), {
    objects: [{ key: key(3), customMetadata: { id: 'flight_003' } }], truncated: false,
  });
});

test('SDK failures propagate on every operation', async () => {
  for (const method of ['get', 'set', 'list', 'delete']) {
    const shared = store();
    const failure = new Error(`SDK ${method} failed`);
    shared[method] = async () => { throw failure; };
    const bucket = new BlobBucket(shared);
    const operation = method === 'set' ? bucket.put(key(1), '{}')
      : method === 'list' ? bucket.list() : bucket[method](key(1));
    await assert.rejects(operation, error => error === failure);
  }
});
