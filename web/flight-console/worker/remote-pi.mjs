// Opt-in command mailbox. The local serial owner remains the final adapter and
// the FPGA still decides whether a stopped-state SET can be committed.
export const REMOTE_PI_TTL_MS = 8000;
export const REMOTE_PI_FRESH_MS = 5000;
const HEX = /^[0-9a-f]{32}$/;
const ID = /^[A-Za-z0-9_-]{8,90}$/;
const GAIN = /^(?:0(?:\.[0-9]{1,4})?|1(?:\.0{1,4})?)$/;
const BUILDS = new Set(['0000B0B4', '0000B0B5']);
const PHASES = new Set(['idle', 'queued_get', 'await_get', 'queued_set', 'await_set_ack', 'queued_verify_get', 'await_verify_get']);
const CODES = new Set(['queued', 'queried', 'verified', 'unknown', 'cancelled', 'timeout', 'mismatch', 'locked', 'nack',
  'stale_sequence', 'blocked', 'rejected', 'expired', 'transport', 'busy', 'stale', 'unsupported', 'not_stopped']);
const HEADERS = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Robots-Tag': 'noindex, nofollow, noarchive' };
const json = (value, status = 200) => new Response(JSON.stringify(value), { status, headers: HEADERS });
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const uint = v => Number.isInteger(v) && v >= 0 && v <= 0xffffffff;
const age = v => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1e12 ? v : null;
const exactKeys = (v, keys) => object(v) && Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v, k));
const resultKey = (epoch, id) => `control/result/${epoch}/${id}.json`;
const requestKey = (epoch, challenge) => `control/request/${epoch}/${challenge}.json`;
const metadata = { httpMetadata: { contentType: 'application/json' } };
const sameCommand = (a, b) => object(a) && object(b) && exactKeys(a, Object.keys(b))
  && Object.keys(b).every(k => a[k] === b[k]);

function configured(env) {
  const a = env.CONTROL_TOKEN, b = env.PUBLISH_TOKEN;
  return typeof a === 'string' && typeof b === 'string' && a.length >= 32 && b.length >= 32
    && a.length <= 4096 && b.length <= 4096 && a !== b;
}
async function matches(received, expected) {
  if (typeof received !== 'string' || received.length > 4096) return false;
  const hash = s => crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  const [a, b] = await Promise.all([hash(received), hash(expected)]);
  const aa = new Uint8Array(a), bb = new Uint8Array(b);
  let diff = 0; for (let i = 0; i < aa.length; i++) diff |= aa[i] ^ bb[i];
  return diff === 0;
}
async function get(bucket, key) { const v = await bucket.get(key); return v ? await v.json() : null; }
async function put(bucket, key, value) { await bucket.put(key, JSON.stringify(value), metadata); }
function active(v) {
  if (!object(v) || typeof v.p_text !== 'string' || !GAIN.test(v.p_text)
    || typeof v.i_text !== 'string' || !GAIN.test(v.i_text) || !uint(v.generation) || !BUILDS.has(v.build)) return null;
  return { p_text: v.p_text, i_text: v.i_text, generation: v.generation, build: v.build, age_ms: age(v.age_ms) };
}
function outcome(v) {
  if (!object(v) || !CODES.has(v.code)) return null;
  const a = active(v.active);
  // A terminal success without a real parameter tuple is never a success.
  const code = ['queried', 'verified'].includes(v.code) && !a ? 'unknown' : v.code;
  return { code, active: a, operation_id: uint(v.operation_id) ? v.operation_id : null };
}
export function sanitizeRemotePIStatus(v) {
  v = object(v) ? v : {};
  const a = active(v.active), transport = v.source === 'SiK' && v.baud === 115200;
  const enabled = v.enabled === true, connected = v.connected === true;
  const busy = v.busy === true;
  const epoch = uint(v.epoch) ? v.epoch : null;
  const supported = v.supported === true && a !== null;
  const can_query = enabled && connected && transport && epoch !== null && !busy && v.can_query === true;
  const can_set = can_query && supported && v.can_set === true;
  return { enabled, connected, source: transport ? 'SiK' : null, baud: transport ? 115200 : null,
    epoch, supported, busy, phase: PHASES.has(v.phase) ? v.phase : 'idle',
    operation_id: uint(v.operation_id) ? v.operation_id : null,
    active: a, result: outcome(object(v.result) ? { ...v.result, active: a } : null), can_query, can_set,
    block_reason: can_set ? '' : can_query ? '请先查询设备，并满足地面站停机检查。' : '地面参数服务尚未就绪。' };
}
async function readJSON(request, max = 8192) {
  const type = request.headers.get('Content-Type') || '';
  if (!/^application\/json(?:\s*;\s*charset=utf-8)?$/i.test(type) || request.headers.has('Content-Encoding')
    || request.headers.has('Transfer-Encoding')) throw Object.assign(Error(), { status: 400 });
  const length = request.headers.get('Content-Length');
  if (length !== null && (!/^\d+$/.test(length) || Number(length) > max)) throw Object.assign(Error(), { status: 413 });
  let total = 0, chunks = [];
  const reader = request.body?.getReader();
  if (!reader) throw Object.assign(Error(), { status: 400 });
  try {
    for (;;) { const { done, value } = await reader.read(); if (done) break;
      total += value.byteLength; if (total > max) { await reader.cancel(); throw Object.assign(Error(), { status: 413 }); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(total); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  const value = JSON.parse(text);
  // JSON.parse accepts duplicate members; control intents deliberately do not.
  const keys = [];
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '{') keys.push(new Set());
    else if (text[i] === '}') keys.pop();
    else if (text[i] === '"') {
      const start = i++; while (i < text.length) { if (text[i] === '\\') i += 2; else if (text[i] === '"') break; else i++; }
      const token = JSON.parse(text.slice(start, i + 1)); let next = i + 1;
      while (/\s/.test(text[next] || '') && next < text.length) next++;
      if (text[next] === ':') { const set = keys.at(-1); if (!set || set.has(token)) throw Error(); set.add(token); }
    }
  }
  return value;
}
function fresh(heartbeat, now) {
  return object(heartbeat) && HEX.test(heartbeat.epoch) && HEX.test(heartbeat.challenge)
    && Number.isFinite(heartbeat.received_at_ms) && now >= heartbeat.received_at_ms
    && now - heartbeat.received_at_ms <= REMOTE_PI_FRESH_MS;
}
function cleanCommand(v, h, now) {
  const fields = ['id', 'epoch', 'challenge', 'action', 'expected_epoch'];
  if (v?.action === 'set') fields.push('p', 'i', 'expected_generation', 'confirmed_stopped');
  if (!exactKeys(v, fields) || !ID.test(v.id) || !HEX.test(v.epoch) || !HEX.test(v.challenge)
    || !['query', 'set'].includes(v.action) || !uint(v.expected_epoch)) throw Object.assign(Error(), { status: 400 });
  if (!fresh(h, now) || h.epoch !== v.epoch || h.challenge !== v.challenge || h.status.epoch !== v.expected_epoch)
    throw Object.assign(Error(), { status: 409 });
  if (!h.status.can_query) throw Object.assign(Error(), { status: 409 });
  if (v.action === 'set' && (!h.status.can_set || v.confirmed_stopped !== true || typeof v.p !== 'string'
    || typeof v.i !== 'string' || !GAIN.test(v.p) || !GAIN.test(v.i) || !uint(v.expected_generation)
    || v.expected_generation !== h.status.active?.generation)) throw Object.assign(Error(), { status: 409 });
  return { ...v, created_at_ms: now, expires_at_ms: now + REMOTE_PI_TTL_MS };
}

/** Returns null for routes owned by the existing read-only telemetry worker. */
export async function handleRemotePI(request, env, { now = Date.now } = {}) {
  const u = new URL(request.url), path = u.pathname;
  if (!path.startsWith('/api/remote-pi/')) return null;
  if (!configured(env)) return json({ error: 'remote_pi_disabled', enabled: false }, 503);
  if (!env.BUCKET) return json({ error: 'storage_unavailable' }, 503);
  const relayRoute = ['/api/remote-pi/heartbeat', '/api/remote-pi/poll', '/api/remote-pi/result'].includes(path);
  const token = request.headers.get(relayRoute ? 'X-Flight-Publish-Token' : 'X-Flight-Control-Token') || '';
  if (!await matches(token, relayRoute ? env.PUBLISH_TOKEN : env.CONTROL_TOKEN)) return json({ error: 'unauthorized' }, 401);
  const t = now();
  try {
    if (request.method === 'POST' && path === '/api/remote-pi/heartbeat') {
      const v = await readJSON(request);
      if (!exactKeys(v, ['epoch', 'challenge', 'status']) || !HEX.test(v.epoch) || !HEX.test(v.challenge) || !object(v.status)) throw Error();
      await put(env.BUCKET, 'control/heartbeat.json', { epoch: v.epoch, challenge: v.challenge,
        status: sanitizeRemotePIStatus(v.status), received_at_ms: t });
      return json({ ok: true, server_now_ms: t });
    }
    if (request.method === 'GET' && path === '/api/remote-pi/status') {
      if (u.search) return json({ error: 'invalid_payload' }, 400);
      const h = await get(env.BUCKET, 'control/heartbeat.json'), relay_fresh = fresh(h, t);
      return json({ enabled: true, relay_fresh, age_ms: h ? Math.max(0, t - h.received_at_ms) : null,
        epoch: h?.epoch ?? null, challenge: relay_fresh ? h.challenge : null,
        status: h ? sanitizeRemotePIStatus(h.status) : null, server_now_ms: t });
    }
    if (request.method === 'POST' && path === '/api/remote-pi/command') {
      if (request.headers.get('Origin') !== u.origin || request.headers.get('Sec-Fetch-Site') === 'cross-site') return json({ error: 'origin' }, 403);
      const v = await readJSON(request, 2048), h = await get(env.BUCKET, 'control/heartbeat.json');
      const command = cleanCommand(v, h, t), key = resultKey(v.epoch, v.id);
      // Persist a tombstone before publishing the mailbox. Duplicate IDs do not
      // refresh the deadline or create a second executable command.
      if (await get(env.BUCKET, key)) return json({ error: 'request_already_used' }, 409);
      await put(env.BUCKET, key, { id: v.id, epoch: v.epoch, challenge: v.challenge,
        created_at_ms: t, intent: command, result: { code: 'queued', active: null, operation_id: null } });
      await put(env.BUCKET, requestKey(v.epoch, v.challenge), command);
      return json({ ok: true, id: v.id, epoch: v.epoch, expires_at_ms: command.expires_at_ms }, 202);
    }
    if (request.method === 'GET' && path === '/api/remote-pi/poll') {
      const params = [...u.searchParams.keys()];
      const epoch = u.searchParams.get('epoch'), challenge = u.searchParams.get('challenge');
      if (params.length !== 2 || new Set(params).size !== 2 || !params.includes('epoch') || !params.includes('challenge')
        || !HEX.test(epoch) || !HEX.test(challenge)) throw Error();
      const h = await get(env.BUCKET, 'control/heartbeat.json');
      if (!fresh(h, t) || h.epoch !== epoch || h.challenge !== challenge) return json({ error: 'relay_changed' }, 409);
      const command = await get(env.BUCKET, requestKey(epoch, challenge));
      const record = command ? await get(env.BUCKET, resultKey(epoch, command.id)) : null;
      const ready = command && command.expires_at_ms > t && command.created_at_ms <= t && record?.result?.code === 'queued';
      return json({ server_now_ms: t, command: ready ? command : null });
    }
    if (request.method === 'POST' && path === '/api/remote-pi/result') {
      const v = await readJSON(request), result = outcome(v?.result);
      if (!exactKeys(v, ['epoch', 'id', 'challenge', 'intent', 'result']) || !HEX.test(v.epoch) || !HEX.test(v.challenge)
        || !ID.test(v.id) || !result || result.code === 'queued') throw Error();
      const key = resultKey(v.epoch, v.id), previous = await get(env.BUCKET, key);
      const command = previous?.intent;
      const h = await get(env.BUCKET, 'control/heartbeat.json');
      if (!command || command.id !== v.id || !previous || previous.challenge !== v.challenge
        || t < command.created_at_ms || t - command.created_at_ms > 60000) return json({ error: 'request_changed' }, 409);
      // Blob storage has no compare-and-set. Concurrent use of one ID may
      // replace its intent; the relay must echo the exact command it consumed.
      // Such ambiguity is a terminal unknown, never another intent's success.
      const unknown = () => { result.code = 'unknown'; result.active = null; result.operation_id = null; };
      if (!sameCommand(v.intent, command)) unknown();
      if (['queried', 'verified'].includes(result.code)
        && (h?.epoch !== v.epoch || h.status?.epoch !== command.expected_epoch)) unknown();
      if (result.code === 'verified' && (command.action !== 'set'
        || Number(result.active?.p_text) !== Number(command.p) || Number(result.active?.i_text) !== Number(command.i)
        || result.active?.generation !== ((command.expected_generation + 1) >>> 0))) unknown();
      if (result.code === 'queried' && command.action !== 'query') unknown();
      // Replayed terminal reports cannot overwrite a previously recorded result.
      if (previous.result?.code !== 'queued') return json({ ok: true, recorded: false });
      await put(env.BUCKET, key, { ...previous, result, completed_at_ms: t });
      return json({ ok: true, recorded: true });
    }
    const match = /^\/api\/remote-pi\/result\/([0-9a-f]{32})\/([A-Za-z0-9_-]{8,90})$/.exec(path);
    if (request.method === 'GET' && match) {
      if (u.search) throw Error();
      const v = await get(env.BUCKET, resultKey(match[1], match[2]));
      return json({ result: v ? outcome(v.result) : null, server_now_ms: t });
    }
    return json({ error: 'method_not_allowed' }, 405);
  } catch (e) { return json({ error: e.status === 413 ? 'payload_too_large' : e.status === 409 ? 'state_changed' : 'invalid_payload' }, e.status === 413 ? 413 : e.status === 409 ? 409 : 400); }
}
