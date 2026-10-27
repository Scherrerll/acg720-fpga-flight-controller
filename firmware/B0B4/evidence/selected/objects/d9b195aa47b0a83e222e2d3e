/* One explicit action, one POST. Serial ownership and Decimal checks stay server-side. */
(() => {
  'use strict';
  const el = name => document.getElementById(`xy-pi-${name}`);
  if (!el('card')) return;
  const fields = [el('p'), el('i')];
  const phases = {idle: '空闲', queued_get: '查询已排队', await_get: '等待设备查询响应',
    queued_set: '写入已排队', await_set_ack: '等待写入 ACK',
    queued_verify_get: '独立读回核对已排队', await_verify_get: '等待独立 GET 核对'};
  let status = null, token = null, online = false, posting = false;
  let pending = null, uncertain = false, dirty = false, lastActive = null;
  let draftRevision = 0, actionRevision = 0, lastEpoch, tokenAttempt = 0, statusFailed = false, lastResultKey;
  let notice = '', tone = 'warn';
  const now = () => performance.now();

  function gain(value) {
    if (typeof value !== 'string' || !/^\d+(?:\.\d{1,4})?$/.test(value)) return null;
    const [rawWhole, fraction = ''] = value.split('.');
    const whole = rawWhole.replace(/^0+(?=\d)/, '');
    if (whole !== '0' && whole !== '1') return null;
    const wire = Number(whole) * 10000 + Number((fraction + '0000').slice(0, 4));
    return wire <= 10000 ? wire : null;
  }
  function validActive(value) {
    return value && Number.isInteger(value.p_wire) && Number.isInteger(value.i_wire) &&
      gain(value.p_text) === value.p_wire && gain(value.i_text) === value.i_wire &&
      Number.isInteger(value.generation) && value.generation >= 0 && value.generation <= 0xffffffff &&
      Number.isFinite(value.age_ms) && value.age_ms >= 0 &&
      value.build === '0000B0B4';
  }
  function validStatus(value) {
    return value && ['enabled', 'connected', 'supported', 'busy', 'can_query', 'can_set'].every(k => typeof value[k] === 'boolean') &&
      (value.epoch === null || Number.isSafeInteger(value.epoch)) &&
      (value.active == null || validActive(value.active));
  }
  function message(text, kind = 'warn') { notice = text; tone = kind; }
  function unknown(text) {
    uncertain = true;
    message(`${text} 结果未知：请先查询确认，禁止自动重发。`, 'bad');
  }
  function render() {
    const busy = posting || !!pending || !!status?.busy;
    const capable = online && !!token && status?.enabled && status?.connected && Number.isSafeInteger(status?.epoch);
    const valid = fields.every(f => gain(f.value) !== null);
    el('query').disabled = !(capable && status.can_query && !busy);
    el('set').disabled = !(capable && status.can_set && status.supported && validActive(status.active) &&
      valid && el('stopped').checked && !busy && !uncertain);
    fields.forEach(f => { f.disabled = busy; f.setAttribute('aria-invalid', String(gain(f.value) === null)); });
    el('defaults').disabled = busy;
    el('stopped').disabled = busy;
    el('card').setAttribute('aria-busy', String(busy));
    el('draft-state').textContent = dirty ? '草稿已编辑 · 尚未写入' : '草稿 · 不代表已生效';
    el('validation').textContent = valid ? '' : '请输入 0～1 的十进制数，最多四位小数；不支持负数、指数或自动舍入。';
    const active = lastActive?.value;
    el('active-p').textContent = active?.p_text ?? '—';
    el('active-i').textContent = active?.i_text ?? '—';
    el('generation').textContent = active ? String(active.generation) : '—';
    el('build').textContent = active ? String(active.build) : '—';
    el('age').textContent = active ? `最后读回距今约 ${((active.age_ms + now() - lastActive.at) / 1000).toFixed(1)} 秒；${online ? '当前写入资格另行检查。' : '状态不可用，以上仅为历史读回。'}` : '尚未取得匹配的设备读回；编辑草稿不代表设备已生效。';
    el('source').textContent = online ? `接收来源 ${String(status.source ?? '—')} · ${String(status.baud ?? '—')} baud · 连接代次 ${String(status.epoch)}` : '参数服务状态不可用。';
    let text = notice;
    if (busy && !posting && status?.busy) text = `正在处理：${phases[status.phase] || String(status.phase || '等待设备响应')}。一次仅处理一个操作，请勿重复提交。`;
    if (!text) text = status?.block_reason || (!token ? '正在取得本机会话资格…' : '请查询设备，确认实际 P / I 和 generation。');
    if (!busy && uncertain && !text.includes('先查询')) text += '\n当前结果尚未确认：请先查询确认，禁止自动重发。';
    if (!busy && online && !status.can_set && status.block_reason && !text.includes(status.block_reason)) text += `\n${status.block_reason}`;
    if (!busy && online && !token) text += '\n本机会话资格不可用，正在重新读取；不会自动提交。';
    el('status').textContent = text;
    el('status').dataset.tone = busy ? 'warn' : tone;
  }
  async function jsonFetch(path, options = {}) {
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 4000);
    try {
      const response = await fetch(path, {cache: 'no-store', credentials: 'same-origin', ...options, signal: abort.signal});
      let body;
      try { body = await response.json(); } catch (_) { throw new Error(`HTTP ${response.status} 响应不是有效 JSON`); }
      return {response, body};
    } finally { clearTimeout(timer); }
  }
  function serverMessage(body) {
    const detail = typeof body?.message === 'string' ? body.message :
      typeof body?.error === 'string' ? body.error : typeof body?.error?.message === 'string' ? body.error.message : '服务拒绝或无法接收此请求';
    return typeof body?.code === 'string' ? `${body.code}：${detail}` : detail;
  }
  function finish(value) {
    const result = value.result;
    if (pending?.operationId == null || value.busy || result?.operation_id !== pending.operationId) return;
    const completed = pending;
    pending = null;
    const code = String(result.code ?? 'unknown');
    const success = (completed.kind === 'query' && code === 'queried') || (completed.kind === 'set' && code === 'verified');
    if (success && validActive(value.active)) {
      if (completed.kind === 'query') {
        uncertain = false;
        if (!dirty && completed.draftRevision === draftRevision) {
          fields[0].value = value.active.p_text; fields[1].value = value.active.i_text;
        }
      } else if (completed.draftRevision === draftRevision) dirty = false;
      message(`${completed.kind === 'query' ? '设备查询完成' : '成对写入完成'} · ${code}：${result.message || '以设备最后读回为准。'}`, 'good');
    } else if (success || ['unknown', 'timeout', 'mismatch', 'cancelled'].includes(code) ||
               !['locked', 'stale_sequence', 'nack'].includes(code)) {
      unknown(`${code}：${result.message || '未取得可确认的最终结果。'}`);
    } else {
      message(`${code}：${result.message || '操作未完成，请检查状态后显式查询。'}`, 'bad');
    }
  }
  async function poll() {
    const revision = actionRevision;
    try {
      const {response, body} = await jsonFetch('/api/xy-pi/status');
      if (!response.ok || !validStatus(body)) throw new Error(`状态接口不可用（HTTP ${response.status}）`);
      if (revision !== actionRevision) return;
      online = true;
      if (statusFailed && !uncertain && !pending) message('参数服务状态已恢复；请核对读回值后显式操作。');
      statusFailed = false;
      if (lastEpoch !== undefined && body.epoch !== lastEpoch) {
        lastActive = null; el('stopped').checked = false;
        if (pending) { pending = null; unknown('接收连接代次已改变。'); }
        else message('接收连接已变化，请重新查询设备。');
      }
      lastEpoch = body.epoch; status = body;
      if (body.active) lastActive = {value: body.active, at: now()};
      finish(body);
      const resultKey = body.result ? `${body.result.operation_id}:${body.result.code}` : null;
      if (!pending && resultKey && resultKey !== lastResultKey && ['unknown', 'timeout', 'mismatch'].includes(body.result.code)) {
        unknown(`${body.result.code}：${body.result.message || '上一笔操作未得到确认。'}`);
      }
      lastResultKey = resultKey;
      if (pending?.operationId != null && !body.busy && now() - pending.started > 2000 &&
          body.result?.operation_id !== pending.operationId) {
        pending = null; unknown('未能将最终状态对应到本次操作。');
      }
      if (!pending && !uncertain && body.block_reason && !body.can_query) message(body.block_reason);
    } catch (error) {
      if (revision === actionRevision) {
        status = null; online = false; statusFailed = true;
        message(`读取参数状态失败：${error.message}。当前查询和写入已禁用；恢复后不会自动提交。`, 'bad');
      }
    } finally {
      if (pending && now() - pending.started > 15000) { pending = null; unknown('等待操作结果超时。'); }
      if (!token && now() - tokenAttempt > 2000) await session();
      render(); setTimeout(poll, 500);
    }
  }
  async function session() {
    tokenAttempt = now();
    try {
      const {response, body} = await jsonFetch('/api/xy-pi/session');
      if (!response.ok || typeof body.token !== 'string' || !body.token) throw new Error('本机会话资格不可用');
      token = body.token;
    } catch (_) { token = null; }
  }
  async function start(kind) {
    render();
    if (el(kind === 'query' ? 'query' : 'set').disabled) return;
    if (!globalThis.crypto?.randomUUID) { message('浏览器不支持安全请求标识；请使用较新的本机浏览器。', 'bad'); render(); return; }
    const operation = {kind, requestId: crypto.randomUUID(), epoch: status.epoch, draftRevision, started: now()};
    const body = {request_id: operation.requestId, epoch: operation.epoch};
    if (kind === 'set') Object.assign(body, {expected_generation: status.active.generation, p: fields[0].value, i: fields[1].value, confirmed_stopped: true});
    actionRevision++; pending = operation; posting = true; el('stopped').checked = false;
    message(kind === 'set' ? '正在提交这一对 P / I，请等待最终核对…' : '正在提交查询，请等待设备读回…'); render();
    try {
      const {response, body: reply} = await jsonFetch(`/api/xy-pi/${kind}`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-XY-PI-Token': token}, body: JSON.stringify(body)});
      if (response.status !== 202) {
        pending = null;
        status = null; online = false;
        if (response.status === 403) token = null;
        if (![400, 403, 409].includes(response.status)) unknown(`HTTP ${response.status}：${serverMessage(reply)}。`);
        else message(`请求未获接受 · HTTP ${response.status}：${serverMessage(reply)}。不会自动重发。`, 'bad');
      } else if (!Number.isSafeInteger(reply.operation_id) || reply.operation_id < 0) {
        pending = null; unknown('服务未返回有效操作编号。');
      } else {
        operation.operationId = reply.operation_id;
        message('服务已接收，正在等待设备响应与最终状态；不会自动重发。');
      }
    } catch (error) {
      pending = null; unknown(`请求响应丢失或不可读：${error.message}。`);
    } finally { posting = false; render(); }
  }
  fields.forEach(field => field.addEventListener('input', () => { dirty = true; draftRevision++; render(); }));
  el('stopped').addEventListener('change', render);
  el('query').addEventListener('click', () => start('query'));
  el('form').addEventListener('submit', event => { event.preventDefault(); return start('set'); });
  el('defaults').addEventListener('click', () => {
    if (el('defaults').disabled) return;
    fields[0].value = '0.1000'; fields[1].value = '0.0350'; dirty = true; draftRevision++;
    el('stopped').checked = false; message('默认值已填入草稿，尚未写入设备。'); render();
  });
  render();
  session().finally(poll);
})();
