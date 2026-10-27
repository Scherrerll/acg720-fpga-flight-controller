"""Prepare source-identical v4 with SYN fanout threshold100, preserving all original physical gates."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,sys,tkinter
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v4_native';M=O/'compact_aw_v4_fan100_native'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v4_native/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v4_fan100_native/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not M.exists() and not NEW.exists()
expected=read(P/'source_freeze.json')['source55']
assert len(expected)==55 and {n:sha(OLD/n) for n in expected}==expected
proof=read(P/'PROOF_BINDING.json');assert proof['passed'] and proof['source55']==expected
parent=Path(proof['parent_proof']);assert sha(parent)==proof['parent_proof_sha256'] and read(parent)['passed']
M.mkdir();shutil.copytree(OLD,NEW)
review=M/'source_review.md'
review.write_text('''# v4 同源综合扇出阈值100

准确复用v4全部55份源码和已绑定功能证明。源码build.tcl也不修改；仅独立执行Tcl将SYN max_fanout从200改成100，map2/area、PNR replicate_resources0/P3或P2/R0均保留。

实际最接近50MHz的v4完整布通报告为49.456MHz/setup−0.220ns，关键路径含fanout115控制网络及较大布线延迟。官方SUG1220-2.1E PDF34说明max_fanout约束输入、网络和寄存器输出扇出。本实验希望综合层的更低阈值改善这些高扇出连接；不宣称必定复制、不预先声称面积或时序改善。另一个独立v4 PNR replicate_resources1尝试仍单独保留，其选项不混入本轮。

全部RTL功能、精度、已批准抗饱和行为/默认参数、50MHz/20ns和唯一radio_rx原例外不变。实际SYN后先运行原网表/时钟/同步器/增益/18端口审计，成功才PNR；真实vendor/root退出、完整route/位流、五余量及setup/hold端点0仍全部必需。不得补造独立SYN wait0。无GUI缓存、增量seed、LOC、硬件或源码promote。
''',encoding='utf8')
freeze=read(P/'source_freeze.json');freeze.update(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_review_sha256=sha(review),parent_native_preparation_sha256=sha(P/'PREPARATION.json'))
(M/'source_freeze.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
(M/'PROOF_BINDING.json').write_bytes((P/'PROOF_BINDING.json').read_bytes())
names=['run_physical.py','audit_synthesis.py','native_physical_audit.py','seal_terminal.py','independent_raw_review.py','launch_physical_hidden.py','physical_snapshot.py']
for name in names:
    t=(P/name).read_text(encoding='utf8').replace('compact_aw_v4_native','compact_aw_v4_fan100_native')
    if name=='run_physical.py':
        before="else line\n                  for line in lines"
        assert t.count(before)==1
        t=t.replace(before,"else 'set_option -max_fanout 100' if line=='set_option -max_fanout 200' else line\n                  for line in lines")
        before="    return tcl";assert t.count(before)==1
        t=t.replace(before,"    assert tcl.count('set_option -max_fanout 100\\n')==1 and 'set_option -max_fanout 200' not in tcl\n    return tcl")
        before="'physical_options':{'place':PLACE"
        assert t.count(before)==1
        t=t.replace(before,"'synthesis_options':{'map_option':2,'max_fanout':100,'opt_goal':'area'},\n        'physical_options':{'place':PLACE")
    if name=='audit_synthesis.py':
        before="    files=[f.attrib"
        assert t.count(before)==1
        t=t.replace(before,"    actual_tcl=(A/'physical.tcl').read_text(encoding='utf8')\n    assert actual_tcl.count('set_option -max_fanout 100\\n')==1 and 'set_option -max_fanout 200' not in actual_tcl\n    assert read(V/'build_input.json')['synthesis_options']=={'map_option':2,'max_fanout':100,'opt_goal':'area'}\n    files=[f.attrib")
        t=t.replace("'Same-source map2 SYN resources; no route/STA pass inference.'","'Same-source map2 max_fanout100 versus original max_fanout200 SYN resources; no route/STA pass inference.'")
    ast.parse(t);(M/name).write_text(t,encoding='utf8')
adapt=read(P/'GATE_ADAPTATION.json');adapt.update(parent_v4_native_preparation_sha256=sha(P/'PREPARATION.json'),
    new_independent_parser_sha256=sha(M/'independent_raw_review.py'),new_physical_auditor_sha256=sha(M/'native_physical_audit.py'),
    option_change='Only effective SYN max_fanout200 to100; raw50MHz, clock, pin, bitstream, five slack, endpoints and real waits unchanged.')
(M/'GATE_ADAPTATION.json').write_text(json.dumps(adapt,indent=2)+'\n',encoding='utf8')
saved=sys.argv;sys.argv=['run_physical.py','3']
try:
    spec=importlib.util.spec_from_file_location('fan100_Tcl_parse_only',M/'run_physical.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
finally:sys.argv=saved
checks={};interpreter=tkinter.Tcl()
for place in [2,3]:
    tcl=worker.build_tcl((NEW/'build.tcl').read_text(encoding='utf8').splitlines(),place)
    assert interpreter.call('info','complete',tcl)==1
    assert tcl.index('run syn')<tcl.index('exec {')<tcl.index('run pnr')
    checks[str(place)]={'Tcl_complete':True,'SYN_audit_PNR_order':True,'tcl_sha256':hashlib.sha256(tcl.encode()).hexdigest()}
(M/'PREPARATION.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'prepared_not_started':True,'source55_unchanged':True,'source_build_tcl_unchanged':True,'effective_SYN_max_fanout':100,
    'script_sha256':{n:sha(M/n) for n in names},'Tcl_parse_preflight':checks,'parent_preparation_sha256':sha(P/'PREPARATION.json'),
    'scope':'Syntax and Tcl parsing only, no vendor/hardware started.'},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_not_started':True,'source_files':55,'scripts_syntax_valid':7,'SYN_max_fanout':100}))
