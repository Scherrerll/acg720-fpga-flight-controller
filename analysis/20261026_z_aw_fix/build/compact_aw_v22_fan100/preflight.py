"""Offline exact source/proof/recipe/AST/Tcl preflight; no vendor command evaluation."""
from pathlib import Path
import ast,hashlib,json,tkinter
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from input_contract import validate
from effective_recipe import make_recipe,PARENT
base=validate();C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
text=make_recipe(C/'build.tcl');interp=tkinter.Tcl();assert interp.call('info','complete',text)==1
assert text.replace('set_option -max_fanout 100\n','set_option -max_fanout 200\n',1)==PARENT.read_text()
for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf8'),filename=str(p))
runner=ast.parse((O/'run_synthesis.py').read_text());audit=ast.parse((O/'audit_synthesis_only.py').read_text())
def calls(t,name,attrs):return [ast.dump(x,include_attributes=False) for x in ast.walk(t) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id==name and x.func.attr in attrs]
std=ast.parse((O.parent/'compact_aw_v22/run_synthesis.py').read_text())
assert calls(runner,'h',['run_phase','check_sources'])==calls(std,'h',['run_phase','check_sources'])
assert len(calls(audit,'helper',['mapped_audit']))==len(calls(audit,'auditor',['extended_audit']))==1
assert "assert not (S/'impl/pnr').exists()" in (O/'audit_synthesis_only.py').read_text()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v22_fan100').exists()
assert not any((O/n).exists() for n in ['SYN_REVIEW_GATE.json','runner_process.json','runner_exit.json','SYNTHESIS_RESULT.json'])
result={'passed':True,'source55':base['source55'],'canonical_source_STD22_only':True,'standard_parent_VG_sha256':base['VG_sha256'],
 'Tcl_info_complete':True,'effective_Tcl_sha256':hashlib.sha256(text.encode()).hexdigest(),'parent_execution_Tcl_sha256':sha(PARENT),
 'source_build_Tcl_sha256':sha(C/'build.tcl'),'sole_effective_option_delta':{'max_fanout':{'from':200,'to':100}},
 'reverse_only_fanout_line_equals_actual_parent_SYN_Tcl':True,'AST_parse_passed':True,'original_process_helper_calls_AST_identical':True,
 'original_mapped_and_gain18pin_helper_gates_present':True,'strict_all_FF_CLK50_audit_present':True,'no_RTL_tests_run':True,'vendor_started':False,'PNR_prepared':False,'runtime_absent':True}
dest=O/'PREFLIGHT_RESULT.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed_offline_preflight':True,'Tcl_complete':True,'single_option_delta':True,'result_sha256':sha(dest),'vendor_started':False,'PNR_prepared':False}))
