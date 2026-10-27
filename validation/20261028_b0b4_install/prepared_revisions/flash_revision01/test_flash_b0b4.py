"""Offline Flash ordering/failure and image-boundary checks. No hardware/HTTP."""
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('flash_b0b4_under_test', Path(__file__).with_name('flash_b0b4.py'))
f = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(f)
OUT = Path(sys.argv.pop().removeprefix('--output=')) if len(sys.argv) > 1 and sys.argv[-1].startswith('--output=') else None


class FlashBoundaries(unittest.TestCase):
    def session(self, name):
        folder = OUT/name; folder.mkdir(); return f.FlashSession(folder, folder/'unused_sram_receipt.json')

    def test_exact_order_and_no_recovery_after_failure(self):
        for fail in (None, 54, 66):
            s = self.session('order_'+str(fail)); operations = []; health = []; gets = []
            s.prior_sram = Mock(); s.guard = Mock(return_value={'flight_info': {'uptime_ms': 20000}})
            s.health = Mock(side_effect=lambda label, at: health.append(label)); s.defaults = Mock(side_effect=lambda label: gets.append(label))
            s.child = Mock(return_value='{"passed":true}')
            def operation(op, label):
                operations.append(op)
                if op == fail: raise ValueError('mock exact programmer failure')
                if op == 1: s.loaded_at = 1.0
            s.operation = operation
            with patch.object(f.b, 'offline', return_value={'passed': True}), patch.object(f.b.importlib.util, 'module_from_spec', return_value=Mock()), patch.object(f.b.importlib.util, 'spec_from_file_location', return_value=Mock()):
                if fail is None:
                    self.assertIs(s.run()['passed'], True)
                    self.assertEqual(operations, [0,54,1,0,66,1,0])
                    self.assertEqual(len(health), 3); self.assertEqual(len(gets), 2)
                else:
                    with self.assertRaises(ValueError): s.run()
                    self.assertEqual(operations, [0,54] if fail == 54 else [0,54,1,0,66])
                    self.assertIs(s.record['passed'], False)
                    self.assertIs(s.record['automatic_recovery'], False)

    def test_flash_whitelist_fixed_image_fresh_bind_and_guard(self):
        s = self.session('whitelist'); s.bind = Mock(return_value=292); s.guard = Mock(return_value={})
        s.child = Mock(return_value='Program and Verify Flash successfully.\nFinished.\n')
        for op in (2, 3, True, '54', -1):
            with self.assertRaises(ValueError): s.operation(op, 'reject')
        s.child.assert_not_called()
        with patch.object(f.b, 'offline', return_value={}), patch.object(f.b, 'sha', return_value=f.b.IMAGE_SHA):
            s.operation(54, 'allowed_flash')
        self.assertEqual(s.child.call_args.args[0], [str(f.b.CLI),'--device','GW5AT-60B','--cable-index','1','--location','292','--run','54','--spiaddr','0x000000','--fsFile',str(f.b.IMAGE)])
        self.assertEqual(s.bind.call_count, 1); self.assertEqual(s.guard.call_count, 1)
        s.child.reset_mock()
        with patch.object(f.b, 'offline', return_value={}), patch.object(f.b, 'sha', return_value='changed'):
            with self.assertRaises(ValueError): s.operation(66, 'changed_image')
        s.child.assert_not_called()
        s.guard = Mock(side_effect=ValueError('not stopped'))
        with patch.object(f.b, 'offline', return_value={}):
            with self.assertRaises(ValueError): s.operation(54, 'not_stopped')
        s.child.assert_not_called()

    def test_exact_integer_wait_gate(self):
        self.assertTrue(f.successful_wait(dict(normal_wait_return=True,actual_p_wait=0)))
        for value in (None, {}, dict(normal_wait_return=True,actual_p_wait=False), dict(normal_wait_return=True,actual_p_wait=0.0),
                      dict(normal_wait_return=1,actual_p_wait=0),dict(normal_wait_return=True,actual_p_wait=1)):
            with self.subTest(value=value): self.assertFalse(f.successful_wait(value))


if __name__ == '__main__':
    if OUT is None: raise SystemExit('Use --output=ABSOLUTE_NEW_TEST_DIR')
    OUT.mkdir(parents=True,exist_ok=False)
    unittest.main()
