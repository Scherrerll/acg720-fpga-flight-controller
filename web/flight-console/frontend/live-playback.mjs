// Presentation only: interpolate between received history points, never beyond
// the last point or through a source gap. Source validity is owned by live-state.
const fields=['roll_deg','pitch_deg','yaw_deg','height_m','speed_mps','roll_sp_deg','pitch_sp_deg','yaw_rate_dps','yaw_rate_sp_dps'];
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const angular=(a,b,f)=>a+(((b-a+180)%360+360)%360-180)*f;

export function createLivePlayback({delayMs=4000,maxGapMs=1600}={}){
 let points=[],cursor=null,lastTick=null,firmware=null,sequence=null,cutoff=-Infinity;
 function reset(){points=[];cursor=null;lastTick=null;firmware=null;sequence=null;cutoff=-Infinity;}
 function ingest(data,now){
  const valid=data?.connected===true&&data?.source_valid===true
   &&(data.mode!=='share'||data.timing_valid===true);
  if(!valid||!Array.isArray(data.history))return false;
  const incoming=data.history.filter(p=>p&&finite(p.t)).map(p=>Object.fromEntries(['t',...fields].map(k=>[k,finite(p[k])?p[k]:null]))).sort((a,b)=>a.t-b.t);
  if(!incoming.length)return false;
  const seq=finite(data.sequence)?data.sequence:null;
  const changed=firmware!==null&&firmware!==data.firmware;
  const restarted=sequence!==null&&seq!==null&&seq<sequence&&sequence-seq<32768;
  if(changed||restarted){points=[];cursor=null;cutoff=incoming.at(-1).t;}
  firmware=data.firmware;sequence=seq;
  const merged=new Map(points.map(p=>[p.t,p]));
  for(const p of incoming)if(p.t>=cutoff)merged.set(p.t,p);
  points=[...merged.values()].sort((a,b)=>a.t-b.t);
  // Retain the playback delay too, so a buffered 60-second plot can stay full.
  const oldest=points.at(-1).t-60000-delayMs;
  points=points.filter(p=>p.t>=oldest).slice(-256);
  const target=Math.max(points[0].t,points.at(-1).t-delayMs);
  if(cursor===null||cursor<points[0].t||points.at(-1).t-cursor>Math.max(12000,delayMs*3))cursor=target;
  if(lastTick===null)lastTick=now;
  return true;
 }
 function sample(now,{advance=true}={}){
  if(!points.length||cursor===null)return null;
  const delta=lastTick===null?0:Math.min(250,Math.max(0,now-lastTick));lastTick=now;
  const latest=points.at(-1).t,target=Math.max(points[0].t,latest-delayMs);
  const rate=cursor<target-1000?1.1:cursor>target+1000?.9:1;
  let next=advance?Math.min(latest,cursor+delta*rate):cursor;
  let upper=points.findIndex(p=>p.t>=next);
  if(upper<0)upper=points.length-1;
  let a=points[Math.max(0,upper-1)],b=points[upper];
  let gap=false;
  if(b.t-a.t>maxGapMs&&next>a.t&&next<b.t){
   gap=true;next=advance&&target>=b.t?b.t:a.t;
   if(next===b.t)a=b;else b=a;
  }
  cursor=next;
  const f=b.t===a.t?0:Math.max(0,Math.min(1,(cursor-a.t)/(b.t-a.t)));
  const result={t:cursor,buffering:cursor>=latest||gap,playing:advance&&cursor<latest&&!gap};
  for(const k of fields){
   result[k]=f===0?a[k]:f===1?b[k]:k.includes('_sp_')?a[k]:finite(a[k])&&finite(b[k])?(k.endsWith('_deg')?angular(a[k],b[k],f):a[k]+(b[k]-a[k])*f):null;
  }
  return result;
 }
 return {ingest,sample,reset,history:()=>points.map(p=>({...p}))};
}

// Latest real attitude is independent of the delayed chart playhead. Keep a
// complete roll/pitch pair together; missing values never replace it with zero.
export function createLivePose(){
 let rp=null,yaw=null,firmware=null,sequence=null,packet=0;
 const reset=()=>{rp=null;yaw=null;firmware=null;sequence=null;packet=0;};
 function ingest(data,now,rtt=0){
  packet++;
  const seq=finite(data?.sequence)?data.sequence:null;
  const build=typeof data?.firmware==='string'?data.firmware:null;
  if(build&&firmware&&build!==firmware||seq!==null&&sequence!==null&&seq<sequence&&sequence-seq<32768){rp=null;yaw=null;}
  if(build)firmware=build;
  if(seq!==null)sequence=seq;
  const qualified=data?.connected===true&&data?.source_valid===true&&data?.health?.imu!==false
   &&(data.mode!=='share'||data.timing_valid===true);
  if(!qualified)return false;
  const a=data.attitude||{},history=Array.isArray(data.history)?data.history:[];
  const stamp=(values,fromHistory=false,t=null)=>{
   const age=fromHistory&&finite(t)&&finite(data.server_response_time_ms)?Math.max(0,data.server_response_time_ms-t):finite(data.age_ms)&&data.age_ms>=0?data.age_ms:null;
   return {values,at:now,age:age===null?null:age+Math.max(0,rtt),packet,fromHistory};
  };
  if(finite(a.roll_deg)&&finite(a.pitch_deg))rp=stamp({roll_deg:a.roll_deg,pitch_deg:a.pitch_deg});
  else if(!rp){
   const previous=history.filter(p=>p&&finite(p.t)&&finite(p.roll_deg)&&finite(p.pitch_deg)).sort((a,b)=>b.t-a.t)[0];
   if(previous)rp=stamp({roll_deg:previous.roll_deg,pitch_deg:previous.pitch_deg},true,previous.t);
  }
  if(finite(a.yaw_deg))yaw=stamp({yaw_deg:a.yaw_deg});
  else if(!yaw){
   const previous=history.filter(p=>p&&finite(p.t)&&finite(p.yaw_deg)).sort((a,b)=>b.t-a.t)[0];
   if(previous)yaw=stamp({yaw_deg:previous.yaw_deg},true,previous.t);
  }
  return rp!==null;
 }
 function sample(now){
  if(!rp&&!yaw)return null;
  const parts=[rp,yaw].filter(Boolean),ages=parts.map(p=>p.age===null?null:p.age+Math.max(0,now-p.at));
  return {attitude:{...(rp?.values||{}),...(yaw?.values||{})},
   retained:parts.some(p=>p.packet!==packet||p.fromHistory),
   age_ms:ages.some(a=>a===null)?null:Math.max(...ages)};
 }
 return {ingest,sample,reset};
}
