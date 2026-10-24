import test from 'node:test';
import assert from 'node:assert/strict';
import {createLivePlayback} from '../frontend/live-playback.mjs';
const point=(t,x=t/1000)=>({t,roll_deg:x,pitch_deg:x*2,yaw_deg:x,height_m:x,speed_mps:x});
const packet=(history,extra={})=>({mode:'share',connected:true,source_valid:true,fresh:true,timing_valid:true,firmware:'B0B0',sequence:1,history,...extra});
test('buffered history advances continuously between actual received points',()=>{
 const p=createLivePlayback();p.ingest(packet(Array.from({length:21},(_,i)=>point(i*500))),0);
 assert.equal(p.sample(0).t,6000);
 const a=p.sample(100),b=p.sample(200);
 assert.equal(a.t,6100);assert.equal(b.t,6200);assert.equal(a.roll_deg,6.1);assert.equal(b.height_m,6.2);
});
test('jittered response batches do not snap the playhead to the latest packet',()=>{
 const p=createLivePlayback();p.ingest(packet(Array.from({length:21},(_,i)=>point(i*500))),0);
 let previous=p.sample(0).t;
 for(let t=100;t<=9000;t+=100){
  if([2300,5100,8500].includes(t))p.ingest(packet(Array.from({length:21},(_,i)=>point(t+i*500)),{sequence:t}),t);
  const s=p.sample(t);assert.ok(s.t>=previous&&s.t-previous<=111);previous=s.t;
 }
});
test('never extrapolates after receiving stops and can be frozen immediately',()=>{
 const p=createLivePlayback({delayMs:500});p.ingest(packet([point(0),point(500),point(1000)]),0);
 for(let t=0;t<3000;t+=100)assert.ok(p.sample(t).t<=1000);
 const end=p.sample(3000);assert.equal(end.t,1000);assert.equal(end.buffering,true);
 assert.equal(p.sample(8000,{advance:false}).t,1000);
});
test('a source gap is not turned into invented intermediate motion',()=>{
 const p=createLivePlayback({delayMs:500});p.ingest(packet([point(0),point(500),point(5000),point(5500)]),0);
 const s=p.sample(0);assert.equal(s.t,5000);
 p.reset();p.ingest(packet([point(0),point(500),point(5000)]),0);
 const gap=p.sample(100);assert.equal(gap.t,500);assert.equal(gap.buffering,true);assert.equal(gap.roll_deg,.5);
});
test('yaw crosses wrap by the shortest path and unknown values stay unknown',()=>{
 const p=createLivePlayback({delayMs:250});p.ingest(packet([{...point(0),yaw_deg:179,height_m:null},{...point(500),yaw_deg:-179}]),0);
 const s=p.sample(0);assert.equal(s.yaw_deg,180);assert.equal(s.height_m,null);
});
test('invalid or unsynchronised packets cannot make playback current',()=>{
 for(const invalid of [{source_valid:false},{timing_valid:false},{fresh:false},{connected:false}]){
  const p=createLivePlayback();assert.equal(p.ingest(packet([point(0)],invalid),0),false);assert.equal(p.sample(0),null);
 }
});
test('firmware changes and sequence restarts discard previous-epoch motion',()=>{
 const p=createLivePlayback();p.ingest(packet([point(0),point(500)],{sequence:100}),0);
 p.ingest(packet([point(0),point(500),point(1000)],{sequence:1}),100);
 assert.equal(p.sample(100).t,1000);assert.equal(p.history().length,1);
 p.ingest(packet([point(1500)],{firmware:'B0B1',sequence:2}),200);assert.equal(p.history()[0].t,1500);
});
test('normal 16-bit sequence wrap keeps the existing buffer',()=>{
 const p=createLivePlayback();p.ingest(packet([point(0),point(500)],{sequence:65535}),0);
 p.ingest(packet([point(500),point(1000)],{sequence:0}),100);assert.equal(p.history().length,3);
});
