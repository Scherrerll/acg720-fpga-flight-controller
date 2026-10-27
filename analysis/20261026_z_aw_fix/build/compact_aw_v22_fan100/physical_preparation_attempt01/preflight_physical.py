"""Python-only physical recipe/contract/status preflight; Tcl info-complete only."""
from pathlib import Path
import ast,hashlib,itertools,json,re,tkinter,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
from physical_input_contract import validate_physical
from physical_recipe import make_physical_recipe
base=validate_physical(require_preparation=False);C=Path(base['canonical_source_root'])
text=make_physical_recipe(C/'build.tcl');assert tkinter.Tcl().call('info','complete',text)==1
names=['physical_recipe.py','physical_input_contract.py','run_physical.py','launch_physical_hidden.py','seal_terminal.py','physical_snapshot.py','independent_raw_review.py','preflight_physical.py','prepare_physical.py']
for n in names:ast.parse((O/n).read_text(),filename=str(O/n))
run=ast.parse((O/'run_physical.py').read_text())
def helper_calls(t):return [ast.dump(x,include_attributes=False) for x in ast.walk(t) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='helper' and x.func.attr in ['run_phase','physical_audit','check_sources']]
assert helper_calls(run)==helper_calls(ast.parse((O.parent/'compact_aw_v22/run_physical.py').read_text()))
entries=[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
root=ET.parse(C/'acg720_ano_port.gprj').getroot();f=root.find('FileList');f.clear()
for path,kind in entries:ET.SubElement(f,'File',dict(path=path,type=kind,enable='1'))
calls=[n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='p' and n.func.attr=='write_bytes']
assert len(calls)==1;serialized=eval(compile(ast.Expression(calls[0].args[0]),'actual_project_serialization_expression','eval'),{'ET':ET,'root':root})
assert serialized.count(b'<?xml')==1 and [(x.attrib['path'],x.attrib['type']) for x in ET.fromstring(serialized).find('FileList')]==entries
def checks(source):
    out={}
    for n in ast.walk(ast.parse(source)):
        if isinstance(n,ast.Assign) and len(n.targets)==1:
            t=n.targets[0]
            if isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='checks' and isinstance(t.slice,ast.Constant):out[t.slice.value]=ast.dump(n.value,include_attributes=False)
    return out
std=(O.parent/'compact_aw_v22/independent_raw_review.py').read_text()
for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json']:std=std.replace("O/'"+n+"'","STANDARD/'"+n+"'")
old,new=checks(std),checks((O/'independent_raw_review.py').read_text());assert all(new[k]==v for k,v in old.items())
receipts=[None,{}, {'actual_p_wait':0},{'normal_wait_return':True},{'normal_wait_return':True,'actual_p_wait':None},{'normal_wait_return':True,'actual_p_wait':1},{'normal_wait_return':False,'actual_p_wait':0},{'normal_wait_return':None,'actual_p_wait':0},{'normal_wait_return':1,'actual_p_wait':0},{'normal_wait_return':True,'actual_p_wait':False},{'normal_wait_return':True,'actual_p_wait':0.0},{'normal_wait_return':True,'actual_p_wait':'0'},{'normal_wait_return':True,'actual_p_wait':0}]
results=[None,{}, {'passed':False},{'passed':None},{'passed':1},{'passed':'true'},{'passed':True}]
good=lambda j:isinstance(j,dict) and j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j.get('actual_p_wait')==0
status_checks=0;funcs=[]
for name in ['seal_terminal.py','physical_snapshot.py']:
    t=ast.parse((O/name).read_text());nodes=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ['successful_receipt','terminal_status']]
    funcs.append(ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False));scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'),scope)
    for result,vendor,runner in itertools.product(results,receipts,receipts):
        expected=isinstance(result,dict) and result.get('passed') is True and good(vendor) and good(runner)
        assert scope['terminal_status'](result,vendor,runner)[0] is expected;status_checks+=1
    zero={'normal_wait_return':True,'actual_p_wait':0};one={'normal_wait_return':True,'actual_p_wait':1}
    assert scope['terminal_status']({'passed':True},zero,one)==(False,'runner_failed_after_physical_gate_pass')
assert len(set(funcs))==1
for n in ['run_physical.py','seal_terminal.py','independent_raw_review.py']:
    source=(O/n).read_text()
    assert "read(O/'PROOF_BINDING.json')" not in source and "read(O/'COMPONENT_REUSE_BINDING.json')" not in source
assert (O/'SYNTHESIS_RESULT.json').is_file() and not (O/'PROOF_BINDING.json').exists()
assert not (R/'out/z_aw_fix_20261026/compact_aw_v22_fan100/physical_p3r0_01').exists()
result={'passed':True,'Tcl_info_complete':True,'profile':'physical_p3r0_01','VG_sha256':base['VG_sha256'],'source55':base['source55'],
 'effective_Tcl_sha256':hashlib.sha256(text.encode()).hexdigest(),'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'source_build_Tcl_unchanged':True,'netlist_only_original_CST_SDC_project_verified':True,
 'XML_declarations':1,'original_helper_gate_calls_AST_identical':True,'all_original_raw_checks_AST_identical_after_metadata_provenance_alias':True,
 'strict_wait_status_checks':status_checks,'strict_status_functions_AST_identical':True,'physical_pass_runner_failure_distinct':True,
 'contract_actual_STD22_functional_and_sealed_fan100_SYN_rechecked':True,'no_DSPLOC':True,'vendor_started':False,'runtime_attempt_absent':True}
dest=O/'PHYSICAL_TCL_PREFLIGHT.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed_physical_preflight':True,'strict_status_checks':status_checks,'Tcl_complete':True,'result_sha256':sha(dest),'vendor_started':False}))
