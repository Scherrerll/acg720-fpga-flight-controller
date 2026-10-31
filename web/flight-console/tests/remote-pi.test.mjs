import test from 'node:test';
import assert from 'node:assert/strict';
import {handleRemotePI, sanitizeRemotePIStatus, REMOTE_PI_TTL_MS} from '../worker/remote-pi.mjs';

const OPERATOR = 'operator-only-fixture-token-1234567890';
const PUBLISHER = 'publisher-only-fixture-token-1234567890';
const epoch = 'a'.repeat(32), challenge = 'b'.repeat(32);
const tuple = {p_text:'0.1000', i_text:'0.0350', generation:7, build:'0000B0B4', age_ms:12};
function setup() {
  const values = new Map(); let time = 1800000000000;
  const env = {CONTROL_TOKEN:OPERATOR, PUBLISH_TOKEN:PUBLISHER, BUCKET:{
    async get(k) { const s = values.get(k); return s === undefined ? null : {json:async()=>JSON.parse(s)}; },
    async put(k,s) { values.set(k,s); },
  }};
  const call = (path, body, role='operator', extra={}) => {
    const method = body === undefined ? 'GET' : 'POST';
    const headers = {'Content-Type':'application/json',
      ...(role === 'operator' ? {'X-Flight-Control-Token':OPERATOR} : role === 'publisher' ? {'X-Flight-Publish-Token':PUBLISHER} : {}),
      ...(method === 'POST' && role === 'operator' ? {Origin:'https://flight.example'} : {}), ...extra};
    return handleRemotePI(new Request('https://flight.example/api/remote-pi/'+path,
      {method,headers,...(body === undefined ? {} : {body:typeof body === 'string'?body:JSON.stringify(body)})}),env,{now:()=>time});
  };
  const status = change => ({enabled:true,connected:true,source:'SiK',baud:115200,epoch:9,
    supported:true,busy:false,phase:'idle',can_query:true,can_set:true,active:{...tuple},...change});
  const heartbeat = change => call('heartbeat',{epoch,challenge,status:status(change)},'publisher');
  const command = change => ({id:'request_1234',epoch,challenge,action:'set',expected_epoch:9,
    expected_generation:7,p:'0.1000',i:'0.0350',confirmed_stopped:true,...change});
  const intent = (id='request_1234') => JSON.parse(values.get(`control/result/${epoch}/${id}.json`)||'null')?.intent??null;
  return {values,env,call,status,heartbeat,command,intent,advance:n=>time+=n,now:()=>time};
}

test('unrelated routes remain owned by the telemetry worker; configuration fails closed',async()=>{
  assert.equal(await handleRemotePI(new Request('https://flight.example/api/live'),{}),null);
  const s=setup();
  for(const env of [{},{...s.env,CONTROL_TOKEN:'short'},{...s.env,CONTROL_TOKEN:PUBLISHER},{...s.env,PUBLISH_TOKEN:''}]) {
    const r=await handleRemotePI(new Request('https://flight.example/api/remote-pi/status'),env);
    assert.equal(r.status,503);assert.equal((await r.json()).enabled,false);
  }
});

test('operator and publisher credentials are isolated for all routes',async()=>{
  const s=setup();
  assert.equal((await s.call('status',undefined,'none')).status,401);
  assert.equal((await s.call('status',undefined,'publisher')).status,401);
  assert.equal((await s.call('heartbeat',{epoch,challenge,status:s.status()},'operator')).status,401);
  assert.equal((await s.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'operator')).status,401);
  assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,result:{code:'verified',active:tuple}},'operator')).status,401);
  assert.equal(s.values.size,0);
});

test('heartbeat, status and terminal results expose only the allowlisted fields',async()=>{
  const s=setup();await s.heartbeat({token:'do-not-expose',port:'COM17',block_reason:'C:/private.txt',
    active:{...tuple,token:'secret'},result:{code:'queried',message:'secret'}});
  const r=await s.call('status');assert.equal(r.status,200);const v=await r.json();
  assert.equal(v.relay_fresh,true);assert.equal(v.epoch,epoch);assert.equal(v.challenge,challenge);
  assert.equal(v.status.active.p_text,'0.1000');
  assert.equal(JSON.stringify(v).includes('secret'),false);assert.equal(JSON.stringify(v).includes('COM17'),false);
  assert.equal(JSON.stringify(v).includes('C:/'),false);assert.equal(JSON.stringify(v).includes('do-not-expose'),false);
});

test('query command roundtrip and result are authenticated; completion is never inferred from a queued request',async()=>{
  const s=setup();await s.heartbeat({supported:false,active:null,can_set:false});
  const command={id:'query_1234',epoch,challenge,action:'query',expected_epoch:9};
  assert.equal((await s.call('command',command)).status,202);
  const before=await (await s.call(`result/${epoch}/query_1234`)).json();assert.equal(before.result.code,'queued');
  const v=await (await s.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'publisher')).json();
  assert.equal(v.command.action,'query');assert.equal(v.command.expires_at_ms-v.command.created_at_ms,REMOTE_PI_TTL_MS);
  assert.equal((await s.call('result',{epoch,id:'query_1234',challenge,intent:s.intent('query_1234'),result:{code:'queried',active:tuple,operation_id:2}},'publisher')).status,200);
  const done=await(await s.call(`result/${epoch}/query_1234`)).json();assert.equal(done.result.code,'queried');
  assert.equal(done.result.active.generation,7);
  assert.equal((await(await s.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'publisher')).json()).command,null);
});

test('only a queried valid local tuple with stopped can_set eligibility can enqueue SET',async()=>{
  for(const change of [{can_set:false},{can_query:false},{supported:false},{busy:true},{connected:false},{enabled:false},
    {source:'USB'},{baud:57600},{active:{...tuple,build:'0000B0B6'}},{active:null}]) {
    const s=setup();await s.heartbeat(change);
    assert.equal((await s.call('command',s.command())).status,409,JSON.stringify(change));
    assert.equal([...s.values.keys()].some(k=>k.startsWith('control/request/')),false);
  }
  const s=setup();await s.heartbeat({active:{...tuple,build:'0000B0B5'}});
  assert.equal((await s.call('command',s.command())).status,202);
});

test('SET validates generation, local epoch, challenge, stopped confirmation and exact decimal intent',async()=>{
  for(const change of [{expected_generation:6},{expected_epoch:8},{epoch:'c'.repeat(32)},{challenge:'c'.repeat(32)},
    {confirmed_stopped:false},{p:0.1},{i:'NaN'},{p:'1.0001'},{i:'0.00001'},{p:'-0.1'}, {p:'1e-1'}]) {
    const s=setup();await s.heartbeat();assert.equal((await s.call('command',s.command(change))).status,409,JSON.stringify(change));
  }
});

test('freshness, time rollback, expiration and rotated challenges fail closed',async()=>{
  const s=setup();await s.heartbeat();s.advance(5001);
  const status=await(await s.call('status')).json();assert.equal(status.relay_fresh,false);assert.equal(status.challenge,null);
  assert.equal((await s.call('command',s.command())).status,409);
  const q=setup();await q.heartbeat();await q.call('command',q.command());q.advance(REMOTE_PI_TTL_MS);
  await q.heartbeat();assert.equal((await(await q.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'publisher')).json()).command,null);
  const r=setup();await r.heartbeat();r.advance(-1);assert.equal((await r.call('command',r.command())).status,409);
  const n=setup();await n.heartbeat();await n.call('heartbeat',{epoch,challenge:'c'.repeat(32),status:n.status()},'publisher');
  assert.equal((await n.call('command',n.command())).status,409);
  assert.equal((await n.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'publisher')).status,409);
});

test('duplicate IDs never refresh TTL, enqueue again or replace an accepted terminal result',async()=>{
  const s=setup();await s.heartbeat();assert.equal((await s.call('command',s.command())).status,202);
  const record=s.values.get(`control/request/${epoch}/${challenge}.json`);
  s.advance(100);assert.equal((await s.call('command',s.command())).status,409);
  assert.equal(record,s.values.get(`control/request/${epoch}/${challenge}.json`));
  const completed={epoch,id:'request_1234',challenge,intent:s.intent(),result:{code:'verified',active:{...tuple,generation:8},operation_id:2}};
  assert.equal((await s.call('result',completed,'publisher')).status,200);
  await s.call('result',{...completed,result:{code:'unknown'}},'publisher');
  assert.equal((await(await s.call(`result/${epoch}/request_1234`)).json()).result.code,'verified');
});

test('same-challenge concurrent mail overwrites only the executable slot and each ID retains its own intent',async()=>{
  const s=setup();await s.heartbeat();await s.call('command',s.command());
  await s.call('command',s.command({id:'request_5678'}));
  assert.equal((await(await s.call(`poll?epoch=${epoch}&challenge=${challenge}`,undefined,'publisher')).json()).command.id,'request_5678');
  assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,intent:s.intent(),result:{code:'verified',active:{...tuple,generation:8}}},'publisher')).status,200);
  assert.equal((await(await s.call(`result/${epoch}/request_1234`)).json()).result.code,'verified');
  assert.equal((await(await s.call(`result/${epoch}/request_5678`)).json()).result.code,'queued');
});

test('missing real readback tuple is unknown even if relay reports success',async()=>{
  const s=setup();await s.heartbeat();await s.call('command',s.command());
  await s.call('result',{epoch,id:'request_1234',challenge,intent:s.intent(),result:{code:'verified',active:null,message:'do-not-copy'}},'publisher');
  const v=await(await s.call(`result/${epoch}/request_1234`)).json();assert.equal(v.result.code,'unknown');
  assert.equal(JSON.stringify(v).includes('do-not-copy'),false);
});

test('result must describe this exact action, parameter pair, generation and local connection',async()=>{
  for(const change of [{code:'queried',active:tuple},{code:'verified',active:tuple},
    {code:'verified',active:{...tuple,p_text:'0.2000',generation:8}},
    {code:'verified',active:{...tuple,i_text:'0.0300',generation:8}}]) {
    const s=setup();await s.heartbeat();await s.call('command',s.command());
    await s.call('result',{epoch,id:'request_1234',challenge,intent:s.intent(),result:change},'publisher');
    assert.equal((await(await s.call(`result/${epoch}/request_1234`)).json()).result.code,'unknown');
  }
  const s=setup();await s.heartbeat();await s.call('command',s.command());await s.heartbeat({epoch:10});
  assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,intent:s.intent(),result:{code:'verified',active:{...tuple,generation:8}}},'publisher')).status,200);
  assert.equal((await(await s.call(`result/${epoch}/request_1234`)).json()).result.code,'unknown');
});

test('failed outcomes settle pending records after local or relay epoch changes',async()=>{
  for (const code of ['unknown','cancelled','expired','transport','blocked']) {
    for (const relayChanged of [false,true]) {
      const s=setup();await s.heartbeat();await s.call('command',s.command());const intent=s.intent();
      await s.call('heartbeat',{epoch:relayChanged?'c'.repeat(32):epoch,challenge:'d'.repeat(32),status:s.status({epoch:10})},'publisher');
      assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,intent,result:{code,active:null}},'publisher')).status,200);
      assert.equal((await(await s.call(`result/${epoch}/request_1234`)).json()).result.code,code);
    }
  }
  const s=setup();await s.heartbeat();await s.call('command',s.command());const intent=s.intent();
  await s.call('heartbeat',{epoch:'c'.repeat(32),challenge:'d'.repeat(32),status:s.status()},'publisher');
  await s.call('result',{epoch,id:'request_1234',challenge,intent,result:{code:'verified',active:{...tuple,generation:8}}},'publisher');
  const out=(await(await s.call(`result/${epoch}/request_1234`)).json()).result;
  assert.equal(out.code,'unknown');assert.equal(out.active,null);
});

test('no-CAS concurrent reuse of one ID across local epochs cannot attribute old success to a replaced intent',async()=>{
  const s=setup();await s.heartbeat();
  const key=`control/result/${epoch}/request_1234.json`,get=s.env.BUCKET.get;
  let heartbeatReads=0,resultReads=0,release,entered;
  const barrier=new Promise(resolve=>release=resolve);
  const firstRead=new Promise(resolve=>entered=resolve);
  s.env.BUCKET.get=async k=>{
    if(k==='control/heartbeat.json'){
      const localEpoch=heartbeatReads++===0?9:10;
      return {json:async()=>({epoch,challenge,status:s.status({epoch:localEpoch}),received_at_ms:s.now()})};
    }
    if(k===key && resultReads++<2){if(resultReads===1)entered();if(resultReads===2)release();await barrier;return null;}
    return get(k);
  };
  const first=s.call('command',s.command({expected_epoch:9}));
  await firstRead;
  const replies=await Promise.all([first,s.call('command',s.command({expected_epoch:10}))]);
  assert.deepEqual(replies.map(r=>r.status),[202,202]);
  const retained=s.intent();
  const consumed={...retained,expected_epoch:retained.expected_epoch===9?10:9};
  const response=await s.call('result',{epoch,id:'request_1234',challenge,intent:consumed,
    result:{code:'verified',active:{...tuple,generation:8},operation_id:3}},'publisher');
  assert.equal(response.status,200);
  const out=(await(await s.call(`result/${epoch}/request_1234`)).json()).result;
  assert.equal(out.code,'unknown');assert.equal(out.active,null);assert.equal(out.operation_id,null);
});

test('missing, partial or altered consumed intent never proves success',async()=>{
  for(const mutation of [()=>null,command=>({...command,p:'0.2000'}),command=>({...command,created_at_ms:command.created_at_ms+1}),
    command=>{const v={...command};delete v.expires_at_ms;return v;}]) {
    const s=setup();await s.heartbeat();await s.call('command',s.command());
    await s.call('result',{epoch,id:'request_1234',challenge,intent:mutation(s.intent()),result:{code:'verified',active:{...tuple,generation:8}}},'publisher');
    const out=(await(await s.call(`result/${epoch}/request_1234`)).json()).result;
    assert.equal(out.code,'unknown');assert.equal(out.active,null);
  }
});

test('only same-origin explicit operator POSTs create commands; unknown fields and duplicate members are rejected',async()=>{
  const s=setup();await s.heartbeat();
  for(const extra of [{Origin:'https://evil.example'},{Origin:''},{'Sec-Fetch-Site':'cross-site'}])
    assert.equal((await s.call('command',s.command(),'operator',extra)).status,403);
  for(const change of [{action:'arm'},{path:'/api/arm'},{url:'http://127.0.0.1:8765/api/connection'}])
    assert.equal((await s.call('command',s.command(change))).status,400);
  const duplicate=JSON.stringify(s.command()).replace('"action":"set"','"action":"query","action":"set"');
  assert.equal((await s.call('command',duplicate)).status,400);
  assert.equal((await s.call('command','{"nested":{"x":1,"x":2}}')).status,400);
  assert.equal((await s.call('command','{"id":NaN}')).status,400);
  assert.equal((await s.call('command',s.command(),'operator',{'Content-Type':'text/plain'})).status,400);
  assert.equal((await s.call('command',s.command(),'operator',{'Content-Encoding':'gzip'})).status,400);
  assert.equal((await s.call('command',JSON.stringify({pad:'x'.repeat(2049)}))).status,413);
});

test('query parsing and malformed reports cannot access arbitrary bucket keys',async()=>{
  const s=setup();await s.heartbeat();
  assert.equal((await s.call(`poll?epoch=${epoch}&challenge=${challenge}&epoch=${epoch}`,undefined,'publisher')).status,400);
  assert.equal((await s.call(`poll?epoch=../secret&challenge=${challenge}`,undefined,'publisher')).status,400);
  assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,intent:null,result:{code:'verified',active:tuple}},'publisher')).status,409);
  assert.equal((await s.call('result',{epoch,id:'request_1234',challenge,result:{code:'armed'}},'publisher')).status,400);
  assert.equal((await s.call(`result/${epoch}/request_1234?token=bad`)).status,400);
  assert.deepEqual((await(await s.call(`result/${epoch}/unknown_1234`)).json()).result,null);
});

test('readback sanitizer rejects extra builds, non-finite ages and malformed or coerced fields',()=>{
  const s=setup();
  const v=sanitizeRemotePIStatus(s.status({active:{...tuple,age_ms:Infinity,private:'no'}}));
  assert.equal(v.active.age_ms,null);assert.equal(v.active.private,undefined);
  assert.equal(sanitizeRemotePIStatus(s.status({epoch:'9'})).can_query,false);
  assert.equal(sanitizeRemotePIStatus(s.status({active:{...tuple,generation:'7'}})).can_set,false);
  assert.equal(sanitizeRemotePIStatus(s.status({active:{...tuple,p_text:'1e-1'}})).active,null);
});
