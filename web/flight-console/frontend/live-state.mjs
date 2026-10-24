// Display timing is separate from the receiver's strict source-validity TTL.
export function liveState(data,{elapsedMs=0,requestRttMs=0}={}){
 const finite=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
 const share=data?.mode==='share';
 const freshLimit=share?5000:finite(data?.source_ttl_ms)?data.source_ttl_ms:1000;
 const linkLimit=share?10000:2000;
 const elapsed=finite(elapsedMs)?elapsedMs:Infinity;
 const rtt=finite(requestRttMs)?requestRttMs:Infinity;
 // Full request RTT is a conservative bound; no cross-machine wall-clock subtraction.
 const age=finite(data?.age_ms)?data.age_ms+elapsed+rtt:null;
 const sourceValid=typeof data?.source_valid==='boolean'?data.source_valid:data?.fresh===true;
 const timingValid=!share||data?.timing_valid===true;
 const connected=data?.connected===true&&elapsed+rtt<=linkLimit&&(age===null||age<=linkLimit);
 const fresh=connected&&sourceValid&&timingValid&&data?.fresh===true&&age!==null&&age<=freshLimit&&elapsed+rtt<=freshLimit;
 // Full RTT is an upper bound, not evidence that the snapshot has expired.
 // Keep recently received values visible with an explicit delay label while
 // that bound straddles the TTL; never promote them to fresh control data.
 const minimumAge=finite(data?.age_ms)?data.age_ms+elapsed:null;
 const recent=fresh||share&&connected&&sourceValid&&timingValid&&data?.fresh===true&&minimumAge!==null&&minimumAge<=freshLimit&&elapsed<=freshLimit;
 let kind=!data?'waiting':!connected?'disconnected':!sourceValid?'source_invalid':!timingValid?'timing_unknown':!recent?'expired':!fresh||share&&age>2500?'delayed':'live';
 return {age_ms:age,connected,fresh,recent,kind};
}
