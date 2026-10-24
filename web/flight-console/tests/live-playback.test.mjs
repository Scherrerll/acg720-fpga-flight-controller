import test from 'node:test';
import assert from 'node:assert/strict';
import {createLiveTween,createLivePose} from '../frontend/live-playback.mjs';
const point=(t,x=t/1000)=>({t,roll_deg:x,pitch_deg:x*2,yaw_deg:x,height_m:x,speed_mps:x});
const packet=(history,extra={})=>({mode:'share',connected:true,source_valid:true,fresh:true,timing_valid:true,firmware:'B0B0',sequence:1,history,...extra});

test('drawing eases to the newest target in 160ms and stops without extrapolation',()=>{
 const p=createLiveTween();assert.equal(p.sample(0),null);
 p.set({roll_deg:0,pitch_deg:0},0);assert.equal(p.sample(0).roll_deg,0);
 p.set({roll_deg:10,pitch_deg:20},1000);
 assert.equal(p.sample(1000).roll_deg,0);assert.equal(p.sample(1080).roll_deg,5);
 assert.deepEqual(p.sample(1160),{roll_deg:10,pitch_deg:20});
 assert.deepEqual(p.sample(100000),{roll_deg:10,pitch_deg:20});
});
test('retargeting starts from the visible pose; repeated targets do not restart motion',()=>{
 const p=createLiveTween();p.set({roll_deg:0},0);p.set({roll_deg:10},100);
 const halfway=p.sample(180).roll_deg;p.set({roll_deg:20},180);
 assert.equal(p.sample(180).roll_deg,halfway);assert.equal(p.sample(260).roll_deg,12.5);
 p.set({roll_deg:20},260);assert.equal(p.sample(340).roll_deg,20);
});
test('roll/yaw wrap follows the short arc, while missing values stay missing',()=>{
 const p=createLiveTween();p.set({roll_deg:179,yaw_deg:179,pitch_deg:null},0);
 p.set({roll_deg:-179,yaw_deg:-179,pitch_deg:2},100);
 assert.deepEqual(p.sample(180),{roll_deg:180,yaw_deg:180,pitch_deg:2});
 assert.deepEqual(p.sample(260),{roll_deg:-179,yaw_deg:-179,pitch_deg:2});
 p.set({roll_deg:null,yaw_deg:null,pitch_deg:null},300);
 assert.deepEqual(p.sample(350),{roll_deg:null,yaw_deg:null,pitch_deg:null});
});
test('resume after a long source gap, explicit instant mode and resets snap to real values',()=>{
 const p=createLiveTween();p.set({roll_deg:1},0);p.set({roll_deg:9},12000);
 assert.equal(p.sample(12000).roll_deg,9);
 p.set({roll_deg:20},12100,{snap:true});assert.equal(p.sample(12100).roll_deg,20);
 p.reset();assert.equal(p.sample(12200),null);p.set({roll_deg:30},12200);assert.equal(p.sample(12200).roll_deg,30);
});
test('clock correction eases without freezing the moving time axis',()=>{
 const p=createLiveTween({angularKeys:[]});p.set({offset:10000},0);p.set({offset:10040},1000);
 assert.equal(1080+p.sample(1080).offset,11100);
 assert.equal(1160+p.sample(1160).offset,11200);
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
test('pose epoch changes can reset drawing transitions; normal sequence wrap does not',()=>{
 const p=createLivePose(),base=packet([],{sequence:65535,age_ms:100,attitude:{roll_deg:1,pitch_deg:2,yaw_deg:3}});
 p.ingest(base,0);const epoch=p.sample(0).epoch;
 p.ingest({...base,sequence:0},500);assert.equal(p.sample(500).epoch,epoch);assert.equal(p.sample(500).receivedAt,500);
 p.ingest({...base,sequence:1,firmware:'B0B1'},1000);assert.notEqual(p.sample(1000).epoch,epoch);
});
