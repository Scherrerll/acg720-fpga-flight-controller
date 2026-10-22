// Synthetic log writes only. Reads current public live status; never replaces it.
// The initial empty-cloud fresh=false acceptance already passed before relay activation.
// No receiver connection; no real flight logs are read.
import {readFile} from 'node:fs/promises';
import {gzipSync} from 'node:zlib';
import assert from 'node:assert/strict';
const base=process.argv[2];
if(!['https://test.gmflylog.com','https://gmflylog.com'].includes(base))throw Error('Use exactly the approved HTTPS test or apex origin');
const token=(await readFile(new URL('../.edgeone/publish-token.txt',import.meta.url),'utf8')).trim();
const request=(path,options={})=>fetch(base+path,{...options,signal:AbortSignal.timeout(20000)});
const post=(path,value,{auth=true,gzip=false}={})=>request(path,{method:'POST',headers:{'Content-Type':'application/json',...auth?{'X-Flight-Publish-Token':token}:{},...gzip?{'Content-Encoding':'gzip'}:{}},body:gzip?gzipSync(JSON.stringify(value)):JSON.stringify(value)});
const health=await request('/api/health');assert.equal(health.status,200,'health');assert.equal((await health.json()).storage_ready,true);
assert.equal((await post('/api/publish/live',{}, {auth:false})).status,401,'anonymous publish');
const id='test_acceptance_20261022';
let primaryError;
try{
 const log={id,samples:[{t_s:0,roll_deg:1,height_m:0.2},{t_s:1,roll_deg:2,height_m:0.3}],summary:{frames:2,complete:true}};
 const published=await post('/api/publish/log',log,{gzip:true});
 assert.equal(published.status,200,'gzip publish: '+await published.text());
 const listed=await(await request('/api/logs')).json();assert.ok(listed.logs.some(v=>v.id===id),'log list');
 const saved=await(await request('/api/logs/'+id)).json();assert.equal(saved.log.samples.length,2,'sample count');
 const csv=await(await request('/api/logs/'+id+'/download.csv')).text();assert.equal(csv.trim().split('\n').length,3,'CSV rows');
 const live=await request('/api/live');assert.equal(live.status,200,'live');const snapshot=await live.json();
 assert.equal(snapshot.schema,1,'live schema');assert.equal(snapshot.mode,'share','public share mode');
 assert.equal(typeof snapshot.fresh,'boolean','fresh boolean');assert.equal(typeof snapshot.connected,'boolean','connected boolean');
 console.log(JSON.stringify({health:true,anonymous_rejected:true,gzip_log_publish:true,durable_read:true,list:true,csv:true,live_schema_and_freshness_contract:true}));
}catch(error){primaryError=error;throw error;}finally{
 try{
  const removed=await post('/api/publish/unshare',{id});assert.equal(removed.status,200,'cleanup: '+await removed.text());
  assert.equal((await request('/api/logs/'+id)).status,404,'removed test record');
  console.log(JSON.stringify({synthetic_log_cleaned:true}));
 }catch(error){if(primaryError)console.error('Synthetic cleanup also failed:',error.message);else throw error;}
}
