import test from 'node:test';
import assert from 'node:assert/strict';

test('latest live values and history update immediately, drawing eases briefly, and raw states and source gaps stay intact',async()=>{
 const nodes=new Map(),listeners=new Map(),frames=new Map(),timers=new Map();let stamp=0,serial=0;
 class CanvasContext{
  constructor(){this.strokes=[];this.texts=[];this.path=[];this.clears=0;this.transforms=[];}
  scale(){this.strokes=[];this.texts=[];}
  setTransform(...values){this.transforms.push(values);}
  clearRect(){this.strokes=[];this.texts=[];this.path=[];this.clears++;}
  beginPath(){this.path=[];}moveTo(x,y){this.path.push({op:'move',x,y});}lineTo(x,y){this.path.push({op:'line',x,y});}
  stroke(){this.strokes.push({color:this.strokeStyle,path:[...this.path]});}
  fillText(value){this.texts.push(value);}save(){}restore(){}rect(){}clip(){}setLineDash(){}
 }
 class Element{
  constructor(tagName=''){this.tagName=tagName;this.children=[];this.attrs={};this.dataset={};this.events={};this.style={};this.textContent='';this.className='';this.lastElementChild={textContent:''};this.hidden=false;this.classes=new Set();this.classList={toggle:(k,on)=>{if(on)this.classes.add(k);else this.classes.delete(k);},add:k=>this.classes.add(k),remove:k=>this.classes.delete(k)};}
  set id(v){this._id=v;nodes.set(v,this);}get id(){return this._id;}
  setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k];}removeAttribute(k){delete this.attrs[k];}
  append(...items){this.children.push(...items);}appendChild(item){this.append(item);}replaceChildren(...items){this.children=[];this.append(...items);}addEventListener(k,fn){this.events[k]=fn;}
  querySelectorAll(tag){return this.children.flatMap(child=>[...(child.tagName===tag?[child]:[]),...child.querySelectorAll(tag)]);}querySelector(tag){return this.querySelectorAll(tag)[0];}
  set width(v){this._width=v;this.widthWrites=(this.widthWrites||0)+1;}get width(){return this._width??300;}
  set height(v){this._height=v;this.heightWrites=(this.heightWrites||0)+1;}get height(){return this._height??150;}
  getBoundingClientRect(){return {width:this.id?.endsWith('-chart')?(this.cssWidth??800):0,height:143,left:0,top:0};}
  getContext(){return this.context??=new CanvasContext();}
 }
 const element=id=>{if(!nodes.has(id)){const e=new Element();e.id=id;}return nodes.get(id);};
 const live={schema:1,mode:'share',connected:true,fresh:true,source_valid:true,timing_valid:true,age_ms:100,
  firmware:'B0B0',sequence:100,server_response_time_ms:10000,received_at:'2026-10-24T00:00:00Z',
  attitude:{roll_deg:10,pitch_deg:20,yaw_deg:10},motion:{height_m:10,speed_mps:10,vx_mps:8,vy_mps:6,vz_mps:1},
  armed:false,control_mode:'ALT_HOLD',motors_us:[1000,1201,1302,1403],rc:{channels:[1500,1500,1000],valid:true},
  history:Array.from({length:21},(_,i)=>({t:i*500,roll_deg:i/2,pitch_deg:i,yaw_deg:i/2,height_m:i/2,speed_mps:i/2,roll_sp_deg:i<12?0:6,pitch_sp_deg:-3,yaw_rate_dps:i/10,yaw_rate_sp_dps:5}))};
 const log={id:'tracking_test_123',samples:[{t_s:0,roll_deg:1,roll_sp_deg:0,pitch_deg:2,pitch_sp_deg:3,yaw_deg:12,yaw_rate_dps:4,yaw_rate_sp_dps:5},{t_s:1,roll_deg:2,roll_sp_deg:3,pitch_deg:3,pitch_sp_deg:4,yaw_deg:13,yaw_rate_dps:5,yaw_rate_sp_dps:6}]};
 const overrides={document:{hidden:false,getElementById:element,createElement:tag=>new Element(tag),createTextNode:text=>Object.assign(new Element(),{textContent:text}),createElementNS:()=>new Element(),addEventListener:(k,fn)=>listeners.set(k,fn)},
  window:{devicePixelRatio:1,addEventListener:(k,fn)=>listeners.set('window:'+k,fn)},location:{hash:'',search:'',href:'http://localhost/'},
  performance:{now:()=>stamp},fetch:async url=>({ok:true,json:async()=>url.includes('capabilities')?{mode:'share'}:url==='/api/logs'?{logs:[log]}:url.includes('/api/logs/')?{log}:structuredClone(live)}),
  requestAnimationFrame:fn=>{const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id),
  setTimeout:(fn,delay)=>{const id=++serial;timers.set(id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id),setInterval:()=>++serial};
 const saved=new Map(Object.keys(overrides).map(k=>[k,Object.getOwnPropertyDescriptor(globalThis,k)]));
 const flushFrames=t=>{stamp=t;const pending=[...frames.values()];frames.clear();for(const fn of pending)fn(t);};
 const pollAt=async t=>{stamp=t;const [id,timer]=[...timers].find(([,timer])=>timer.delay===1000);timers.delete(id);await timer.fn();await new Promise(resolve=>setImmediate(resolve));};
 try{
  for(const [k,v] of Object.entries(overrides))Object.defineProperty(globalThis,k,{configurable:true,writable:true,value:v});
  await import('../frontend/app.js?live-view-test');await new Promise(resolve=>setImmediate(resolve));
  flushFrames(100);
  const trend=element('live-orientation-chart');
  const backingWrites=[trend.widthWrites,trend.heightWrites];
  const clears=trend.context.clears;
  flushFrames(140);
  assert.deepEqual([trend.widthWrites,trend.heightWrites],backingWrites,'unchanged charts must retain their backing buffer between animation frames');
  assert.ok(trend.context.clears>clears,'each retained buffer is still cleared before drawing, without leaving old traces');
  assert.equal(element('horizon-roll').textContent,'10.0°','default attitude follows the latest real value, not the chart buffer');
  assert.match(element('pose-status').textContent,/最新接收值/);
  assert.equal(element('height-value').textContent,'10.00');
  assert.match(element('playback-status').textContent,/无额外回放缓冲/);
  // Change the real packet through the existing poller, without a visibility reset.
  const first=element('attitude-rotation').getAttribute('transform');
  live.attitude={roll_deg:15,pitch_deg:25,yaw_deg:12};live.motion.height_m=11;live.sequence++;
  await pollAt(200);
  assert.equal(element('horizon-roll').textContent,'15.0°');
  assert.equal(element('height-value').textContent,'11.00');
  assert.equal(element('attitude-rotation').getAttribute('transform'),first,'numeric update does not wait for the drawing');
  const drawnRoll=()=>-Number(element('attitude-rotation').getAttribute('transform').match(/rotate\(([^,]+)/)[1]);
  flushFrames(280);const middle=drawnRoll();assert.ok(middle>10&&middle<15);
  flushFrames(360);assert.ok(drawnRoll()>middle&&drawnRoll()<15);
  assert.equal(element('horizon-roll').textContent,'15.0°','numeric labels remain the real latest value while the drawing follows');
  assert.equal(element('motor-value-1').textContent,'1201');assert.equal(element('armed-value').textContent,'未解锁');
  const series=(id,color)=>element(id).context.strokes.find(s=>s.color===color).path;
  const roll=series('live-orientation-chart','#2dd4bf');
  assert.equal(roll[0].x,52,'short received history starts at the left edge instead of an empty fixed 60-second window');
  assert.ok(roll.at(-1).x>750,'newest received history point is already visible');
  assert.equal(roll.length,21,'all 21 actual samples are drawn immediately, including the newest four seconds');
  assert.match(element('live-history-window').textContent,/10\.2 s/);
  const yaw=series('live-orientation-chart','#ffb454');
  const pitch=series('live-orientation-chart','#7395ff');
  assert.ok(yaw.length>2,'relative yaw is actually drawn, not just added to the legend');
  assert.equal(yaw[0].x,roll[0].x);assert.equal(yaw.at(-1).x,roll.at(-1).x);
  assert.equal(pitch[0].y,roll[0].y);assert.equal(yaw.at(-1).y,roll.at(-1).y);
  assert.ok(pitch.at(-1).y<roll.at(-1).y,'all three angles share the same vertical scale');
  assert.equal(element('live-attitude-chart').context,undefined,'detailed target plots are initially collapsed');
  element('live-tracking').open=true;element('live-tracking').events.toggle();
  const target=series('live-attitude-chart','#8cbaa6');
  assert.ok(target.some((point,i)=>i>0&&point.x===target[i-1].x&&point.y!==target[i-1].y),'setpoint changes are drawn as steps');
  assert.ok(series('live-pitch-chart','#d4b574').length>2);assert.ok(series('live-pitch-chart','#8cbaa6').length>2);
  assert.ok(series('live-yaw-rate-chart','#65a5e7').length>2);assert.ok(series('live-yaw-rate-chart','#8cbaa6').length>2);
  element('smooth-live').events.click();
  assert.equal(element('smooth-live').getAttribute('aria-pressed'),'false');
  assert.equal(element('horizon-roll').textContent,'15.0°');
  assert.equal(element('height-value').textContent,'11.00');
  assert.equal(element('motor-value-1').textContent,'1201');
  assert.match(element('playback-status').textContent,/无额外回放缓冲/);
  element('pose-instant').events.click();
  assert.match(element('playback-status').textContent,/即时切换/);
  element('pose-instant').events.click();
  element('smooth-live').events.click();
  // Refresh through the real visibility/resume path with a full window and a
  // genuine five-second source gap. Adaptive axes must not hide or fill it.
  overrides.document.hidden=true;listeners.get('visibilitychange')();
  live.server_response_time_ms=70000;live.sequence=2000;live.fresh=false;live.age_ms=6500;
  live.control_mode='DISARMED';live.flags={requested:'ATT_ALT_HOLD'};
  live.history=Array.from({length:141},(_,i)=>({t:i*500,roll_deg:i,pitch_deg:i/2,yaw_deg:i/3,height_m:1,speed_mps:0})).filter(p=>p.t<=35000||p.t>=40500);
  overrides.document.hidden=false;listeners.get('visibilitychange')();await new Promise(resolve=>setImmediate(resolve));
  flushFrames(500);
  assert.match(element('live-history-window').textContent,/60\.0 s/);
  const delayedPose=element('attitude-rotation').getAttribute('transform');flushFrames(550);
  assert.equal(element('attitude-rotation').getAttribute('transform'),delayedPose,'no old history is replayed while the latest snapshot is delayed');
  assert.match(element('connection').lastElementChild.textContent,/已连接.*数据延迟/);
  assert.equal(element('mode-value').textContent,'待机 / DISARMED');assert.equal(element('requested-value').textContent,'自稳 + 高度控制');
  assert.ok(series('live-attitude-chart','#65a5e7').filter(p=>p.op==='move').length>=2,'real source gaps remain disconnected');
  overrides.document.hidden=true;listeners.get('visibilitychange')();
  for(const p of live.history)p.yaw_deg=null;live.attitude.yaw_deg=null;live.sequence++;
  overrides.document.hidden=false;listeners.get('visibilitychange')();await new Promise(resolve=>setImmediate(resolve));
  flushFrames(600);
  assert.equal(series('live-orientation-chart','#ffb454').length,0,'missing yaw is never plotted as zero');
  assert.ok(series('live-orientation-chart','#2dd4bf').length>0,'missing yaw does not hide the other angles');
  const heldRoll=element('horizon-roll').textContent,heldPitch=element('horizon-pitch').textContent;
  overrides.document.hidden=true;listeners.get('visibilitychange')();
  live.attitude={roll_deg:null,pitch_deg:99,yaw_deg:null};live.sequence++;
  overrides.document.hidden=false;listeners.get('visibilitychange')();await new Promise(resolve=>setImmediate(resolve));flushFrames(650);
  assert.equal(element('horizon-roll').textContent,heldRoll);assert.equal(element('horizon-pitch').textContent,heldPitch);
  assert.match(element('pose-status').textContent,/最后有效值/);
  // A slow cloud cadence must keep following after the old 160ms animation would have stopped.
  live.attitude={roll_deg:22,pitch_deg:30,yaw_deg:3};live.fresh=true;live.age_ms=100;live.sequence++;
  const beforeSlow=element('attitude-rotation').getAttribute('transform');await pollAt(3300);
  assert.equal(element('horizon-roll').textContent,'22.0°');
  assert.equal(element('attitude-rotation').getAttribute('transform'),beforeSlow,'2.6-second response spacing must not disable transitions');
  flushFrames(3700);const late=drawnRoll();flushFrames(4100);assert.ok(drawnRoll()>late&&drawnRoll()<22,'graphical attitude still moves between slow packets');
  const beforeDpr=[trend.widthWrites,trend.heightWrites];
  overrides.window.devicePixelRatio=2;flushFrames(4140);
  assert.equal(trend.width,1600);assert.equal(trend.height,286);
  assert.deepEqual([trend.widthWrites,trend.heightWrites],beforeDpr.map(v=>v+1),'a DPR change resizes each backing dimension once');
  flushFrames(4180);
  assert.deepEqual([trend.widthWrites,trend.heightWrites],beforeDpr.map(v=>v+1));
  assert.deepEqual(trend.context.transforms.at(-1),[2,0,0,2,0,0],'DPR scaling is replaced per frame, never accumulated');
  trend.cssWidth=810;flushFrames(4220);
  assert.equal(trend.width,1620);assert.equal(trend.widthWrites,beforeDpr[0]+2);assert.equal(trend.heightWrites,beforeDpr[1]+1,'CSS width changes leave the unchanged height allocation alone');
  assert.equal(element('horizon-roll').textContent,'22.0°');
  assert.match(element('playback-status').textContent,/连续跟随/);
  overrides.location.hash='#logs';listeners.get('window:hashchange')();await new Promise(resolve=>setImmediate(resolve));
  await element('log-list').children.find(child=>child.tagName==='button').events.click();flushFrames(4300);
  assert.equal(element('tracking-axis').value,'roll');
  const checked=()=>element('field-selector').querySelectorAll('input').filter(input=>input.checked).map(input=>input.value).sort();
  assert.deepEqual(checked(),['roll_deg','roll_sp_deg']);
  element('tracking-axis').value='pitch';element('tracking-axis').events.change();assert.deepEqual(checked(),['pitch_deg','pitch_sp_deg']);
  element('tracking-axis').value='yaw_rate';element('tracking-axis').events.change();assert.deepEqual(checked(),['yaw_rate_dps','yaw_rate_sp_dps']);
  assert.ok(element('log-chart').context.texts.includes('°/s'),'yaw rate comparison keeps rate units in log view');
  element('tracking-axis').value='overview';element('tracking-axis').events.change();
  assert.deepEqual(checked(),['pitch_deg','roll_deg','yaw_deg']);
  overrides.document.hidden=true;listeners.get('visibilitychange')();assert.equal(frames.size,0);
 }finally{
  for(const [k,descriptor] of saved){if(descriptor)Object.defineProperty(globalThis,k,descriptor);else delete globalThis[k];}
 }
});
