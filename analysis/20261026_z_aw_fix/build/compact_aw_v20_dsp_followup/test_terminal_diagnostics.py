"""Focused pure truth checks over actual dormant sealer/snapshot call expressions."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,itertools,json
O=Path(__file__).resolve().parent;P=O.parent/'prepare_v20_dsp_followup.py';OLD=O/'prepared_revisions/revision_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('thin_status_truth',O/'terminal_diagnostics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
trees={n:ast.parse((O/n).read_text()) for n in ['seal_terminal.py','physical_snapshot.py']}
expressions={}
for n,t in trees.items():
    imports=[x for x in t.body if isinstance(x,ast.ImportFrom) and x.module=='terminal_diagnostics']
    assert len(imports)==1 and [x.name for x in imports[0].names]==['terminal_status']
    calls=[x.value for x in ast.walk(t) if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='terminal_status']
    assert len(calls)==1
    expressions[n]=compile(ast.Expression(calls[0]),n,'eval')
    field='passed' if n=='seal_terminal.py' else 'full_gate_pass'
    outputs=[x for x in ast.walk(t) if isinstance(x,ast.keyword) and x.arg==field]
    assert outputs and all(isinstance(x.value,ast.Name) and x.value.id=='passed' for x in outputs)
receipts=[None,{}, {'actual_p_wait':0}, {'normal_wait_return':True},
          {'normal_wait_return':True,'actual_p_wait':None}, {'normal_wait_return':True,'actual_p_wait':1},
          {'normal_wait_return':False,'actual_p_wait':0}, {'normal_wait_return':None,'actual_p_wait':0},
          {'normal_wait_return':1,'actual_p_wait':0}, {'normal_wait_return':True,'actual_p_wait':False},
          {'normal_wait_return':True,'actual_p_wait':0.0}, {'normal_wait_return':True,'actual_p_wait':'0'},
          {'normal_wait_return':True,'actual_p_wait':0}]
results=[None,{}, {'passed':False},{'passed':None},{'passed':1},{'passed':'true'},{'passed':True}]
truth=lambda x:isinstance(x,dict) and x.get('normal_wait_return') is True and type(x.get('actual_p_wait')) is int and x.get('actual_p_wait')==0
cases=0;script_checks=0
for result,vendor,runner in itertools.product(results,receipts,receipts):
    expected=isinstance(result,dict) and result.get('passed') is True and truth(vendor) and truth(runner)
    for name,expression in expressions.items():
        actual,classification=eval(expression,{'terminal_status':m.terminal_status,'build_result':result,'result':result,'vendor':vendor,'runner':runner,'audit':{'passed':True,'criteria':{'full_route':True}},'unrouted':[],'physical_log':'','text':''})
        assert actual is expected,(name,result,vendor,runner,actual,expected)
        if truth(vendor) and runner is not None and not truth(runner):assert classification=='runner_failed_after_physical_gate_pass'
        script_checks+=1
    cases+=1
zero={'normal_wait_return':True,'actual_p_wait':0};one={'normal_wait_return':True,'actual_p_wait':1}
assert m.terminal_status({'passed':True},zero,one,None,[],'')==(False,'runner_failed_after_physical_gate_pass')
assert m.terminal_status(None,zero,one,{'passed':True},[],'')==(False,'runner_failed_after_physical_gate_pass')
assert m.terminal_status(None,zero,one,{'passed':False,'criteria':{'full_route':True,'fmax_at_least_50':False}},[],'')==(False,'completed_full_route_timing_failure')
assert m.terminal_status({'passed':True},zero,None,None,[],'')==(False,'awaiting_runner_exit_receipt')
assert m.terminal_status({'passed':True},None,zero,None,[],'')==(False,'runner_ended_without_vendor_exit_receipt')
assert m.terminal_status(None,one,one,None,[1],'DesRoute failed.')==(False,'vendor_nonzero_route_failure')
preparer=ast.parse(P.read_text());functions=[x for x in preparer.body if isinstance(x,ast.FunctionDef) and x.name in ['one','tighten_terminal']]
scope={};exec(compile(ast.Module(body=functions,type_ignores=[]),str(P),'exec'),scope)
literal=next(ast.literal_eval(x.value) for x in preparer.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='DIAGNOSTICS_SOURCE' for y in x.targets))
assert literal==(O/'terminal_diagnostics.py').read_text()
for name,kind in [('seal_terminal.py','seal'),('physical_snapshot.py','snapshot')]:assert scope['tighten_terminal']((OLD/name).read_text(),kind)==(O/name).read_text()
seal_asserts=[x for x in trees['seal_terminal.py'].body if isinstance(x,ast.Assert) and isinstance(x.msg,ast.Constant) and x.msg.value=='Both terminal receipt files must exist before sealing']
assert len(seal_asserts)==1 and 'and' in ast.unparse(seal_asserts[0].test) and ast.unparse(seal_asserts[0].test).count('.is_file()')==2
files=['terminal_diagnostics.py','seal_terminal.py','physical_snapshot.py','test_terminal_diagnostics.py']
j={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'distinct_truth_vectors':cases,'actual_script_expression_checks':script_checks,
   'scripts_sha256':{n:sha(O/n) for n in files},'preparer_sha256':sha(P),'preparer_deterministic_output_parity':True,
   'exact_true_and_int_zero_only':True,'missing_nonzero_null_boolean_float_string_abnormal_receipts_false':True,
   'physical_pass_runner_failure_distinct_from_timing_failure':True,'real_fullroute_failed_timing_still_classified':True,
   'sealer_missing_terminal_file_refuses_early_seal':True,'scope':'Pure function and AST-selected actual script expressions only. No physical scripts or preparer top-level executed, no runtime files/vendor/hardware.'}
dest=O/'DIAGNOSTIC_TRUTH_CHECKS.json';assert not dest.exists();dest.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'distinct_truth_vectors':cases,'actual_script_expression_checks':script_checks,'result_sha256':sha(dest),'runtime_created':False,'vendor_started':False}))
