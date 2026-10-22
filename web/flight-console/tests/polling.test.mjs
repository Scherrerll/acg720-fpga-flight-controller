import test from 'node:test';
import assert from 'node:assert/strict';
import {createLivePoller} from '../frontend/polling.mjs';
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('visible polling is 1s, disconnect backs off, hidden stops and resume polls now',async()=>{
 let shown=true,online=true,calls=0,next=null;
 const poller=createLivePoller({poll:async()=>{calls++;},visible:()=>shown,connected:()=>online,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;}});
 poller.resume();await settle();assert.equal(calls,1);assert.equal(next.delay,1000);
 online=false;await next.fn();assert.equal(calls,2);assert.equal(next.delay,10000);
 shown=false;poller.suspend();assert.equal(next,null);poller.resume();await settle();assert.equal(calls,2);
 shown=true;poller.resume();await settle();assert.equal(calls,3);assert.equal(next.delay,10000);
});
test('visibility resume during a request never overlaps and requests again immediately',async()=>{
 let shown=true,calls=0,next=null,release;
 const poller=createLivePoller({poll:()=>{calls++;return new Promise(r=>{release=r;});},visible:()=>shown,connected:()=>true,
 setTimer:(fn,delay)=>(next={fn,delay}),clearTimer:()=>{next=null;}});
 poller.resume();shown=false;poller.suspend();shown=true;poller.resume();assert.equal(calls,1);
 release();await settle();assert.equal(next.delay,0);next.fn();assert.equal(calls,2);
 shown=false;poller.suspend();release();await settle();assert.equal(next,null);
});
