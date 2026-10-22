// Only the local publisher has write access. Public routes are read-only.
const ASSETS = globalThis.__FLIGHT_ASSETS__ || {};
const FIELDS=['t_s','roll_deg','pitch_deg','yaw_deg','height_m','vx_mps','vy_mps','vz_mps','speed_mps','m1_us','m2_us','m3_us','m4_us','throttle_us','armed'];
const ID=/^[A-Za-z0-9_-]{8,90}$/;
const SECURE={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow, noarchive','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'"};
const num=(v,lo=-1e12,hi=1e12)=>typeof v==='number'&&Number.isFinite(v)&&v>=lo&&v<=hi?v:null;
const bool=v=>typeof v==='boolean'?v:null;
const mode=v=>typeof v==='string'&&['ATT_STAB','LOC_HOLD','MANUAL','XYZ','ALT_HOLD','STABILIZE','DISARMED','自稳','定高','定点','未上报'].includes(v)?v:num(v,0,255);
const numbers=(o,keys)=>Object.fromEntries(keys.map(k=>[k,num(o?.[k])]));
const json=(o,status=200,headers={})=>new Response(JSON.stringify(o),{status,headers:{...SECURE,'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',...headers}});
const SHARE_FRESH_MS=5000,SHARE_DISCONNECT_MS=10000;
function cleanLive(v,now=Date.now()){
 if(!v||v.schema!==1)throw Error('schema');
 const firmware=typeof v.firmware==='string'&&/^B[0-9A-F]{3}$/i.test(v.firmware)?v.firmware.toUpperCase():null;
 const state={schema:1,mode:'share',connected:v.connected===true,fresh:false,
  age_ms:num(v.age_ms,0,1e10),received_at:new Date(now).toISOString(),source_publish_at:null,firmware,
  source_valid:v.source_valid===true&&firmware!==null,source_ttl_ms:num(v.source_ttl_ms,1,1000),
  timing_version:2,timing_valid:false,clock_uncertainty_ms:num(v.clock_uncertainty_ms,0,2000),
  fresh_timeout_ms:SHARE_FRESH_MS,disconnect_timeout_ms:SHARE_DISCONNECT_MS,
  sequence:num(v.sequence,0,Number.MAX_SAFE_INTEGER),armed:bool(v.armed),
  control_mode:mode(v.control_mode),
  attitude:numbers(v.attitude,['roll_deg','pitch_deg','yaw_deg']),
  motion:numbers(v.motion,['height_m','vx_mps','vy_mps','speed_mps','x_m','y_m','vz_mps']),
  rc:{valid:bool(v.rc?.valid),throttle_us:num(v.rc?.throttle_us,0,3000),channels:Array.isArray(v.rc?.channels)?v.rc.channels.slice(0,16).map(x=>num(x,0,3000)):[]},
  motors_us:Array.from({length:4},(_,i)=>num(v.motors_us?.[i],0,3000)),
  health:Object.fromEntries(['imu','flow','range','nav','rc'].map(k=>[k,bool(v.health?.[k])])),
  flags:{requested:mode(v.flags?.requested),xy_active:bool(v.flags?.xy_active),z_active:bool(v.flags?.z_active),reason_text:''},
  recording:{...numbers(v.recording,['frames','missing_frames','decode_errors','sequence_resets','bytes']),active:bool(v.recording?.active)},history:[]};
 const sourceTime=Date.parse(v.source_publish_at);
 const transit=now-sourceTime;
 state.timing_valid=v.timing_version===2&&v.timing_valid===true&&state.clock_uncertainty_ms!==null&&Number.isFinite(sourceTime)
  &&transit>=-state.clock_uncertainty_ms-100&&transit<=120000;
 if(state.timing_valid){
  state.source_publish_at=new Date(sourceTime).toISOString();
  if(state.age_ms!==null)state.age_ms+=Math.max(0,transit)+state.clock_uncertainty_ms;
 }else state.age_ms=null;
 state.fresh=state.source_valid&&state.connected&&state.timing_valid&&state.age_ms!==null&&state.age_ms<=SHARE_FRESH_MS;
 if(!state.source_valid)state.flags.reason_text='源遥测未更新或身份未确认';
 else if(!state.timing_valid)state.flags.reason_text='转发时间尚未确认';
 else if(!state.fresh)state.flags.reason_text='公开快照已过期';
 else if(['LOC_HOLD','XYZ','定点'].includes(state.flags.requested)&&!state.flags.xy_active)state.flags.reason_text='定点已请求，水平控制未启用';
 const historyReference=num(v.history_reference_time_ms,1,253402300799000);
 if(state.timing_valid&&historyReference!==null&&Array.isArray(v.history)){
  const offset=sourceTime-historyReference;
  state.history=v.history.slice(-120).map(p=>({...numbers(p,['roll_deg','pitch_deg','yaw_deg','height_m','speed_mps']),t:num(typeof p?.t==='number'?p.t+offset:null,0,now+state.clock_uncertainty_ms+100)})).filter(p=>p.t!==null);
 }
 return state;
}
function cleanLog(v){
 if(!v||!ID.test(v.id)||!Array.isArray(v.samples)||v.samples.length>20000)throw Error('log');
 const samples=v.samples.map(p=>({...numbers(p,FIELDS),armed:typeof p?.armed==='boolean'?Number(p.armed):num(p?.armed,0,1)}));
 for(let i=0;i<samples.length;i++)if(samples[i].t_s===null||samples[i].t_s<0||(i&&samples[i].t_s<samples[i-1].t_s))throw Error('time');
 return {id:v.id,title:v.id,created_at:new Date().toISOString(),columns:FIELDS.filter(k=>samples.some(p=>p[k]!==null)),samples,
  summary:{...numbers(v.summary,['duration_s','frames','missing_frames','sequence_resets','original_rows','source_rows','eligible_samples']),
   sampled:v.summary?.sampled===true||v.summary?.downsampled===true,downsampled:v.summary?.downsampled===true||v.summary?.sampled===true,
   complete:bool(v.summary?.complete),source_complete:bool(v.summary?.source_complete),exported_samples:samples.length,exported_rows:samples.length}};
}
const csv=log=>log.columns.join(',')+'\n'+log.samples.map(p=>log.columns.map(k=>p[k]===null?'':String(p[k])).join(',')).join('\n')+'\n';
function getAge(v,now=Date.now()){
 const elapsed=Math.max(0,now-Date.parse(v.received_at));
 const age=v.age_ms===null?null:v.age_ms+elapsed;
 return {...v,mode:'share',age_ms:age,server_response_time_ms:now,fresh_timeout_ms:SHARE_FRESH_MS,disconnect_timeout_ms:SHARE_DISCONNECT_MS,
  connected:v.connected===true&&Number.isFinite(elapsed)&&elapsed<=SHARE_DISCONNECT_MS&&(age===null||age<=SHARE_DISCONNECT_MS),
  fresh:v.source_valid===true&&v.timing_valid===true&&v.connected===true&&age!==null&&age<=SHARE_FRESH_MS&&Number.isFinite(elapsed)&&elapsed<=SHARE_FRESH_MS};
}
async function authorized(request,env){
 if(!env.PUBLISH_TOKEN||env.PUBLISH_TOKEN.length<32)return false;
 const hash=async s=>new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)));
 const [a,b]=await Promise.all([hash(request.headers.get('X-Flight-Publish-Token')||''),hash(env.PUBLISH_TOKEN)]);
 let d=0;for(let i=0;i<a.length;i++)d|=a[i]^b[i];return d===0;
}
async function body(request,limit=8*1024*1024){
 if(!request.headers.get('Content-Type')?.startsWith('application/json'))throw Error('type');
 const failSize=()=>Object.assign(Error('size'),{status:413});
 const readLimited=async(stream,max)=>{
  if(!stream)return new Uint8Array();
  const reader=stream.getReader(),chunks=[];let size=0;
  try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw failSize();}chunks.push(value);}}
  finally{reader.releaseLock();}
  const data=new Uint8Array(size);let offset=0;for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.byteLength;}return data;
 };
 const encodedLimit=Math.min(limit,5*1024*1024);
 if(Number(request.headers.get('Content-Length')||0)>encodedLimit)throw failSize();
 const encoding=(request.headers.get('Content-Encoding')||'identity').toLowerCase();
 if(!['identity','gzip'].includes(encoding))throw Error('encoding');
 let data=await readLimited(request.body,encodedLimit);
 if(encoding==='gzip')data=await readLimited(new Response(data).body.pipeThrough(new DecompressionStream('gzip')),limit);
 return JSON.parse(new TextDecoder().decode(data));
}
async function handle(request,env){
 const u=new URL(request.url),path=u.pathname;
 if(request.method==='GET'||request.method==='HEAD'){
  if(path==='/api/capabilities')return json({mode:'share',can_share_logs:false,share_url:u.origin});
  if(path==='/api/health')return json({ok:true,read_only:true,storage_ready:!!env.BUCKET,server_time_ms:Date.now()});
  if(path==='/api/live'){
   if(!env.BUCKET)return json({error:'storage_unavailable'},503);
   const o=await env.BUCKET.get('telemetry/latest.json');
   return json(o?getAge(await o.json()):{schema:1,mode:'share',connected:false,fresh:false,age_ms:null,history:[],firmware:null});
  }
  if(path==='/api/logs'){
   if(!env.BUCKET)return json({logs:[],local_controls:false});
   const r=await env.BUCKET.list({prefix:'logs/',limit:100,include:['customMetadata']});
   const logs=r.objects.map(o=>{const m=o.customMetadata||{};return {id:m.id,title:m.id,created_at:m.created_at,
    frames:m.frames?num(Number(m.frames),0):null,duration_s:m.duration_s?num(Number(m.duration_s),0):null,missing_frames:m.missing_frames?num(Number(m.missing_frames),0):null,shared:true};})
    .filter(o=>ID.test(o.id)).sort((a,b)=>(b.created_at||'').localeCompare(a.created_at||''));
   return json({logs,local_controls:false,truncated:r.truncated});
  }
  const m=/^\/api\/logs\/([A-Za-z0-9_-]{8,90})(\/download\.csv)?$/.exec(path);
  if(m){
   const o=env.BUCKET?await env.BUCKET.get('logs/'+m[1]+'.json'):null;if(!o)return json({error:'not_found'},404);
   const log=await o.json();
   return m[2]?new Response(csv(log),{headers:{...SECURE,'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="'+log.id+'.csv"','Cache-Control':'no-store'}}):json({log});
  }
  const name=path==='/'||path==='/logs'?'index.html':path==='/favicon.ico'?'gm-fly-mark.svg':path.slice(1);
  if(Object.hasOwn(ASSETS,name)){
   const asset=ASSETS[name],body=request.method==='HEAD'?null:asset.encoding==='base64'?Uint8Array.from(atob(asset.body),c=>c.charCodeAt(0)):asset.body;
   return new Response(body,{headers:{...SECURE,'Content-Type':asset.type,'Cache-Control':'no-cache'}});
  }
  return json({error:'not_found'},404);
 }
 if(request.method==='POST'&&path.startsWith('/api/publish/')){
  if(!await authorized(request,env))return json({error:'unauthorized'},401);
  if(!env.BUCKET)return json({error:'storage_unavailable'},503);
  try{
   if(path==='/api/publish/live'){
    const v=cleanLive(await body(request,150000));await env.BUCKET.put('telemetry/latest.json',JSON.stringify(v),{httpMetadata:{contentType:'application/json'}});return json({ok:true});
   }
   if(path==='/api/publish/log'){
    const v=cleanLog(await body(request));await env.BUCKET.put('logs/'+v.id+'.json',JSON.stringify(v),{httpMetadata:{contentType:'application/json'},customMetadata:{id:v.id,created_at:v.created_at,
     frames:String(v.summary.frames??''),duration_s:String(v.summary.duration_s??''),missing_frames:String(v.summary.missing_frames??'')}});return json({ok:true,id:v.id});
   }
   if(path==='/api/publish/unshare'){
    const v=await body(request,200);if(!ID.test(v.id))throw Error('id');await env.BUCKET.delete('logs/'+v.id+'.json');return json({ok:true});
   }
   return json({error:'not_found'},404);
  }catch(error){return json({error:error.status===413?'payload_too_large':'invalid_payload'},error.status===413?413:400);}
 }
 return json({error:'method_not_allowed'},405,{'Allow':'GET, HEAD'});
}
export {cleanLive,cleanLog,csv,getAge};
export default {async fetch(request,env){try{return await handle(request,env);}catch{return json({error:'temporarily_unavailable'},503);}}};
