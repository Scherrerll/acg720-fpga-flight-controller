// Presentation only: interpolate between received history points, never beyond
// the last point or through a source gap. Source validity is owned by live-state.
const fields=['roll_deg','pitch_deg','yaw_deg','height_m','speed_mps'];
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const angular=(a,b,f)=>a+(((b-a+180)%360+360)%360-180)*f;

export function createLivePlayback({delayMs=4000,maxGapMs=1600}={}){
 let points=[],cursor=null,lastTick=null,firmware=null,sequence=null,cutoff=-Infinity;
 function reset(){points=[];cursor=null;lastTick=null;firmware=null;sequence=null;cutoff=-Infinity;}
 function ingest(data,now){
  const valid=data?.connected===true&&data?.source_valid===true&&data?.fresh===true
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
   result[k]=f===0?a[k]:f===1?b[k]:finite(a[k])&&finite(b[k])?(k.endsWith('_deg')?angular(a[k],b[k],f):a[k]+(b[k]-a[k])*f):null;
  }
  return result;
 }
 return {ingest,sample,reset,history:()=>points.map(p=>({...p}))};
}
