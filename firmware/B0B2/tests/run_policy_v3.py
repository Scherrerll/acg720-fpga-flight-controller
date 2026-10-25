"""Actual-RTL tests for the confirmed timeout policy; never opens hardware."""
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,subprocess
TESTS=Path(__file__).resolve().parent
FW=TESTS.parent;REPO=FW.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--iverilog',type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args()
    iv=args.iverilog or REPO.parents[1]/'.tools/iverilog/app/bin/iverilog.exe'
    output=args.output or REPO/'out/B0B2'/datetime.now(timezone.utc).strftime('policy_v3_checks_%Y%m%dT%H%M%S_%fZ')
    assert not output.exists(),'Never replace an earlier verification';output.mkdir(parents=True)
    source=FW/'source';rtl=TESTS/'rtl_v3';archive=FW/'evidence/source_revisions/copy99_v1/source'
    hashes={p.relative_to(source).as_posix():sha(p)for p in source.rglob('*')if p.is_file()}
    baseline=output/'baseline';baseline.mkdir()
    transforms=[('core/bmi088_reader.v','bmi088_reader','bmi088_reader_baseline'),('core/imu_checked_guard_pipelined.v','imu_checked_guard_pipelined','imu_checked_guard_baseline'),('core/imu_temporal_check_pipelined.v','imu_temporal_check','imu_temporal_check_baseline'),('core/imu_pipeline_pipelined.v','imu_pipeline','imu_pipeline_baseline')]
    for name,old,new in transforms:
        text=(archive/name).read_text();assert ('module '+old+' #')in text
        text=text.replace('module '+old+' #','module '+new+' #')
        if old=='imu_pipeline':
            text=text.replace('bmi088_reader reader','bmi088_reader_baseline reader').replace('imu_checked_guard_pipelined #','imu_checked_guard_baseline #').replace('imu_temporal_check #','imu_temporal_check_baseline #')
        (baseline/(new+'.v')).write_text(text)
    temporary=output/'tmp';temporary.mkdir();env=dict(os.environ,TMP=str(temporary),TEMP=str(temporary),TMPDIR=str(temporary))
    sources=sorted(source.rglob('*.v'));results={}
    def run(label,bench,inputs,simulate=True):
        argv=[iv,'-g2012','-I',source,'-s',label,'-o',temporary/(label+'.vvp')]+([bench]if bench else[])+inputs
        commands=[]
        for command in [argv]+([[iv.with_name('vvp.exe'),'-n',temporary/(label+'.vvp')]]if simulate else[]):
            r=subprocess.run(list(map(str,command)),capture_output=True,text=True,env=env,timeout=240)
            commands.append(dict(argv=list(map(str,command)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));(output/(label+'_commands.json')).write_text(json.dumps(commands,indent=2)+'\n');r.check_returncode()
        expected='timeout_alignment'if label=='timeout_boundaries'else label
        if simulate:assert 'PASS '+expected in commands[-1]['stdout'],commands[-1]['stdout']
        results[label]=dict(compiled=True,simulation_passed=simulate,commands_sha256=sha(output/(label+'_commands.json')))
        print(commands[-1]['stdout'].strip()or'PASS '+label+' elaboration only',flush=True)
    run('acg720_ano_port',None,sources,False)
    for label in ('reader_policy','pipeline_policy'):run(label,rtl/(label+'.v'),sources+sorted(baseline.glob('*.v')))
    run('timeout_boundaries',rtl/'timeout_boundaries.v',[source/'core/rc_ppm.v',source/'sensor/mtf01p_reader.v'])
    run('policy_boundaries',rtl/'policy_boundaries.v',sources)
    run('range_geometry_policy',rtl/'range_geometry_policy.v',sources+[rtl/'range_geometry_before.v'])
    for name,h in hashes.items():assert sha(source/name)==h,'Source changed during verification: '+name
    receipt=dict(passed=True,source_sha256=hashes,tests=results,baseline_source='archived copy99_v1; only type names isolated for A/B simulation',test_inputs_sha256={str(p.relative_to(TESTS)):sha(p)for p in rtl.glob('*.v')},runner_sha256=sha(Path(__file__)),hardware_accessed=False,flash_changed=False,old_equivalence_proofs_reused=False,flight_ready=False)
    (output/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS policy v3 RTL verification: '+str(output),flush=True)
if __name__=='__main__':main()
