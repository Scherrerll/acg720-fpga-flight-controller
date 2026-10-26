/* Dependency-free UI contract proof. Run: node ground/B0B3/test_xy_pi_ui.cjs
 * Reads the real HTML/JS; fake DOM, fetch and timers only. No listener, network,
 * serial device, Python import, or disk writes. This is not browser/hardware QA.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const html = fs.readFileSync(path.join(__dirname, 'dashboard.html'), 'utf8');
const source = fs.readFileSync(path.join(__dirname, 'xy-pi-ui.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, 'xy-pi-ui.css'), 'utf8');
const tags = [...html.matchAll(/<[^>]+\bid="(xy-pi-[^"]+)"[^>]*>/g)];
const ids = tags.map(match => match[1]);
assert.equal(new Set(ids).size, ids.length, 'HTML IDs must be unique');
for (const used of source.matchAll(/el\('([^']+)'\)/g)) {
  assert(ids.includes(`xy-pi-${used[1]}`), `JS references a missing real HTML ID: ${used[1]}`);
}
assert(html.indexOf('id="xy-pi-card"') > html.indexOf('control-card'));
assert(html.indexOf('id="xy-pi-card"') < html.indexOf('导航与传感器'));
assert(html.includes('href="/xy-pi-ui.css"') && html.includes('src="/xy-pi-ui.js"'));
assert(html.includes('href="/pi-help"') && html.includes('aria-live="polite"'));
for (const field of ['p', 'i', 'stopped']) assert(html.includes(`for="xy-pi-${field}"`));
assert(css.includes('.xy-pi-card') && css.includes('@media(max-width:760px)'));

const base = {
  enabled: true, connected: true, source: 'SiK', baud: 115200, epoch: 1,
  supported: false, busy: false, phase: 'idle', operation_id: null,
  active: null, result: null, can_query: true, can_set: false, block_reason: ''
};
const active = {
  p_text: '0.0500', i_text: '0.0000', p_wire: 500, i_wire: 0,
  generation: 0, build: '0000B0B3', age_ms: 10
};
const flush = async () => { for (let n = 0; n < 30; n++) await Promise.resolve(); };

async function setup() {
  const elements = Object.fromEntries(tags.map(match => {
    const tag = match[0];
    return [match[1], {
      value: /\bvalue="([^"]*)"/.exec(tag)?.[1] ?? '',
      checked: /\schecked(?:\s|>|=)/.test(tag),
      disabled: /\sdisabled(?:\s|>|=)/.test(tag),
      textContent: '', dataset: {}, attrs: {}, listeners: {},
      setAttribute(key, value) { this.attrs[key] = value; },
      addEventListener(key, listener) { this.listeners[key] = listener; }
    }];
  }));
  const env = {
    server: structuredClone(base), clock: 100, failStatus: false, failPost: false,
    failSession: false, nextReply: null, calls: [], timers: [], uuid: 0,
    deferredStatus: null
  };
  const sandbox = {
    document: {getElementById: id => elements[id]},
    performance: {now: () => env.clock}, AbortController,
    crypto: {randomUUID: () => `request-${++env.uuid}`},
    setTimeout(fn, delay) { const timer = {fn, delay}; env.timers.push(timer); return timer; },
    clearTimeout(timer) { env.timers = env.timers.filter(value => value !== timer); },
    async fetch(url, options) {
      // No real fetch is available in this context. Reject unknown mock routes.
      env.calls.push({url, options});
      if (url === '/api/xy-pi/session') {
        if (env.failSession) throw new Error('mock session unavailable');
        return {ok: true, status: 200, json: async () => ({token: 'test-token'})};
      }
      if (url === '/api/xy-pi/status') {
        if (env.failStatus) throw new Error('mock status offline');
        const captured = structuredClone(env.server);
        if (env.deferredStatus) await env.deferredStatus;
        return {ok: true, status: 200, json: async () => captured};
      }
      assert(['/api/xy-pi/query', '/api/xy-pi/set'].includes(url), `unexpected mock route: ${url}`);
      assert.equal(options.method, 'POST');
      if (env.failPost) throw new Error('mock response lost');
      const reply = env.nextReply ?? {status: 202, body: {operation_id: env.uuid}};
      return {ok: reply.status < 400, status: reply.status, json: async () => reply.body};
    }
  };
  vm.runInNewContext(source, sandbox, {filename: 'xy-pi-ui.js'});
  await flush();
  env.e = name => {
    assert(elements[`xy-pi-${name}`], `missing real HTML element ${name}`);
    return elements[`xy-pi-${name}`];
  };
  env.click = async name => { await env.e(name).listeners.click(); await flush(); };
  env.submit = async () => { await env.e('form').listeners.submit({preventDefault() {}}); await flush(); };
  env.poll = async () => {
    const timer = env.timers.find(value => value.delay === 500);
    assert(timer, 'one next status poll must be scheduled');
    env.timers.splice(env.timers.indexOf(timer), 1);
    env.clock += 500;
    await timer.fn();
    await flush();
  };
  env.edit = (name, value) => { env.e(name).value = value; env.e(name).listeners.input(); };
  env.confirm = () => { env.e('stopped').checked = true; env.e('stopped').listeners.change(); };
  env.posts = () => env.calls.filter(call => call.options.method === 'POST');
  env.complete = async (operationId, code = 'queried', values = active) => {
    env.server = {...base, supported: true, can_set: true, active: {...values},
      operation_id: operationId,
      result: {code, message: 'mock final result', operation_id: operationId, sequence: 10 + operationId}};
    await env.poll();
  };
  return env;
}

async function run() {
  let x = await setup();
  assert(!x.e('query').disabled && x.e('set').disabled);
  assert.equal(x.posts().length, 0, 'startup and polling never issue a POST');
  assert.equal(x.e('p').value, '0.0500');
  assert.equal(x.e('i').value, '0.0000');
  x.confirm(); assert(x.e('set').disabled, 'a label or checkbox is not a matched capability GET');
  await x.click('query');
  assert.equal(x.posts().length, 1);
  assert(x.e('query').disabled && x.e('set').disabled, 'only one in-flight action');
  let request = x.posts()[0];
  assert.deepEqual(JSON.parse(request.options.body), {request_id: 'request-1', epoch: 1});
  assert.equal(request.options.headers['X-XY-PI-Token'], 'test-token');
  assert.equal(request.options.headers['Content-Type'], 'application/json');
  await x.complete(1, 'queried', {...active, p_text: '0.1500', p_wire: 1500});
  assert.equal(x.e('p').value, '0.1500', 'successful first GET populates an untouched draft');
  assert(x.e('status').textContent.includes('设备查询完成'));
  x.edit('p', '0.2500'); await x.poll();
  assert.equal(x.e('p').value, '0.2500', 'polling does not overwrite edited drafts');
  await x.click('query'); await x.complete(2);
  assert.equal(x.e('p').value, '0.2500', 'even an explicit GET preserves an already edited draft');

  for (const value of ['-0.1', '1.0001', '0.00001', '1e-3', '.05', '0.05 ', 'NaN', 'Infinity', '']) {
    x.edit('p', value); x.confirm(); assert(x.e('set').disabled, `invalid decimal: ${value}`);
  }
  for (const value of ['0', '1', '0.0001', '1.0000', '0.1234']) {
    x.edit('p', value); x.confirm(); assert(!x.e('set').disabled, `valid exact decimal: ${value}`);
  }
  x.edit('p', '0.2500'); x.confirm(); await x.submit();
  request = x.posts()[2];
  assert.deepEqual(JSON.parse(request.options.body), {request_id: 'request-3', epoch: 1,
    expected_generation: 0, p: '0.2500', i: '0.0000', confirmed_stopped: true});
  assert(!x.e('stopped').checked, 'each SET consumes the explicit confirmation');
  x.server = {...base, supported: true, busy: true, can_query: false,
    phase: 'await_verify_get', operation_id: 3};
  await x.poll();
  assert(x.e('status').textContent.includes('独立 GET'));
  await x.complete(3, 'verified', {...active, p_text: '0.2500', p_wire: 2500, generation: 1});
  assert.equal(x.e('generation').textContent, '1');
  assert(x.e('status').textContent.includes('成对写入完成'));
  let count = x.posts().length;
  await x.click('defaults');
  assert.equal(x.e('p').value, '0.0500'); assert.equal(x.posts().length, count, 'defaults do not POST');
  x.confirm(); x.failPost = true; await x.submit();
  assert(x.e('status').textContent.includes('结果未知'));
  x.failPost = false; await x.poll(); x.confirm();
  assert(x.e('set').disabled, 'unknown result stays blocked despite a current can_set=true');
  assert.equal(x.posts().length, count + 1, 'lost response never auto-retries a POST');
  await x.click('defaults'); assert(x.e('status').textContent.includes('先查询'));
  await x.click('query'); await x.complete(5, 'queried'); x.confirm();
  assert(!x.e('set').disabled, 'only an explicit matched queried result recovers the unknown state');
  x.failStatus = true; await x.poll();
  assert(x.e('query').disabled && x.e('set').disabled);
  assert(x.e('age').textContent.includes('历史'));
  x.failStatus = false; await x.poll(); assert(x.e('status').textContent.includes('恢复'));
  x.server = {...base, epoch: 2}; await x.poll();
  assert.equal(x.e('active-p').textContent, '—');
  assert(x.e('set').disabled && !x.e('stopped').checked, 'new epoch invalidates old device values/confirmation');

  x = await setup();
  x.server = {...base, source: 'USB', can_query: false, block_reason: 'USB 镜像只读'}; await x.poll();
  assert(x.e('query').disabled && x.e('set').disabled && x.e('status').textContent.includes('USB'));
  x = await setup();
  x.server = {...base, enabled: false, connected: false, epoch: null, can_query: false,
    block_reason: '未启用参数入口'}; await x.poll();
  assert(x.e('status').textContent.includes('未启用'));
  assert(!x.e('status').textContent.includes('状态接口不可用'), 'null offline epoch is a valid offline state');

  for (const code of ['unknown', 'timeout', 'mismatch', 'cancelled', 'UNEXPECTED', 'verified']) {
    x = await setup(); await x.click('query'); await x.complete(1, code); x.confirm();
    assert(x.e('status').textContent.includes('先查询') && x.e('set').disabled, `GET cannot treat ${code} as queried`);
  }
  for (const code of ['locked', 'stale_sequence', 'nack']) {
    x = await setup(); await x.click('query'); await x.complete(1, code);
    assert(x.e('status').textContent.includes(code));
    assert(!x.e('status').textContent.includes('设备查询完成'));
  }
  x = await setup(); await x.complete(7, 'unknown');
  assert(x.e('status').textContent.includes('先查询'), 'reload exposes prior unknown controller result');
  x = await setup(); await x.complete(9); x.confirm(); await x.submit(); await x.complete(1, 'queried');
  assert(x.e('status').textContent.includes('先查询'), 'SET cannot treat queried as verified');

  for (const [phase, label] of Object.entries({queued_get: '查询已排队', await_get: '等待设备查询响应',
    queued_set: '写入已排队', await_set_ack: '等待写入 ACK', queued_verify_get: '独立读回核对已排队',
    await_verify_get: '等待独立 GET 核对'})) {
    x = await setup(); x.server = {...base, busy: true, can_query: false, phase}; await x.poll();
    assert(x.e('status').textContent.includes(label), `display actual controller phase ${phase}`);
    assert(x.e('query').disabled && x.e('set').disabled);
  }
  // Idle was exercised through every completed operation above.
  x = await setup(); x.nextReply = {status: 403, body: {code: 'token', error: 'token changed'}};
  await x.click('query');
  assert(x.e('status').textContent.includes('HTTP 403') && x.e('status').textContent.includes('token'));
  x.clock += 2500; await x.poll();
  assert(x.calls.filter(call => call.url.endsWith('/session')).length >= 2);
  assert.equal(x.posts().length, 1, '403 refreshes only GET session; never retries POST');
  for (const status of [400, 409, 503]) {
    x = await setup(); x.nextReply = {status, body: {code: 'mock_guard', error: 'specific rejection'}};
    await x.click('query'); await x.poll();
    assert(x.e('status').textContent.includes(`HTTP ${status}`));
    assert(x.e('status').textContent.includes('mock_guard'));
    assert.equal(x.posts().length, 1);
  }
  x = await setup();
  x.server = {...base, supported: true, can_set: true, active: {...active, build: '0000B0B2'}};
  await x.poll(); x.confirm(); assert(x.e('set').disabled, 'old firmware label is not capability proof');
  x = await setup(); x.server = {...base, supported: true, can_set: true, active: {...active, p_wire: null}};
  await x.poll(); x.confirm(); assert(x.e('set').disabled, 'invalid active wire fields fail closed');

  x = await setup(); await x.complete(8);
  let release;
  x.deferredStatus = new Promise(resolve => { release = resolve; });
  const oldPoll = x.poll(); await flush();
  await x.click('query');
  release(); x.deferredStatus = null; await oldPoll;
  assert(x.e('query').disabled, 'a status GET started before the explicit action cannot clear its in-flight state');
  assert.equal(x.posts().length, 1);
  await x.complete(1, 'queried'); assert(!x.e('query').disabled);

  console.log('PASS: real HTML/JS wiring; actual queried/verified result contract; all seven phases; numeric operation IDs;');
  console.log('decimal boundaries; dirty drafts; token/UUID/epoch/generation paired SET; one in flight; defaults no write;');
  console.log('unknown query-only recovery; no POST retry; status/epoch/USB/old-build guards; HTTP errors; stale poll race.');
  console.log('Scope: in-memory DOM/API/timers only. No network, serial, browser rendering, or hardware acceptance.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
