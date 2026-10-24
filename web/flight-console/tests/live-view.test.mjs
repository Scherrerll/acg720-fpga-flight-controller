import test from 'node:test';
import assert from 'node:assert/strict';

test('live view animates received history, leaves discrete values raw, and switches to instant mode',async()=>{
 const nodes=new Map(),listeners=new Map(),frames=new Map();let stamp=0,serial=0;
 class Element{
  constructor(){this.attrs={};this.events={};this.style={};this.textContent='';this.className='';this.lastElementChild={textContent:''};this.hidden=false;this.classes=new Set();this.classList={toggle:(k,on)=>{if(on)this.classes.add(k);else this.classes.delete(k);},add:k=>this.classes.add(k),remove:k=>this.classes.delete(k)};}
  set id(v){this._id=v;nodes.set(v,this);}get id(){return this._id;}
  setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k];}removeAttribute(k){delete this.attrs[k];}
  append(){}appendChild(){}replaceChildren(){}addEventListener(k,fn){this.events[k]=fn;}
  getBoundingClientRect(){return {width:0,height:0,left:0,top:0};}
 }
 const element=id=>{if(!nodes.has(id)){const e=new Element();e.id=id;}return nodes.get(id);};
 const live={schema:1,mode:'share',connected:true,fresh:true,source_valid:true,timing_valid:true,age_ms:100,
  firmware:'B0B0',sequence:100,server_response_time_ms:10000,received_at:'2026-10-24T00:00:00Z',
  attitude:{roll_deg:10,pitch_deg:20,yaw_deg:10},motion:{height_m:10,speed_mps:10,vx_mps:8,vy_mps:6,vz_mps:1},
  armed:false,control_mode:'ALT_HOLD',motors_us:[1000,1201,1302,1403],rc:{channels:[1500,1500,1000],valid:true},
  history:Array.from({length:21},(_,i)=>({t:i*500,roll_deg:i/2,pitch_deg:i,yaw_deg:i/2,height_m:i/2,speed_mps:i/2}))};
 const overrides={document:{hidden:false,getElementById:element,createElement:()=>new Element(),createElementNS:()=>new Element(),addEventListener:(k,fn)=>listeners.set(k,fn)},
  window:{devicePixelRatio:1,addEventListener(){}},location:{hash:'',search:'',href:'http://localhost/'},
  performance:{now:()=>stamp},fetch:async url=>({ok:true,json:async()=>url.includes('capabilities')?{mode:'share'}:structuredClone(live)}),
  requestAnimationFrame:fn=>{const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame:id=>frames.delete(id),
  setTimeout:()=>++serial,clearTimeout(){},setInterval:()=>++serial};
 const saved=new Map(Object.keys(overrides).map(k=>[k,Object.getOwnPropertyDescriptor(globalThis,k)]));
 const flushFrames=t=>{stamp=t;const pending=[...frames.values()];frames.clear();for(const fn of pending)fn(t);};
 try{
  for(const [k,v] of Object.entries(overrides))Object.defineProperty(globalThis,k,{configurable:true,writable:true,value:v});
  await import('../frontend/app.js?live-view-test');await new Promise(resolve=>setImmediate(resolve));
  flushFrames(100);const first=element('attitude-rotation').getAttribute('transform');flushFrames(200);
  assert.notEqual(element('attitude-rotation').getAttribute('transform'),first);
  assert.equal(element('horizon-roll').textContent,'6.2°');
  assert.equal(element('height-value').textContent,'6.20');
  assert.equal(element('motor-value-1').textContent,'1201');assert.equal(element('armed-value').textContent,'未解锁');
  assert.match(element('playback-status').textContent,/平滑回放/);
  element('smooth-live').events.click();
  assert.equal(element('smooth-live').getAttribute('aria-pressed'),'false');
  assert.equal(element('horizon-roll').textContent,'10.0°');
  assert.equal(element('height-value').textContent,'10.00');
  assert.equal(element('motor-value-1').textContent,'1201');
  assert.match(element('playback-status').textContent,/即时显示/);
  overrides.document.hidden=true;listeners.get('visibilitychange')();assert.equal(frames.size,0);
 }finally{
  for(const [k,descriptor] of saved){if(descriptor)Object.defineProperty(globalThis,k,descriptor);else delete globalThis[k];}
 }
});
