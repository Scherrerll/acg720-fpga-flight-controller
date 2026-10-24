import test from 'node:test';
import assert from 'node:assert/strict';
import {liveState} from '../frontend/live-state.mjs';
import {cleanLive,getAge} from '../worker/flight.mjs';
const shared=(extra={})=>({mode:'share',connected:true,source_valid:true,timing_valid:true,fresh:true,age_ms:1400,...extra});
test('normal 1Hz relay with network jitter is not a source-expiry alarm',()=>{
 const v=shared();
 assert.equal(liveState(v,{elapsedMs:800,requestRttMs:900}).kind,'delayed');
 assert.equal(liveState(v,{elapsedMs:800,requestRttMs:900}).fresh,true);
 assert.equal(liveState(v,{elapsedMs:3000,requestRttMs:900}).kind,'delayed');
 assert.equal(liveState(v,{elapsedMs:3000,requestRttMs:900}).fresh,false);
 assert.equal(liveState(v,{elapsedMs:4000,requestRttMs:900}).kind,'expired');
 assert.equal(liveState(v,{elapsedMs:11000,requestRttMs:900}).kind,'disconnected');
});
test('source invalid, unsynchronised and unknown ages cannot become live',()=>{
 assert.equal(liveState(shared({source_valid:false,fresh:false})).kind,'source_invalid');
 assert.equal(liveState(shared({timing_valid:false,fresh:false,age_ms:null})).kind,'timing_unknown');
 for(const age_ms of [null,-1,NaN,Infinity])assert.equal(liveState(shared({age_ms})).fresh,false);
 assert.equal(liveState({mode:'local',connected:true,source_valid:true,fresh:false,source_ttl_ms:500,age_ms:510}).fresh,false);
});
test('slow responses keep qualified values visible without calling them fresh',()=>{
 const timing={requestRttMs:1500,elapsedMs:300};
 const delayed=liveState(shared({age_ms:3600}),timing);
 assert.equal(delayed.kind,'delayed');assert.equal(delayed.recent,true);assert.equal(delayed.fresh,false);
 for(const override of [{fresh:false},{source_valid:false},{timing_valid:false},{connected:false},{age_ms:null}]){
  assert.equal(liveState(shared({age_ms:3600,...override}),timing).recent,false);
 }
 const expired=liveState(shared({age_ms:3600}),{requestRttMs:1500,elapsedMs:1500});
 assert.equal(expired.kind,'expired');assert.equal(expired.recent,false);assert.equal(expired.fresh,false);
});
test('cloud to browser timing accounts for request RTT and ignores browser wall-clock jumps',()=>{
 const server=1800000000000;
 const v=cleanLive({schema:1,firmware:'B0AC',connected:true,source_valid:true,fresh:false,age_ms:510,source_ttl_ms:500,timing_version:2,timing_valid:true,clock_uncertainty_ms:150,source_publish_at:new Date(server-400).toISOString()},server);
 const read=getAge(v,server+700);
 const timing={elapsedMs:900,requestRttMs:800};
 const result=liveState(read,timing);
 assert.equal(result.age_ms,3460);assert.equal(result.fresh,true);
 const original=Date.now;
 try{Date.now=()=>server+3600000;assert.deepEqual(liveState(read,timing),result);Date.now=()=>server-3600000;assert.deepEqual(liveState(read,timing),result);}finally{Date.now=original;}
 assert.equal(liveState(read,{elapsedMs:2600,requestRttMs:800}).fresh,false);
});
