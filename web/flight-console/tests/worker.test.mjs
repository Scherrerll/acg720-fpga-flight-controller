import test from 'node:test';import assert from 'node:assert/strict';
import worker,{cleanLive,cleanLog,getAge,csv} from '../worker/flight.mjs';
class Bucket{data=new Map();async put(k,v,o={}){this.data.set(k,{v,customMetadata:o.customMetadata});}async get(k){const a=this.data.get(k);return a?{json:async()=>JSON.parse(a.v)}:null;}async delete(k){this.data.delete(k);}async list(){return {objects:[...this.data].filter(([k])=>k.startsWith('logs/')).map(([key,v])=>({key,customMetadata:v.customMetadata})),truncated:false};}}
const request=(path,o,token='')=>new Request('https://test.invalid'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Flight-Publish-Token':token},body:JSON.stringify(o)});
const snapshot=(overrides={},now=Date.now())=>({schema:1,connected:true,fresh:true,source_valid:true,firmware:'B0AC',source_ttl_ms:500,age_ms:20,timing_version:2,timing_valid:true,clock_uncertainty_ms:0,source_publish_at:new Date(now).toISOString(),...overrides});

test('reported tracking fields survive cloud live/history/log allowlists without exposing metadata',()=>{
 const now=1800000000000,tracking={roll_sp_deg:5,pitch_sp_deg:-4,yaw_rate_dps:1.5,yaw_rate_sp_dps:2,private:'secret'};
 const v=cleanLive(snapshot({firmware:'B0B0',tracking,history_reference_time_ms:now,history:[{t:now-500,...tracking}]},now),now);
 assert.equal(v.tracking.roll_sp_deg,5);assert.equal(v.tracking.private,undefined);
 assert.equal(v.history[0].yaw_rate_sp_dps,2);assert.equal(v.history[0].private,undefined);
 const log=cleanLog({id:'tracking_test_123',samples:[{t_s:0,...tracking},{t_s:1,roll_sp_deg:null,pitch_sp_deg:'invalid'}]});
 assert.equal(log.samples[0].pitch_sp_deg,-4);assert.equal(log.samples[1].pitch_sp_deg,null);
 assert.ok(log.columns.includes('yaw_rate_sp_dps'));assert.equal(log.samples[0].private,undefined);
});
test('anonymous visitors cannot publish or execute aircraft commands',async()=>{
 const env={PUBLISH_TOKEN:'a'.repeat(64),BUCKET:new Bucket()};
 assert.equal((await worker.fetch(request('/api/publish/live',{schema:1}),env)).status,401);
 for(const p of ['/api/arm','/api/calibration/apply','/api/connection','/api/service/stop'])assert.equal((await worker.fetch(request(p,{}),env)).status,405);
 assert.equal(env.BUCKET.data.size,0);
});
test('live allowlist, nullable values and expiry',()=>{
 const now=Date.now(),v=cleanLive(snapshot({source:{usb_device:'private'},port:'COM17',attitude:{roll_deg:2,pitch_deg:NaN},flags:{reason_text:'C:/private/file'}},now),now);
 assert.equal(v.attitude.pitch_deg,null);assert.equal(v.port,undefined);assert.equal(v.source,undefined);assert.equal(v.flags.reason_text,'');
 assert.equal(getAge(v,now+6000).fresh,false);assert.equal(getAge(v,now+6000).age_ms,6020);
 assert.equal(getAge(v,now+3000).fresh,true);
 assert.equal(getAge({...v,age_ms:4900},now+100).fresh,true);
 assert.equal(getAge({...v,age_ms:4900},now+200).fresh,false);
 assert.equal(cleanLive({schema:1,control_mode:'LOC_HOLD',flags:{requested:'LOC_HOLD'}}).flags.requested,'LOC_HOLD');
 assert.equal(cleanLive(snapshot({flags:{requested:'自稳',xy_active:false}})).flags.reason_text,'');
});
test('source validity is separate from local cache TTL and includes upload timing',()=>{
 const now=1800000000000;
 const v=cleanLive(snapshot({fresh:false,age_ms:510,source_publish_at:new Date(now-200).toISOString(),clock_uncertainty_ms:100},now),now);
 assert.equal(v.source_valid,true);assert.equal(v.age_ms,810);assert.equal(v.fresh,true);
 assert.equal(getAge(v,now+4200).fresh,false);
 for(const change of [{source_valid:false},{connected:false},{timing_valid:false},{clock_uncertainty_ms:null},{source_publish_at:new Date(now+5000).toISOString()},{age_ms:null}]){
  assert.equal(cleanLive(snapshot(change,now),now).fresh,false,JSON.stringify(change));
 }
 assert.equal(getAge(v,now+11000).connected,false);
});
test('clock-mapped history and public clock response do not require equal wall clocks',async()=>{
 const now=1800000000000,pc=now-35800;
 const v=cleanLive(snapshot({history_reference_time_ms:pc,history:[{t:pc-500,height_m:.21}]},now),now);
 assert.equal(v.history[0].t,now-500);
 const later=getAge(v,now+4000);assert.equal(later.server_response_time_ms,now+4000);assert.equal(Date.parse(later.received_at),now);assert.equal(later.server_response_time_ms-later.history[0].t,4500);
 const response=await worker.fetch(new Request('https://test.invalid/api/health'),{});
 const h=await response.json();assert.ok(Math.abs(Date.now()-h.server_time_ms)<2000);assert.equal(response.headers.get('Cache-Control'),'no-store');
});
test('publisher roundtrip, public CSV, explicit unshare',async()=>{
 const token='a'.repeat(64),env={PUBLISH_TOKEN:token,BUCKET:new Bucket()};
 assert.equal((await worker.fetch(request('/api/publish/live',snapshot(),token),env)).status,200);
 assert.equal((await(await worker.fetch(new Request('https://test.invalid/api/live'),env)).json()).firmware,'B0AC');
 const log={id:'20261022T000000Z_test',samples:[{t_s:0,roll_deg:1,private:'no'},{t_s:1,roll_deg:2}],summary:{frames:2,duration_s:1}};
 assert.equal((await worker.fetch(request('/api/publish/log',log,token),env)).status,200);
 assert.equal((await(await worker.fetch(new Request('https://test.invalid/api/logs'),env)).json()).logs.length,1);
 assert.equal(await(await worker.fetch(new Request('https://test.invalid/api/logs/'+log.id+'/download.csv'),env)).text(),'t_s,roll_deg\n0,1\n1,2\n');
 assert.equal((await worker.fetch(request('/api/publish/unshare',{id:log.id},token),env)).status,200);
 assert.equal((await(await worker.fetch(new Request('https://test.invalid/api/logs'),env)).json()).logs.length,0);
});
test('log validation and sampling provenance',()=>{
 assert.throws(()=>cleanLog({id:'../secrets',samples:[]}));assert.throws(()=>cleanLog({id:'good_log_1',samples:[{t_s:2},{t_s:1}]}));
 const l=cleanLog({id:'good_log_1',samples:[{t_s:0}],summary:{sampled:true,original_rows:100}});
 assert.equal(l.summary.sampled,true);assert.equal(l.summary.original_rows,100);assert.equal(l.summary.exported_rows,1);assert.equal(csv(l),'t_s\n0\n');
 const partial=cleanLog({id:'good_log_2',samples:[{t_s:0,armed:true},{t_s:1,armed:0}],summary:{downsampled:true,source_rows:25000,eligible_samples:22000,complete:false,source_complete:true}});
 assert.equal(partial.summary.sampled,true);assert.equal(partial.summary.complete,false);assert.equal(partial.summary.source_rows,25000);
 assert.equal(partial.samples[0].armed,1);assert.equal(partial.samples[1].armed,0);
});
