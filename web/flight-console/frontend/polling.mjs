// One in-flight request; hidden pages create no polling requests.
export function createLivePoller({poll, visible, connected, intervalMs=()=>1000, setTimer=setTimeout, clearTimer=clearTimeout, clock=()=>performance.now()}) {
  let timer=null, busy=false, immediate=false, failures=0;
  const clear=()=>{if(timer!==null)clearTimer(timer);timer=null;};
  async function run(){
    clear();
    if(!visible())return;
    if(busy){immediate=true;return;}
    busy=true;
    const started=clock();
    try{await poll();}finally{
      busy=false;
      if(visible()){
        const online=connected();
        failures=online?0:Math.min(failures+1,5);
        // Keep a one-second start cadence. Slow requests must not add another
        // idle second; brief outages retry before entering the ten-second cap.
        const period=Math.max(200,Math.min(10000,Number(intervalMs())||1000));
        const delay=immediate?0:online?Math.max(0,period-Math.max(0,clock()-started)):Math.min(10000,1000*2**(failures-1));
        immediate=false;timer=setTimer(run,delay);
      }
    }
  }
  return {resume(){clear();failures=0;if(visible())void run();},suspend(){clear();immediate=false;}};
}
