"""Fixed-image B0B3 Flash transaction for this explicitly authorized bench session.

Import/default CLI is offline only. No serial port is opened by this script.
The running ground station remains the only serial owner. Cold boot is separate.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
NEW=REPO/'firmware/B0B3/release/B0B3_selected_P3R0.fs'
OLD=REPO/'firmware/B0B3/release/current_P005_I0.fs'
NEW_SHA='a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd'
OLD_SHA='a876c8ed073588e17b6289f8aac7573334a5d5e9c992d394d0d14f61ed17db7c'
MANIFEST_SHA='23374b5c3aca40e8e71a8ae7ad037541484416a752c683b378083a78a3d4f7a7'
HELPER=REPO/'firmware/B0B2/tools/install_sram.py'
HELPER_SHA='6b872ec4ab8c0425f8d477d9e2ac63a21f01f8f0bfe69635cbf3420b796f49b1'
CLI=Path('C:/Gowin/Gowin_V1.9.12.04_x64/Programmer/bin/programmer_cli.exe')
CLI_SHA='ca28fe178b04fd99780267787f61b0e0ec3729d579fe237ff454c1a0353e8ef6'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8765'+path,timeout=4) as response:return json.load(response)

def verify():
    for path,digest in [(NEW,NEW_SHA),(OLD,OLD_SHA),(HELPER,HELPER_SHA),(CLI,CLI_SHA),
                        (REPO/'firmware/B0B3/export_manifest.json',MANIFEST_SHA)]:
        require(sha(path)==digest,'Pinned file changed: '+str(path))
    ran=subprocess.run([sys.executable,'-B',str(REPO/'firmware/B0B3/verify_export.py')],cwd=REPO,
                       capture_output=True,text=True,encoding='utf-8',timeout=60)
    require(ran.returncode==0,'B0B3 qualification failed: '+ran.stderr)
    result=json.loads(ran.stdout)
    require(result.get('passed')is True and result.get('manifest_sha256')==MANIFEST_SHA,'Unexpected qualification')
    return result

class UnsafePostLoad(RuntimeError):pass

def no_activity(snapshot):
    if snapshot.get('connected')is True and snapshot.get('fresh')is True:
        data=snapshot.get('data')or{}
        active=any(data.get(k)is True for k in ('armed','controller_enabled','command_fresh','physical_output_active'))
        active|=any(type(v)in(int,float)and v!=1000 for key in ('pwm_us','command_us') for v in (data.get(key)or[]))
        if active:raise UnsafePostLoad('Fresh telemetry reports activity; stop automatic hardware operations')

def stopped(snapshot):
    no_activity(snapshot)
    require(snapshot.get('connected')is True and snapshot.get('fresh')is True and
            snapshot.get('flight_info_fresh')is True and snapshot.get('status')=='live','Fresh live telemetry required')
    require(snapshot.get('port')=='COM17','Unexpected telemetry port')
    data=snapshot.get('data')or{};info=snapshot.get('flight_info')or{}
    require(info.get('build_id')==0xB0B2 and info.get('taking_off')is False,'Legacy identity/taking-off status mismatch')
    require(all(data.get(k)is False for k in ('armed','controller_enabled','command_fresh','physical_output_active')),'Stopped booleans required')
    require(data.get('pwm_us')==[1000]*4 and data.get('command_us')==[1000]*4,'Reported PWM/command must be 1000')
    rc=data.get('rc_us')or[]
    require(data.get('rc_valid')is True and len(rc)==8 and all(type(v)is int for v in rc),'Live complete RC required')
    require(all(800<=rc[k]<=1100 for k in (2,4,6))and all(1450<=rc[k]<=1550 for k in (0,1,3)),
            'CH3/CH5/CH7 low and centered sticks required')
    return snapshot

class FlashSession:
    def __init__(self,folder=HERE,approved=False):
        self.folder=Path(folder);self.approved=approved;self.location=None;self.cable=None;self.inventory=None
        self.hw=None;self.reloaded_at=None
        self.images={'new':NEW,'old':self.folder/'previous_P005_I0.fs'}
        self.hashes={'new':NEW_SHA,'old':OLD_SHA}
        self.record=dict(installed=False,device_change_started=False,flash_write_started=False,flash_written=False,flash_contents_certified=False,
                         independent_flash_verify_passed=False,physical_cold_boot_verified=False,flight_ready=False,
                         previous_default='P005/I0 B0B2',intended_default='B0B3 .05/0',operations=[],
                         authorization='Direct user chose permanent B0B3 after SRAM-vs-Flash explanation; prior props-off/low CH5 bench confirmation retained, live stopped checks required.',
                         new_sha256=NEW_SHA,previous_sha256=OLD_SHA,operator_flash_approval=bool(approved))

    def persist(self):
        self.record['updated_utc']=datetime.now(timezone.utc).isoformat()
        save(self.folder/'flash_install_report.json',self.record)

    def args(self,operation,which=None):
        require(self.approved is True,'Explicit session Flash authorization required')
        require(type(operation)is int and operation in (0,1,2,54,66),'Operation outside fixed whitelist')
        require(type(self.location)is int and self.location>0,'Fresh positive cable location required')
        args=[str(CLI),'--device','GW5AT-60B','--cable-index','1','--location',str(self.location),'--run',str(operation)]
        if operation in (2,54,66):
            require(which in self.images,'Fixed image required')
            require(operation!=2 or which=='old','SRAM fallback is restricted to preserved P005')
            require(sha(self.images[which])==self.hashes[which],'Image changed at operation boundary')
            if operation in (54,66):args+=['--spiaddr','0x000000']
            args+=['--fsFile',str(self.images[which])]
        else:require(which is None,'Identity/reload cannot specify image')
        return args

    def guard(self):
        snapshot=stopped(get('/api/state'))
        params=get('/api/xy-pi/status')
        require(params.get('busy')is False,'Wait for outstanding parameter request')
        return snapshot

    def op(self,operation,label,which=None):
        args=self.args(operation,which)
        require(sha(CLI)==CLI_SHA and sha(HELPER)==HELPER_SHA,'Programmer/helper changed')
        require(self.hw.known_programmer(self.hw.programmers())==self.inventory,'Programmer inventory changed')
        require(self.hw.scan_cables(self.folder/(label+'_cable.txt'))==self.cable,'Cable selection changed')
        if operation in (54,66):
            save(self.folder/(label+'_preflight.json'),self.guard())
        elif operation in (1,2):no_activity(get('/api/state'))
        entry=dict(operation=operation,label=label,image=which,args=args,started_utc=datetime.now(timezone.utc).isoformat())
        if operation in (1,2,54,66):self.record['device_change_started']=True
        if operation==54 and which=='new':self.record['flash_write_started']=True
        self.record['operations'].append(entry);self.persist()
        print('START '+label,flush=True)
        started=time.monotonic()
        try:
            run=subprocess.run(args,capture_output=True,text=True,errors='replace',timeout=240,
                               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except subprocess.TimeoutExpired as exc:
            def decoded(value):return value.decode(errors='replace')if isinstance(value,bytes)else value or ''
            output=decoded(exc.stdout)+decoded(exc.stderr)
            (self.folder/(label+'.txt')).write_text(output+'\nTIMEOUT\n',encoding='utf-8')
            entry.update(timeout=True,elapsed_s=time.monotonic()-started);self.persist();raise
        output=run.stdout+run.stderr
        (self.folder/(label+'.txt')).write_text(output,encoding='utf-8')
        entry.update(exit_code=run.returncode,elapsed_s=round(time.monotonic()-started,3),log_sha256=sha(self.folder/(label+'.txt')))
        self.persist()
        require(run.returncode==0 and 'Finished.'in output and not re.search(r'\b(error|failed)\b',output,re.I),'Programmer failed: '+label)
        if operation==54:require('Program and Verify Flash successfully.'in output,'Missing program-and-verify success')
        if operation==66:require('Verify Flash successfully.'in output,'Missing independent verify success')
        if operation in (1,2):self.reloaded_at=time.monotonic()
        print('DONE '+label+' '+str(entry['elapsed_s'])+'s',flush=True)
        return output

    def identity(self,label,build):
        identity=self.hw.identity(self.op(0,label))
        require(identity==(0x0001481B,build),'Wrong device identity '+str(identity))
        return identity

    def wait(self,label):
        deadline=time.monotonic()+35;good=[];last_error=''
        while time.monotonic()<deadline:
            try:
                value=self.guard();data=value['data'];info=value['flight_info']
                require(all(data.get(k)is True for k in ('calibrated','attitude_valid','sensor_ok')),'Waiting for IMU/attitude')
                uptime=info.get('uptime_ms')
                require(type(uptime)is int and 0<=uptime<35000 and self.reloaded_at is not None and
                        uptime<=(time.monotonic()-self.reloaded_at)*1000+5000,'Waiting for new boot epoch')
                n=value.get('navigation')or{};m=value.get('mtf_sensor')or{}
                require(value.get('navigation_fresh')and value.get('mtf_fresh')and m.get('link_valid')and
                        m.get('source_age_ms',9999)<100 and n.get('height_fusion_ready')and n.get('velocity_fusion_ready'),
                        'Waiting for current navigation/MTF')
                if good:require(uptime>=good[-1]['flight_info']['uptime_ms'],'Boot counter rolled back during wait')
                if not good or value['sequence']!=good[-1]['sequence']:good.append(value)
                if len(good)>=5:
                    require(good[-1]['flight_info']['uptime_ms']>good[0]['flight_info']['uptime_ms'],'Boot time must progress')
                    first=good[0].get('imu_diagnostic')or{};last=good[-1].get('imu_diagnostic')or{}
                    require(value.get('imu_diagnostic_fresh')and all(type(last.get(k))is int and last[k]>first.get(k,last[k])for k in ('raw_count','pose_count')),
                            'IMU boot counters must progress')
                    save(self.folder/(label+'.json'),good)
                    print('HEALTHY '+label,flush=True)
                    return value
            except (ValueError,OSError,KeyError)as exc:
                good=[];last_error=str(exc)
            time.sleep(.2)
        raise RuntimeError('Stopped healthy boot not proven: '+label+' '+last_error)

    def run(self):
        require(self.approved is True,'Explicit current Flash approval required')
        require(not(self.folder/'flash_install_report.json').exists(),'Session already has a receipt; do not rerun')
        self.record['qualification']=verify();self.record['script_sha256']=sha(Path(__file__))
        shutil.copyfile(OLD,self.images['old']);require(sha(self.images['old'])==OLD_SHA,'Backup changed')
        spec=importlib.util.spec_from_file_location('pinned_flash_inventory_helpers',HELPER)
        self.hw=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.hw)
        self.inventory=self.hw.known_programmer(self.hw.programmers())
        self.cable=self.hw.scan_cables(self.folder/'initial_cable.txt');self.location=self.cable['location']
        self.record.update(programmer=self.inventory,cable=self.cable)
        self.persist()
        try:
            save(self.folder/'telemetry_before.json',self.guard())
            self.identity('01_previous_identity',0xB0B2)
            self.op(1,'02_previous_flash_reload');self.wait('03_previous_stopped')
            self.identity('04_previous_loaded_identity',0xB0B2)
            self.op(66,'05_previous_flash_verify','old')
            self.record['previous_flash_verified']=True;self.persist()
            self.op(1,'06_previous_reload_after_verify');self.wait('07_previous_stopped_before_write')
            self.identity('08_write_boundary_identity',0xB0B2)
            require(verify()==self.record['qualification'],'Qualification changed at write boundary')
            save(self.folder/'write_boundary_stopped.json',self.guard())
            self.op(54,'09_B0B3_program_verify','new');self.record['flash_written']=True;self.persist()
            self.op(1,'10_B0B3_reload');self.wait('11_B0B3_stopped')
            self.identity('12_B0B3_identity',0xB0B3)
            self.op(66,'13_B0B3_independent_verify','new')
            self.record['independent_flash_verify_passed']=True;self.persist()
            self.op(1,'14_B0B3_final_reload');self.wait('15_B0B3_final_stopped')
            self.identity('16_B0B3_final_identity',0xB0B3)
            self.record.update(installed=True,flash_contents_certified=True,default_after='B0B3')
        except Exception as exc:
            self.record['error']=type(exc).__name__+': '+str(exc);self.persist()
            if isinstance(exc,UnsafePostLoad):
                self.record.update(unsafe_activity_reported=True,automatic_recovery_skipped=True)
            else:
                try:
                    if not self.record['device_change_started']:
                        self.record['preflight_rejected_no_device_change']=True
                    elif self.record['flash_write_started']:
                        no_activity(get('/api/state'))
                        self.op(2,'recovery_P005_sram','old');self.wait('recovery_P005_stopped')
                        self.identity('recovery_P005_identity',0xB0B2)
                        self.op(54,'rollback_P005_program_verify','old')
                        self.op(1,'rollback_P005_reload');self.wait('rollback_P005_stopped')
                        self.op(66,'rollback_P005_verify','old')
                        self.op(1,'rollback_P005_final_reload');self.wait('rollback_P005_final_stopped')
                        self.identity('rollback_P005_final_identity',0xB0B2)
                        self.record.update(rollback_verified=True,flash_contents_certified=True,default_after='P005/I0 B0B2')
                    else:
                        self.op(1,'recover_unchanged_flash');self.wait('recover_unchanged_stopped')
                        self.record['previous_flash_not_written']=True
                except Exception as recovery:
                    self.record.update(recovery_error=repr(recovery),flash_contents_certified=False)
                    if isinstance(recovery,UnsafePostLoad):
                        self.record.update(unsafe_activity_reported=True,automatic_recovery_skipped=True)
            raise
        finally:self.persist()
        return self.record

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--flash-approved',action='store_true')
    args=parser.parse_args()
    if not args.install:
        print(json.dumps(verify(),indent=2));return
    require(args.flash_approved,'Explicit user approval flag missing')
    result=FlashSession(approved=True).run()
    print(json.dumps({k:result[k]for k in ('installed','flash_written','flash_contents_certified','independent_flash_verify_passed','physical_cold_boot_verified','new_sha256')},indent=2))

if __name__=='__main__':main()
