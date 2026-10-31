/* One explicit action produces one POST. The control key stays in page memory. */
const HEX32 = /^[a-f0-9]{32}$/i;
const BUILDS = new Set(['0000B0B4', '0000B0B5']);
const uint = v => Number.isSafeInteger(v) && v >= 0 && v <= 0xffffffff;
const gainText = wire => `${Math.floor(wire / 10000)}.${String(wire % 10000).padStart(4, '0')}`;
export function gain(value) {
  if (typeof value !== 'string' || !/^\d+(?:\.\d{1,4})?$/.test(value)) return null;
  const [whole, fraction = ''] = value.split('.');
  const normalized = whole.replace(/^0+(?=\d)/, '');
  if (normalized !== '0' && normalized !== '1') return null;
  const wire = Number(normalized) * 10000 + Number(fraction.padEnd(4, '0'));
  return wire <= 10000 ? wire : null;
}
export function validActive(a) {
  return !!a && gain(a.p_text) !== null && gain(a.i_text) !== null && uint(a.generation) &&
    BUILDS.has(a.build) && Number.isFinite(a.age_ms) && a.age_ms >= 0 &&
    (a.p_wire === undefined || a.p_wire === gain(a.p_text)) &&
    (a.i_wire === undefined || a.i_wire === gain(a.i_text));
}
export function validStatus(s) {
  return !!s && typeof s.enabled === 'boolean' && typeof s.relay_fresh === 'boolean' &&
    HEX32.test(s.epoch) && HEX32.test(s.challenge) && Number.isFinite(s.server_now_ms) &&
    !!s.status && uint(s.status.epoch) &&
    ['can_query', 'can_set', 'supported', 'busy'].every(k => typeof s.status[k] === 'boolean');
}
const sameActive = (a, b) => validActive(a) && validActive(b) && a.generation === b.generation &&
  a.build === b.build && gain(a.p_text) === gain(b.p_text) && gain(a.i_text) === gain(b.i_text);

export class RemotePI {
  constructor({fetchFn = globalThis.fetch?.bind(globalThis), now = () => performance.now(),
    uuid = () => globalThis.crypto.randomUUID(), sleep = ms => new Promise(resolve => setTimeout(resolve, ms)),
    timeoutMs = 3000, resultMs = 20000, onChange = () => {}} = {}) {
    Object.assign(this, {fetchFn, now, uuid, sleep, timeoutMs, resultMs, onChange});
    this.token = ''; this.revision = 0; this.actionRevision = 0; this.polling = false;
    this.draft = {p: '0.1000', i: '0.0350'}; this.dirty = false; this.draftRevision = 0;
    this.busy = false; this.status = null; this.lastStatusAt = -Infinity; this.active = null;
    this.activeAt = 0; this.qualified = false; this.stopped = false; this.notice = '参数转发默认关闭。请先在地面端开启授权。'; this.tone = 'warn';
  }
  emit() { this.onChange(this); }
  invalidate(message) { this.qualified = false; this.stopped = false; this.notice = message; this.tone = 'warn'; }
  disconnect(message = '已退出；密钥及查询资格已清除。') {
    this.revision++; this.actionRevision++; this.token = ''; this.status = null; this.active = null;
    this.lastStatusAt = -Infinity; this.busy = false; this.polling = false;
    this.invalidate(message); this.emit();
  }
  async connect(key) {
    this.disconnect('正在连接参数服务…');
    if (typeof key !== 'string' || key.length < 32 || key.length > 512 || /[\s\x00-\x1f\x7f]/.test(key)) {
      this.notice = '请输入有效的独立控制密钥。'; this.tone = 'bad'; this.emit(); return false;
    }
    this.token = key; this.emit(); return this.refresh();
  }
  edit(field, value) {
    if (!['p', 'i'].includes(field)) return;
    this.draft[field] = value; this.dirty = true; this.draftRevision++; this.emit();
  }
  defaults() {
    if (this.busy) return;
    this.draft = {p: '0.1000', i: '0.0350'}; this.dirty = true; this.draftRevision++;
    this.notice = '默认值仅填入草稿，尚未发送。'; this.tone = 'warn'; this.emit();
  }
  confirm(value) { this.stopped = value === true; this.emit(); }
  tick() {
    if (this.token && this.status && this.now() - this.lastStatusAt >= 3000) {
      this.invalidate('状态已过期，请等待恢复并重新查询设备。');
    }
    this.emit();
  }
  get fresh() { return !!this.token && !!this.status && this.now() - this.lastStatusAt < 3000 && this.status.enabled && this.status.relay_fresh; }
  get canQuery() { return this.fresh && !this.busy && this.status.status.can_query && !this.status.status.busy; }
  get canSet() {
    return this.fresh && !this.busy && !this.status.status.busy && this.status.status.supported &&
      this.status.status.can_set && this.qualified && this.stopped && sameActive(this.active, this.status.status.active) &&
      gain(this.draft.p) !== null && gain(this.draft.i) !== null;
  }
  async request(path, options = {}, timeout = this.timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await this.fetchFn(path, {cache: 'no-store', credentials: 'omit', redirect: 'error',
        referrerPolicy: 'no-referrer', ...options, headers: {...options.headers, 'X-Flight-Control-Token': this.token}, signal: controller.signal});
      if (response.status === 401 || response.status === 403) throw Object.assign(new Error('auth'), {auth: true});
      let body; try { body = await response.json(); } catch { throw new Error('json'); }
      return {response, body};
    } finally { clearTimeout(timer); }
  }
  async refresh() {
    if (!this.token || this.polling) return false;
    this.polling = true;
    const revision = this.revision, action = this.actionRevision;
    try {
      const {response, body} = await this.request('/api/remote-pi/status');
      if (revision !== this.revision || action !== this.actionRevision) return false;
      if (!response.ok || !validStatus(body)) throw new Error('status');
      if (this.status && (body.epoch !== this.status.epoch || body.status.epoch !== this.status.status.epoch)) {
        this.active = null; this.invalidate('地面连接身份已改变，请重新查询设备。');
      } else if (this.qualified && !sameActive(this.active, body.status.active)) {
        this.invalidate('设备参数或读回状态已改变，请重新查询。');
      }
      this.status = body; this.lastStatusAt = this.now();
      if (!body.enabled || !body.relay_fresh) this.invalidate('地面参数转发未开启或连接已过期。');
      return true;
    } catch (error) {
      if (revision !== this.revision || action !== this.actionRevision) return false;
      if (error.auth) this.disconnect('鉴权失败，已锁定。请重新连接。');
      else { this.lastStatusAt = -Infinity; this.invalidate('参数状态不可用；恢复后请重新查询，未自动发送命令。'); }
      return false;
    } finally { if (revision === this.revision) this.polling = false; this.emit(); }
  }
  async command(action) {
    if (!['query', 'set'].includes(action) || !(action === 'query' ? this.canQuery : this.canSet)) return false;
    const status = this.status, revision = this.revision, draftRevision = this.draftRevision;
    const expectedBuild = action === 'set' ? this.active.build : null;
    const id = this.uuid();
    if (typeof id !== 'string' || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(id)) return false;
    const payload = {id, epoch: status.epoch, challenge: status.challenge, action, expected_epoch: status.status.epoch};
    if (action === 'set') Object.assign(payload, {p: gainText(gain(this.draft.p)), i: gainText(gain(this.draft.i)), expected_generation: this.active.generation, confirmed_stopped: true});
    this.actionRevision++; this.busy = true; this.notice = '正在提交一次请求，等待地面端和设备确认…'; this.tone = 'warn'; this.emit();
    const deadline = this.now() + this.resultMs;
    try {
      const {response} = await this.request('/api/remote-pi/command', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      if (revision !== this.revision) return false;
      if (response.status !== 202) throw new Error('rejected');
      this.notice = '请求已排队；尚未取得设备最终确认。'; this.emit();
      while (this.now() < deadline) {
        if (revision !== this.revision) return false;
        if (this.status?.epoch !== payload.epoch || this.status?.status.epoch !== payload.expected_epoch) throw new Error('epoch');
        const {response: resultResponse, body} = await this.request(`/api/remote-pi/result/${payload.epoch}/${id}`, {}, Math.max(1, Math.min(this.timeoutMs, deadline - this.now())));
        if (revision !== this.revision) return false;
        if (this.now() >= deadline) throw new Error('timeout');
        if (!resultResponse.ok) throw new Error('result');
        const result = body?.result;
        if (result != null && !['queued', 'pending', 'running'].includes(result.code)) {
          if (!((action === 'query' && result.code === 'queried') || (action === 'set' && result.code === 'verified')) ||
              !validActive(result.active) || !Number.isSafeInteger(result.operation_id) || result.operation_id <= 0 ||
              this.status?.epoch !== payload.epoch || this.status?.status.epoch !== payload.expected_epoch) throw new Error('unconfirmed');
          if (action === 'set' && (gain(result.active.p_text) !== gain(payload.p) || gain(result.active.i_text) !== gain(payload.i) ||
              result.active.generation !== ((payload.expected_generation + 1) >>> 0) || result.active.build !== expectedBuild)) throw new Error('mismatch');
          this.active = {...result.active}; this.activeAt = this.now(); this.qualified = true; this.stopped = false;
          if (action === 'query' && !this.dirty && draftRevision === this.draftRevision) this.draft = {p: result.active.p_text, i: result.active.i_text};
          if (action === 'set' && draftRevision === this.draftRevision) this.dirty = false;
          // Local snapshot remains conservative until a new status confirms it.
          this.notice = action === 'query' ? '设备查询完成，以最后确认读回值为准。' : '成对写入完成，已由设备独立读回核对。'; this.tone = 'good';
          return true;
        }
        await this.sleep(Math.min(400, Math.max(1, deadline - this.now())));
      }
      throw new Error('timeout');
    } catch (error) {
      if (revision !== this.revision) return false;
      if (error.auth) this.disconnect('鉴权失败，已锁定。已提交请求的结果未知，请重新连接后查询。');
      else { this.invalidate('操作未获确认或结果未知。请先查询设备；不会自动重发命令。'); this.tone = 'bad'; }
      return false;
    } finally { if (revision === this.revision) this.busy = false; this.emit(); }
  }
}

export function mount(document) {
  const el = id => document.getElementById(`pi-${id}`);
  if (!el('card')) return null;
  const model = new RemotePI({onChange: render});
  function render() {
    const fresh = model.fresh, active = model.active;
    el('query').disabled = !model.canQuery; el('set').disabled = !model.canSet;
    el('connect').disabled = model.busy; el('disconnect').disabled = !model.token;
    el('card').setAttribute('aria-busy', String(model.busy));
    for (const field of ['p', 'i']) {
      el(field).disabled = model.busy;
      if (el(field).value !== model.draft[field]) el(field).value = model.draft[field];
      el(field).setAttribute('aria-invalid', String(gain(model.draft[field]) === null));
    }
    el('defaults').disabled = model.busy; el('stopped').disabled = model.busy; el('stopped').checked = model.stopped;
    el('active-p').textContent = active?.p_text ?? '—'; el('active-i').textContent = active?.i_text ?? '—';
    el('generation').textContent = active ? String(active.generation) : '—'; el('build').textContent = active?.build ?? '—';
    el('age').textContent = active ? `最后确认读回距今约 ${((active.age_ms + model.now() - model.activeAt) / 1000).toFixed(1)} 秒；当前写入资格另行检查。` : '尚未取得本会话确认读回。';
    el('connection').textContent = !model.token ? '未连接参数服务' : fresh ? '参数服务已连接' : '参数服务不可用 / 已过期';
    el('service-state').textContent = fresh ? '地面端已授权连接' : '需要地面端授权';
    el('qualification').textContent = model.qualified && fresh ? '本会话已查询设备，写入仍需停机确认和地面端资格。' : '请查询设备以取得本会话资格。';
    el('draft-state').textContent = model.dirty ? '草稿已编辑 · 尚未写入' : '草稿不代表已生效';
    el('validation').textContent = gain(model.draft.p) === null || gain(model.draft.i) === null ? '请输入 0～1 的十进制数，最多四位小数；不支持指数、符号或自动舍入。' : '';
    const reason = fresh && !model.busy && typeof model.status.status.block_reason === 'string' ? model.status.status.block_reason.slice(0, 300) : '';
    el('notice').textContent = model.notice + (reason ? `\n地面端状态：${reason}` : ''); el('notice').dataset.tone = model.tone;
  }
  el('access-form').addEventListener('submit', event => { event.preventDefault(); const key = el('key').value; el('key').value = ''; void model.connect(key); });
  el('disconnect').addEventListener('click', () => { el('key').value = ''; model.disconnect(); });
  el('form').addEventListener('submit', event => { event.preventDefault(); void model.command('set'); });
  el('query').addEventListener('click', () => { void model.command('query'); });
  el('defaults').addEventListener('click', () => model.defaults());
  el('stopped').addEventListener('change', () => model.confirm(el('stopped').checked));
  for (const field of ['p', 'i']) el(field).addEventListener('input', () => model.edit(field, el(field).value));
  let tick, poll;
  const start = () => { clearInterval(tick); clearInterval(poll); tick = setInterval(() => model.tick(), 250); poll = setInterval(() => { void model.refresh(); }, 800); };
  const clear = () => { clearInterval(tick); clearInterval(poll); el('key').value = ''; model.disconnect(); };
  document.defaultView?.addEventListener('pagehide', clear);
  document.defaultView?.addEventListener('pageshow', event => { if (event.persisted) start(); });
  start();
  render(); return model;
}
if (typeof document !== 'undefined') mount(document);
