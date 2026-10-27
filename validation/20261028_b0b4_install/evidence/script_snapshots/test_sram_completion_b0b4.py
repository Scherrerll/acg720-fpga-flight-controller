"""Offline exact-transient and operation0-only completion checks."""
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest.mock import Mock, patch

OUT = Path(sys.argv.pop().removeprefix('--output=')) if len(sys.argv)>1 and sys.argv[-1].startswith('--output=') else None
SPEC=importlib.util.spec_from_file_location('completion_under_test',Path(__file__).with_name('sram_completion_b0b4.py'))
c=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(c)


class CompletionBoundaries(unittest.TestCase):
    def test_only_exact_same_group_mismatch_retries(self):
        with patch.object(c.b,'http',return_value={}) as http, patch.object(c.b,'stopped',side_effect=[ValueError('Same-group telemetry required'), {'strict':True}]), patch.object(c.b.time,'sleep'):
            self.assertEqual(c.strict_stopped(c.b),{'strict':True});self.assertEqual(http.call_count,2)
        for error in (ValueError('Fresh live telemetry required'),ValueError('CH3/5/7 low and sticks centered required'),c.b.UnsafeActivity('activity')):
            with patch.object(c.b,'http',return_value={}) as http, patch.object(c.b,'stopped',side_effect=error):
                with self.assertRaises(type(error)):c.strict_stopped(c.b)
                self.assertEqual(http.call_count,1)
        with patch.object(c.b,'http',return_value={}),patch.object(c.b,'stopped',side_effect=ValueError('Same-group telemetry required')),patch.object(c.b.time,'monotonic',side_effect=[0,4]):
            with self.assertRaisesRegex(ValueError,'Same-group'):c.strict_stopped(c.b)

    def test_completion_cannot_program_or_reload(self):
        folder=OUT/'no_program';folder.mkdir();s=c.Completion(folder,folder/'old.json',folder/'root.json')
        s.bind=Mock();s.child=Mock()
        for op in (1,2,54,66,True,'0'):
            with self.assertRaises(ValueError):s.operation(op,'reject')
        s.bind.assert_not_called();s.child.assert_not_called()

    def test_defaults_still_requires_new_query_id_epoch_and_defaults(self):
        folder=OUT/'GET';folder.mkdir();s=c.Completion(folder,folder/'old.json',folder/'root.json')
        s.guard=Mock(return_value={})
        statuses=iter([dict(can_query=True,epoch=7),dict(busy=True,epoch=7,operation_id=10),
                       dict(busy=False,epoch=7,operation_id=10,supported=True,
                            active=dict(build='0000B0B4',p_wire=1000,i_wire=350,generation=0),result=dict(code='queried',operation_id=10))])
        calls=[]
        def http(path,body=None,token=None):
            calls.append((path,body))
            if path=='/api/xy-pi/status':return next(statuses)
            if path=='/api/xy-pi/session':return dict(token='test-only-in-memory')
            if path=='/api/xy-pi/query':return dict(operation_id=10)
            raise AssertionError('Unexpected route')
        with patch.object(c.b,'http',side_effect=http),patch.object(c,'strict_stopped',side_effect=[{'strict':True},{'strict':True}]),patch.object(c.b.time,'sleep'):
            self.assertEqual(s.defaults('new_GET')['operation_id'],10)
        self.assertEqual(len([x for x in calls if x[0]=='/api/xy-pi/query']),1)
        self.assertNotIn('test-only-in-memory',(folder/'new_GET.json').read_text())


if __name__=='__main__':
    if OUT is None:raise SystemExit('Use --output=ABSOLUTE_NEW_TEST_DIR')
    OUT.mkdir(parents=True,exist_ok=False);unittest.main()
