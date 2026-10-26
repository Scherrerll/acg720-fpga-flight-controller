"""Offline mock proof of this one pinned Flash-session script; no hardware I/O."""
from contextlib import ExitStack, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SCRIPT = Path(__file__).with_name('flash_b0b3.py')
SCRIPT_SHA = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
SPEC = importlib.util.spec_from_file_location('offline_flash_session_under_test', SCRIPT)
flash = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(flash)


def stopped_state(sequence=1, uptime=100):
    return dict(connected=True, fresh=True, status='live', port='COM17', sequence=sequence,
                flight_info_fresh=True,
                flight_info=dict(build_id=0xb0b2, taking_off=False, uptime_ms=uptime),
                data=dict(armed=False, controller_enabled=False, command_fresh=False,
                          physical_output_active=False, pwm_us=[1000]*4, command_us=[1000]*4,
                          rc_valid=True, rc_us=[1500, 1500, 1000, 1500, 1000, 1500, 1000, 1500],
                          calibrated=True, attitude_valid=True, sensor_ok=True),
                navigation_fresh=True, mtf_fresh=True,
                navigation=dict(height_fusion_ready=True, velocity_fusion_ready=True),
                mtf_sensor=dict(link_valid=True, source_age_ms=1),
                imu_diagnostic_fresh=True,
                imu_diagnostic=dict(raw_count=sequence*10, pose_count=sequence*9))


class Clock:
    def __init__(self):self.now=100.0
    def monotonic(self):return self.now
    def sleep(self, seconds):self.now+=seconds


class World:
    """All external interfaces mocked; actual run/op/guard/wait logic retained."""
    def __init__(self):
        self.stack=ExitStack();self.clock=Clock();self.calls=[];self.identities=[]
        self.flash_build=self.loaded_build=0xb0b2
        self.sequence=0;self.uptime=0
        self.new54_failure=False;self.unsafe_after_failure=False
        self.new_hash_changed=False;self.initial_missing=False
        self.helper=SimpleNamespace(programmers=Mock(return_value=['mock-usb']),
             known_programmer=Mock(return_value={'mock':'only-programmer'}),
             scan_cables=Mock(return_value={'location':3,'mock':'only-cable'}),
             identity=Mock(side_effect=self.identity))

    def __enter__(self):
        self.folder=Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix='offline-b3-flash-')))
        self.session=flash.FlashSession(self.folder,approved=True)
        self.stack.enter_context(patch.object(flash,'get',side_effect=self.get))
        self.stack.enter_context(patch.object(flash.urllib.request,'urlopen',side_effect=AssertionError('Real HTTP forbidden')))
        self.stack.enter_context(patch.object(flash.subprocess,'Popen',side_effect=AssertionError('Real subprocess forbidden')))
        self.stack.enter_context(patch.object(flash.subprocess,'run',side_effect=self.run))
        self.stack.enter_context(patch.object(flash,'verify',return_value={'passed':True,'manifest_sha256':flash.MANIFEST_SHA}))
        self.stack.enter_context(patch.object(flash,'sha',side_effect=self.sha))
        self.stack.enter_context(patch.object(flash.shutil,'copyfile',side_effect=lambda src,dst:Path(dst).write_bytes(b'mock preserved image')))
        spec=SimpleNamespace(loader=SimpleNamespace(exec_module=Mock()))
        self.stack.enter_context(patch.object(flash.importlib.util,'spec_from_file_location',return_value=spec))
        self.stack.enter_context(patch.object(flash.importlib.util,'module_from_spec',return_value=self.helper))
        self.stack.enter_context(patch.object(flash.time,'monotonic',side_effect=self.clock.monotonic))
        self.stack.enter_context(patch.object(flash.time,'sleep',side_effect=self.clock.sleep))
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        return self

    def __exit__(self,*exc):self.stack.close()

    def sha(self,path):
        p=Path(path)
        if p==flash.NEW:return 'changed' if self.new_hash_changed else flash.NEW_SHA
        if p==flash.OLD or p==self.session.images['old']:return flash.OLD_SHA
        if p==flash.CLI:return flash.CLI_SHA
        if p==flash.HELPER:return flash.HELPER_SHA
        if p==flash.REPO/'firmware/B0B3/export_manifest.json':return flash.MANIFEST_SHA
        return hashlib.sha256(p.read_bytes()).hexdigest()

    def get(self,path):
        if path=='/api/xy-pi/status':return {'busy':False}
        assert path=='/api/state'
        self.sequence+=1;self.uptime+=100
        value=stopped_state(self.sequence,self.uptime)
        if self.initial_missing:value.pop('flight_info_fresh')
        if self.unsafe_after_failure and any(c['operation']==54 and c['image']=='new' for c in self.calls):
            value['data']['armed']=True
        return value

    def identity(self,text):
        value=int(re.search(r'MOCK_BUILD=(\d+)',text)[1])
        self.identities.append(value)
        return 0x0001481b,value

    def run(self,args,**kwargs):
        assert args[0]==str(flash.CLI)
        assert kwargs.get('timeout')==240
        operation=int(args[args.index('--run')+1])
        image=None
        if '--fsFile' in args:
            target=args[args.index('--fsFile')+1]
            assert target in (str(flash.NEW),str(self.session.images['old']))
            image='new' if target==str(flash.NEW) else 'old'
        self.calls.append(dict(operation=operation,image=image,args=list(args)))
        if operation in (54,66):assert args[args.index('--spiaddr')+1]=='0x000000'
        if operation==54:
            if image=='new' and self.new54_failure:
                return subprocess.CompletedProcess(args,1,'mock failed program\n','')
            self.flash_build=0xb0b3 if image=='new' else 0xb0b2
        if operation==2:
            assert image=='old';self.loaded_build=0xb0b2;self.uptime=0
        if operation==1:self.loaded_build=self.flash_build;self.uptime=0
        if operation==66:assert self.flash_build==(0xb0b3 if image=='new' else 0xb0b2)
        output='Finished.\n'
        if operation==0:output+='MOCK_BUILD='+str(self.loaded_build)+'\n'
        if operation==54:output+='Program and Verify Flash successfully.\n'
        if operation==66:output+='Verify Flash successfully.\n'
        return subprocess.CompletedProcess(args,0,output,'')


class FlashTests(unittest.TestCase):
    def test_import_and_default_cli_never_install(self):
        with patch.object(flash,'verify',return_value={'passed':True}), \
             patch.object(flash,'FlashSession',side_effect=AssertionError('Install forbidden')), \
             patch.object(flash,'get',side_effect=AssertionError('HTTP forbidden')), \
             patch.object(sys,'argv',['flash_b0b3.py']),redirect_stdout(io.StringIO()):
            flash.main()
        with patch.object(sys,'argv',['flash_b0b3.py','--install']),self.assertRaises(ValueError):
            flash.main()

    def test_operation_whitelist_rejects_bool_approval_location_and_arbitrary_image(self):
        with World() as w:
            s=w.session;s.location=3
            for operation in (True,False,None,'54',54.0,-1,3,53,55,67):
                with self.subTest(operation=operation),self.assertRaises(ValueError):s.args(operation)
            for approval in (False,None,1,'yes'):
                s.approved=approval
                with self.assertRaises(ValueError):s.args(0)
            s.approved=True
            for location in (None,True,False,0,-1,'3',3.0):
                s.location=location
                with self.assertRaises(ValueError):s.args(0)
            s.location=3
            for operation,which in ((54,None),(54,'C:/arbitrary.fs'),(2,'new'),(0,'old'),(1,'new')):
                with self.assertRaises(ValueError):s.args(operation,which)

    def test_fixed_images_zero_address_and_old_only_sram(self):
        with World() as w:
            s=w.session;s.location=3
            self.assertEqual(s.images,{'new':flash.NEW,'old':w.folder/'previous_P005_I0.fs'})
            for operation,which in ((54,'new'),(54,'old'),(66,'new'),(66,'old')):
                args=s.args(operation,which)
                self.assertEqual(args[:9],[str(flash.CLI),'--device','GW5AT-60B','--cable-index','1','--location','3','--run',str(operation)])
                self.assertEqual(args[9:11],['--spiaddr','0x000000'])
                self.assertEqual(args[-2:],['--fsFile',str(s.images[which])])
            self.assertNotIn('--spiaddr',s.args(2,'old'))
            self.assertEqual(s.args(0)[-2:],['--run','0'])
            self.assertEqual(s.args(1)[-2:],['--run','1'])
            w.new_hash_changed=True
            with self.assertRaises(ValueError):s.args(54,'new')

    def test_verify_checks_every_pinned_hash_and_qualification_without_hardware(self):
        pins={flash.NEW:flash.NEW_SHA,flash.OLD:flash.OLD_SHA,flash.HELPER:flash.HELPER_SHA,
              flash.CLI:flash.CLI_SHA,flash.REPO/'firmware/B0B3/export_manifest.json':flash.MANIFEST_SHA}
        success=subprocess.CompletedProcess([],0,json.dumps({'passed':True,'manifest_sha256':flash.MANIFEST_SHA}),'')
        with patch.object(flash.subprocess,'run',return_value=success)as run,patch.object(flash,'sha',side_effect=lambda p:pins[Path(p)]):
            self.assertTrue(flash.verify()['passed'])
            self.assertEqual(run.call_args.args[0][:2],[sys.executable,'-B'])
            self.assertEqual(Path(run.call_args.args[0][2]).name,'verify_export.py')
        for changed in pins:
            with self.subTest(changed=str(changed)),patch.object(flash.subprocess,'run',side_effect=AssertionError('Qualification must not run after hash rejection')),patch.object(flash,'sha',side_effect=lambda p:'changed'if Path(p)==changed else pins[Path(p)]),self.assertRaises(ValueError):
                flash.verify()

    def test_stopped_missing_fields_and_rc_bounds_fail_closed(self):
        self.assertEqual(flash.stopped(stopped_state())['port'],'COM17')
        for field in ('connected','fresh','flight_info_fresh','status','port','flight_info','data'):
            value=stopped_state();value.pop(field)
            with self.subTest(field=field),self.assertRaises(ValueError):flash.stopped(value)
        for field in ('armed','controller_enabled','command_fresh','physical_output_active','pwm_us','command_us','rc_valid','rc_us'):
            value=stopped_state();value['data'].pop(field)
            with self.subTest(data_field=field),self.assertRaises(ValueError):flash.stopped(value)
        for channel in (0,1,3):
            value=stopped_state();value['data']['rc_us'][channel]=1600
            with self.assertRaises(ValueError):flash.stopped(value)
        for channel in (2,4,6):
            for bad in (799,1101,1500,True):
                value=stopped_state();value['data']['rc_us'][channel]=bad
                with self.assertRaises(ValueError):flash.stopped(value)
        for bound in (800,1100):
            value=stopped_state()
            for channel in (2,4,6):value['data']['rc_us'][channel]=bound
            flash.stopped(value)

    def test_fresh_unsafe_activity_is_a_distinct_stop_signal(self):
        for field in ('armed','controller_enabled','command_fresh','physical_output_active'):
            value=stopped_state();value['data'][field]=True
            with self.subTest(field=field),self.assertRaises(flash.UnsafePostLoad):flash.stopped(value)
        for field in ('pwm_us','command_us'):
            value=stopped_state();value['data'][field][2]=1001
            with self.assertRaises(flash.UnsafePostLoad):flash.no_activity(value)

    def test_wait_requires_five_distinct_new_epoch_healthy_frames_and_progressing_counters(self):
        with World() as w:
            w.session.reloaded_at=w.clock.now
            values=[stopped_state(sequence=n,uptime=n*10)for n in (1,1,2,3,4,5)]
            guard=Mock(side_effect=values)
            with patch.object(w.session,'guard',guard):result=w.session.wait('healthy')
            self.assertEqual(guard.call_count,6)
            saved=json.loads((w.folder/'healthy.json').read_text(encoding='utf8'))
            self.assertEqual([v['sequence']for v in saved],[1,2,3,4,5])
            self.assertEqual(result['sequence'],5)

    def test_wait_rejects_old_epoch_unhealthy_and_nonprogressing_counters(self):
        for fault in ('old_epoch','no_reload','no_imu','stale_mtf','counters'):
            with self.subTest(fault=fault),World()as w:
                w.session.reloaded_at=None if fault=='no_reload'else w.clock.now
                index=[0]
                def value():
                    index[0]+=1;v=stopped_state(index[0],index[0]*10)
                    if fault=='old_epoch':v['flight_info']['uptime_ms']=40000
                    if fault=='no_imu':v['data']['calibrated']=False
                    if fault=='stale_mtf':v['mtf_sensor']['source_age_ms']=100
                    if fault=='counters':v['imu_diagnostic']={'raw_count':1,'pose_count':1}
                    return v
                with patch.object(w.session,'guard',side_effect=value),self.assertRaises(RuntimeError):w.session.wait('rejected')
                self.assertFalse((w.folder/'rejected.json').exists())

    def test_wait_uptime_regression_discards_the_previous_partial_window(self):
        with World()as w:
            w.session.reloaded_at=w.clock.now
            values=[stopped_state(n,uptime)for n,uptime in [(1,100),(2,110),(3,1),(4,2),(5,3),(6,4),(7,5),(8,6)]]
            with patch.object(w.session,'guard',side_effect=values):w.session.wait('regression')
            saved=json.loads((w.folder/'regression.json').read_text(encoding='utf8'))
            self.assertEqual([v['sequence']for v in saved],[4,5,6,7,8])

    def test_full_transaction_verifies_old_flash_first_b3_identity_and_two_new_reloads(self):
        with World()as w:
            result=w.session.run()
            self.assertEqual([(c['operation'],c['image'])for c in w.calls],[(0,None),(1,None),(0,None),(66,'old'),(1,None),(0,None),(54,'new'),(1,None),(0,None),(66,'new'),(1,None),(0,None)])
            self.assertEqual(w.identities,[0xb0b2,0xb0b2,0xb0b2,0xb0b3,0xb0b3])
            self.assertEqual([c['operation']for c in w.calls[7:]],[1,0,66,1,0])
            self.assertTrue(all(result[k]is True for k in ('installed','flash_written','flash_contents_certified','independent_flash_verify_passed')))
            self.assertIs(result['physical_cold_boot_verified'],False)
            self.assertEqual(result['script_sha256'],SCRIPT_SHA)
            self.assertEqual(result['default_after'],'B0B3')

    def test_failed_new54_runs_exact_preserved_p005_recovery_sequence(self):
        with World()as w:
            w.new54_failure=True
            with self.assertRaises(ValueError):w.session.run()
            tail=w.calls[7:]
            self.assertEqual([(c['operation'],c['image'])for c in tail],[(2,'old'),(0,None),(54,'old'),(1,None),(66,'old'),(1,None),(0,None)])
            self.assertTrue(w.session.record['rollback_verified'])
            self.assertEqual(w.session.record['default_after'],'P005/I0 B0B2')
            self.assertFalse(w.session.record['installed'])

    def test_fresh_unsafe_after_failed54_immediately_skips_automatic_recovery(self):
        with World()as w:
            w.new54_failure=True;w.unsafe_after_failure=True
            with self.assertRaises(ValueError):w.session.run()
            self.assertEqual(len(w.calls),7)
            self.assertTrue(w.session.record['automatic_recovery_skipped'])
            self.assertTrue(w.session.record['unsafe_activity_reported'])
            self.assertNotIn('rollback_verified',w.session.record)

    def test_initial_preflight_rejection_never_reloads_or_erases_flash(self):
        with World()as w:
            w.initial_missing=True
            with self.assertRaises(ValueError):w.session.run()
            self.assertEqual(w.calls,[])
            self.assertTrue(w.session.record['preflight_rejected_no_device_change'])
            self.assertFalse(w.session.record['flash_write_started'])

    def test_new_image_hash_rejected_before_write_never_programs_flash(self):
        with World()as w:
            w.new_hash_changed=True
            with self.assertRaises(ValueError):w.session.run()
            self.assertFalse(any(c['operation']==54 for c in w.calls))
            self.assertFalse(w.session.record['flash_write_started'])
            self.assertTrue(w.session.record['previous_flash_not_written'])
            self.assertEqual(w.flash_build,0xb0b2)

    def test_programmer_timeout_keeps_bytes_or_text_receipts_and_propagates(self):
        for stdout,stderr in ((b'part',b'error'),('part',None)):
            with self.subTest(stdout=stdout),World()as w:
                s=w.session;s.hw=w.helper;s.inventory={'mock':'only-programmer'};s.cable={'location':3,'mock':'only-cable'};s.location=3
                failure=subprocess.TimeoutExpired('mock',240,output=stdout,stderr=stderr)
                with patch.object(flash.subprocess,'run',side_effect=failure),self.assertRaises(subprocess.TimeoutExpired):s.op(0,'timeout')
                text=(w.folder/'timeout.txt').read_text(encoding='utf8')
                self.assertIn('part',text);self.assertIn('TIMEOUT',text)
                self.assertTrue(s.record['operations'][0]['timeout'])


if __name__=='__main__':unittest.main()
