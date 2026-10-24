(()=>{
const box=document.createElement('section');box.hidden=true;
box.style.cssText='margin:16px;padding:16px;background:#132333;color:#e5f1ff;border:1px solid #3a5568;border-radius:10px;font:14px system-ui';
const title=document.createElement('h3');title.textContent='MTF-01P · 台架观察';
const note=document.createElement('p');note.textContent='模块坐标和状态码待实物确认；速度按水平面换算，未接入定高／定点控制。毫米输出不代表毫米精度。';
const values=document.createElement('pre');values.style.cssText='white-space:pre-wrap;line-height:1.7';
const navTitle=document.createElement('h4');navTitle.hidden=true;
const navNote=document.createElement('p');navNote.hidden=true;navNote.textContent='原厂测量比例保持不变。以下为临时机体／局部坐标估计，安装方向和转动补偿尚未验收；位置由速度积分得到。影子指令只用于观察，不驱动电机，当前不能确认定点可飞。';
const navValues=document.createElement('pre');navValues.hidden=true;navValues.style.cssText=values.style.cssText;
box.append(title,note,values,navTitle,navNote,navValues);document.body.prepend(box);
const legacyCards=['sensor-status','range-chart','flow-chart','range-diag-status'].map(id=>document.getElementById(id)?.closest('section')).filter(Boolean);
const legacyHealth=['health-range','health-flow'].map(id=>document.getElementById(id)?.closest('.diagnostic-item')).filter(Boolean);
const fmt=(v,n=2)=>Number.isFinite(v)?v.toFixed(n):'--';
async function refresh(){let timeout;try{
 const controller=new AbortController();timeout=setTimeout(()=>controller.abort(),500);
 const response=await fetch('/api/state',{cache:'no-store',signal:controller.signal});if(!response.ok)throw new Error('state unavailable');
 const s=await response.json(),m=s.mtf_sensor,v=s.mtf_values??{},n=s.navigation,nv=s.navigation_values??{};
 const observer=s.flight_info_fresh===true&&[0xb0a7,0xb0a8,0xb0a9,0xb0aa].includes(s.flight_info?.build_id);
 const experimental=s.flight_info_fresh===true&&[0xb0ab,0xb0ac,0xb0ad,0xb0ae,0xb0af].includes(s.flight_info?.build_id);
 for(const element of [...legacyCards,...legacyHealth])element.hidden=observer||experimental;
 box.hidden=!m&&!n;if(m){
  title.textContent=`${s.synthetic_preview?'【合成数据软件预览】 ':''}MTF-01P · ${s.mtf_fresh&&m.link_valid?'实时接收':'失效／等待'} · ${experimental?'XYZ控制候选／无停机锁':observer?'四路台架停机':'固件身份未确认'}`;
  note.textContent=experimental?'B0AB/B0AC实验控制路径已连接，实物安装和纠偏资格未完成，DO_NOT_PROGRAM；数值日志不能证明可以飞行。原厂测量比例保持不变。':observer?'模块坐标和状态码待实物确认；速度按水平面换算，当前是停机观察版，未接入物理定高／定点控制。毫米输出不代表毫米精度。':'身份未知／过期，不能确认当前停机锁或控制路径；以下仅保留最后帧诊断，失效测量不作为实时值显示。';
  values.textContent=`测距 ${fmt(v.mtf_range_cm,1)} cm　质量 ${v.mtf_quality??'--'}\n模块X速度 ${fmt(v.mtf_vx_mm_s)} mm/s　模块Y速度 ${fmt(v.mtf_vy_mm_s)} mm/s\n模块X累计 ${fmt(v.mtf_x_mm)} mm　模块Y累计 ${fmt(v.mtf_y_mm)} mm\n模块样本 ${m.sample_count}　源年龄 ${v.mtf_source_age_ms??'--'} ms　模块时间 ${m.module_time_ms??'--'} ms\n测距状态 ${m.tof_status??'--'}　光流状态 ${m.flow_status??'--'}（状态语义未验收）\n模块缺样 ${m.module_missing}　重复 ${m.module_duplicates}　重启／倒序 ${m.module_restarts}\nUART帧错 ${m.uart_errors}　校验错 ${m.checksum_errors}　长度错 ${m.length_errors}　断帧 ${m.packet_timeouts}\n积分中断 ${m.integration_breaks}　饱和 ${m.saturated?'是':'否'}\n模块100Hz输入，页面5Hz汇总；完整100Hz日志需独立有线采集。`;
  if(s.height_loss_fallback_active){title.textContent='MTF-01P · 测高失效，已降级自稳';note.textContent='油门由遥控杆接管；测距恢复不会自动重新定高。SWA低档立即停机。';}
 }else{title.textContent='MTF-01P · 等待传感器汇总';values.textContent='--';}
 for(const element of [navTitle,navNote,navValues])element.hidden=!n;
 if(n){
  const wired=n.version>=4;
  navTitle.textContent=`${wired?'B0AB/B0AC XYZ控制候选 · 实物资格未完成':n.version===3?'B0AA XYZ定点观察 · 定点含定高':n.version===2?'B0A9 水平定点观察 · 手动油门':'B0A8 导航观察'} · ${s.navigation_fresh&&n.module_link_fresh?'实时数据':'等待／失效'} · ${wired?'控制路径存在／未经飞行验收':'控制未启用'}`;
  navNote.textContent=wired?'高档同时锁定XYZ，低／中档手动自稳，没有独立定高档位。本版本指令已经连接控制核心，不是停机影子；安装方向、转动响应和实物纠偏未验收。实验候选DO_NOT_PROGRAM，当前不能确认可飞。':'原厂测量比例保持不变。以下为临时机体／局部坐标估计，安装方向和转动补偿尚未验收；位置由速度积分得到。影子指令只用于观察，不驱动电机，当前不能确认定点可飞。';
  const joint=n.version===5?`\n匿名光流速度控制；高度环在两档持续工作\n上推升高、中位悬停、下拉下降；SWA低档停机`:n.version>=3?`\nXYZ一起锁定、一起退出；没有独立定高档位\nXYZ请求／就绪／活动 ${s.navigation_fresh?[n.xyz_requested,n.xyz_ready,n.xyz_active].map(v=>v?'是':'否').join('／'):'--'}\n${wired?'控制':'影子'}总油门 ${fmt(nv.nav_z_collective_us,0)} μs　目标高度 ${fmt(nv.nav_target_height_mm,1)} mm\n最后帧Z原因 0x${n.z_reason.toString(16)}`:'';
  navValues.textContent=`${n.version===2?`测距几何高度 ${fmt(nv.nav_height_mm,1)} mm（用于光流尺度）；定高已停用，油门手动`:`垂直高度 ${fmt(nv.nav_height_mm,1)} mm　融合高度 ${fmt(nv.nav_fused_height_mm,1)} mm　垂直速度 ${fmt(nv.nav_fused_vz_mm_s)} mm/s`}\n机体前向 ${fmt(nv.nav_body_vx_mm_s)} mm/s　机体右向 ${fmt(nv.nav_body_vy_mm_s)} mm/s\n局部X速度 ${fmt(nv.nav_world_vx_mm_s)} mm/s　局部Y速度 ${fmt(nv.nav_world_vy_mm_s)} mm/s\n融合X速度 ${fmt(nv.nav_fused_vx_mm_s)} mm/s　融合Y速度 ${fmt(nv.nav_fused_vy_mm_s)} mm/s\n积分位置X ${fmt(nv.nav_position_x_mm)} mm　Y ${fmt(nv.nav_position_y_mm)} mm（无绝对参照）\n${wired?'控制':'影子'}横滚 ${fmt(nv.nav_shadow_roll_deg)}°　俯仰 ${fmt(nv.nav_shadow_pitch_deg)}°　油门增量 ${fmt(nv.nav_shadow_throttle_delta_us,0)} μs${joint}\n源年龄 ${nv.nav_source_age_ms??'--'} ms　方向验收：未完成　转动补偿验收：未完成\n以下诊断为最后收到帧：导航序号 ${n.navigation_sequence}　原因 0x${n.reason.toString(16)}　位置原因 0x${n.nav_position_reason.toString(16)}　就绪位 0x${n.flags.toString(16)}`;
 }
}catch(e){if(!box.hidden){title.textContent='MTF-01P · 网页连接中断';values.textContent='--';navTitle.textContent='导航观察 · 网页连接中断';navValues.textContent='--';}}finally{clearTimeout(timeout);setTimeout(refresh,200)}}refresh();
})();
