"""Prepare B0B0 persistent boot offline; installation requires explicit Flash approval.

No hardware call occurs for --prepare or module import. Reuses the exact-image
verifier and read-only receiver from install_sram, never its SRAM-only writer.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import install_sram as base

ROOT = Path(__file__).resolve().parents[1]
OLD_ROOT = ROOT.parent/'routing_rescue_20261015/mtf01p_b0ac_preserve_fsm'
OLD_IMAGE = OLD_ROOT/'fixture/impl/pnr/acg720_ano_port.fs'
OLD_SHA = '212f31daed0c96e71c4cd3f1e56a580cdc1b9d425a15ba391cf2a37e74e92c34'
OLD_RECEIPT = OLD_ROOT/'hardware/flash_install_20261020T084011_527389Z/flash_install.json'
REVIEW = ROOT/'bench/hardware/powered_direction_20261024T041227Z/review.json'
PLAN = ROOT/'bench/hardware/default_preparation/plan.json'


def verify_files():
    manifest = base.verify()
    prior = base.read(OLD_RECEIPT)
    base.require(prior['installed'] and prior['flash_contents_certified'] and prior['default_after']=='B0AC', 'Prior B0AC Flash receipt required')
    base.require(base.sha(OLD_IMAGE)==OLD_SHA, 'B0AC rollback image changed')
    review = base.read(REVIEW)
    base.require(review['passed'] and all(review['checks'].values()) and review['checks']['final_stopped'], 'Current powered correction acceptance required')
    base.require(review['script_sha256']==base.sha(ROOT/'review_powered_direction.py'), 'Correction reviewer changed')
    for name, digest in review['source_sha256'].items():
        base.require(base.sha(REVIEW.parent/name)==digest, 'Correction evidence changed: '+name)
    return dict(new_build='B0B0',new_image=str(base.IMAGE),new_sha256=base.IMAGE_SHA,
                previous_build='B0AC',previous_image=str(OLD_IMAGE),previous_sha256=OLD_SHA,
                manifest_sha256=manifest,powered_review_sha256=base.sha(REVIEW),
                prior_flash_receipt_sha256=base.sha(OLD_RECEIPT),installer_sha256=base.sha(Path(__file__)),
                shared_verifier_sha256=base.sha(Path(base.__file__)))


def prepare():
    p = verify_files()
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    rollback = PLAN.parent/'previous_default_B0AC.fs'
    if rollback.exists():
        base.require(base.sha(rollback)==OLD_SHA, 'Existing rollback copy changed')
    else:
        shutil.copy2(OLD_IMAGE,rollback)
    base.require(base.sha(rollback)==OLD_SHA, 'Rollback copy mismatch')
    help_result = subprocess.run([base.CLI,'--help'],capture_output=True,text=True,errors='replace',timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
    base.require(help_result.returncode==0 and '54: exFlash Erase,Program,Verify Arora V' in help_result.stdout
                 and '66: exFlash Verify Arora V' in help_result.stdout, 'Vendor operation definitions differ')
    (PLAN.parent/'programmer_help.txt').write_text(help_result.stdout+help_result.stderr,encoding='utf-8')
    p.update(utc=dt.datetime.now(dt.timezone.utc).isoformat(),prepared=True,hardware_accessed=False,
             flash_written=False,flash_approval_received=False,physical_cold_boot_verified=False,flight_ready=False,
             backup=str(rollback),backup_sha256=base.sha(rollback),
             programmer_help_sha256=base.sha(PLAN.parent/'programmer_help.txt'),
             expected_programmer=dict(vid=0x403,pid=0x6014,serial='6',location=353,device='GW5AT-60B',idcode='0x0001481B'),
             flash_address='0x000000',
             operations=['Read current B0B0 identity with motors stopped',
                         'Reload expected B0AC Flash and independently verify against saved B0AC image before erase',
                         'Reload B0AC again after verification bridge; verify low controls and identity',
                         'Program-and-verify exact B0B0 at address zero with vendor operation54',
                         'Reload B0B0; independently verify Flash using operation66; reload B0B0 again',
                         'Check B0B0 identity and fresh stopped IMU/MTF/navigation telemetry',
                         'Operator removes all board power including USB, then battery-only cold boot remains required'],
             recovery='Before write starts restore B0B0 SRAM without Flash writes. After write starts restore B0AC SRAM, program/verify B0AC Flash, independently verify, then reload B0AC. Report any recovery failure.',
             approval_reason='Changes persistent power-on firmware from B0AC to B0B0; earlier motor test authorization alone did not explicitly request this Flash write.')
    PLAN.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(prepared=True,plan=str(PLAN),hardware_accessed=False,flash_written=False)))


class Installer:
    def __init__(self,folder,approved,location):
        self.folder=Path(folder);self.approved=approved;self.location=location
        self.images={'new':base.IMAGE,'old':self.folder/'previous_default_B0AC.fs'}
        self.hashes={'new':base.IMAGE_SHA,'old':OLD_SHA}
        self.record=dict(installed=False,flash_write_started=False,flash_written=False,flash_contents_certified=False,
                         device_change_started=False,physical_cold_boot_verified=False,flight_ready=False,
                         default_before_expected='B0AC',intended_default='B0B0',flash_approval_received=approved)

    def save(self):
        self.record.update(utc=dt.datetime.now(dt.timezone.utc).isoformat(),attempt=str(self.folder))
        (self.folder/'flash_install.json').write_text(json.dumps(self.record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def args(self,op,which=None):
        base.require(self.approved,'Explicit human Flash approval required')
        base.require(type(op)is int and op in (0,1,2,54,66),'Unknown programmer operation')
        args=[base.CLI,'--device','GW5AT-60B','--cable-index','1','--location',str(self.location),'--run',str(op)]
        if op in (2,54,66):
            base.require(which in self.images,'Fixed verified image required')
            base.require(base.sha(self.images[which])==self.hashes[which],'Image changed before operation')
            if op in (54,66):args+=['--spiaddr','0x000000']
            args+=['--fsFile',str(self.images[which])]
        else:base.require(which is None,'Identity/reload cannot take image')
        return args

    def op(self,op,label,which=None):
        args=self.args(op,which)
        print(label,flush=True)
        run=subprocess.run(args,capture_output=True,text=True,errors='replace',timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
        output=run.stdout+run.stderr
        (self.folder/(label+'.txt')).write_text(output,encoding='utf-8')
        base.require(run.returncode==0 and 'Finished.' in output and not re.search(r'\b(error|failed)\b',output,re.I),'Programmer failed: '+label)
        return output

    def identity(self,label,build):
        output=self.op(0,label)
        base.require('0x0001481B' in output and re.search(r'User Code is:\s*0x0*'+f'{build:x}'+r'\b',output,re.I),'Wrong device/build: '+label)

    def guard(self,s,build):
        base.stopped(s,build)
        rc=s['data']['rc_us']
        base.require(len(rc)==8 and 800<=rc[2]<=1100 and rc[4]<=1200 and rc[6]<=1200
                     and all(1450<=rc[k]<=1550 for k in (0,1,3)), 'Low throttle/SWA/SWC and centered sticks required')

    def wait(self,build,label):
        started=time.monotonic();good=[]
        while time.monotonic()-started<35:
            try:
                s=base.state();self.guard(s,build)
                base.require(all(s['data'][k] for k in ['calibrated','attitude_valid','sensor_ok']), 'Waiting for IMU')
                if build==0xb0b0:
                    n=s.get('navigation') or {};m=s.get('mtf_sensor') or {}
                    base.require(s.get('navigation_fresh') and s.get('mtf_fresh') and m.get('link_valid')
                                 and m.get('source_age_ms',9999)<100 and n.get('height_fusion_ready') and n.get('velocity_fusion_ready'), 'Waiting for current MTF/navigation')
                if not good or s['sequence']!=good[-1]['sequence']:good.append(s)
                if len(good)>=5:
                    (self.folder/(label+'.json')).write_text(json.dumps([base.summary(x) for x in good],indent=2)+'\n',encoding='utf-8')
                    return s
            except (ValueError,OSError,KeyError):good=[]
            time.sleep(.2)
        raise RuntimeError('Healthy stopped telemetry did not return: '+label)

    def run(self):
        base.require(self.approved,'Explicit human Flash approval required')
        self.save()
        try:
            self.guard(base.state(),0xb0b0);self.identity('01_B0B0_sram_identity',0xb0b0)
            self.record['device_change_started']=True;self.save()
            self.op(1,'02_previous_flash_reload');self.wait(0xb0ac,'03_previous_stopped')
            self.identity('04_previous_identity',0xb0ac)
            self.op(66,'05_previous_flash_independent_verify','old')
            self.record['previous_default_independently_verified']=True;self.save()
            self.op(1,'06_previous_flash_reload_after_verify');self.wait(0xb0ac,'07_previous_stopped_before_write')
            self.identity('08_write_entry_identity',0xb0ac)
            verify_files();self.guard(base.state(),0xb0ac)
            self.record['flash_write_started']=True;self.save()
            self.op(54,'09_B0B0_program_verify','new');self.record['flash_written']=True;self.save()
            self.op(1,'10_B0B0_reload');self.wait(0xb0b0,'11_B0B0_stopped')
            self.identity('12_B0B0_identity',0xb0b0)
            self.op(66,'13_B0B0_independent_verify','new')
            self.op(1,'14_B0B0_final_reload');s=self.wait(0xb0b0,'15_B0B0_final_stopped')
            self.identity('16_B0B0_final_identity',0xb0b0)
            self.record.update(installed=True,flash_contents_certified=True,independent_flash_verify_passed=True,default_after='B0B0',after=base.summary(s))
            self.save()
        except Exception as error:
            self.record['error']=repr(error);self.save()
            try:
                if not self.record['device_change_started']:
                    self.record['preflight_rejected_no_device_change']=True
                elif self.record['flash_write_started']:
                    self.op(2,'recovery_B0AC_sram','old');self.wait(0xb0ac,'recovery_B0AC_stopped')
                    self.identity('recovery_B0AC_identity',0xb0ac)
                    self.op(54,'rollback_B0AC_program_verify','old')
                    self.op(1,'rollback_B0AC_reload');self.wait(0xb0ac,'rollback_B0AC_stopped')
                    self.op(66,'rollback_B0AC_independent_verify','old')
                    self.op(1,'rollback_B0AC_final_reload');self.wait(0xb0ac,'rollback_B0AC_final_stopped')
                    self.identity('rollback_B0AC_final_identity',0xb0ac)
                    self.record.update(rollback_verified=True,default_after='B0AC',flash_contents_certified=True)
                else:
                    self.op(2,'recover_B0B0_sram','new');self.wait(0xb0b0,'recover_B0B0_stopped')
                    self.record.update(previous_flash_not_written=True,sram_B0B0_restored=True)
            except Exception as recovery:
                self.record.update(recovery_error=repr(recovery),flash_contents_certified=False)
            self.save();raise


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--install',action='store_true')
    p.add_argument('--flash-approved',action='store_true');p.add_argument('--location',type=int)
    a=p.parse_args()
    if a.prepare:prepare();return
    base.require(a.flash_approved,'User must explicitly approve persistent Flash update first')
    plan=base.read(PLAN);current=verify_files()
    base.require(all(plan[k]==v for k,v in current.items()),'Preparation changed')
    base.require(a.location==plan['expected_programmer']['location'],'Location must match reviewed plan')
    base.require(len([x for x in base.list_ports.comports() if (x.vid,x.pid,x.serial_number)==(0x403,0x6014,'6')])==1,'Known sole FT232H serial6 required')
    base.require(base.sha(Path(plan['backup']))==OLD_SHA,'Prepared rollback changed')
    folder=ROOT/'bench/hardware'/dt.datetime.now(dt.timezone.utc).strftime('flash_install_%Y%m%dT%H%M%S_%fZ')
    folder.mkdir(parents=True,exist_ok=False)
    shutil.copy2(plan['backup'],folder/'previous_default_B0AC.fs')
    worker=Installer(folder,True,a.location);worker.record['preparation']=plan;worker.run()
    print(json.dumps(worker.record,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
