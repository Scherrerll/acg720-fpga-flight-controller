"""Prepare v4 plus local synthesis-only fanout hints at two actual late-path nets."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[2];M=O/'compact_aw_v14'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v14/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
expected=read(O/'v4_release_proofs/RESULT.json')['source55']
assert len(expected)==55 and {n:sha(OLD/n) for n in expected}==expected
assert not M.exists() and not NEW.exists();M.mkdir();shutil.copytree(OLD,NEW)
changes={
 'acg720_ano_port.v':(' reg previous_pose_valid=0;',' reg previous_pose_valid /* synthesis syn_maxfan = 10 */ =0;'),
 'core/height_loss_fallback.v':(' assign active=rst_n && healthy && armed && (latched || enter);',
     ' // Same live expression, locally constrain only its combinational driver.\n wire active_fanout_limited /* synthesis syn_maxfan = 50 */;\n assign active_fanout_limited=rst_n && healthy && armed && (latched || enter);\n assign active=active_fanout_limited;')}
diff='';reversions={}
for name,(before,after) in changes.items():
    raw=(OLD/name).read_text(encoding='utf8');assert raw.count(before)==1
    current=raw.replace(before,after);(NEW/name).write_text(current,encoding='utf8',newline='\n')
    restored=current.replace(after,before);assert restored==raw
    reversions[name]={'baseline_sha256':sha(OLD/name),'candidate_sha256':sha(NEW/name),
        'reverse_exact_text_sha256':hashlib.sha256(restored.encode()).hexdigest(),
        'reverse_transform_equals_original_text':True,'before':before,'after':after}
    diff+=''.join(difflib.unified_diff(raw.splitlines(True),current.splitlines(True),fromfile='v4/'+name,tofile='v14/'+name))
after={n:sha(NEW/n) for n in expected};assert sorted(n for n in expected if after[n]!=expected[n])==sorted(changes)
review=M/'source_review.md'
review.write_text('''# v14：只约束两个原始关键网络的综合扇出

从准确冻结v4源55出发，仅改两个文件。顶层previous_pose_valid原reg增加syn_maxfan=10；fallback的原组合active表达式逐字不改，通过一个普通wire同值连接输出，对该驱动wire施加syn_maxfan=50。没有添加寄存器、always块、状态或周期，普通四态连线语义相同。每处替换均有精确反向文本校验，撤去局部属性和同值wire连接后，两个文件文本逐字等于v4。

依据实际v4原始TR：Path1最差setup−0.220ns，fallback active末级fanout115且到selected_throttle布线1.569ns；Path8 previous_pose_valid到共享乘法器数据端点setup−0.140ns，首网布线6.920ns。此前max_fanout100实际新综合把fallback115拆为58/57，但全芯片同时增加81FF/83LUT，其完整物理结果尚未返回。本候选只请求这两个网络的复制，避免全局改变；实际工具是否应用及资源影响必须等新SYN审计，不能从属性字面推断。

官方SUG550-2.4E PDF65-66支持wire/reg的syn_maxfan，可复制寄存器或逻辑；不适用于clock/CE/reset信号，子模块输入端口应约束驱动端。本轮直接约束原数据reg及内部组合驱动wire，不新建或修改clock/CE/reset定义。若工具忽略某个属性，应按真实新网表如实记录。

控制器、PID/Q16精度、全部保护/降级/着陆条件、已批准的抗饱和行为、wire1000/350默认、50MHz/20ns及唯一radio_rx原例外均不改。53文件逐字不变，五场景/FRAC边界/四客户端按原完全相同控制依赖复用；新准确顶层13项门需重新运行。功能复用证明不是新的综合或物理通过。本候选目前只准备，禁止下载；firmware/B0B4/source原型保持。
''',encoding='utf8')
(M/'source_changes.diff').write_text(diff,encoding='utf8')
manual=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG550-2.4E_GowinSynthesis User Guide.pdf')
(M/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps({'scope':'Exact source transformations only: one synthesis comment and one combinational wire alias with synthesis comment; no simulation/tool-output equivalence claim.',
    'transformations':reversions,'unchanged_files':53,'official_manual_sha256':sha(manual),'official_manual_pdf_pages':[65,66],
    'all_source_restored_text_exact':True,'v4_functional_binding_sha256':sha(O/'v4_release_proofs/RESULT.json')},indent=2)+'\n',encoding='utf8')
(M/'source_freeze.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source55':after,'baseline_source55':expected,'changed_files':list(changes),'source_review_sha256':sha(review),
    'source_equivalence_basis_sha256':sha(M/'SOURCE_EQUIVALENCE_BASIS.json'),'prepared_only':True},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_only':True,'source_files':55,'changed_files':list(changes),'control_and_clock_logic_unchanged':True,'vendor_started':False}))
