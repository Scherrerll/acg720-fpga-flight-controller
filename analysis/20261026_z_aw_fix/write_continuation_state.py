"""Publish a current read-only build view without altering frozen handoff evidence."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8',errors='replace'))
bindings=read(O/'handoff_20261026/SOURCE_BINDINGS.json')
promotion=read(O/'PROMOTION.json') if (O/'PROMOTION.json').is_file() else None
qualification=read(R/'firmware/B0B4/qualification.json') if (R/'firmware/B0B4/qualification.json').is_file() else {}
installed=bool(qualification.get('installed_B0B4',False))
cold_boot=bool(qualification.get('true_cold_boot_verified',False))
hardware_started=bool(qualification.get('hardware_activity_started',False) or installed)
preserved={}
checked_roots={}
for tag,expected in bindings['source_sha256'].items():
    root=Path(promotion['initial_prototype_backup']) if promotion and tag=='B0B4_unpromoted_prototype' else Path(bindings['roots'][tag])
    checked_roots[tag]=str(root);preserved[tag]=all(sha(root/p)==v for p,v in expected.items())
runs=[]
for tag in ['v7','v8','v9','v4_p2_followup','v10','v4_p3r1_followup','v4_timing','v4_p3mf60_followup','v4_loc3_followup','v4_incplace_loc3_followup','v4_p1_followup','v4_partial_floorplan_followup','v4_data_routing_followup','v11','v12','v13','v13_map1','v13_native','v4_native','v4_clockbuf1_followup','v4_rep1_followup','v4_fan100_native','v14','v4_incplace_native','v15','v16','v17','v18','v18_dsp_followup','v19','v20','v20_dsp_followup','v21','v22','v22_dsp_followup','v22_fan100']:
    base=O/'build'/('compact_aw_'+tag)
    if not (base/'physical_snapshot.py').exists():continue
    result=subprocess.run([sys.executable,'-B',str(base/'physical_snapshot.py')],capture_output=True,text=True,check=True)
    for row in json.loads(result.stdout):
        physical_root='compact_aw_v4' if tag.startswith('v4_') and tag.endswith('_followup') else 'compact_aw_'+tag
        if tag in ['v18_dsp_followup','v20_dsp_followup','v22_dsp_followup']:physical_root='compact_aw_'+tag.split('_',1)[0]
        v=R/'out/z_aw_fix_20261026'/physical_root/row['profile']/'verification'
        row.update(variant=tag,started=(v/'physical_process.json').exists())
        review=base/row['profile']/'INDEPENDENT_RAW_REVIEW.json'
        row['independent_raw_passed']=bool(review.is_file() and read(review).get('passed'))
        if row['terminal']:
            row['status']='full_gate_pass' if row['full_gate_pass'] else row.get('failure_class','terminal_failure')
        else:row['status']='running' if row['started'] else 'not_started'
        if row['terminal'] and (v/'incremental_fallback_cancel.json').exists():
            row['status']='cancelled_incremental_fallback';row['failure_class']='cancelled_incremental_fallback'
            row['cancellation_receipt']=str(v/'incremental_fallback_cancel.json')
        if row['terminal'] and (v/'controlled_cancellation.json').exists():
            row['status']=read(v/'controlled_cancellation.json')['classification'];row['failure_class']=row['status']
            row['cancellation_receipt']=str(v/'controlled_cancellation.json')
        runs.append(row)
now=datetime.datetime.now(datetime.timezone.utc)
v9base=O/'build/compact_aw_v9';v9proof=v9base/'proofs_retry02'
v9five=read(v9proof/'five/results.json') if (v9proof/'five/results.json').exists() else {}
v9result=read(v9proof/'results.json') if (v9proof/'results.json').exists() else {}
v9exit=read(v9proof/'runner_exit.json') if (v9proof/'runner_exit.json').exists() else {}
v9={'scope':'v4 controller + exact four v8 guard files',
    'five_completed':v9five.get('completed',0),'full_proofs_passed':bool(v9result.get('passed')),
    'proof_runner_actual_wait':v9exit.get('actual_p_wait'),'proof_path':str(v9proof),
    'physical_started':any(r['variant']=='v9' and r['started'] for r in runs),
    'synthesis_runner_actual_wait':read(v9base/'runner_exit.json').get('actual_p_wait') if (v9base/'runner_exit.json').exists() else None}
v10base=O/'build/compact_aw_v10';v10proof=v10base/'proofs_retry02'
v10={'scope':'v9 plus Z diagnostic snapshot mask commutation only',
    'proofs_passed':read(v10proof/'results.json').get('passed') if (v10proof/'results.json').exists() else False,
    'proof_runner_actual_wait':read(v10proof/'runner_exit.json').get('actual_p_wait') if (v10proof/'runner_exit.json').exists() else None,
    'synthesis_runner_actual_wait':read(v10base/'runner_exit.json').get('actual_p_wait') if (v10base/'runner_exit.json').exists() else None,
    'physical_started':any(r['variant']=='v10' and r['started'] for r in runs)}
timing_base=O/'build/compact_aw_v4_timing'
timing={'scope':'Exact v4 source55; SYN opt_goal area to timing only;50MHz unchanged',
    'actual_runner_wait':read(timing_base/'runner_exit.json').get('actual_p_wait') if (timing_base/'runner_exit.json').exists() else None,
    'SYN_only_passed':read(timing_base/'SYNTHESIS_RESULT.json').get('passed_SYN_only') if (timing_base/'SYNTHESIS_RESULT.json').exists() else False,
    'physical_started':any(r['variant']=='v4_timing' and r['started'] for r in runs)}
data={'updated_utc':now.isoformat(),'updated_china':now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'repo':str(R),'offline_only':not hardware_started,'installed_B0B4':installed,'true_cold_boot_verified':cold_boot,'qualified_B0B4':any(r['full_gate_pass'] and r['independent_raw_passed'] for r in runs),
    'firmware_B0B4_source_unpromoted_prototype':not bool(promotion),'protected_source55_match':preserved,'protected_source55_locations_checked':checked_roots,
    'promoted_source55_match':({p:sha(R/'firmware/B0B4/source'/p) for p in promotion['source55_after']}==promotion['source55_after']) if promotion else None,
    'v8_hold_unchanged_from_v7':True,'v8_VG_sha256':'5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e',
    'v8_proofs_actual_runner_wait':read(O/'build/compact_aw_v8/proofs_completion02/runner_exit.json')['actual_p_wait'],
    'v8_synthesis_actual_runner_wait':read(O/'build/compact_aw_v8/runner_exit.json')['actual_p_wait'],
    'runs':runs,'v9':v9,'v10':v10,'v4_timing_goal':timing,'next':'Only genuine50MHz here; at most one own physical build, second slot belongs to isolated49MHz chat. Require actual terminal receipts and independent raw report gates.',
    'hardware_next':'Only after qualified offline package: fresh props-off and CH3/CH5/CH7 low/connection confirmation, SRAM ground readback, then Flash and true power cycle.',
    'git_next':'Submit/push qualified final code/docs/evidence; exclude unrelated B0B2 copy99 proof.zip. Do not publish a failed candidate as the release.'}
(O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
lines=['# B0B4 接续实时状态','',f"更新时间：中国时间 {data['updated_china']}",'',
    ('本地同仓库离线工作；B0B4尚未安装。' if not hardware_started else f'本轮已有硬件操作；B0B4安装标记={installed}，真冷启动验证={cold_boot}，具体以qualification.json及硬件收据为准。')+
    ('源码已按合格原始报告promote，初始原型55源保存在PROMOTION.json所列位置。' if promotion else 'firmware/B0B4/source仍未promote。')+'原handoff_20261026为冻结快照，接续已获用户确认。','',
    '| 候选 | 方案 | 状态 | 最后阶段 | vendor / runner真实wait |','|---|---|---|---|---|']
for row in runs:
    code=lambda x:'尚无回执' if x is None else str(x)
    lines.append(f"| {row['variant']} | {row['profile']} | {row['status']} | {row['last_stage'] or '未启动'} | {code(row['vendor_actual_p_wait'])} / {code(row['runner_actual_p_wait'])} |")
lines += ['',f"v9以曾完整布通的v4控制器配合同一份v8范围标志。五场景已完成{v9['five_completed']}/5，完整批次通过={v9['full_proofs_passed']}，proof root真实wait={v9['proof_runner_actual_wait']}，SYN runner真实wait={v9['synthesis_runner_actual_wait']}；物理实现已启动={v9['physical_started']}。首轮启动器自指文件名错误在仿真前退出1，原件保留，新retry02仅修正该路径。",'', 'v7五场景、边界、top13、四客户端和综合沿用已核验结果。v8在v7上只增加与az同拍发布的原范围谓词，控制器不变；生产者444003拍、融合3194862拍和top13通过，综合vendor/runner真实0，时钟/同步器/增益/18端口审计通过。资源FF27689/LUT36075，映射组合链缩短不代表物理时序通过。', '',
    'v8首次测试驱动因vvp附加finish提示而解析失败，原runner1保留；completion02复用真实已完成的exit0阶段，剩余验证及最终runner0均有原回执。详见[证明报告](build/compact_aw_v8/PROOF_REPORT.md)、[综合收据](build/compact_aw_v8/SYNTHESIS_RESULT.json)。', '',
    '下载前仍须重新确认当前拆桨和低位；先SRAM地面验证，再固化和真正断电读回默认值。低空掉高不在本轮处理；仿真时间不是实机着陆等待建议。', '',
    '机器状态和各尝试完整结果见[CONTINUATION_STATE.json](CONTINUATION_STATE.json)。原B3、v4～v7源55匹配归档。'+('尚未触及串口或下载器。' if not hardware_started else '本轮硬件操作以qualification.json及对应原始收据为准。')]
lines += ['',f"v10仅交换Z诊断mask与同拍快照顺序：两个复位模式各720位、160001拍及top13通过={v10['proofs_passed']}，proof真实wait={v10['proof_runner_actual_wait']}，SYN真实wait={v10['synthesis_runner_actual_wait']}，PNR已启动={v10['physical_started']}。首轮抽取夹具缺声明的compile4/root1保留，retry02补齐显式声明并禁用隐式网络；RTL未因夹具修正而改变。"]
lines += ['',f"v4相同55源的timing目标综合：SYN审计通过={timing['SYN_only_passed']}，root真实wait={timing['actual_runner_wait']}，PNR已启动={timing['physical_started']}。LUT+4666/FF+81/ALU+6；旧关键逻辑锥体19→16级、最大扇出115→118，仅映射拓扑而非STA。旧v4已布通报告Logic77%/CLS89%，全局路由资源占用满，较大映射有面积取舍。"]
v4proof=O/'build/v4_release_proofs/RESULT.json'
if v4proof.is_file():
    data['exact_v4_functional_proof_binding']=read(v4proof)
    lines += ['', '最终v4原始55源的13项顶层保护门新回执实际wait0；五场景、FRAC0/16边界与四客户端按六项完全相同依赖哈希复用v9真实通过记录。地面站53项Python及Node界面测试仅核对未变输入和原日志SHA，不重复测试，不连接硬件。见build/v4_release_proofs/RESULT.json。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v12base=O/'build/compact_aw_v12'
if (v12base/'PROOF_BINDING.json').is_file():
    proof12=read(v12base/'PROOF_BINDING.json');sx=read(v12base/'runner_exit.json') if (v12base/'runner_exit.json').is_file() else {}
    data['v12']={'scope':'v11 one-expression equivalent next-age comparison; retain full32bit counter','proofs_passed':proof12['passed'],'proof_actual_wait':proof12['actual_proof_runner_wait'],
        'predicate_integer_limits':9,'predicate_vectors':200040,'full_fusion_cases':8,'top13':proof12['top13'],'SYN_actual_runner_wait':sx.get('actual_p_wait')}
    lines += ['',f"v12只将自增分支比较等价改写为非零阈值下age<(AGE_LIMIT-32d1)，保留全32位年龄、原优先级及同拍撤销。九种integer阈值/200040向量、完整融合两模式/六边沿案例、top13和19阶段/root真实wait0；全部六刺激哈希冻结。SYN root实际wait={sx.get('actual_p_wait','尚无回执')}；综合资源详见该候选SYNTHESIS_RESULT，物理资格另按原始报告和独立复核验收。"]
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v13base=O/'build/compact_aw_v13'
if (v13base/'PROOF_BINDING.json').is_file():
    proof13=read(v13base/'PROOF_BINDING.json');sx=read(v13base/'runner_exit.json') if (v13base/'runner_exit.json').is_file() else {}
    data['v13']={'scope':'v12 plus same-edge MTF age<200/1000 predicates only','proofs_passed':proof13['passed'],
        'proof_actual_wait':proof13['actual_proof_runner_wait'],'inductive_vectors':105632,
        'UART':proof13['UART'],'top13':proof13['top13'],'SYN_actual_runner_wait':sx.get('actual_p_wait')}
    lines += ['',f"v13仅缓存MTF同拍age<200/1000谓词，原32位年龄/重复时间戳/接口与其余54文件不变。105632组抽取年龄转移、完整UART两模式各1200513拍和1140公开位、199/200与999/1000边沿/恢复、top13均通过，7阶段及root真实wait0。UART按1.152MHz加速毫秒老化，抽取转移独立于tick周期，全顶层仍50MHz；不预置完整reader内部状态。SYN root实际wait={sx.get('actual_p_wait','尚无回执')}；该段只报告功能/综合证据，物理资格见上表和独立raw复核。"]
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
map1base=O/'build/compact_aw_v13_map1'
if (map1base/'PREPARATION.json').is_file():
    mx=read(map1base/'runner_exit.json') if (map1base/'runner_exit.json').is_file() else {}
    data['v13_map1']={'scope':'Exact proven v13 source55; SYN map2 to map1 only, immutable source build.tcl unchanged',
        'SYN_started':(map1base/'runner_process.json').is_file(),'SYN_actual_runner_wait':mx.get('actual_p_wait'),
        'physical_started':any(r['variant']=='v13_map1' and r['started'] for r in runs)}
    lines += ['',f"v13同源map1对照仅在独立SYN Tcl把map2改为map1，其余源码/约束/参数不变；未宣称面积或速度更好。SYN root实际wait={mx.get('actual_p_wait','尚无回执')}；当前物理启动={data['v13_map1']['physical_started']}。"]
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
nativebase=O/'build/compact_aw_v13_native'
if (nativebase/'PREPARATION.json').is_file():
    data['v13_native']={'scope':'Identical proven v13 source55, original RTL project SYN/audit/PNR within one vendor process',
        'scripts_and_Tcl_preflight_passed':True,'physical_started':any(r['variant']=='v13_native' and r['started'] for r in runs),
        'standalone_SYN_p_wait_claimed':False,'gate_adaptation':str(nativebase/'GATE_ADAPTATION.json')}
    lines += ['',f"v13原生工程备选保留原RTL FileList，同一gw_sh先综合、执行真实网表审计，成功后才PNR。7脚本语法及Tcl结构/顺序预检通过，vendor已启动={data['v13_native']['physical_started']}。原helper字节不改；流程识别改查真实SYN/hook/原工程绑定，50MHz/20ns、五余量、端点、引脚/B4身份和真实退出门均保留。完整vendor进程只有一份真实wait，不补造单独SYN退出0；详见GATE_ADAPTATION。"]
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v4native=O/'build/compact_aw_v4_native'
if (v4native/'PREPARATION.json').is_file():
    data['v4_native']={'scope':'Exact frozen v4 source55 in native full RTL project flow; reference fullroute49.456MHz remains unqualified',
        'physical_started':any(r['variant']=='v4_native' and r['started'] for r in runs),'standalone_SYN_p_wait_claimed':False}
    lines += ['',f"v4原生流对照逐字节使用冻结v4源55（B3相对三文件），复用已绑定top13/控制器/地面站功能证明；参考旧完整布通49.456MHz仍不合格。本轮保留RTL工程先SYN审计再PNR，已启动={data['v4_native']['physical_started']}；不能将参考报告或GUI状态当作新的50MHz验收。"]
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v11base=O/'build/compact_aw_v11'
if (v11base/'PROOF_BINDING.json').is_file():
    proof11=read(v11base/'PROOF_BINDING.json');syn11=read(v11base/'SYNTHESIS_RESULT.json') if (v11base/'SYNTHESIS_RESULT.json').is_file() else {}
    data['v11']={'scope':'v9 plus same-edge publication-age predicate only','proofs_passed':proof11['passed'],'proof_actual_wait':proof11['actual_proof_runner_wait'],
        'ordinary_cases':2,'expiry_cases':6,'top13':proof11['top13'],'SYN_vendor_wait':syn11.get('vendor_actual_wait'),'SYN_runner_wait':syn11.get('runner_actual_wait'),'VG_sha256':syn11.get('netlist_sha256')}
    lines += ['', 'v11仅在v9高度融合内缓存同拍age<AGE_LIMIT谓词。完整融合两模式及六组AGE=1/31/65536超时边沿、top13真实wait0；普通+边沿共4067304拍。一次新SYN和clock/radio/gain/18ports审计真实0，VG f239c61b…，相对v9实测+7FF/+789LUT/+3ALU；不以源码新增一位推算映射资源。空综合启动与Windows封装修正记录保留，正式SYN retry02成功。物理门另验。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
fan100base=O/'build/compact_aw_v4_fan100_native'
if (fan100base/'PREPARATION.json').is_file():
    syn100=R/'out/z_aw_fix_20261026/compact_aw_v4_fan100_native/physical_p3r0_01/verification/native_synthesis_audit.json'
    data['v4_option_trials']={'scope':'Exact proven v4 source55; two separate option-only trials, no mixed options',
        'PNR_replication1_started':any(r['variant']=='v4_rep1_followup' and r['started'] for r in runs),
        'SYN_max_fanout100_started':any(r['variant']=='v4_fan100_native' and r['started'] for r in runs),
        'max100_actual_SYN_audit_passed':read(syn100)['passed'] if syn100.is_file() else False,
        'max100_netlist_sha256':read(syn100)['netlist_sha256'] if syn100.is_file() else None,
        'standalone_SYN_p_wait_claimed':False}
    lines += ['', 'v4两条独立选项对照：一条在同一冻结VG上仅启用PNR高扇出资源复制；另一条同源原生工程仅将实际SYN max_fanout200降为100，源码build.tcl保持原字节。max100实际审计通过='+str(data['v4_option_trials']['max100_actual_SYN_audit_passed'])+'，不补造单独SYN wait。实际网表比较见build/compact_aw_v4_fan100_native/MAPPED_FANOUT_COMPARISON.json：原fallback控制115个负载拆为58/57，实际+81FF/+83LUT，仍不能代替新STA。首次启动器缺空报告目录未创建vendor进程；补齐目录后retry02真实启动，见PRESTART_CORRECTION.json。']
    restore=O/'build/compact_aw_v4_native/GUI_CACHE_RESTORATION.json'
    if restore.is_file():
        data['v4_native_GUI_view']={'restoration_sha256':sha(restore),'record':str(restore),
            'all_original_artifact_bytes_restored':read(restore)['all_98_original_artifact_bytes_restored']}
        lines += ['', 'v4原生失败工程已由官方FloorPlanner读取，当前器件回标对话框未提供普通FF/LUT全布局导出。未执行回标、GUI构建或硬件操作。GUI自动改写的UI配置及device.cfg已先独立保存，再从已校验的查看前备份逐字节恢复；全部98文件重核一致，原失败收据仍保留。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v14base=O/'build/compact_aw_v14'
if (v14base/'PROOF_BINDING.json').is_file():
    q14=read(v14base/'PROOF_BINDING.json');r14=read(v14base/'runner_exit.json') if (v14base/'runner_exit.json').is_file() else {}
    data['v14']={'scope':'v4 plus two local synthesis fanout hints and a combinational identity wire alias; no clock/state/cycle/control equation changes',
        'source_files':55,'B3_relative_changed_files':5,'new_exact_top13_passed':q14['top13']['passed'],
        'actual_top13_root_wait':q14['actual_proof_runner_wait'],'SYN_started':(v14base/'runner_process.json').is_file(),
        'SYN_actual_runner_wait':r14.get('actual_p_wait'),'PNR_started':any(r['variant']=='v14' and r['started'] for r in runs)}
    lines += ['', 'v14从冻结v4仅给previous_pose_valid数据reg设置局部syn_maxfan10，并对fallback原active组合表达式经普通wire同值连接设置syn_maxfan50；没有新状态/时钟或周期。两文件的精确反向文本核对通过，fallback CRLF→LF单独披露；新完整顶层原13项刺激字节一致，compile/vvp/root实际0，六控制依赖及地面站43输入重核不变。SYN已启动='+str(data['v14']['SYN_started'])+'、root实际wait='+str(r14.get('actual_p_wait'))+'；实际是否复制需新网表审计，不预先宣称生效或时序通过。五份B3相对改动及全55重建哈希已保存在implementation_history/v14_local_fanout。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
steering49=O/'USER_STEERING_20261027_49MHZ_FALLBACK.json'
if steering49.is_file():
    clock49=O/'build/clock49_generate';adapter49=O/'build/clock49_time_adapter'
    model49=clock49/'simulation/RESULT.json';unit49=adapter49/'proofs/RESULT.json'
    data['clock49_fallback']={'authorization_record':str(steering49),'authorization_sha256':sha(steering49),
        'preferred_functional_clock_Hz':50000000,'conditionally_authorized_fallback_Hz':49000000,
        'official_PLLA_IP_generated':(clock49/'REFERENCE_IP_MANIFEST.json').is_file(),
        'isolated_PLL_model_passed':read(model49)['passed'] if model49.is_file() else False,
        'tick_to_us_unit_passed':read(unit49)['passed'] if unit49.is_file() else False,
        'full_flight_controller_clock_changed':False,'working_source_is_incomplete':True,
        'current50MHz_gates_unchanged':True,'fallback_hardware_qualified':False,
        'implementation_review_pending':str(clock49/'IMPLEMENTATION_REVIEW_PENDING.json')}
    lines += ['', '用户2026-10-27新指示：继续直到成功；50MHz确实困难时允许考虑约49MHz实际降频后备。该指示不是拆桨/低位等当前实体状态确认。当前v14 P3/P2仍按完整50MHz/20ns门运行，不能把旧49.456MHz失败改称50MHz通过。']
    lines += ['', '后备前置验证：厂商PLL_ADV已为GW5AT-60B生成50→49MHz的PLLA+PLL_INIT，phase0/无SSC，三份RTL及IPC原样归档；独立未修改厂商模型锁定后49000周期约1ms，compile/vvp实际0。隔离clock49_working目录仅开始tick→us转换器单元适配：默认50与旧模块139公开位/除法状态逐拍一致，49除数及余数进位12000事务/57取消/47忙时重入、409173拍真实0。完整飞控时钟、其余时基和地面站均未改；该工作源不允许全机构建或下载。见build/clock49_generate/IMPLEMENTATION_REVIEW_PENDING.json及build/clock49_time_adapter/SOURCE_BINDING.json。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for candidate in ['v15','v16','v17']:
    base=O/'build'/('compact_aw_'+candidate)
    if not (base/'PROOF_BINDING.json').is_file():continue
    proof=read(base/'PROOF_BINDING.json')
    syn=read(base/'SYNTHESIS_RESULT.json') if (base/'SYNTHESIS_RESULT.json').is_file() else {}
    data[candidate]={'scope':'Combinational pre-mux landing threshold' + (' plus active-driver syn_maxfan50 and previous_pose_valid syn_maxfan10' if candidate=='v17' else ' plus one local data-driver syn_maxfan50' if candidate=='v16' else ''),
        'source55':proof['source55'],'proofs_passed':proof['passed'],'new_top13_cases':13,
        'flight_state_miter':proof['flight_state_miter'],'new_state_or_cycle':False,
        'SYN_only_passed':syn.get('passed_SYN_only'),'VG_sha256':syn.get('netlist_sha256'),
        'physical_started':any(r['variant']==candidate and r['started'] for r in runs)}
    lines += ['',candidate+'把油门<1250比较放到数值分支之后、晚到的availability选择之前，不增加状态/周期；'+('额外限制active组合驱动扇出50和previous_pose_valid数据reg扇出10。' if candidate=='v17' else '仅额外限制实际187负载组合数据驱动扇出50。' if candidate=='v16' else '')+'完整旧/新/default飞行状态在TICKS_PER_MS=1/3/7逐拍比较，2097152阈值向量、100000随机转换、自然起飞/着陆/撤销、实际fallback关系与原top13通过。首轮v15夹具compile3保留，retry02仅改保留字标识符和初始化声明；RTL未因夹具修正改变。SYN通过='+str(syn.get('passed_SYN_only'))+'，物理另验。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for candidate,predicate,binding_name in [('v18','input velocity range','VY_BINDING.json'),('v19','AZ range','GUARD_REUSE_RECHECK.json')]:
    base=O/'build'/('compact_aw_'+candidate)
    if not (base/'PROOF_BINDING.json').is_file():continue
    proof=read(base/'PROOF_BINDING.json')
    syn=read(base/'SYNTHESIS_RESULT.json') if (base/'SYNTHESIS_RESULT.json').is_file() else {}
    data[candidate]={'scope':'v17 plus same-publication '+predicate+' predicate',
        'source55':proof['source55'],'proofs_passed':proof['passed'],'top13':proof['top13'],
        'flight_state_miter':proof['flight_state_miter'],'new_private_predicate_bits':1,'old_public_cycle_changes':0,
        'component_binding':str(base/binding_name),'component_binding_sha256':sha(base/binding_name),
        'SYN_only_passed':syn.get('passed_SYN_only'),'VG_sha256':syn.get('netlist_sha256'),
        'physical_started':any(r['variant']==candidate and r['started'] for r in runs)}
    lines += ['',candidate+'在v17基础上缓存与原数据同拍发布的'+predicate+'谓词，真实新增一个私有状态位，原公开周期不变。组件证明、完整飞行状态比较及原top13均有实际成功回执；控制器及地面站相同依赖按哈希复用。SYN通过='+str(syn.get('passed_SYN_only'))+'；组合级数减少不能代替物理验收。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for candidate,scope in [('v20','Combined same-publication AZ and input-velocity predicates'),('v21','Exact v18 with extension-only same-edge snapshot moved to vendor SP'),('v22','Exact v20 arithmetic with one local logic-multiplier synthesis hint and same-value wire')]:
    base=O/'build'/('compact_aw_'+candidate)
    if not (base/'source_freeze.json').is_file():continue
    freeze=read(base/'source_freeze.json');expected=freeze['source55']
    root=R/'out/z_aw_fix_20261026'/('compact_aw_'+candidate)/'canonical/source'
    assert len(expected)==55 and {n:sha(root/n) for n in expected}==expected
    proof=read(base/'PROOF_BINDING.json') if (base/'PROOF_BINDING.json').is_file() else {}
    syn=read(base/'SYNTHESIS_RESULT.json') if (base/'SYNTHESIS_RESULT.json').is_file() else {}
    sx=read(base/'runner_exit.json') if (base/'runner_exit.json').is_file() else {}
    data[candidate]={'scope':scope,'source55':expected,'frozen_source55_rechecked':True,
        'functional_proof_binding_present':bool(proof),'functional_proofs_passed':proof.get('passed',False),
        'SYN_preparation_present':(base/'SYNTHESIS_PREPARATION.json').is_file(),
        'SYN_started':(base/'runner_process.json').is_file(),'SYN_actual_runner_wait':sx.get('actual_p_wait'),
        'SYN_only_passed':syn.get('passed_SYN_only',False),'VG_sha256':syn.get('netlist_sha256'),
        'physical_started':any(r['variant']==candidate and r['started'] for r in runs),
        'new_private_predicate_bits_relative_v4':1 if candidate=='v21' else 2,'legacy_public_output_cycle_change':0}
    completion=base/'audit_retry02/completion_result.json'
    if candidate=='v21' and completion.is_file():
        recovered=read(completion)
        data[candidate]['post_SYN_audit_completion']={'passed':recovered.get('passed_audit_completion',False),
            'result_path':str(completion),'result_sha256':sha(completion),
            'original_vendor_wait':recovered['original_vendor_actual_wait'],
            'original_audit_wait':recovered['original_audit_actual_wait'],'original_runner_wait':recovered['original_runner_actual_wait'],
            'new_successful_audit_wait':recovered['successful_audit_wait'],'new_actual_completion_root_wait':recovered['actual_completion_root_wait'],
            'SYN_rerun':recovered['SYN_rerun']}
    lines += ['',candidate+'：'+scope+'；完整源55已核对，功能证据通过='+str(data[candidate]['functional_proofs_passed'])+'，SYN真实runner wait='+str(sx.get('actual_p_wait'))+'，物理资格须单独测量。新完整候选不能冒充任一父版本的完整55文件证明。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
dspbase=O/'build/compact_aw_v18_dsp_followup'
if (dspbase/'PHYSICAL_PREPARATION.json').is_file():
    prep=read(dspbase/'PHYSICAL_PREPARATION.json')
    data['v18_dsp_followup']={'scope':'Exact v18 source55/VG with 44 DSP + 2 BSRAM official compatible locations appended to full original CST prefix',
        'preparation_sha256':sha(dspbase/'PHYSICAL_PREPARATION.json'),'profile':prep['profile'],
        'source_and_functional_evidence_origin':'compact_aw_v18','old_public_cycle_changes':0,
        'physical_started':any(r['variant']=='v18_dsp_followup' and r['started'] for r in runs)}
    lines += ['', 'v18 DSP/BSRAM物理对照复用完全相同的v18源55、功能证明和综合VG。官方FloorPlanner从隔离原生工程导出的52条位置约束中，仅保留与该VG实例及类型匹配的44 DSP和2 BSRAM；完整原CST前缀逐字节保留，combined CST另存并被physical.gprj实际选用。cst_warn_to_error=1；50MHz/20ns及原完整物理门不变。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for candidate in ['v20','v22']:
    dspbase=O/'build'/('compact_aw_'+candidate+'_dsp_followup')
    if not (dspbase/'PHYSICAL_PREPARATION.json').is_file():continue
    prep=read(dspbase/'PHYSICAL_PREPARATION.json')
    tag=candidate+'_dsp_followup'
    data[tag]={'scope':'Exact standard '+candidate+' source/proof/SYN with official type/name-compatible DSP/BSRAM locations appended to the complete original CST prefix',
        'preparation_sha256':sha(dspbase/'PHYSICAL_PREPARATION.json'),'profile':prep['profile'],
        'source_and_functional_evidence_origin':'compact_aw_'+candidate,'measured_counts':prep['measured_counts'],
        'physical_started':any(r['variant']==tag and r['started'] for r in runs)}
    lines += ['',tag+'：薄层仅增加匹配实际VG的官方位置约束，测得数量='+str(prep['measured_counts'])+'；源55、功能和SYN证明均来自standard '+candidate+'，不能冒充新的同源功能测试。原CST完整前缀和50MHz门保持。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
fanbase=O/'build/compact_aw_v22_fan100'
if (fanbase/'SYNTHESIS_RESULT.json').is_file():
    syn=read(fanbase/'SYNTHESIS_RESULT.json');sx=read(fanbase/'runner_exit.json')
    parent=O/'build/compact_aw_v22';expected=read(parent/'source_freeze.json')['source55']
    source=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
    assert syn['source55']==expected and {n:sha(source/n) for n in expected}==expected
    data['v22_fan100']={'scope':'Exact standard v22 source55 and functional proof; effective SYN max_fanout 200 to 100 only',
        'source_and_functional_evidence_origin':'compact_aw_v22','SYN_only_passed':syn['passed_SYN_only'],
        'VG_sha256':syn['netlist_sha256'],'actual_vendor_wait':syn['vendor_actual_wait'],
        'actual_audit_wait':syn['audit_actual_wait'],'actual_runner_wait':sx['actual_p_wait'],
        'source_build_tcl_unchanged':syn['source_build_tcl_unchanged'],'effective_option_delta':syn['effective_option_delta'],
        'physical_started':any(r['variant']=='v22_fan100' and r['started'] for r in runs)}
    lines += ['', 'v22_fan100复用完整相同的standard v22源55与功能证明，仅执行用综合max_fanout从200改为100；source/build.tcl仍保持原件。实际SYN/vendor、audit、runner均0，译码节点最大负载174降到100，FF和LUT各增加83。该测量不代表布线或50MHz时序通过。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
coordination=O/'SEPARATE_CHAT_COORDINATION.json'
if coordination.is_file():
    data['separate49_chat']=read(coordination)
    data['clock49_fallback']['implementation_owner']='separate49_chat'
    data['clock49_fallback']['local_snapshot_scope']='Frozen incomplete snapshot only; separate chat progress may differ'
    lines += ['', '用户最新要求已执行：49MHz交由独立会话01a17a00-9d49-7860-ba99-03fe403f6b62，开会话前已写完整需求并逐文件核对复制58份输入到runtime_b0b4_49mhz_20261027。本会话只攻真实50MHz；独立会话不得写共享仓库或接触硬件，主会话统一烧录/发布。上述49单测段落只是交接时冻结状态，后续49实现进度以独立目录为准。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if data['qualified_B0B4']:
    data['next']='Genuine standard v22 50MHz physical qualification achieved. Finish the exact-source offline package, then obtain fresh bench-state confirmation before SRAM/Flash/cold-boot acceptance.'
    if promotion:
        data['next']='Selected standard v22 is promoted and qualified offline. Verify the sealed package; hardware installation and cold-boot readback require fresh bench-state confirmation.'
    lines += ['', '真实50MHz完整物理门及独立raw复核已通过：standard v22 / physical_p3r0_01，50.075MHz，setup +0.030ns，setup/hold端点0/0。其它备选不再推进；下载及冷启动状态独立记录，不能由离线通过推断。']
    (O/'CONTINUATION_STATE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'CONTINUATION_STATUS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'updated_china':data['updated_china'],'protected_sources_unchanged':all(preserved.values()),
    'current_physical':[{k:r[k] for k in ['variant','profile','status','last_stage','vendor_actual_p_wait','runner_actual_p_wait','unrouted']} for r in runs if r['status']=='running'],
    'v9_proofs':{k:v9[k] for k in ['five_completed','full_proofs_passed','proof_runner_actual_wait','synthesis_runner_actual_wait']},'v10':v10,'timing_goal_SYN':timing},separators=(',',':')))
