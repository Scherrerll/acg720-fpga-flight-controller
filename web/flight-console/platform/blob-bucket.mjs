// R2 subset used by worker/flight.mjs. The injected store is an EdgeOne Blob Store.
// Payload and metadata share one atomic set; there is no mutable listing index.
const KEY = /^(?:telemetry\/latest\.json|logs\/[A-Za-z0-9_-]{8,90}\.json|control\/heartbeat\.json|control\/request\/[0-9a-f]{32}\/[0-9a-f]{32}\.json|control\/result\/[0-9a-f]{32}\/[A-Za-z0-9_-]{8,90}\.json)$/;
function validKey(key) {
  if (typeof key !== 'string' || !KEY.test(key)) throw new TypeError('Invalid bucket key');
}
function record(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.values(value).every(v => typeof v === 'string');
}
function metadata(value = {}) {
  if (!record(value)) throw new TypeError('Metadata must contain strings');
  return { ...value };
}
function decode(raw) {
  if (raw === null) return null;
  try {
    const v = JSON.parse(raw);
    if (v?.version !== 1 || typeof v.payload !== 'string'
      || !record(v.customMetadata) || !record(v.httpMetadata)) return null;
    return v;
  } catch { return null; }
}

export class BlobBucket {
  constructor(store) {
    if (!store || ['get', 'set', 'list', 'delete'].some(k => typeof store[k] !== 'function')) {
      throw new TypeError('An EdgeOne Blob Store is required');
    }
    this.store = store;
  }

  async get(key) {
    validKey(key);
    const value = decode(await this.store.get(key, { type: 'text', consistency: 'strong' }));
    if (!value) return null;
    return {
      key, customMetadata: { ...value.customMetadata }, httpMetadata: { ...value.httpMetadata },
      text: async () => value.payload,
      json: async () => JSON.parse(value.payload),
    };
  }

  async put(key, payload, options = {}) {
    validKey(key);
    if (typeof payload !== 'string') throw new TypeError('Payload must be a string');
    await this.store.set(key, JSON.stringify({ version: 1, payload,
      customMetadata: metadata(options.customMetadata), httpMetadata: metadata(options.httpMetadata) }));
  }

  async delete(key) {
    validKey(key);
    await this.store.delete(key);
  }

  async list({ prefix = 'logs/', limit = 100, include = [] } = {}) {
    if (prefix !== 'logs/') throw new TypeError('Only the logs/ prefix is supported');
    if (!Number.isInteger(limit) || limit < 1 || limit > 1000) throw new TypeError('Invalid list limit');
    const objects = [];
    const cursors = new Set();
    const seen = new Set();
    let cursor;
    do {
      const page = await this.store.list({ prefix, paginate: false, consistency: 'strong',
        ...(cursor ? { cursor } : {}) });
      if (!page || !Array.isArray(page.blobs)) throw new Error('Invalid Blob list response');
      for (const blob of page.blobs) {
        const key = blob?.key;
        if (typeof key !== 'string' || !KEY.test(key) || !key.startsWith(prefix) || seen.has(key)) continue;
        seen.add(key);
        const object = await this.get(key);
        if (!object) continue;
        // Read at most one extra valid envelope to establish actual truncation.
        if (objects.length === limit) return { objects, truncated: true };
        objects.push({ key, ...(include.includes('customMetadata')
          ? { customMetadata: object.customMetadata } : {}) });
      }
      cursor = page.cursor;
      if (cursor) {
        if (typeof cursor !== 'string' || cursors.has(cursor)) throw new Error('Invalid Blob pagination cursor');
        cursors.add(cursor);
      }
    } while (cursor);
    return { objects, truncated: false };
  }
}

export const createBlobBucket = store => new BlobBucket(store);
