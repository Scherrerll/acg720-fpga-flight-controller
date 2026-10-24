(()=>{
const nav=document.createElement('div');
nav.style.cssText='position:sticky;top:0;z-index:40;background:#132333;color:#e5f1ff;padding:10px 18px;border-bottom:1px solid #3a5568;font:14px system-ui;display:flex;gap:18px;align-items:center;flex-wrap:wrap';
const link=document.createElement('a');link.href='/logs';link.textContent='数传设置 · 飞行日志 · 回放分析';link.style.color='#72e5df';
const text=document.createElement('span');nav.append(link,text);document.body.prepend(nav);
async function refresh(){try{const r=await fetch('/api/state',{cache:'no-store'}),s=await r.json(),v=s.recording;
text.textContent=`${s.source?.source??'--'} · ${s.source?.port??'--'} · ${s.fresh?'接收快照更新中':'数据失效/等待'} · 自动记录 ${v?.session_id??'--'} · ${v?.bytes??0} B${v?.error?' · '+v.error:''}`;
text.style.color=v?.error?'#ff8e8e':s.fresh?'#9be3b7':'#ffd17c';
}catch(e){text.textContent='日志服务连接中断：'+e.message}finally{setTimeout(refresh,1000)}}refresh();
})();
