import test from 'node:test';
import assert from 'node:assert/strict';
import {createLivePlayback,createLivePose} from '../frontend/live-playback.mjs';
const point=(t,x=t/1000)=>({t,roll_deg:x,pitch_deg:x*2,yaw_deg:x,height_m:x,speed_mps:x});
const packet=(history,extra={})=>({mode:'share',connected:true,source_valid:true,fresh:true,timing_valid:true,firmware:'B0B0',sequence:1,history,...extra});

test('setpoints hold their reported step while measured rate is interpolated',()=>{
 const p=createLivePlayback({delayMs:250});
 p.ingest(packet([{...point(0),roll_sp_deg:0,yaw_rate_sp_dps:2,yaw_rate_dps:0},{...point(500),roll_sp_deg:10,yaw_rate_sp_dps:6,yaw_rate_dps:4}]),0);
 const first=p.sample(0);assert.equal(first.roll_sp_deg,0);assert.equal(first.yaw_rate_sp_dps,2);assert.equal(first.yaw_rate_dps,2);
 const next=p.sample(250);assert.equal(next.roll_sp_deg,10);assert.equal(next.yaw_rate_sp_dps,6);
});
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
 for(const invalid of [{source_valid:false},{timing_valid:false},{connected:false}]){
  const p=createLivePlayback();assert.equal(p.ingest(packet([point(0)],invalid),0),false);assert.equal(p.sample(0),null);
 }
});

test('delayed but valid received history can play without claiming current data',()=>{
 const p=createLivePlayback({delayMs:250});
 assert.equal(p.ingest(packet([point(0),point(500)],{fresh:false,age_ms:6500}),0),true);
 assert.equal(p.sample(100).t,350);
});

test('latest pose ignores chart delay and retains coherent roll/pitch through missing fields',()=>{
 const p=createLivePose(),base=packet([],{sequence:100,age_ms:100,attitude:{roll_deg:1,pitch_deg:2,yaw_deg:3}});
 p.ingest(base,0,200);assert.equal(p.sample(0).attitude.roll_deg,1);
 p.ingest({...base,sequence:101,attitude:{roll_deg:null,pitch_deg:99,yaw_deg:null}},500,200);
 assert.deepEqual(p.sample(600).attitude,{roll_deg:1,pitch_deg:2,yaw_deg:3});
 assert.equal(p.sample(600).retained,true);assert.equal(p.sample(600).age_ms,900);
 p.ingest({...base,sequence:102,attitude:{roll_deg:4,pitch_deg:5,yaw_deg:6}},700,200);
 assert.equal(p.sample(700).retained,false);assert.equal(p.sample(700).attitude.roll_deg,4);
});

test('latest pose uses actual historical values at startup, never zero placeholders',()=>{
 const p=createLivePose();assert.equal(p.sample(0),null);
 p.ingest(packet([{...point(1000),roll_deg:4,pitch_deg:5,yaw_deg:6}],{age_ms:6000,fresh:false,server_response_time_ms:7000}),0,500);
 const s=p.sample(0);assert.deepEqual(s.attitude,{roll_deg:4,pitch_deg:5,yaw_deg:6});
 assert.equal(s.retained,true);assert.equal(s.age_ms,6500);
});

test('invalid source keeps last valid pose aged; real epoch changes discard it',()=>{
 const p=createLivePose(),base=packet([],{sequence:100,age_ms:100,attitude:{roll_deg:1,pitch_deg:2,yaw_deg:3}});
 p.ingest(base,0);
 p.ingest({...base,source_valid:false,attitude:{roll_deg:99,pitch_deg:99,yaw_deg:99}},500);
 assert.equal(p.sample(800).attitude.roll_deg,1);assert.equal(p.sample(800).age_ms,900);assert.equal(p.sample(800).retained,true);
 p.ingest({...base,firmware:'B0B1',source_valid:false},1000);assert.equal(p.sample(1000),null);
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

test('a running buffer retains 60 seconds behind its delayed playhead',()=>{
 const p=createLivePlayback();
 p.ingest(packet(Array.from({length:121},(_,i)=>point(i*500)),{sequence:1}),0);
 p.ingest(packet(Array.from({length:121},(_,i)=>point(4000+i*500)),{sequence:2}),4000);
 assert.equal(p.history()[0].t,0);
 for(let t=0;t<=4000;t+=100)p.sample(t);
 const now=p.sample(4000).t;
 assert.ok(now-p.history()[0].t>=60000);
});
