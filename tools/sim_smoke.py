"""Replay selected self-checking B0AE RTL benches in an isolated, ignored output folder."""
from pathlib import Path, PureWindowsPath
import argparse
import datetime
import json
import os
import shutil
import subprocess
from verify_export import ROOT, RELEASE, sha, verify

BENCHES={
 'control_races':'CONTROL_RACE_PASS', 'core_control':'CORE_ANO_PASS',
 'geometry_domain':'GEOMETRY_DOMAIN_PASS', 'navigation_control':'NAVIGATION_PASS',
 'bounded_divide':'BOUNDED_DIVIDE_PASS', 'divide36_equivalence':'DIVIDE36_EQUIVALENCE_PASS',
 'mask_diagnostic':'DIAGNOSTIC_MASK_COMMUTATION_PASS', 'mask_pwm':'PWM_PRECONVERSION_EXACT_PASS',
 'mask_handoff':'HANDOFF_MASK_COMMUTATION_PASS',
}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iverilog',default=shutil.which('iverilog'))
    p.add_argument('--vvp',default=shutil.which('vvp'))
    a=p.parse_args()
    if not a.iverilog or not a.vvp:p.error('Install Icarus Verilog or pass --iverilog and --vvp')
    verify()
    folder=ROOT/'out'/('rtl_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True)
    # Recorded vector files remain unchanged; all RTL-generated output goes into this copy.
    for src in (RELEASE/'tests').glob('*.txt'):shutil.copyfile(src,folder/src.name)
    temp=folder/'tmp';temp.mkdir()
    env=dict(os.environ,PATH=str(Path(a.iverilog).resolve().parent)+os.pathsep+os.environ.get('PATH',''),
             TMP=str(temp),TEMP=str(temp),TMPDIR=str(temp))
    results=[]
    for name,marker in BENCHES.items():
        proof=json.loads((RELEASE/'tests'/(name+'.proof.json')).read_text(encoding='utf-8'))
        sources=[]
        for rel,expected in proof['source_sha256'].items():
            wp=PureWindowsPath(rel)
            src=(RELEASE/'tests/external_producer_models.v' if wp.is_absolute()
                 else RELEASE/rel.replace('\\','/'))
            if wp.is_absolute() and wp.name!='external_producer_models.v':
                raise ValueError('Unmapped historical source: '+rel)
            if sha(src)!=expected:raise ValueError('Proof input changed: '+rel)
            sources.append(str(src))
        target=folder/(name+'.vvp')
        compiled=subprocess.run([a.iverilog,'-g2012','-I',str(RELEASE/'fixture'),'-s','tb','-o',str(target),*sources],
            capture_output=True,text=True,env=env,timeout=120)
        (folder/(name+'.compile.log')).write_text(compiled.stdout+compiled.stderr,encoding='utf-8')
        if compiled.returncode:raise RuntimeError(name+' compile failed: '+compiled.stderr)
        run=subprocess.run([a.vvp,str(target)],cwd=folder,capture_output=True,text=True,env=env,timeout=300)
        (folder/(name+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode or marker not in run.stdout:raise RuntimeError(name+' failed: '+run.stdout+run.stderr)
        results.append({'bench':name,'passed':True,'marker':marker})
        print(name+' PASS',flush=True)
    summary={'passed':True,'tests':results,'hardware_accessed':False,
             'full_historical_qualification_replayed':False}
    (folder/'result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('Selected RTL replay passed: '+str(folder/'result.json'))

if __name__=='__main__':main()
