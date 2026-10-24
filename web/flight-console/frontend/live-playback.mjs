// Presentation transitions only. Numeric values and chart samples always use
// the latest received data; no delayed playhead or predicted telemetry.
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const angular=(a,b,f)=>a+(((b-a+180)%360+360)%360-180)*f;

export function createLiveTween({durationMs=160,maxGapMs=10000,angularKeys=['roll_deg','yaw_deg']}={}){
 let from=null,target=null,started=0,updated=null;
 const reset=()=>{from=null;target=null;updated=null;};
 function sample(now){
  if(!target)return null;
  const f=Math.max(0,Math.min(1,(now-started)/durationMs));
  const eased=f*f*(3-2*f);
  return Object.fromEntries(Object.entries(target).map(([key,value])=>[key,
   f===1||!finite(value)||!finite(from?.[key])?value:
   angularKeys.includes(key)?angular(from[key],value,eased):from[key]+(value-from[key])*eased]));
 }
 function set(values,now,{snap=false}={}){
  if(!values){reset();return;}
  const current=sample(now),gap=updated===null||now-updated>maxGapMs;updated=now;
  if(target&&Object.keys(values).length===Object.keys(target).length&&Object.entries(values).every(([key,value])=>Object.is(value,target[key]))&&!snap)return;
  from=current;target={...values};started=now;
  if(snap||gap||!current)from={...target};
 }
 return {set,sample,reset};
}

// Latest real attitude is independent of presentation transitions. Keep a
// complete roll/pitch pair together; missing values never replace it with zero.
export function createLivePose(){
 let rp=null,yaw=null,firmware=null,sequence=null,packet=0,epoch=0;
 const reset=()=>{rp=null;yaw=null;firmware=null;sequence=null;packet=0;epoch++;};
 function ingest(data,now,rtt=0){
  packet++;
  const seq=finite(data?.sequence)?data.sequence:null;
  const build=typeof data?.firmware==='string'?data.firmware:null;
  if(build&&firmware&&build!==firmware||seq!==null&&sequence!==null&&seq<sequence&&sequence-seq<32768){rp=null;yaw=null;epoch++;}
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
  return {epoch,receivedAt:Math.max(...parts.map(p=>p.at)),attitude:{...(rp?.values||{}),...(yaw?.values||{})},
   retained:parts.some(p=>p.packet!==packet||p.fromHistory),
   age_ms:ages.some(a=>a===null)?null:Math.max(...ages)};
 }
 return {ingest,sample,reset};
}
