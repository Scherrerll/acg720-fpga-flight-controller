// One in-flight request; hidden pages create no polling requests.
export function createLivePoller({poll, visible, connected, setTimer=setTimeout, clearTimer=clearTimeout}) {
  let timer=null, busy=false, immediate=false;
  const clear=()=>{if(timer!==null)clearTimer(timer);timer=null;};
  async function run(){
    clear();
    if(!visible())return;
    if(busy){immediate=true;return;}
    busy=true;
    try{await poll();}finally{
      busy=false;
      if(visible()){
        const delay=immediate?0:connected()?1000:10000;
        immediate=false;timer=setTimer(run,delay);
      }
    }
  }
  return {resume(){clear();if(visible())void run();},suspend(){clear();immediate=false;}};
}
