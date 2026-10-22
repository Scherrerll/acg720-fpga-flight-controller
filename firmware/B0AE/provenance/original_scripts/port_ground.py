from pathlib import Path
r=Path(__file__).resolve().parent/'ground'
def read(p):return p.read_text(encoding='utf8')
def save(p,s):p.write_text(s,encoding='utf8')
for name in ['nav_protocol.py','ground_server.py','launch.py','test_system.py']:
 p=r/name;save(p,read(p).replace('mtf01p.b0ad_review_fixes.v4','mtf01p.b0ae_ano_control.v5').replace('flight-console.20261019.v1','flight-console.20261021.ano.v1'))
p=r/'nav_protocol.py';s=read(p).replace('0xb0ad: 4}', '0xb0ad: 4, 0xb0ae: 5}').replace('0xb0ad: 2}', '0xb0ad: 2, 0xb0ae: 2}').replace('(0xb0ab,0xb0ac,0xb0ad)', '(0xb0ab,0xb0ac,0xb0ad,0xb0ae)').replace('(1, 2, 3, 4)', '(1, 2, 3, 4, 5)').replace("control = row['version'] == 4", "control = row['version'] in (4, 5)")
a=s.index('    elif any(tail):')
s=s[:a]+'''    elif row['version']==5:
        collective,z_reason,target=struct.unpack('>HHi',tail)
        row.update(z_collective_us=collective,z_reason=z_reason,target_height_mm=target)
        shadow=row['shadow_flags']
        if row['reason'] & (1<<17) or not row['reason'] & (1<<19):raise ValueError('A582 ANO height/qualification contract')
        if shadow & 0x20 and shadow & 0x3b != 0x3b:raise ValueError('A582 ANO XY requires Z-active and XY-ready/requested')
        if shadow & 0x10:
            if not shadow & 1 or not shadow & 4 or not 1000<=collective<=2000 or not -2000<=target<=7000:raise ValueError('A582 ANO Z active qualifications')
        elif any((collective,target,row['shadow_throttle_delta_us'])):raise ValueError('A582 ANO inactive Z command')
        if not shadow & 0x20 and any((row['shadow_roll_cdeg'],row['shadow_pitch_cdeg'])):raise ValueError('A582 ANO inactive XY commands')
''' +s[a:]
s=s.replace("(2, 3, 4) else None", "(2, 3, 4, 5) else None")
s=s.replace("xyz_requested=xyz and", "xyz_requested=(xyz or row['version']==5) and").replace("xyz_ready=xyz and bool(row['shadow_flags'] & 3)","xyz_ready=(xyz or row['version']==5) and (row['shadow_flags'] & 3)==3").replace("xyz_active=xyz and bool(row['shadow_flags'] & 0x30)","xyz_active=(xyz or row['version']==5) and (row['shadow_flags'] & 0x30)==0x30,\n               ano_control=row['version']==5,vertical_active=bool(row['shadow_flags'] & 0x10)")
# v5 display separates Z availability from optical-flow availability.
a=s.index('    return values',s.index('    commands_visible ='))
s=s[:a]+'''    if row.get('ano_control') and row.get('vertical_active') and row['height_fusion_ready']:
        values['nav_z_reason']=row['z_reason'];values['nav_z_collective_us']=row['z_collective_us'];values['nav_target_height_mm']=row['target_height_mm']
'''+s[a:]
save(p,s)
p=r/'protocol.py';s=read(p).replace("    else:raise ValueError('A580 version/build')", "    elif row['version']==3 and row['build_id']==0xb0ae:\n        if row['info_flags'] & ~15:raise ValueError('A580 ANO state flags')\n        row.update(throttle_takeover_active=False,sticky_yaw_fault=row.pop('reserved'),taking_off=bool(row['info_flags']&1),motor_prepared=bool(row['info_flags']&2),flying=bool(row['info_flags']&4),auto_takeoff=bool(row['info_flags']&8))\n    else:raise ValueError('A580 version/build')").replace('(0xb0ab,0xb0ac,0xb0ad)', '(0xb0ab,0xb0ac,0xb0ad,0xb0ae)').replace('observed==0xb0ad','observed in (0xb0ad,0xb0ae)');save(p,s)
p=r/'analysis.py';save(p,read(p).replace('(0xb0ab,0xb0ac,0xb0ad)', '(0xb0ab,0xb0ac,0xb0ad,0xb0ae)'))
p=r/'dashboard.js';s=read(p)
old="text('xyz',!nf?'状态未知':n.xyz_active?'XYZ 锁定中':n.xyz_requested?'请求已提交':'未启用');text('xyz-detail',!nf?'等待导航状态':n.xyz_active?'X / Y / 高度联合控制':n.xyz_ready?'导航数据就绪 · 控制未启用':'等待导航就绪');"
new="""if(n.ano_control){
 const fi=s.flight_info||{};
 text('xyz',!nf?'状态未知':n.xyz_active?'光流刹停 + 高度控制':n.xyz_requested?'光流模式已选择':'自稳 + 高度控制');
 text('xyz-detail',!nf?'等待有效导航状态':!d.armed?'尚未解锁；模式已选择':!fi.motor_prepared?'电机准备中':!fi.taking_off?'等待推杆起飞；中位不触发起飞':!n.height_fusion_ready?'高度参考无效':n.xyz_requested&&!n.xyz_ready?'光流暂不可用；查看原因码':'油门上推上升、中位悬停、下拉下降；SWA低档停机');
 }else{OLD}""".replace('OLD',old)
assert old in s;save(p,s.replace(old,new))
p=r/'mtf-ui.js';s=read(p).replace('const wired=n.version===4;', 'const wired=n.version>=4;');s=s.replace("const joint=n.version>=3?", "const joint=n.version===5?`\\n匿名光流速度控制；高度环在两档持续工作\\n上推升高、中位悬停、下拉下降；SWA低档停机`:n.version>=3?");save(p,s)
print('Isolated B0AE host updated; running service untouched')
