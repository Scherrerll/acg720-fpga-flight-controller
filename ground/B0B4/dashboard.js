'use strict';
const $=id=>document.getElementById(id);
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const fmt=(v,n=1)=>finite(v)?v.toFixed(n):'—';
let latest=null;
function text(id,v){$(id).textContent=v}
function badge(id,label,kind=''){text(id,label);$(id).className='pill '+kind}
function health(id,ok,validLabel='有效'){text(id,ok?validLabel:'无有效数据');$(id).className=ok?'good-text':'warn-text'}
function numHTML(id,v,unit,n=1){$(id).replaceChildren(document.createTextNode(fmt(v,n)));if(finite(v)){const small=document.createElement('small');small.textContent=unit;$(id).append(small)}}
for(let i=0;i<4;i++){const div=document.createElement('div');div.className='motor';div.innerHTML=`<span>M${i+1} · ${['左前','右前','右后','左后'][i]}</span><strong id="motor-${i}">—</strong><div class="track"><i id="motor-bar-${i}"></i></div>`;$('motors').append(div)}
for(let i=0;i<8;i++){const div=document.createElement('div');div.className='channel';div.innerHTML=`<label>CH${i+1}<span>${['横滚','俯仰','油门','偏航','解锁','','模式',''][i]}</span></label><strong id="ch-${i}">—</strong><div class="track"><i id="ch-bar-${i}"></i></div>`;$('channels').append(div)}
function update(s){
 latest=s;const d=s.data||{},n=s.navigation||{},v=s.navigation_values||{},m=s.mtf_sensor||{},mv=s.mtf_values||{},r=s.recording||{},fresh=!!s.fresh,att=fresh&&d.attitude_valid,nf=fresh&&s.navigation_fresh,mf=fresh&&s.mtf_fresh;
 const valid=(value,ok=fresh)=>ok&&finite(value)?value:null;
 document.body.classList.toggle('degraded',!fresh);$('headline-dot').className='live-dot'+(fresh?' online':'');
 badge('connection',fresh?'● 实时连接':s.connected?'● 数据已过期':'● 连接断开',fresh?'good':'warn');
 text('source-label',`${s.source?.source||'—'} · ${s.source?.port||s.port||'—'} · ${s.source?.baud||'—'} baud`);
 text('build',s.flight_info_fresh&&finite(s.flight_info?.build_id)?'B'+s.flight_info.build_id.toString(16).toUpperCase().replace(/^B/,''):'未知');
 text('age',finite(s.frame_age_ms)?s.frame_age_ms<1000?fmt(s.frame_age_ms,0)+' ms':fmt(s.frame_age_ms/1000,1)+' s':'—');
 const recording=!r.closed&&!r.error&&!!r.session_id;
 text('record-label',r.error?'● 日志异常':recording?'● 自动记录中':'● 记录已停止');$('record-label').className='record-label '+(recording?'good-text':'bad-text');
 $('qualification').hidden=s.flight_ready===true;
 $('takeover-warning').hidden=!(fresh&&s.throttle_takeover_active);
 text('takeover-detail',finite(s.throttle_pickup_us)&&s.throttle_pickup_us>=1200?
  `当前保留总油门 ${s.throttle_pickup_us} μs；缓慢调整左杆至 CH3 约 ${Math.round(1100+(s.throttle_pickup_us-1200)*900/800)}，稳定匹配后接管。此时不再锁高度；SWA低档立即停机。`:
  '当前保留退出时总油门，等待手动匹配接管。此时不再锁高度；SWA低档立即停机。');
 text('attitude-state',att?'姿态有效':'等待有效姿态');
 for(const [id,key]of [['roll','roll_deg'],['pitch','pitch_deg'],['yaw','yaw_relative_deg']])text(id,att&&finite(d[key])?fmt(d[key],1)+'°':'—');
 badge('armed',fresh?d.armed?'已解锁':'未解锁':'状态未知',fresh?d.armed?'warn':'good':'');
 text('mode',fresh?d.mode_active||'—':'—');text('rc-state',fresh?d.rc_valid?'PPM 输入有效':'PPM 输入无效':'PPM 状态未知');text('controller',fresh?d.controller_enabled?'控制已启用':'控制待机':'控制状态未知');
 text('inhibit',fresh?d.inhibit_text||d.mode_inhibit_reason||'—':'遥测已过期，不能确认当前输出');
 for(let i=0;i<4;i++){let pwm=valid(d.pwm_us?.[i]);text('motor-'+i,fmt(pwm,0));$('motor-bar-'+i).style.width=finite(pwm)?Math.max(0,Math.min(100,(pwm-1000)/10))+'%':'0%'}
 numHTML('height',nf&&n.height_fusion_ready&&finite(v.nav_fused_height_mm)?v.nav_fused_height_mm/10:null,'cm');
 text('range',mf&&m.range_provisionally_valid?fmt(mv.mtf_range_cm,1)+' cm':'—');text('vz',nf&&n.height_fusion_ready?fmt(v.nav_fused_vz_mm_s,1)+' mm/s':'—');
 numHTML('vx',valid(v.nav_body_vx_mm_s,nf&&n.provisional_world_velocity_ready),'mm/s');numHTML('vy',valid(v.nav_body_vy_mm_s,nf&&n.provisional_world_velocity_ready),'mm/s');
 text('fusion-speed',nf&&n.velocity_fusion_ready?`控制融合速度（局部坐标）X ${fmt(v.nav_fused_vx_mm_s,1)} / Y ${fmt(v.nav_fused_vy_mm_s,1)} mm/s`:'控制融合速度 —');
 text('flow-status',mf&&m.flow_provisionally_valid?'光流数据有效 · 模块原厂尺度':'等待有效光流');
 if(n.ano_control){
 const fi=s.flight_info||{};
 text('xyz',!nf?'状态未知':n.xyz_active?'光流刹停 + 高度控制':n.xyz_requested?'光流模式已选择':'自稳 + 高度控制');
 text('xyz-detail',!nf?'等待有效导航状态':!d.armed?'尚未解锁；模式已选择':!fi.motor_prepared?'电机准备中':!fi.taking_off?'等待推杆起飞；中位不触发起飞':!n.height_fusion_ready?'高度参考无效':n.xyz_requested&&!n.xyz_ready?'光流暂不可用；查看原因码':'油门上推上升、中位悬停、下拉下降；SWA低档停机');
 }else{text('xyz',!nf?'状态未知':n.xyz_active?'XYZ 锁定中':n.xyz_requested?'请求已提交':'未启用');text('xyz-detail',!nf?'等待导航状态':n.xyz_active?'X / Y / 高度联合控制':n.xyz_ready?'导航数据就绪 · 控制未启用':'等待导航就绪');}
 text('target-height',nf&&finite(v.nav_target_height_mm)?fmt(v.nav_target_height_mm/10,1)+' cm':'—');
 health('imu-health',att&&d.sensor_ok);health('mtf-health',mf&&m.range_provisionally_valid&&m.flow_provisionally_valid);text('quality',mf?fmt(mv.mtf_quality,0):'—');text('nav-age',nf?fmt(v.nav_source_age_ms,0)+' ms':'—');
 for(let i=0;i<8;i++){const rc=valid(d.rc_us?.[i]);text('ch-'+i,fmt(rc,0));$('ch-bar-'+i).style.width=finite(rc)?Math.max(0,Math.min(100,(rc-1000)/10))+'%':'0%'}
 text('record-state',r.error?'记录异常：'+r.error:recording?'● 正在自动保存':'记录已停止');text('session',r.session_id||'—');text('record-size',finite(r.bytes)?fmt(r.bytes/1048576,1)+' MiB':'—');text('record-frames',finite(r.primary_frames)?r.primary_frames.toLocaleString():'—');text('record-missing',r.missing_primary_frames??'—');
 text('integrity',`主帧累计    ${s.stats?.frames??'—'}\n校验错误    ${s.stats?.checksum_errors??'—'}\n接收序号缺帧 ${s.stats?.missing_frames??'—'}\n日志队列    ${r.queue_depth??'—'}\n丢弃数据块  ${r.dropped_chunks??'—'}\n写入延迟P95 ${fmt(r.ingest_latency_p95_ms,2)} ms\n累计计数不代表此刻仍在丢帧。`);
 text('nav-diag',`导航帧有效    ${!!nf}\nXYZ 请求/就绪/启用 ${n.xyz_requested??'—'} / ${n.xyz_ready??'—'} / ${n.xyz_active??'—'}\n方向资格     ${n.mapping_verified?'已完成':'未完成'}\n转动补偿资格 ${n.rotation_verified?'已完成':'未完成'}\n控制原因码   ${n.reason??'—'}\n高度原因码   ${v.nav_z_reason??'—'}\n位置 X / Y  ${fmt(valid(v.nav_position_x_mm,nf),2)} / ${fmt(valid(v.nav_position_y_mm,nf),2)} mm\n位置来自速度积分，不是绝对位置。`);
 text('accel',`传感器轴（包含重力）\nX ${fmt(valid(d.sensor_accel_x_m_s2,fresh&&d.sensor_accel_valid),3)}  Y ${fmt(valid(d.sensor_accel_y_m_s2,fresh&&d.sensor_accel_valid),3)}  Z ${fmt(valid(d.sensor_accel_z_m_s2,fresh&&d.sensor_accel_valid),3)}\n相对世界轴（去重力）\nX ${fmt(valid(d.linear_accel_x_m_s2,fresh&&d.linear_accel_valid),3)}  Y ${fmt(valid(d.linear_accel_y_m_s2,fresh&&d.linear_accel_valid),3)}  Z ${fmt(valid(d.linear_accel_z_m_s2,fresh&&d.linear_accel_valid),3)}`);
 text('module-diag',`模块校验错误 ${m.checksum_errors??'—'}\nUART 错误   ${m.uart_errors??'—'}\n模块缺帧     ${m.module_missing??'—'}\n积分中断     ${m.integration_breaks??'—'}\n光流/测距状态 ${m.flow_status??'—'} / ${m.tof_status??'—'}\n模块 100 Hz 输入；网页为接收快照。\n完整 100 Hz 日志须独立专项采集。`);
 text('updated','更新于 '+new Date().toLocaleTimeString('zh-CN',{hour12:false}));drawHorizon(valid(d.roll_deg,att),valid(d.pitch_deg,att));drawTrend(fresh?s.history||[]:[]);
}
function setupCanvas(id){const c=$(id),rect=c.getBoundingClientRect(),dpr=window.devicePixelRatio||1;c.width=Math.round(rect.width*dpr);c.height=Math.round(rect.height*dpr);const ctx=c.getContext('2d');ctx.scale(dpr,dpr);return {ctx,w:rect.width,h:rect.height}}
function drawHorizon(roll,pitch){const {ctx,w,h}=setupCanvas('horizon');ctx.save();ctx.translate(w/2,h/2);if(!finite(roll)||!finite(pitch)){ctx.fillStyle='#202830';ctx.fillRect(-w,-h,w*2,h*2);ctx.fillStyle='#8b9cb1';ctx.font='12px system-ui';ctx.textAlign='center';ctx.fillText('等待有效姿态',0,4);ctx.restore();return}ctx.save();ctx.rotate(-roll*Math.PI/180);ctx.translate(0,pitch*3);ctx.fillStyle='#253c4b';ctx.fillRect(-w*3,-h*5,w*6,h*5);ctx.fillStyle='#3d3933';ctx.fillRect(-w*3,0,w*6,h*5);ctx.strokeStyle='#9cbaae';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(-w*3,0);ctx.lineTo(w*3,0);ctx.stroke();ctx.strokeStyle='#c9dbe0a0';ctx.fillStyle='#ccdde3a0';ctx.font='9px system-ui';ctx.textAlign='center';for(let p=-30;p<=30;p+=10){if(!p)continue;const y=-p*3;ctx.beginPath();ctx.moveTo(-25,y);ctx.lineTo(25,y);ctx.stroke();ctx.fillText(p,-37,y+3);ctx.fillText(p,37,y+3)}ctx.restore();ctx.strokeStyle='#e1e6ec';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-55,0);ctx.lineTo(-13,0);ctx.lineTo(0,9);ctx.lineTo(13,0);ctx.lineTo(55,0);ctx.stroke();ctx.strokeStyle='#a5bfcc80';ctx.lineWidth=1;ctx.beginPath();ctx.arc(0,0,Math.min(w,h)*.39,-Math.PI*.77,-Math.PI*.23);ctx.stroke();ctx.fillStyle='#cfdee8';ctx.beginPath();ctx.moveTo(-4,-h*.39);ctx.lineTo(4,-h*.39);ctx.lineTo(0,-h*.34);ctx.fill();ctx.restore()}
function drawTrend(history){const {ctx,w,h}=setupCanvas('trend'),keys=['roll_deg','pitch_deg','yaw_relative_deg'],colors=['#72abe2','#d3b77b','#b29dcd'];const end=history.at(-1)?.t,rows=finite(end)?history.filter(p=>p.t>=end-60):[];ctx.font='10px system-ui';ctx.fillStyle='#9aa6b3';if(!rows.length){ctx.fillText('等待连续遥测数据',12,h/2);return}const values=rows.flatMap(p=>keys.map(k=>p[k])).filter(finite);if(!values.length)return;let lo=Math.floor(Math.min(...values,-5)/10)*10,hi=Math.ceil(Math.max(...values,5)/10)*10;const left=38,right=w-9,top=13,bottom=h-25;const x=t=>left+(t-(end-60))/60*(right-left),y=v=>bottom-(v-lo)/(hi-lo)*(bottom-top);for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,Y=y(v);ctx.strokeStyle='#313840';ctx.beginPath();ctx.moveTo(left,Y);ctx.lineTo(right,Y);ctx.stroke();ctx.fillText(fmt(v,0)+'°',0,Y+3)}for(let i=0;i<=4;i++)ctx.fillText(i===4?'现在':`${60-i*15}s`,left+(right-left)*i/4-(i===4?20:0),h-5);keys.forEach((k,j)=>{ctx.strokeStyle=colors[j];ctx.lineWidth=1.6;ctx.beginPath();let previous=null;for(const p of rows){if(!finite(p[k])){previous=null;continue}if(!previous||p.t-previous.t>1||p.t<=previous.t||k==='yaw_relative_deg'&&Math.abs(p[k]-previous[k])>180)ctx.moveTo(x(p.t),y(p[k]));else ctx.lineTo(x(p.t),y(p[k]));previous=p}ctx.stroke()})}
async function poll(){try{const response=await fetch('/api/state',{cache:'no-store',signal:AbortSignal.timeout(2000)});if(!response.ok)throw new Error('HTTP '+response.status);update(await response.json())}catch(e){update({...latest,fresh:false,connected:false,navigation_fresh:false,mtf_fresh:false,flight_info_fresh:false});text('updated','服务连接中断 · 正在重试');text('record-label','● 记录状态未知');text('record-state','无法确认后台记录状态')}finally{setTimeout(poll,200)}}
$('snapshot').onclick=()=>{if(!latest)return;const blob=new Blob([JSON.stringify(latest,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='acg720-snapshot-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
window.addEventListener('resize',()=>{if(latest)update(latest)});poll();
