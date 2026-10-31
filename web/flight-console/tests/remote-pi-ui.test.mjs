import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {RemotePI, gain, validActive, validStatus} from '../frontend/remote-pi-ui.js';

const epoch = 'a'.repeat(32), challenge = 'b'.repeat(32), key = 'independent-private-control-key-32-characters';
const uuid = '12345678-1234-4234-9234-123456789abc';
const active = (extra = {}) => ({p_text: '0.1000', i_text: '0.0350', generation: 5, build: '0000B0B4', age_ms: 20, ...extra});
const status = (extra = {}) => ({enabled: true, relay_fresh: true, epoch, challenge,
  status: {epoch: 3, can_query: true, can_set: true, supported: true, busy: false, active: active(), block_reason: '', ...extra}, server_now_ms: 1800000000000});
const reply = (body, code = 200) => ({ok: code >= 200 && code < 300, status: code, json: async () => body});

function harness(options = {}) {
  let time = 100, currentStatus = status(), queue = [], commandCode = 202, failure = null, customResult = null;
  const calls = [];
  const model = new RemotePI({now: () => time, uuid: () => uuid, sleep: async ms => { time += ms; }, resultMs: 1000,
    fetchFn: async (url, init) => {
      calls.push({url, init});
      if (failure) throw failure;
      if (url.endsWith('/status')) return reply(currentStatus);
      if (init.method === 'POST') return reply({queued: true}, commandCode);
      if (customResult) return customResult();
      return reply({result: queue.length ? queue.shift() : null});
    }, ...options});
  return {model, calls, setStatus: s => { currentStatus = s; }, results: (...values) => { queue = values; },
    code: n => { commandCode = n; }, fail: v => { failure = v; }, advance: ms => { time += ms; },
    resultFn: f => { customResult = f; }, posts: () => calls.filter(c => c.init.method === 'POST')};
}
async function queried(h) {
  await h.model.connect(key);
  h.results({code: 'queried', active: active(), operation_id: 1});
  assert.equal(await h.model.command('query'), true);
}

test('gain boundaries reject rounding, signs, spaces and exponent notation', () => {
  for (const s of ['0', '1', '1.0000', '0.0001', '000.1000']) assert.notEqual(gain(s), null);
  for (const s of ['-0', '+0.1', ' 0.1', '0.1 ', '.1', '1.', '1.0001', '0.00001', '1e-1', '', null]) assert.equal(gain(s), null);
  assert.equal(gain('0.0350'), 350);
});

test('active/status validation fails closed including null ages and unsupported builds', () => {
  assert.equal(validActive(active()), true); assert.equal(validActive(active({build: '0000B0B5'})), true);
  for (const x of [{age_ms: null}, {age_ms: -1}, {p_text: '0.00001'}, {p_wire: 12}, {generation: -1}, {build: '0000B0B3'}]) assert.equal(validActive(active(x)), false);
  assert.equal(validStatus(status()), true);
  for (const x of [{epoch: ''}, {challenge: 'not-a-challenge'}, {server_now_ms: null}, {status: {epoch: 3}}]) assert.equal(validStatus({...status(), ...x}), false);
});

test('fresh status never substitutes for this-session query or stopped confirmation', async () => {
  const h = harness(); await h.model.connect(key);
  h.model.confirm(true); assert.equal(h.model.canSet, false);
  h.results({code: 'queried', active: active(), operation_id: 1}); await h.model.command('query');
  assert.equal(h.model.canSet, false); h.model.confirm(true); assert.equal(h.model.canSet, true);
});

test('query uses one authenticated POST, waits through queued results, then fills untouched draft', async () => {
  const h = harness(); await h.model.connect(key);
  h.results(null, {code: 'queued'}, {code: 'queried', active: active({p_text: '0.2500', i_text: '0.0400'}), operation_id: 9});
  assert.equal(await h.model.command('query'), true);
  assert.deepEqual(h.model.draft, {p: '0.2500', i: '0.0400'}); assert.equal(h.posts().length, 1);
  const sent = JSON.parse(h.posts()[0].init.body);
  assert.deepEqual(sent, {id: uuid, epoch, challenge, action: 'query', expected_epoch: 3});
  for (const call of h.calls) {
    assert.equal(call.init.headers['X-Flight-Control-Token'], key);
    assert.equal(call.url.includes(key), false); assert.equal(call.init.body?.includes(key) ?? false, false);
    assert.equal(call.init.redirect, 'error'); assert.equal(call.init.cache, 'no-store');
  }
});

test('periodic status and query completion preserve a manually edited draft', async () => {
  const h = harness(); await h.model.connect(key); h.model.edit('p', '0.4567');
  await h.model.refresh(); assert.equal(h.model.draft.p, '0.4567');
  h.results({code: 'queried', active: active(), operation_id: 1}); await h.model.command('query');
  assert.equal(h.model.draft.p, '0.4567'); assert.equal(h.model.dirty, true);
});

test('SET includes both decimal drafts, expected generation and stopped confirmation; ACK alone is insufficient', async () => {
  const h = harness(); await queried(h); h.model.edit('p', '0.2000'); h.model.confirm(true);
  h.results({code: 'queued'}, {code: 'verified', active: active({p_text: '0.2000', generation: 6}), operation_id: 2});
  assert.equal(await h.model.command('set'), true);
  const payload = JSON.parse(h.posts()[1].init.body);
  assert.deepEqual(payload, {id: uuid, epoch, challenge, action: 'set', expected_epoch: 3, p: '0.2000', i: '0.0350', expected_generation: 5, confirmed_stopped: true});
  assert.equal(h.model.active.generation, 6); assert.equal(h.model.dirty, false); assert.equal(h.model.stopped, false);
  assert.equal(h.model.canSet, false); // a fresh status must match the new generation
});

test('leading-zero drafts submit canonical fixed-four-place decimal text', async () => {
  const h = harness(); await queried(h); h.model.edit('p', '00.1'); h.model.edit('i', '000.035'); h.model.confirm(true);
  h.results({code: 'verified', active: active({generation: 6}), operation_id: 2});
  assert.equal(await h.model.command('set'), true);
  const payload = JSON.parse(h.posts()[1].init.body);
  assert.equal(payload.p, '0.1000'); assert.equal(payload.i, '0.0350');
});

test('SET result must match submitted build and exactly next uint32 generation', async () => {
  for (const extra of [{generation: 7}, {generation: 5}, {generation: 6, build: '0000B0B5'}]) {
    const h = harness(); await queried(h); h.model.confirm(true);
    h.results({code: 'verified', active: active(extra), operation_id: 2});
    assert.equal(await h.model.command('set'), false); assert.equal(h.model.qualified, false);
    assert.equal(h.posts().length, 2); assert.match(h.model.notice, /先查询/);
  }
  const h = harness(); h.setStatus(status({active: active({generation: 0xffffffff})})); await h.model.connect(key);
  h.results({code: 'queried', active: active({generation: 0xffffffff}), operation_id: 1});
  await h.model.command('query'); h.model.confirm(true);
  h.results({code: 'verified', active: active({generation: 0}), operation_id: 2});
  assert.equal(await h.model.command('set'), true); assert.equal(h.model.active.generation, 0);
});

test('control key shorter than server minimum is rejected without a request', async () => {
  const h = harness(); assert.equal(await h.model.connect('k'.repeat(31)), false); assert.equal(h.calls.length, 0);
  assert.equal(await h.model.connect('k'.repeat(32)), true);
});

test('an unknown or mismatched result revokes write qualification and never retries a POST', async () => {
  for (const result of [{code: 'unknown'}, {code: 'expired'}, {code: 'rejected'}, {code: 'verified', active: active({p_text: '0.9000'}), operation_id: 2}]) {
    const h = harness(); await queried(h); h.model.confirm(true); h.results(result);
    assert.equal(await h.model.command('set'), false); assert.equal(h.posts().length, 2);
    assert.equal(h.model.qualified, false); assert.equal(h.model.canSet, false); assert.match(h.model.notice, /先查询/);
  }
});

test('success code requires legitimate active and positive operation ID', async () => {
  for (const result of [{code: 'queried', active: active()}, {code: 'queried', active: active(), operation_id: '1'},
    {code: 'queried', active: active({age_ms: null}), operation_id: 1}, {code: 'verified', active: active(), operation_id: 1}]) {
    const h = harness(); await h.model.connect(key); h.results(result);
    assert.equal(await h.model.command('query'), false); assert.equal(h.model.qualified, false);
  }
});

test('twenty-second budget and transport failure leave result unknown without retransmission', async () => {
  assert.equal(new RemotePI().resultMs, 20000);
  const h = harness({resultMs: 20000}); await h.model.connect(key);
  assert.equal(await h.model.command('query'), false); assert.equal(h.posts().length, 1); assert.equal(h.model.busy, false);
  const f = harness(); await queried(f); f.model.confirm(true); f.fail(new Error('network'));
  assert.equal(await f.model.command('set'), false); assert.equal(f.posts().length, 2); assert.equal(f.model.qualified, false);
});

test('late status from a previous login cannot replace or lock the new login', async () => {
  const h = harness();
  let resolveOld;
  h.model.fetchFn = async () => new Promise(done => { resolveOld = done; });
  const old = h.model.connect(key);
  h.model.fetchFn = async () => reply(status());
  assert.equal(await h.model.connect('a-different-private-control-key-32-characters'), true);
  resolveOld(reply({}, 401));
  assert.equal(await old, false);
  assert.equal(h.model.token, 'a-different-private-control-key-32-characters'); assert.equal(h.model.fresh, true);
});

test('disabled relay and unsupported firmware cannot obtain SET capability', async () => {
  const h = harness(); await queried(h); h.model.confirm(true);
  h.setStatus(status({supported: false})); await h.model.refresh(); assert.equal(h.model.canSet, false);
  h.setStatus({...status(), relay_fresh: false}); await h.model.refresh();
  assert.equal(h.model.canQuery, false); assert.equal(h.model.qualified, false);
});

test('status expires at three seconds and restore still requires a new query', async () => {
  const h = harness(); await queried(h); h.model.confirm(true);
  h.advance(3000); assert.equal(h.model.canSet, false); h.model.tick();
  await h.model.refresh(); h.model.confirm(true); assert.equal(h.model.canSet, false);
});

test('relay or local epoch change and external generation change revoke query qualification', async () => {
  for (const s of [{...status(), epoch: 'c'.repeat(32)}, status({epoch: 4}), status({active: active({generation: 6})})]) {
    const h = harness(); await queried(h); h.model.confirm(true); h.setStatus(s); await h.model.refresh();
    assert.equal(h.model.qualified, false); assert.equal(h.model.canSet, false); assert.equal(h.model.stopped, false);
  }
});

test('auth failure clears key/qualification; defaults and disconnect produce no POST', async () => {
  const h = harness(); await queried(h); const count = h.posts().length;
  h.model.defaults(); assert.equal(h.posts().length, count); assert.equal(h.model.draft.p, '0.1000');
  h.model.fetchFn = async () => reply({}, 401); await h.model.refresh();
  assert.equal(h.model.token, ''); assert.equal(h.model.qualified, false); assert.equal(h.model.canQuery, false); assert.equal(h.model.active, null);
  h.model.disconnect(); assert.equal(h.posts().length, count);
});

test('one operation in flight and disconnect make a delayed success inert', async () => {
  const h = harness(); await h.model.connect(key);
  let resolve; h.resultFn(() => new Promise(done => { resolve = done; }));
  const first = h.model.command('query');
  await new Promise(done => setImmediate(done));
  assert.equal(await h.model.command('query'), false); assert.equal(h.posts().length, 1);
  h.model.disconnect(); resolve(reply({result: {code: 'queried', active: active(), operation_id: 1}}));
  assert.equal(await first, false); assert.equal(h.model.token, ''); assert.equal(h.model.active, null);
});

test('an epoch change while waiting rejects even an otherwise successful delayed response', async () => {
  const h = harness(); await h.model.connect(key);
  let resolve; h.resultFn(() => new Promise(done => { resolve = done; })); const pending = h.model.command('query');
  await new Promise(done => setImmediate(done));
  h.setStatus({...status(), epoch: 'd'.repeat(32)}); await h.model.refresh();
  resolve(reply({result: {code: 'queried', active: active(), operation_id: 1}}));
  assert.equal(await pending, false); assert.equal(h.model.qualified, false);
});

test('page wiring uses real module, same-origin assets, accessible controls and no persistent key storage', async () => {
  const html = await readFile(new URL('../frontend/parameters.html', import.meta.url), 'utf8');
  const js = await readFile(new URL('../frontend/remote-pi-ui.js', import.meta.url), 'utf8');
  assert.match(html, /src="\/remote-pi-ui.js"/); assert.match(html, /href="\/styles.css"/);
  for (const id of ['key', 'connect', 'disconnect', 'query', 'set', 'defaults', 'stopped', 'notice', 'active-p', 'active-i']) assert.ok(html.includes(`id="pi-${id}"`));
  assert.match(html, /href="\/parameters" aria-current="page"/); assert.match(html, /href="\/#live"/); assert.match(html, /href="\/#logs"/);
  assert.match(html, /底部水上电机已停止/);
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]); assert.equal(ids.length, new Set(ids).size);
  assert.doesNotMatch(js, /localStorage|sessionStorage|console\.|URLSearchParams/);
  assert.doesNotMatch(html, /(?:src|href)="https?:/); assert.match(html, /type="password" autocomplete="off"/);
  assert.match(js, /el\('key'\)\.value = ''/); assert.match(js, /pagehide/);
});
