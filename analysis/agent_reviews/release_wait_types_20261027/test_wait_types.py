"""Receipt scalar rejection tests only; no export, qualification file or tools."""
from pathlib import Path
import ast, copy, importlib.util, sys, unittest
sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent
R = D.parents[2]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj
v = module('wait_current_verifier', R/'firmware/B0B4/verify_release.py')
old = module('wait_previous42_verifier', D/'previous_42_snapshot/verify_release.py')
MISSING = object()
class E:
    origins = {'repo':'c:/review'}
    def __init__(self, receipt):self.receipt=receipt
    def read(self, *args):return self.receipt
    def check(self, *args):pass
    def blob(self, *args):return b''

class WaitTypes(unittest.TestCase):
    def values(self, wanted):
        return [MISSING, None, False, True, 0.0, 1.0, '0', '1', -1, 0, 1, 2]
    def valid(self, value, expected):return type(value) is int and value == expected
    def exercise(self, callback, receipt, field, normal, expected):
        for value in self.values(expected):
            item=copy.deepcopy(receipt)
            if value is MISSING:item.pop(field,None)
            else:item[field]=value
            with self.subTest(field=field,value=repr(value),type=type(value).__name__):
                if self.valid(value,expected):callback(E(item))
                else:
                    with self.assertRaises(AssertionError):callback(E(item))
        for flag in [False, 0, 1, 0.0, 1.0, 'true', None, MISSING]:
            item=copy.deepcopy(receipt)
            if flag is MISSING:item.pop(normal,None)
            else:item[normal]=flag
            with self.subTest(field=field,normal=repr(flag)):
                with self.assertRaises(AssertionError):callback(E(item))
    def test_preserved42_reproduces_boolean_float_acceptance(self):
        for field, normal in [('actual_p_wait','normal_wait_return'),('actual_completedprocess_returncode','normal_return')]:
            for bad in [False,0.0]:old.check_receipt(E({field:bad,normal:True}),'c:/review/test_exit.json')
    def test_check_receipt_actual_wait_and_completed_process(self):
        for field,normal in [('actual_p_wait','normal_wait_return'),('actual_completedprocess_returncode','normal_return')]:
            self.exercise(lambda e:v.check_receipt(e,'c:/review/test_exit.json'),{field:0,normal:True},field,normal,0)
    def test_raw_success_all_actual_fields(self):
        for field in ['actual_p_wait','actual_child_p_wait','actual_completedprocess_returncode']:
            normal='normal_return' if field=='actual_completedprocess_returncode' else 'normal_wait_return'
            self.exercise(lambda e:v.raw_success_receipt(e,'c:/review/test_exit.json',None,field),{field:0,normal:True},field,normal,0)
    def test_original_failure_is_integer_one(self):
        receipt={'actual_p_wait':1,'normal_wait_return':True,'stdout_sha256':'a'*64,'stderr_sha256':'b'*64}
        self.exercise(lambda e:v.check_failed_receipt(e,'c:/review/test_exit.json',None),receipt,'actual_p_wait','normal_wait_return',1)
    def test_actual_standard_terminal_gate(self):
        expected={f'{i}.v':'a'*64 for i in range(55)}
        terminal={'passed':True,'source55':expected,'vg_sha256':'b'*64,'vendor_actual_p_wait':0,'runner_actual_p_wait':0}
        class Terminal(E):
            origins={'repo':'c:/review','metadata':'c:/review/meta','report':'c:/review/report'}
            def read(self,path,*args):return self.receipt if str(path).endswith('TERMINAL_MANIFEST.json') else {'passed':False}
        q={'source_sha256':expected,'netlist_sha256':'b'*64}
        # Real integer zeros advance through the actual terminal gate to the next independent-review gate.
        with self.assertRaisesRegex(AssertionError,'Independent raw acceptance failed'):
            v.validate_standard_evidence(Terminal(terminal),q)
        for field in ['vendor_actual_p_wait','runner_actual_p_wait']:
            for bad in [False,0.0,'0',None,MISSING]:
                value=copy.deepcopy(terminal)
                if bad is MISSING:value.pop(field)
                else:value[field]=bad
                with self.subTest(field=field,value=repr(bad)):
                    with self.assertRaisesRegex(AssertionError,'Selected terminal qualification failed'):
                        v.validate_standard_evidence(Terminal(value),q)
    def test_export_terminal_gate_without_running_export(self):
        # Execute only the actual exporter assertion AST; its main is never called.
        tree=ast.parse((R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py').read_text())
        nodes=[n for n in ast.walk(tree) if isinstance(n,ast.Assert) and 'exact_exit' in ast.unparse(n.test) and 'vendor_actual_p_wait' in ast.unparse(n.test)]
        self.assertEqual(len(nodes),1)
        gate=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual_export_terminal_gate','exec')
        exec(gate,{'validation':v,'manifest':{'vendor_actual_p_wait':0,'runner_actual_p_wait':0}})
        for field in ['vendor_actual_p_wait','runner_actual_p_wait']:
            for bad in [False,0.0,'0',None,MISSING]:
                value={'vendor_actual_p_wait':0,'runner_actual_p_wait':0}
                if bad is MISSING:value.pop(field)
                else:value[field]=bad
                with self.subTest(field=field,value=repr(bad)):
                    with self.assertRaises(AssertionError):exec(gate,{'validation':v,'manifest':value})

if __name__=='__main__':unittest.main(verbosity=2)
