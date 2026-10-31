import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHandler} from '../cloud-functions/api/[[default]].js';

const token='test-only-not-a-real-credential-123456789';
function setup({enhanced=false,controlToken}={}){
 const data=new Map();
 const store={get:async k=>data.get(k)??null,set:async(k,v)=>data.set(k,v),delete:async k=>data.delete(k),list:async()=>({blobs:[...data.keys()].filter(k=>k.startsWith('logs/')).map(key=>({key}))})};
 const handler=createHandler({storeFactory:()=>store});
 return (path,options={})=>{
  const request=new Request('https://example.test'+path,options);
  // EdgeOne shadows Request.body with parsed data (or a pending Promise).
  // Throwing here proves that production parsing never accesses that getter.
  if(enhanced){
   Object.defineProperty(request,'body',{get(){throw Error('EdgeOne parsed body getter accessed');}});
   Object.defineProperty(request,'signal',{value:undefined,configurable:true});
  }
  return handler({request,env:{PUBLISH_TOKEN:token,CONTROL_TOKEN:controlToken}});
 };
}
const options=(body,{authorized=true,encoding='gzip'}={})=>({method:'POST',headers:{'Content-Type':'application/json','Content-Encoding':encoding,...authorized?{'X-Flight-Publish-Token':token}:{}},body:encoding==='gzip'?gzipSync(body):body});
test('cloud route preserves authentication and bounded gzip publication',async()=>{
 const request=setup();
 assert.equal((await request('/api/publish/log',options('invalid',{authorized:false}))).status,401);
 assert.equal((await request('/api/publish/log',options('invalid'))).status,400);
 assert.equal((await request('/api/publish/log',options(JSON.stringify({id:'log_123456',samples:[{t_s:0,roll_deg:2}]})))).status,200);
 assert.equal((await(await request('/api/logs')).json()).logs.length,1);
 assert.equal((await request('/api/publish/log',options(JSON.stringify({padding:'x'.repeat(8*1024*1024)})))).status,413);
 assert.equal((await request('/api/publish/log',options(Buffer.alloc(5*1024*1024+1),{encoding:'identity'}))).status,413);
});
test('large valid logs roundtrip compressed, with no silent truncation',async()=>{
 const request=setup();
 const fields=['roll_deg','pitch_deg','yaw_deg','height_m','vx_mps','vy_mps','vz_mps','speed_mps','m1_us','m2_us','m3_us','m4_us','throttle_us'];
 const samples=Array.from({length:20000},(_,t_s)=>({t_s,...Object.fromEntries(fields.map(k=>[k,999999999999])),armed:1}));
 const log=JSON.stringify({id:'large_log_123',samples});
 assert.ok(Buffer.byteLength(log)>5*1024*1024);
 assert.ok(Buffer.byteLength(log)<8*1024*1024);
 assert.equal((await request('/api/publish/log',options(log))).status,200);
 const response=await request('/api/logs/large_log_123',{headers:{'Accept-Encoding':'gzip'}});
 assert.equal(response.status,200);assert.equal(response.headers.get('Content-Encoding'),'gzip');
 const decoded=JSON.parse(gunzipSync(Buffer.from(await response.arrayBuffer())));
 assert.equal(decoded.log.samples.length,20000);
 assert.equal((await request('/api/logs/large_log_123',{headers:{'Accept-Encoding':'gzip;q=0'}})).status,413);
 assert.equal((await request('/api/logs/large_log_123',{method:'HEAD'})).body,null);
});
test('SDK construction failures return sanitized retryable status',async()=>{
 const handler=createHandler({storeFactory(){throw Error('private diagnostic');}});
 const response=await handler({request:new Request('https://example.test/api/live')});
 assert.equal(response.status,503);assert.deepEqual(await response.json(),{error:'temporarily_unavailable'});
});

test('EdgeOne adapter keeps control disabled by default and carries isolated control mail through BlobBucket',async()=>{
 const disabled=setup();
 assert.equal((await disabled('/api/remote-pi/status')).status,503);
 const controlToken='operator-only-adapter-fixture-123456789';
 const request=setup({enhanced:true,controlToken});
 const epoch='a'.repeat(32),challenge='b'.repeat(32);
 const publish=body=>({method:'POST',headers:{'Content-Type':'application/json','X-Flight-Publish-Token':token},body:JSON.stringify(body)});
 const status={enabled:true,connected:true,source:'SiK',baud:115200,epoch:9,
  supported:false,busy:false,can_query:true,can_set:false,active:null};
 assert.equal((await request('/api/remote-pi/heartbeat',publish({epoch,challenge,status}))).status,200);
 assert.equal((await request('/api/remote-pi/status',{headers:{'X-Flight-Control-Token':token}})).status,401);
 const headers={'X-Flight-Control-Token':controlToken};
 const snapshot=await(await request('/api/remote-pi/status',{headers})).json();
 assert.equal(snapshot.relay_fresh,true);
 const command={id:'adapter_query_123',epoch,challenge,action:'query',expected_epoch:9};
 assert.equal((await request('/api/remote-pi/command',{method:'POST',headers:{...headers,Origin:'https://example.test','Content-Type':'application/json'},body:JSON.stringify(command)})).status,202);
 const polled=await(await request(`/api/remote-pi/poll?epoch=${epoch}&challenge=${challenge}`,{headers:{'X-Flight-Publish-Token':token}})).json();
 assert.equal(polled.command.id,command.id);
 const active={p_text:'0.1000',i_text:'0.0350',generation:0,build:'0000B0B5',age_ms:0};
 assert.equal((await request('/api/remote-pi/result',publish({epoch,id:command.id,challenge,intent:polled.command,result:{code:'queried',active,operation_id:1}}))).status,200);
 const result=await(await request(`/api/remote-pi/result/${epoch}/${command.id}`,{headers})).json();
 assert.equal(result.result.code,'queried');
 assert.deepEqual((await(await request('/api/logs')).json()).logs,[]);
});

test('EdgeOne enhanced Requests preserve bounded identity and gzip write/delete',async()=>{
 const request=setup({enhanced:true});
 const health=await request('/api/health');
 assert.equal(health.status,200);
 assert.equal((await health.json()).storage_ready,true);
 for(const encoding of ['identity','gzip']){
  const id=`enhanced_${encoding}_123`;
  const body=JSON.stringify({id,samples:[{t_s:0,roll_deg:2}]});
  assert.equal((await request('/api/publish/log',options(body,{encoding}))).status,200);
  assert.equal((await request('/api/logs/'+id)).status,200);
  assert.equal((await request('/api/publish/unshare',options(JSON.stringify({id}),{encoding}))).status,200);
  assert.equal((await request('/api/logs/'+id)).status,404);
 }
 assert.equal((await request('/api/publish/log',options('invalid',{encoding:'identity'}))).status,400);
 assert.equal((await request('/api/publish/log',options('invalid',{authorized:false}))).status,401);
 assert.equal((await request('/api/publish/log',options(JSON.stringify({padding:'x'.repeat(8*1024*1024)})))).status,413);
 assert.equal((await request('/api/publish/log',options(Buffer.alloc(5*1024*1024+1),{encoding:'identity'}))).status,413);
 assert.equal((await request('/api/publish/live',options(JSON.stringify({padding:'x'.repeat(150001)})))).status,413);
 assert.equal((await request('/api/publish/unshare',options(JSON.stringify({padding:'x'.repeat(201)})))).status,413);
});
