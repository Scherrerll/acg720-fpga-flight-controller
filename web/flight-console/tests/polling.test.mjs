import test from 'node:test';
import assert from 'node:assert/strict';
import {createLivePoller} from '../frontend/polling.mjs';
const settle=()=>new Promise(resolve=>setImmediate(resolve));

test('local monitoring may poll at 100ms while cloud remains at 1s',async()=>{
 let local=true,next=null;
 const poller=createLivePoller({poll:async()=>{},visible:()=>true,connected:()=>true,intervalMs:()=>local?100:1000,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;},clock:()=>0});
 poller.resume();await settle();assert.equal(next.delay,100);
 local=false;await next.fn();assert.equal(next.delay,1000);
});
test('visible polling is 1s, brief disconnect retries quickly, hidden stops and resume polls now',async()=>{
 let shown=true,online=true,calls=0,next=null;
 const poller=createLivePoller({poll:async()=>{calls++;},visible:()=>shown,connected:()=>online,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;},clock:()=>0});
 poller.resume();await settle();assert.equal(calls,1);assert.equal(next.delay,1000);
 online=false;await next.fn();assert.equal(calls,2);assert.equal(next.delay,1000);
 await next.fn();assert.equal(calls,3);assert.equal(next.delay,2000);
 shown=false;poller.suspend();assert.equal(next,null);poller.resume();await settle();assert.equal(calls,3);
 shown=true;poller.resume();await settle();assert.equal(calls,4);assert.equal(next.delay,1000);
});
test('slow responses do not add an idle second or overlap requests',async()=>{
 let now=0,calls=0,next=null,inFlight=0;
 const poller=createLivePoller({poll:async()=>{assert.equal(inFlight++,0);calls++;now+=1500;inFlight--;},visible:()=>true,connected:()=>true,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;},clock:()=>now});
 poller.resume();await settle();assert.equal(calls,1);assert.equal(next.delay,0);
 await next.fn();assert.equal(calls,2);assert.equal(next.delay,0);
});
test('long outages cap retries and recovery returns to normal cadence',async()=>{
 let online=false,next=null;
 const poller=createLivePoller({poll:async()=>{},visible:()=>true,connected:()=>online,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;},clock:()=>0});
 poller.resume();await settle();assert.equal(next.delay,1000);
 for(const delay of [2000,4000,8000,10000,10000]){await next.fn();assert.equal(next.delay,delay);}
 online=true;await next.fn();assert.equal(next.delay,1000);
 online=false;await next.fn();assert.equal(next.delay,1000);
});
test('visibility resume during a request never overlaps and requests again immediately',async()=>{
 let shown=true,calls=0,next=null,release;
 const poller=createLivePoller({poll:()=>{calls++;return new Promise(r=>{release=r;});},visible:()=>shown,connected:()=>true,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;}});
 poller.resume();shown=false;poller.suspend();shown=true;poller.resume();assert.equal(calls,1);
 release();await settle();assert.equal(next.delay,0);next.fn();assert.equal(calls,2);
 shown=false;poller.suspend();release();await settle();assert.equal(next,null);
});
