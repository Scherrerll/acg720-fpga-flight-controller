"""Pure truth checks over exact generated status functions and their actual call AST."""
from pathlib import Path
import ast,datetime,hashlib,itertools,json,re
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
trees={n:ast.parse((O/n).read_text()) for n in ['seal_terminal.py','physical_snapshot.py']}
functions={};expressions={};scopes={}
for n,t in trees.items():
    nodes=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ['successful_receipt','terminal_status']]
    assert len(nodes)==2
    functions[n]=ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False)
    scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),n,'exec'),scope);scopes[n]=scope
    calls=[x.value for x in ast.walk(t) if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='terminal_status']
    assert len(calls)==1;expressions[n]=compile(ast.Expression(calls[0]),n,'eval')
    field='passed' if n=='seal_terminal.py' else 'full_gate_pass';var=field
    outputs=[x for x in ast.walk(t) if isinstance(x,ast.keyword) and x.arg==field]
    assert outputs and all(isinstance(x.value,ast.Name) and x.value.id==var for x in outputs)
assert len(set(functions.values()))==1
receipts=[None,{}, {'actual_p_wait':0}, {'normal_wait_return':True},
          {'normal_wait_return':True,'actual_p_wait':None}, {'normal_wait_return':True,'actual_p_wait':1},
          {'normal_wait_return':False,'actual_p_wait':0}, {'normal_wait_return':None,'actual_p_wait':0},
          {'normal_wait_return':1,'actual_p_wait':0}, {'normal_wait_return':True,'actual_p_wait':False},
          {'normal_wait_return':True,'actual_p_wait':0.0}, {'normal_wait_return':True,'actual_p_wait':'0'},
          {'normal_wait_return':True,'actual_p_wait':0}]
results=[None,{}, {'passed':False},{'passed':None},{'passed':1},{'passed':'true'},{'passed':True}]
truth=lambda x:isinstance(x,dict) and x.get('normal_wait_return') is True and type(x.get('actual_p_wait')) is int and x.get('actual_p_wait')==0
cases=checks=0
for result,vendor,runner in itertools.product(results,receipts,receipts):
    expected=isinstance(result,dict) and result.get('passed') is True and truth(vendor) and truth(runner)
    for n,expression in expressions.items():
        scope=dict(scopes[n],build_result=result,result=result,vendor=vendor,runner=runner,audit={'passed':True,'criteria':{'full_route':True}},unrouted=[],physical_log='',text='',re=re)
        actual,classification=eval(expression,scope)
        assert actual is expected,(n,result,vendor,runner,actual,expected)
        if truth(vendor) and isinstance(runner,dict) and runner.get('normal_wait_return') is True and type(runner.get('actual_p_wait')) is int and runner['actual_p_wait']!=0:
            assert classification=='runner_failed_after_physical_gate_pass'
        checks+=1
    cases+=1
zero={'normal_wait_return':True,'actual_p_wait':0};one={'normal_wait_return':True,'actual_p_wait':1}
for scope in scopes.values():
    status=scope['terminal_status']
    assert status({'passed':True},zero,one)==(False,'runner_failed_after_physical_gate_pass')
    assert status(None,zero,one,{'passed':True})==(False,'runner_failed_after_physical_gate_pass')
    assert status(None,zero,one,{'passed':False,'criteria':{'full_route':True,'fmax_at_least_50':False}})==(False,'completed_full_route_timing_failure')
    assert status({'passed':True},zero,None)[0] is False and status({'passed':True},None,zero)[0] is False
seal_assert=[x for x in trees['seal_terminal.py'].body if isinstance(x,ast.Assert) and isinstance(x.msg,ast.Constant) and x.msg.value=='Cannot seal before both terminal receipts exist']
assert len(seal_assert)==1
j={'passed':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'distinct_truth_vectors':cases,'actual_script_expression_checks':checks,
   'functions_AST_identical_between_status_scripts':True,'strict_receipt_exact_true_int_zero_only':True,
   'physical_pass_runner1_classified_runner_failure':True,'missing_receipts_never_PASS_or_early_seal':True,
   'scripts_sha256':{n:sha(O/n) for n in ['seal_terminal.py','physical_snapshot.py','test_terminal_diagnostics.py']},
   'scope':'Only extracted pure functions and actual terminal_status call AST expressions evaluated; status script top-level, preparer, vendor and runtime not executed.'}
dest=O/'DIAGNOSTIC_TRUTH_CHECKS.json';assert not dest.exists();dest.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'distinct_truth_vectors':cases,'actual_script_expression_checks':checks,'result_sha256':sha(dest),'vendor_started':False,'runtime_created':False}))
