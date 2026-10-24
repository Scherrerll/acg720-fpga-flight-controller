'use strict';
import {liveState} from './live-state.mjs';
import {createLivePoller} from './polling.mjs';
import {createLiveTween,createLivePose} from './live-playback.mjs';

(() => {
  const $ = id => document.getElementById(id);
  const valid = value => typeof value === 'number' && Number.isFinite(value);
  const fmt = (value, digits = 1) => valid(value) ? value.toFixed(digits) : '—';
  const integer = value => valid(value) ? value.toLocaleString('zh-CN', { maximumFractionDigits: 0 }) : '—';
  const text = (id, value) => { $(id).textContent = value == null || value === '' ? '—' : String(value); };
  const boolText = (value, yes, no) => value === true ? yes : value === false ? no : '—';
  const logArmed = value => value === true || value === 1 ? true : value === false || value === 0 ? false : null;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const fields = [
    ['roll_deg', '横滚 Estimate', '°', '#65a5e7'], ['pitch_deg', '俯仰 Estimate', '°', '#d4b574'],
    ['yaw_deg', '相对航向', '°', '#b29dcd'], ['height_m', '融合高度', 'm', '#80b9a4'],
    ['vx_mps', '水平速度 X', 'm/s', '#65a5e7'], ['vy_mps', '水平速度 Y', 'm/s', '#d4b574'],
    ['vz_mps', '垂直速度', 'm/s', '#b29dcd'], ['m1_us', 'M1', 'µs', '#65a5e7'],
    ['m2_us', 'M2', 'µs', '#80b9a4'], ['m3_us', 'M3', 'µs', '#d4b574'],
    ['m4_us', 'M4', 'µs', '#b29dcd'], ['throttle_us', '油门', 'µs', '#d28f88'],
    ['armed', '解锁状态', '状态', '#80b9a4'],
    ['roll_sp_deg', '横滚 Setpoint', '°', '#8cbaa6'], ['pitch_sp_deg', '俯仰 Setpoint', '°', '#8cbaa6'],
    ['yaw_rate_dps', '偏航角速度 Estimate', '°/s', '#65a5e7'], ['yaw_rate_sp_dps', '偏航角速度 Setpoint', '°/s', '#8cbaa6']
  ].map(([key, label, unit, color]) => ({ key, label, unit, color, step:key.includes('_sp_') }));
  const trackingPairs = {overview:['roll_deg','pitch_deg','yaw_deg'], roll:['roll_deg','roll_sp_deg'], pitch:['pitch_deg','pitch_sp_deg'], yaw_rate:['yaw_rate_dps','yaw_rate_sp_dps']};
  const attitudeOverview = fields.slice(0, 3).map((field, i) => ({...field, color:['#2dd4bf','#7395ff','#ffb454'][i]}));
  const chartFields = keys => keys.map(key => fields.find(field => field.key === key));
  const state = {
    smooth: true, animatePose: true, live: null, lastSuccess: 0, liveRtt: 0, pollBusy: false, pollFailed: false, caps: null, logsLocal: false,
    logs: [], selected: null, logId: null, samples: [], selectedFields: new Set(),
    cursor: 0, start: 0, end: 0, playing: false, playStamp: 0, page: 'live', requestId: 0
  };

  async function api(url, options = {}) {
    const {timeoutMs = 7000, ...fetchOptions} = options;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { cache: 'no-store', ...fetchOptions, signal: controller.signal });
      if (!response.ok) {
        const error = new Error(`请求失败 (${response.status})`); error.status = response.status; throw error;
      }
      return await response.json();
    } finally { clearTimeout(timer); }
  }

  function formatTime(value) {
    if (!valid(value)) return '—';
    const s = Math.max(0, value);
    return `${String(Math.floor(s / 60)).padStart(2, '0')}:${(s % 60).toFixed(1).padStart(4, '0')}`;
  }

  function dateText(value) {
    if (value == null || value === '') return '时间未记录';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '时间未记录' : date.toLocaleString('zh-CN', { hour12: false });
  }

  const ns = 'http://www.w3.org/2000/svg';
  for (let angle = -60; angle <= 60; angle += 10) {
    if (!angle) continue;
    const y = 140 - angle * 3;
    const width = Math.abs(angle) % 20 ? 34 : 55;
    const line = document.createElementNS(ns, 'path');
    line.setAttribute('d', `M${200 - width} ${y}h${width * 2}`);
    line.setAttribute('stroke', '#9babb8'); line.setAttribute('stroke-width', '1');
    $('pitch-ladder').append(line);
    for (const side of [-1, 1]) {
      const label = document.createElementNS(ns, 'text');
      label.setAttribute('x', String(200 + side * (width + 12))); label.setAttribute('y', String(y + 3));
      label.setAttribute('text-anchor', 'middle'); label.setAttribute('font-size', '9'); label.setAttribute('fill', '#b8c6d0');
      label.textContent = String(Math.abs(angle)); $('pitch-ladder').append(label);
    }
  }
  const healthNames = [['imu', 'IMU 姿态'], ['flow', '光流'], ['range', '测距'], ['nav', '导航估计'], ['rc', '遥控帧']];
  healthNames.forEach(([key, name]) => {
    const row = document.createElement('div'); const dt = document.createElement('dt'); const dd = document.createElement('dd');
    dt.textContent = name; dd.id = `health-${key}`; dd.textContent = '—'; dd.className = 'health-unknown';
    row.append(dt, dd); $('health-list').append(row);
  });
  for (let i = 0; i < 4; i++) {
    const row = document.createElement('div'); row.className = 'motor';
    const name = document.createElement('span'); name.textContent = `M${i + 1}`;
    const track = document.createElement('div'); track.className = 'motor-track';
    const bar = document.createElement('i'); bar.id = `motor-bar-${i}`; track.append(bar);
    const value = document.createElement('strong'); value.id = `motor-value-${i}`; value.textContent = '—';
    row.append(name, track, value); $('motors').append(row);
  }
  for (let i = 0; i < 8; i++) {
    const item = document.createElement('div'); item.className = 'channel';
    const name = document.createElement('span'); name.textContent = `CH${i + 1}`;
    const value = document.createElement('b'); value.id = `channel-${i}`; value.textContent = '—';
    item.append(name, value); $('channels').append(item);
  }

  function liveFresh() {
    return liveStatus().fresh;
  }
  function liveStatus(){return liveState(state.live,{elapsedMs:Math.max(0,performance.now()-state.lastSuccess),requestRttMs:state.liveRtt});}

  const livePose = createLivePose();
  const poseTransition = createLiveTween();
  const chartClock = createLiveTween({angularKeys:[]});
  const chartTransitions = new Map();
  let poseEpoch = null, poseStamp = null;
  let animationId = null, lastVisualFrame = 0, lastChartFrame = 0;
  function renderMotion() {
    const now = performance.now(), pose = livePose.sample(now);
    if (pose?.epoch !== poseEpoch) { poseTransition.reset(); poseStamp = null; chartTransitions.clear(); poseEpoch = pose?.epoch; }
    const a = pose?.attitude || {}, m = state.live?.motion || {};
    if (pose?.receivedAt !== poseStamp) { poseTransition.set(pose?.attitude, now, {snap:!state.animatePose}); poseStamp = pose?.receivedAt; }
    const displayed = state.animatePose ? poseTransition.sample(now) || {} : a;
    // Readouts report the latest real sample immediately. Only the drawing eases.
    text('horizon-roll', valid(a.roll_deg) ? `${fmt(a.roll_deg)}°` : '等待');
    text('horizon-pitch', valid(a.pitch_deg) ? `${fmt(a.pitch_deg)}°` : '等待');
    const attitudeValid = valid(a.roll_deg) && valid(a.pitch_deg);
    $('attitude-rotation').setAttribute('transform', `rotate(${attitudeValid ? -displayed.roll_deg : 0},200,140)`);
    $('attitude-pitch').setAttribute('transform', `translate(0,${attitudeValid ? clamp(displayed.pitch_deg, -90, 90) * 3 : 0})`);
    $('attitude-rotation').style.opacity = attitudeValid ? '1' : '0.2';
    $('horizon').setAttribute('aria-label', attitudeValid ? `${pose?.retained || !liveStatus().recent ? '最后有效' : '最新接收'}姿态：横滚${fmt(a.roll_deg)}度，俯仰${fmt(a.pitch_deg)}度` : '等待首个有效姿态');
    for (const [id, value, digits] of [['yaw-value', a.yaw_deg, 1], ['height-value', m.height_m, 2], ['speed-value', m.speed_mps, 2]]) text(id, fmt(value, digits));
    const poseAge = valid(pose?.age_ms) ? pose.age_ms / 1000 : null;
    const held = pose?.retained || !liveStatus().recent;
    text('pose-status', !pose ? '等待首个有效姿态' : `${held ? '姿态保留最后有效值' : '姿态为最新接收值'}${poseAge === null ? '' : ` · 估计源龄 ${poseAge.toFixed(1)} s`}`);
    text('playback-status', `数值和曲线均按最新接收数据更新 · ${state.animatePose || state.smooth ? '画面短过渡 160 ms' : '画面即时切换'} · 无额外回放缓冲`);
  }
  function stopVisuals() { if (animationId !== null) cancelAnimationFrame(animationId); animationId = null; }
  function startVisuals() {
    if (animationId !== null || document.hidden || state.page !== 'live') return;
    const frame = now => {
      if (document.hidden || state.page !== 'live') { animationId = null; return; }
      if (now - lastVisualFrame >= 1000 / 60) {
        renderMotion(); lastVisualFrame = now;
        if (now - lastChartFrame >= 1000 / 30) { drawLive(); lastChartFrame = now; }
      }
      animationId = requestAnimationFrame(frame);
    };
    animationId = requestAnimationFrame(frame);
  }
  $('smooth-live').addEventListener('click', () => {
    state.smooth = !state.smooth; $('smooth-live').setAttribute('aria-pressed', String(state.smooth));
    chartTransitions.clear(); renderLive();
  });
  $('pose-instant').addEventListener('click', () => {
    state.animatePose = !state.animatePose; $('pose-instant').setAttribute('aria-pressed', String(state.animatePose));
    if (!state.animatePose) poseTransition.set(livePose.sample(performance.now())?.attitude, performance.now(), {snap:true});
    renderLive();
  });

  function renderLive() {
    const data = state.live;
    const status=liveStatus(),fresh=status.fresh,recent=status.recent;
    const pose = livePose.sample(performance.now());
    $('connection').className = `connection${fresh ? ' fresh' : status.kind === 'delayed' ? ' buffered' : data ? ' stale' : ''}`;
    $('connection').lastElementChild.textContent = {live:'实时接收',delayed:'同步有延迟',source_invalid:'源遥测未更新',timing_unknown:'同步时间未确认',expired:'已连接 · 数据延迟',disconnected:'连接中断',waiting:'等待连接'}[status.kind];
    $('instrument-content').classList.toggle('is-stale', !(recent && pose && !pose.retained));
    $('motors').classList.toggle('is-stale', !recent);
    $('channels').classList.toggle('is-stale', !recent);
    $('mode-value').classList.toggle('is-stale', !recent);
    $('armed-value').classList.toggle('is-stale', !recent);
    $('stale-banner').className = `status-banner ${status.kind === 'delayed' ? 'playback' : fresh ? 'fresh' : 'stale'}`;
    $('stale-banner').textContent = status.kind === 'delayed' ? '数据已接收，公网同步有延迟 · 当前显示最新接收值。' : fresh ? '只读遥测接收中 · 数值与曲线显示最新接收数据，画面短过渡。' : status.kind === 'source_invalid' ? '源遥测尚无有效更新 · 保留最后有效姿态，灰色读数不代表当前状态。' : status.kind === 'timing_unknown' ? '正在确认转发时间 · 保留最后有效姿态。' : status.kind === 'expired' ? '连接正常，当前数据更新延迟 · 保留最后有效值，等待新数据。' : data ? '遥测连接中断 · 正在重试，姿态保留最后有效值并显示数据年龄。' : '等待遥测连接 · 尚无有效接收数据。';
    text('value-state', !pose ? '等待有效姿态' : recent && !pose.retained ? '最新接收' : '最后有效姿态');
    text('firmware', `固件 ${data?.firmware ?? '—'}`);
    text('sequence', `SEQ ${data?.sequence ?? '—'}`);
    const age = status.age_ms;
    text('age', age === null ? '源龄 —' : `源龄估计 ${(age / 1000).toFixed(1)} s`);
    text('sample-time', data?.received_at ? `最后接收 ${dateText(data.received_at)}` : '尚未收到遥测');
    renderMotion();
    const m = data?.motion ?? {};
    for (const [id, value] of [['vx-value', m.vx_mps], ['vy-value', m.vy_mps], ['vz-value', m.vz_mps]]) text(id, fmt(value, 2));
    text('armed-value', boolText(data?.armed, '已解锁', '未解锁'));
    const mode = data?.control_mode;
    const modeNames = { ATT_STAB: '自稳', LOC_HOLD: '定点', ALT_HOLD: '定高', DISARMED:'待机', ATT_ALT_HOLD:'自稳 + 高度控制', FLOW_ALT_HOLD:'光流 + 高度控制', ATT_MANUAL_THR:'自稳 · 手动油门接管' };
    text('mode-value', typeof mode === 'string' && modeNames[mode] ? `${modeNames[mode]} / ${mode}` : mode);
    text('requested-value', modeNames[data?.flags?.requested] || data?.flags?.requested);
    text('axes-value', `${boolText(data?.flags?.xy_active, '启用', '停用')} / ${boolText(data?.flags?.z_active, '启用', '停用')}`);
    text('reason-text', data?.flags?.reason_text || '未提供额外状态说明');
    for (const [key] of healthNames) {
      const value = data?.health?.[key]; const item = $(`health-${key}`);
      item.className = !fresh || value == null ? 'health-unknown' : value === true ? 'health-yes' : 'health-no';
      item.textContent = !data ? '—' : !fresh ? '最后状态' : boolText(value, '有效', '无效');
    }
    for (let i = 0; i < 4; i++) {
      const value = data?.motors_us?.[i]; text(`motor-value-${i}`, fmt(value, 0));
      $(`motor-bar-${i}`).style.width = valid(value) ? `${clamp((value - 1000) / 10, 0, 100)}%` : '0%';
    }
    text('rc-valid', !fresh && data ? '最后接收值' : boolText(data?.rc?.valid, '帧有效', '帧无效'));
    text('throttle-value', fmt(data?.rc?.throttle_us, 0));
    for (let i = 0; i < 8; i++) text(`channel-${i}`, fmt(data?.rc?.channels?.[i], 0));
    const r = data?.recording;
    text('recording-active', boolText(r?.active, '记录中', '未记录'));
    for (const [id, key] of [['record-frames', 'frames'], ['record-missing', 'missing_frames'], ['record-errors', 'decode_errors'], ['record-resets', 'sequence_resets']]) text(id, integer(r?.[key]));
    if (state.page === 'live') drawLive();
  }

  async function pollLive() {
    if (document.hidden || state.pollBusy) return;
    state.pollBusy = true;
    const started=performance.now();
    try {
      const data = await api('/api/live');
      if (!data || data.schema !== 1) throw new Error('不支持的数据格式');
      state.pollFailed = false; state.live = data; state.lastSuccess = performance.now();state.liveRtt=state.lastSuccess-started;
      livePose.ingest(data, state.lastSuccess, state.liveRtt);
      const reference = valid(data.server_response_time_ms) ? data.server_response_time_ms : Date.parse(data.received_at);
      if (valid(reference)) chartClock.set({offset:reference + state.liveRtt - state.lastSuccess}, state.lastSuccess);
    } catch { state.pollFailed = true; /* Age and stale state continue advancing. */ }
    finally { state.pollBusy = false; renderLive(); }
  }

  async function loadCapabilities() {
    try { state.caps = await api('/api/capabilities'); }
    catch { state.caps = null; }
    text('access-mode', state.caps?.mode === 'local' ? '本地接收端' : state.caps?.mode === 'share' ? '分享视图' : '权限未知');
    updateShare();
    let toggle = $('live-sharing-toggle');
    if (!toggle && state.caps?.mode === 'local' && state.caps?.can_share_logs) {
      toggle = document.createElement('button'); toggle.id = 'live-sharing-toggle'; toggle.type = 'button';
      $('access-mode').parentElement.append(toggle);
      toggle.addEventListener('click', async () => {
        toggle.disabled = true;
        try {
          const result = await api('/api/sharing', {timeoutMs:20000, method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({enabled:state.caps?.sharing_enabled !== true})});
          state.caps.sharing_enabled = result.sharing_enabled;
        } catch { alert('分享开关操作失败，请刷新本地页面确认状态。'); }
        finally { toggle.disabled = false; await loadCapabilities(); }
      });
    }
    if (toggle) {
      toggle.hidden = state.caps?.mode !== 'local' || !state.caps?.can_share_logs;
      toggle.textContent = state.caps?.sharing_enabled ? '停止实时分享' : '开始实时分享';
    }
  }

  function updateShare() {
    const allowed = state.caps?.mode === 'local' && state.caps?.can_share_logs === true && state.logsLocal === true;
    $('share-log').hidden = !allowed;
    $('share-log').disabled = !state.selected;
  }

  function configureCanvas(canvas) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width) return null;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    ctx.font = '10px "Segoe UI", "Microsoft YaHei", sans-serif';
    return { ctx, width: rect.width, height: rect.height };
  }

  const chartViews = new Map();
  function bindChartScale(id, buttonId, redraw) {
    const canvas = $(id), button = $(buttonId);
    const view = { ranges: new Map(), lanes: [], left: 0, right: 0, redraw, button };
    let drag = null, suppressClickUntil = 0;
    chartViews.set(canvas, view);
    function endDrag(event) {
      if (!drag || event && event.pointerId !== drag.pointerId) return;
      const ended = drag; drag = null;
      canvas.classList.remove('is-panning');
      if (ended.moved && event?.type === 'pointerup') suppressClickUntil = performance.now() + 400;
      if (canvas.hasPointerCapture(ended.pointerId)) canvas.releasePointerCapture(ended.pointerId);
    }
    const reset = () => { endDrag(); view.ranges.clear(); redraw(); };
    button.addEventListener('click', reset);
    canvas.addEventListener('wheel', event => {
      if (drag || event.ctrlKey || event.metaKey || !valid(event.deltaY) || event.deltaY === 0) return;
      const rect = canvas.getBoundingClientRect();
      const px = event.clientX - rect.left, py = event.clientY - rect.top;
      if (px < view.left || px > view.right) return;
      const lane = view.lanes.find(l => l.hasValues && py >= l.y0 && py <= l.y1);
      if (!lane) return;
      const pixels = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? rect.height : 1);
      if (!valid(pixels)) return;
      const span = lane.max - lane.min;
      const nextSpan = clamp(span * Math.exp(clamp(pixels, -240, 240) * 0.0025), lane.unit === 'µs' ? 2 : 0.0001, 1e12);
      const ratio = clamp((lane.y1 - py) / (lane.y1 - lane.y0), 0, 1);
      const anchor = lane.min + span * ratio;
      const min = anchor - nextSpan * ratio, max = anchor + nextSpan * (1 - ratio);
      if (!valid(min) || !valid(max) || max <= min) return;
      event.preventDefault();
      view.ranges.set(lane.unit, { min, max });
      redraw();
    }, { passive: false });
    canvas.addEventListener('pointerdown', event => {
      suppressClickUntil = 0;
      if (event.pointerType !== 'mouse' || event.button !== 0 || event.ctrlKey || event.metaKey) return;
      const rect = canvas.getBoundingClientRect();
      const px = event.clientX - rect.left, py = event.clientY - rect.top;
      if (px < view.left || px > view.right) return;
      const lane = view.lanes.find(l => l.hasValues && py >= l.y0 && py <= l.y1);
      if (!lane || lane.y1 <= lane.y0) return;
      drag = { pointerId: event.pointerId, startY: event.clientY, unit: lane.unit,
        min: lane.min, max: lane.max, height: lane.y1 - lane.y0, moved: false };
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener('pointermove', event => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      const dy = event.clientY - drag.startY;
      if (!drag.moved && Math.abs(dy) < 3) return;
      const shift = dy / drag.height * (drag.max - drag.min);
      const min = drag.min + shift, max = drag.max + shift;
      if (!valid(min) || !valid(max) || max <= min) return;
      drag.moved = true; canvas.classList.add('is-panning');
      view.ranges.set(drag.unit, { min, max });
      redraw();
    });
    for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, endDrag);
    canvas.addEventListener('click', event => {
      if (performance.now() >= suppressClickUntil) return;
      suppressClickUntil = 0; event.preventDefault(); event.stopImmediatePropagation();
    }, true);
    canvas.addEventListener('keydown', event => {
      if (event.key !== '0' || event.ctrlKey || event.metaKey || event.altKey) return;
      event.preventDefault(); reset();
    });
  }

  function chart(canvas, samples, selected, start, end, cursor = null, groups = false, animate = false) {
    const context = configureCanvas(canvas); if (!context) return;
    const { ctx, width, height } = context;
    const unitGroups = [];
    selected.forEach(field => {
      let group = unitGroups.find(g => g.unit === field.unit);
      if (!group || !groups) {
        if (!groups && unitGroups.length) group = unitGroups[0];
        else { group = { unit: field.unit, fields: [] }; unitGroups.push(group); }
      }
      group.fields.push(field);
    });
    if (!unitGroups.length) unitGroups.push({ unit: '', fields: [] });
    const left = 52, right = width - 18, top = groups ? 27 : 14, bottom = height - 26;
    const view = chartViews.get(canvas);
    if (view) {
      view.left = left; view.right = right; view.lanes = [];
      const units = new Set(unitGroups.map(group => group.unit));
      for (const unit of view.ranges.keys()) if (!units.has(unit)) view.ranges.delete(unit);
      view.button.disabled = view.ranges.size === 0;
      canvas.dataset.scaleMode = view.ranges.size ? 'manual' : 'auto';
    }
    const laneHeight = (bottom - top) / unitGroups.length;
    const timeSpan = Math.max(0.001, end - start);
    const x = time => left + (time - start) / timeSpan * (right - left);
    const val = (sample, field) => field.key === 'armed' ? logArmed(sample.armed) === true ? 1 : logArmed(sample.armed) === false ? 0 : null : sample[field.key];
    unitGroups.forEach((group, index) => {
      const y0 = top + laneHeight * index + (groups ? 10 : 0);
      const y1 = top + laneHeight * (index + 1) - (groups ? 19 : 0);
      let min = Infinity, max = -Infinity;
      samples.forEach(s => group.fields.forEach(f => { const v = val(s, f); if (valid(v)) { min = Math.min(min, v); max = Math.max(max, v); } }));
      const hasValues = min !== Infinity;
      if (!hasValues) { min = -1; max = 1; }
      if (max === min) { const pad = Math.max(Math.abs(max) * 0.05, group.unit === 'µs' ? 20 : 1); min -= pad; max += pad; }
      else { const pad = (max - min) * 0.13; min -= pad; max += pad; }
      const manual = view?.ranges.get(group.unit);
      if (manual) { min = manual.min; max = manual.max; }
      if (animate && !manual && hasValues) {
        let transitions = chartTransitions.get(canvas);
        if (!transitions) { transitions = new Map(); chartTransitions.set(canvas, transitions); }
        let transition = transitions.get(group.unit);
        if (!transition) { transition = createLiveTween({angularKeys:[]}); transitions.set(group.unit, transition); }
        transition.set({min,max},performance.now());
        const eased = transition.sample(performance.now());
        // Expand immediately so a new extreme is never clipped; ease contraction.
        min = Math.min(min,eased.min); max = Math.max(max,eased.max);
      }
      view?.lanes.push({ unit: group.unit, y0, y1, min, max, hasValues });
      const y = value => y1 - (value - min) / (max - min) * (y1 - y0);
      ctx.lineWidth = 1;
      for (let j = 0; j <= 2; j++) {
        const yy = y0 + (y1 - y0) * j / 2;
        ctx.strokeStyle = '#303842'; ctx.beginPath(); ctx.moveTo(left, yy); ctx.lineTo(right, yy); ctx.stroke();
        ctx.fillStyle = '#7e8c9a'; ctx.textAlign = 'right';
        const v = max - (max - min) * j / 2;
        const digits = group.unit === 'µs' ? 0 : Math.min(6, Math.max(0, -Math.floor(Math.log10((max - min) / 2))));
        ctx.fillText(v.toFixed(digits), left - 9, yy + 3);
      }
      for (let j = 0; j <= 4; j++) {
        const xx = left + (right - left) * j / 4;
        ctx.strokeStyle = '#28313a'; ctx.beginPath(); ctx.moveTo(xx, y0); ctx.lineTo(xx, y1); ctx.stroke();
      }
      if (groups) { ctx.fillStyle = '#a6b4c1'; ctx.textAlign = 'left'; ctx.fillText(group.unit, left, y0 - 8); }
      ctx.save(); ctx.beginPath(); ctx.rect(left, y0, right - left, Math.max(0, y1 - y0)); ctx.clip();
      group.fields.forEach(field => {
        ctx.strokeStyle = field.color; ctx.lineWidth = 1.5; ctx.beginPath(); let pen = false; let prev = null, prevValue = null;
        // Interleaved protocol rows omit unrelated fields. Connect consecutive
        // valid values of this field, preserving every exported sample/spike.
        const fieldSamples = samples.filter(s => valid(s.t_s) && valid(val(s, field)) && s.t_s >= start && s.t_s <= end);
        for (const s of fieldSamples) {
          const t = s.t_s, v = val(s, field);
          if (prev !== null && t - prev > 2) pen = false;
          if (pen) { if (field.step) ctx.lineTo(x(t), y(prevValue)); ctx.lineTo(x(t), y(v)); }
          else ctx.moveTo(x(t), y(v));
          pen = true; prev = t; prevValue = v;
        }
        ctx.stroke();
      });
      if (valid(cursor)) { ctx.strokeStyle = '#d9e1e8'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(x(cursor), y0); ctx.lineTo(x(cursor), y1); ctx.stroke(); ctx.setLineDash([]); }
      ctx.restore();
      if (!hasValues) { ctx.fillStyle = '#728190'; ctx.textAlign = 'center'; ctx.fillText(group.fields.length ? '此时段无有效数据' : '选择字段以显示曲线', (left + right) / 2, (y0 + y1) / 2); }
    });
    ctx.textAlign = 'center'; ctx.fillStyle = '#778695';
    for (let i = 0; i <= 4; i++) {
      const t = start + timeSpan * i / 4;
      ctx.fillText(groups ? `${t.toFixed(1)} s` : `${Math.round(t - end)} s`, left + (right - left) * i / 4, height - 9);
    }
  }

  function drawLive() {
    const received=valid(state.live?.server_response_time_ms)?state.live.server_response_time_ms:Date.parse(state.live?.received_at);
    const history = Array.isArray(state.live?.history) ? state.live.history : [];
    const stamp = performance.now();
    const offset = state.smooth ? chartClock.sample(stamp)?.offset : null;
    const wallTime = valid(offset) ? stamp + offset : Number.isFinite(received) ? received+state.liveRtt+Math.max(0,stamp-state.lastSuccess) : Date.now();
    // Include every newly received point immediately; only the viewport clock
    // and automatic Y range ease. Never move a telemetry point or replay old data.
    const newest = history.reduce((t,s)=>valid(s.t)?Math.max(t,s.t):t,-Infinity);
    const now = Math.max(wallTime,newest);
    const samples = history.filter(s => valid(s.t) && s.t >= now - 60000 && s.t <= now).map(s => ({ ...s, t_s: s.t / 1000 })).sort((a, b) => a.t_s - b.t_s);
    const end = now / 1000;
    // Expand to 60 seconds as history arrives; leave actual source gaps intact.
    const oldest = history.reduce((t, s) => valid(s.t) && s.t <= now ? Math.min(t, s.t) : t, now) / 1000;
    const start = samples.length ? Math.max(end - 60, Math.min(end - 5, oldest)) : end - 60;
    text('live-history-window', samples.length ? `接收时间 · 当前显示 ${(end - start).toFixed(1)} s · 最多 60 s` : '接收时间 · 等待历史记录');
    chart($('live-orientation-chart'), samples, attitudeOverview, start, end, null, false, state.smooth);
    chart($('live-height-chart'), samples, [fields[3]], start, end, null, false, state.smooth);
    if ($('live-tracking').open) {
      chart($('live-attitude-chart'), samples, chartFields(trackingPairs.roll), start, end, null, false, state.smooth);
      chart($('live-pitch-chart'), samples, chartFields(trackingPairs.pitch), start, end, null, false, state.smooth);
      chart($('live-yaw-rate-chart'), samples, chartFields(trackingPairs.yaw_rate), start, end, null, false, state.smooth);
    }
    const current = liveFresh();
    for (const id of ['live-orientation-chart', 'live-attitude-chart', 'live-pitch-chart', 'live-yaw-rate-chart', 'live-height-chart']) $(id).classList.toggle('is-stale', !current);
  }

  async function loadLogs() {
    $('refresh-logs').disabled = true;
    try {
      const result = await api('/api/logs');
      state.logs = Array.isArray(result.logs) ? result.logs : [];
      state.logsLocal = result.local_controls === true;
      renderLogList(); updateShare();
    } catch {
      $('log-list').replaceChildren(); const p = document.createElement('p'); p.className = 'empty-note'; p.textContent = '无法获取日志列表，请稍后刷新。'; $('log-list').append(p);
      text('log-count', '连接失败');
    } finally { $('refresh-logs').disabled = false; }
  }

  function renderLogList() {
    $('log-list').replaceChildren(); text('log-count', `${state.logs.length} 份`);
    if (!state.logs.length) {
      const p = document.createElement('p'); p.className = 'empty-note';
      p.textContent = state.caps?.mode === 'share' ? '还没有分享日志。由本地接收端选定日志后，才会显示在这里。' : '没有可用记录。接收端保存日志后可在此查看。';
      $('log-list').append(p); return;
    }
    state.logs.forEach(log => {
      const button = document.createElement('button'); button.type = 'button'; button.className = `log-entry${state.logId === log.id ? ' active' : ''}`;
      button.setAttribute('aria-pressed', String(state.logId === log.id));
      const title = document.createElement('strong'); title.textContent = log.title || String(log.id);
      const date = document.createElement('time'); date.textContent = dateText(log.created_at);
      const meta = document.createElement('span'); meta.className = 'entry-meta';
      const count = document.createElement('span'); count.textContent = `${integer(log.frames)} 帧`;
      const duration = document.createElement('span'); duration.textContent = formatTime(log.duration_s);
      meta.append(count, duration);
      if (log.shared === true) { const tag = document.createElement('span'); tag.className = 'shared-tag'; tag.textContent = '已分享'; meta.append(tag); }
      button.append(title, date, meta); button.addEventListener('click', () => selectLog(log.id)); $('log-list').append(button);
    });
  }

  async function selectLog(id) {
    pause(); const requestId = ++state.requestId; state.logId = id; state.selected = null;
    chartViews.get($('log-chart')).ranges.clear();
    state.samples = []; state.selectedFields.clear(); state.start = 0; state.end = 0; state.cursor = 0;
    text('play-time', '00:00.0'); text('total-time', '00:00.0'); renderCursor();
    $('download-csv').hidden = true; $('field-selector').disabled = true; $('timeline').disabled = true; $('play-log').disabled = true;
    $('field-selector').replaceChildren(); text('selected-log-title', '正在读取日志…'); text('log-summary', '');
    $('tracking-axis').disabled = true;
    text('log-message', '正在加载所选日志'); renderLogList(); updateShare(); drawLog();
    try {
      const result = await api(`/api/logs/${encodeURIComponent(id)}`);
      if (requestId !== state.requestId) return;
      if (!result.log || !Array.isArray(result.log.samples)) throw new Error('日志格式错误');
      state.selected = result.log;
      state.samples = result.log.samples.filter(s => s && valid(s.t_s)).sort((a, b) => a.t_s - b.t_s);
      state.start = state.samples[0]?.t_s ?? 0; state.end = state.samples.at(-1)?.t_s ?? 0; state.cursor = state.start;
      text('selected-log-title', result.log.title || id);
      const summary = result.log.summary ?? {};
      const exported = summary.exported_samples ?? summary.exported_rows ?? result.log.exported_samples ?? result.log.exported_rows;
      const source = summary.eligible_samples ?? summary.original_rows ?? result.log.eligible_samples ?? result.log.original_rows ?? summary.source_rows ?? result.log.source_rows;
      const sampled = [summary, result.log].some(meta => meta.downsampled === true || meta.sampled === true || meta.sample === true || meta.complete === false) || valid(source) && source > (valid(exported) ? exported : state.samples.length);
      const rowSummary = valid(exported) || valid(source) ? ` · 显示 ${integer(exported ?? state.samples.length)} / 原始 ${integer(source)} 行` : '';
      const samplingWarning = sampled ? ' · 抽样视图，请以本地完整原始日志诊断' : '';
      text('log-summary', `${integer(summary.frames ?? state.samples.length)} 帧 · ${formatTime(summary.duration_s ?? state.end - state.start)} · 序号缺口 ${integer(summary.missing_frames)} · 重置 ${integer(summary.sequence_resets)}${rowSummary}${samplingWarning}`);
      $('download-csv').href = `/api/logs/${encodeURIComponent(id)}/download.csv`; $('download-csv').setAttribute('download', ''); $('download-csv').hidden = false;
      $('timeline').min = String(state.start); $('timeline').max = String(state.end); $('timeline').value = String(state.start);
      $('timeline').disabled = state.samples.length < 2; $('play-log').disabled = state.samples.length < 2;
      text('total-time', formatTime(state.end));
      buildFields(); updateShare(); setCursor(state.start);
      text('log-message', state.samples.length ? sampled ? '抽样视图，请以本地完整原始日志诊断。时间轴仅回放已导出的样本。' : '拖动时间轴或点击曲线定位；播放仅回放日志，不发送飞控指令。' : '这份日志没有可绘制的有效时间样本。');
    } catch (error) {
      if (requestId !== state.requestId) return;
      const tooLarge = error.status === 413;
      text('selected-log-title', tooLarge ? '日志过大' : '日志读取失败');
      text('log-summary', tooLarge ? '保留原接收端的完整记录' : '可刷新列表后重试');
      text('log-message', tooLarge ? '日志过大，请在原接收端查看完整记录' : '所选日志暂时不可用。');
    }
  }

  function buildFields() {
    $('field-selector').replaceChildren();
    const available = fields.filter(field => state.samples.some(s => field.key === 'armed' ? logArmed(s.armed) !== null : valid(s[field.key])));
    const keys = new Set(available.map(field => field.key));
    const hasRoll = trackingPairs.roll.every(key => keys.has(key));
    const defaults = hasRoll ? trackingPairs.roll : ['roll_deg', 'pitch_deg', 'height_m'];
    $('tracking-axis').value = hasRoll ? 'roll' : 'custom';
    $('tracking-axis').disabled = !available.length;
    for (const axis of Object.keys(trackingPairs)) $(`tracking-${axis}`).disabled = !trackingPairs[axis].every(key => keys.has(key));
    available.forEach(field => {
      const label = document.createElement('label'); const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.value = field.key;
      checkbox.checked = defaults.includes(field.key); if (checkbox.checked) state.selectedFields.add(field.key);
      const line = document.createElement('i'); line.className = `series-${field.key}`;
      const name = document.createElement('span'); name.textContent = `${field.label} ${field.unit}`;
      label.append(checkbox, line, name); $('field-selector').append(label);
      checkbox.addEventListener('change', () => { $('tracking-axis').value = 'custom'; if (checkbox.checked) state.selectedFields.add(field.key); else state.selectedFields.delete(field.key); chartViews.get($('log-chart')).ranges.delete(field.unit); drawLog(); renderCursor(); });
    });
    if (!state.selectedFields.size && available.length) {
      state.selectedFields.add(available[0].key); $('field-selector').querySelector('input').checked = true;
    }
    $('field-selector').disabled = !available.length;
  }

  $('tracking-axis').addEventListener('change', () => {
    const keys = trackingPairs[$('tracking-axis').value]; if (!keys) return;
    state.selectedFields = new Set(keys);
    for (const input of $('field-selector').querySelectorAll('input')) input.checked = state.selectedFields.has(input.value);
    chartViews.get($('log-chart')).ranges.clear(); drawLog(); renderCursor();
  });

  function selectedFields() { return fields.filter(f => state.selectedFields.has(f.key)); }
  function drawLog() {
    const selected = selectedFields(); const groups = new Set(selected.map(f => f.unit)).size;
    $('log-chart').style.height = `${Math.max(320, groups * 145 + 35)}px`;
    chart($('log-chart'), state.samples, selected, state.start, state.end, state.selected ? state.cursor : null, true);
  }

  bindChartScale('live-attitude-chart', 'reset-attitude-scale', drawLive);
  bindChartScale('live-pitch-chart', 'reset-pitch-scale', drawLive);
  bindChartScale('live-yaw-rate-chart', 'reset-yaw-rate-scale', drawLive);
  bindChartScale('live-orientation-chart', 'reset-orientation-scale', drawLive);
  $('live-tracking').addEventListener('toggle', () => { if (state.page === 'live') drawLive(); });
  bindChartScale('live-height-chart', 'reset-height-scale', drawLive);
  bindChartScale('log-chart', 'reset-log-scale', drawLog);

  function cursorSample() {
    let low = 0, high = state.samples.length - 1, result = null;
    while (low <= high) { const mid = (low + high) >>> 1; if (state.samples[mid].t_s <= state.cursor) { result = state.samples[mid]; low = mid + 1; } else high = mid - 1; }
    return result;
  }

  function renderCursor() {
    const sample = cursorSample(); $('cursor-readings').replaceChildren();
    if (!sample) { const s = document.createElement('span'); s.className = 'muted'; s.textContent = '无选中数据'; $('cursor-readings').append(s); return; }
    const stamp = document.createElement('span'); stamp.textContent = `样本 ${fmt(sample.t_s, 2)} s`; $('cursor-readings').append(stamp);
    selectedFields().forEach(field => {
      const item = document.createElement('span'), line = document.createElement('i'), number = document.createElement('b');
      line.className = `series-${field.key}`; number.textContent = field.key === 'armed' ? boolText(logArmed(sample.armed), '已解锁', '未解锁') : `${fmt(sample[field.key], field.unit === 'µs' ? 0 : 2)} ${field.unit}`;
      item.append(line, document.createTextNode(field.label), number); $('cursor-readings').append(item);
    });
  }

  function setCursor(value) {
    state.cursor = clamp(value, state.start, state.end); $('timeline').value = String(state.cursor);
    text('play-time', formatTime(state.cursor)); $('timeline').setAttribute('aria-valuetext', `${state.cursor.toFixed(2)} 秒`); renderCursor(); if (state.page === 'logs') drawLog();
  }

  function pause() { state.playing = false; $('play-log').textContent = '播放'; $('play-log').setAttribute('aria-label', '播放日志'); }
  function playback(stamp) {
    if (!state.playing) return;
    const delta = Math.min(0.25, (stamp - state.playStamp) / 1000); state.playStamp = stamp;
    setCursor(state.cursor + delta * Number($('play-speed').value));
    if (state.cursor >= state.end) pause(); else requestAnimationFrame(playback);
  }
  $('play-log').addEventListener('click', () => {
    if (state.playing) { pause(); return; }
    if (!state.samples.length) return;
    if (state.cursor >= state.end) setCursor(state.start);
    state.playing = true; state.playStamp = performance.now(); $('play-log').textContent = '暂停'; $('play-log').setAttribute('aria-label', '暂停日志'); requestAnimationFrame(playback);
  });
  $('timeline').addEventListener('input', event => { pause(); setCursor(Number(event.target.value)); });
  $('log-chart').addEventListener('click', event => {
    if (!state.selected) return;
    const rect = $('log-chart').getBoundingClientRect(); const ratio = clamp((event.clientX - rect.left - 52) / (rect.width - 70), 0, 1);
    pause(); setCursor(state.start + ratio * (state.end - state.start));
  });
  $('log-chart').addEventListener('keydown', event => {
    if (!state.selected || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault(); pause(); setCursor(state.cursor + (event.key === 'ArrowRight' ? 1 : -1) * (event.shiftKey ? 10 : 0.1));
  });
  $('refresh-logs').addEventListener('click', async () => { await loadCapabilities(); await loadLogs(); });
  $('share-log').addEventListener('click', async () => {
    if (state.caps?.mode !== 'local' || !state.caps.can_share_logs || !state.selected || !state.logsLocal) return;
    const id = state.logId; $('share-log').disabled = true; text('log-message', '正在分享所选日志…');
    try {
      const result = await api('/api/share/log', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
      await loadCapabilities(); await loadLogs();
      text('log-message', '所选日志已分享。');
      const raw = result.share_url ?? state.caps?.share_url;
      if (raw) {
        const url = new URL(raw, location.href);
        if (['https:', 'http:'].includes(url.protocol)) { const link = document.createElement('a'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = '打开分享视图'; $('log-message').append(document.createTextNode(' '), link); }
      }
    } catch { text('log-message', '分享未完成，请检查本地接收端连接后重试。'); }
    finally { updateShare(); }
  });

  function route() {
    const requestedLog = new URLSearchParams(location.search).get('log');
    state.page = location.hash === '#logs' || !location.hash && requestedLog ? 'logs' : 'live';
    const logs = state.page === 'logs'; $('live-view').hidden = logs; $('logs-view').hidden = !logs;
    for (const page of ['live', 'logs']) {
      const item = $(`nav-${page}`); item.classList.toggle('active', state.page === page);
      if (state.page === page) item.setAttribute('aria-current', 'page'); else item.removeAttribute('aria-current');
    }
    if (logs) {
      stopVisuals(); loadLogs();
      if (requestedLog && state.logId !== requestedLog) selectLog(requestedLog);
      requestAnimationFrame(drawLog);
    } else { pause(); startVisuals(); requestAnimationFrame(drawLive); }
  }
  window.addEventListener('hashchange', route);
  let resizeTimer; window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => state.page === 'logs' ? drawLog() : drawLive(), 80); });
  const livePoller = createLivePoller({poll:pollLive, visible:()=>!document.hidden, connected:()=>!state.pollFailed && liveStatus().connected, intervalMs:()=>state.caps?.mode === 'local' ? 200 : 1000});
  document.addEventListener('visibilitychange', () => { if (document.hidden) { pause(); stopVisuals(); livePoller.suspend(); } else { poseTransition.reset(); poseStamp = null; chartClock.reset(); chartTransitions.clear(); livePoller.resume(); startVisuals(); loadCapabilities(); } });
  function tick() { if (document.hidden) return; text('clock', new Date().toLocaleTimeString('zh-CN', { hour12: false })); renderLive(); }
  renderLive(); route(); if (!document.hidden) loadCapabilities(); livePoller.resume(); tick();
  setInterval(tick, 1000);
})();
