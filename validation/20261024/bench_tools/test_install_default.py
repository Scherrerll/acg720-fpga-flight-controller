"""Offline ordering, rejection and fault recovery checks; no hardware calls."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import install_default as subject


class FakeInstaller(subject.Installer):
    def __init__(self,folder,fail=None):
        super().__init__(folder,True,353)
        self.flash=0xb0ac;self.running=0xb0b0;self.calls=[];self.fail=fail

    def op(self,op,label,which=None):
        self.calls.append((op,label,which))
        if label==self.fail:raise RuntimeError('Injected programmer failure')
        if op==1:self.running=self.flash
        if op==2:self.running=0xb0b0 if which=='new' else 0xb0ac
        if op==54:self.flash=0xb0b0 if which=='new' else 0xb0ac
        if op==66:assert self.flash==(0xb0b0 if which=='new' else 0xb0ac)
        return f'ID Code is: 0x0001481B\nUser Code is: 0x{self.running:08X}\nFinished.'

    def wait(self,build,label):
        assert self.running==build
        self.guard(self.state(),build)
        return self.state()

    def state(self):
        return dict(status='live',fresh=True,flight_info_fresh=True,receiver_profile='mtf01p.b0b0_synthesis_fix.v7',serial_writes=False,
                    flight_info=dict(build_id=self.running),data=dict(armed=False,controller_enabled=False,physical_output_active=False,
                    command_us=[1000]*4,pwm_us=[1000]*4,rc_valid=True,rc_us=[1500,1500,1000,1500,1000,1000,1000,1000],
                    calibrated=True,attitude_valid=True,sensor_ok=True))


class InstallerTests(unittest.TestCase):
    def simulate(self,fail=None):
        with tempfile.TemporaryDirectory() as folder:
            w=FakeInstaller(folder,fail)
            with patch.object(subject.base,'state',w.state),patch.object(subject,'verify_files',return_value={}):
                if fail:
                    with self.assertRaises(RuntimeError):w.run()
                else:w.run()
            return w

    def test_success_checks_old_before_erase_and_new_before_final_reload(self):
        w=self.simulate();labels=[x[1] for x in w.calls]
        self.assertTrue(w.record['installed']);self.assertEqual(w.flash,0xb0b0)
        self.assertLess(labels.index('05_previous_flash_independent_verify'),labels.index('09_B0B0_program_verify'))
        self.assertLess(labels.index('09_B0B0_program_verify'),labels.index('13_B0B0_independent_verify'))
        self.assertLess(labels.index('13_B0B0_independent_verify'),labels.index('14_B0B0_final_reload'))
        self.assertFalse(w.record['physical_cold_boot_verified']);self.assertFalse(w.record['flight_ready'])

    def test_prewrite_verify_failure_preserves_flash_and_restores_current_sram(self):
        w=self.simulate('05_previous_flash_independent_verify')
        self.assertFalse(any(x[0]==54 for x in w.calls));self.assertEqual((w.flash,w.running),(0xb0ac,0xb0b0))
        self.assertTrue(w.record['previous_flash_not_written'])

    def test_write_failure_restores_and_independently_verifies_old_default(self):
        w=self.simulate('09_B0B0_program_verify')
        self.assertEqual((w.flash,w.running),(0xb0ac,0xb0ac));self.assertTrue(w.record['rollback_verified'])
        self.assertIn((66,'rollback_B0AC_independent_verify','old'),w.calls)

    def test_postwrite_verification_failure_rolls_back(self):
        w=self.simulate('13_B0B0_independent_verify')
        self.assertEqual((w.flash,w.running),(0xb0ac,0xb0ac));self.assertTrue(w.record['rollback_verified'])

    def test_no_approval_rejects_every_programmer_operation(self):
        w=subject.Installer('unused',False,353)
        for op in (0,1,2,54,66):
            with self.assertRaises(ValueError):w.args(op,'new' if op in (2,54,66) else None)
        with self.assertRaises(ValueError):w.run()

    def test_preflight_rejection_never_reprograms_or_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            w=FakeInstaller(folder);s=w.state();s['data']['rc_us'][4]=1507
            with patch.object(subject.base,'state',return_value=s):
                with self.assertRaises(ValueError):w.run()
            self.assertEqual(w.calls,[])
            self.assertTrue(w.record['preflight_rejected_no_device_change'])
            self.assertFalse(w.record['flash_write_started'])

    def test_operation_whitelist_image_hash_and_flash_address(self):
        with tempfile.TemporaryDirectory() as folder:
            w=subject.Installer(folder,True,353)
            for bad in (99,True):
                with self.assertRaises(ValueError):w.args(bad)
            with self.assertRaises(ValueError):w.args(54,'arbitrary')
            Path(folder,'previous_default_B0AC.fs').write_bytes(b'changed')
            with self.assertRaises(ValueError):w.args(54,'old')
            args=w.args(54,'new')
            self.assertEqual(args[args.index('--spiaddr')+1],'0x000000')

    def test_live_guards_reject_high_switch_stale_and_nonidle_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            w=FakeInstaller(folder)
            for mutation in ('swa','swc','throttle','stale','active','wrong_build'):
                s=w.state()
                if mutation in ('swa','swc','throttle'):s['data']['rc_us'][{'swa':4,'swc':6,'throttle':2}[mutation]]=1900
                if mutation=='stale':s['fresh']=False
                if mutation=='active':s['data']['pwm_us'][0]=1200
                if mutation=='wrong_build':s['flight_info']['build_id']=0xb0ac
                with self.assertRaises(ValueError,msg=mutation):w.guard(s,0xb0b0)


if __name__=='__main__':unittest.main(verbosity=2)
