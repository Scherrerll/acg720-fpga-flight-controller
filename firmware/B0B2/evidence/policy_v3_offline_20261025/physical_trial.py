"""Exact-netlist physical experiment; no programmer, UART or release authority."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
TOP='acg720_ano_port'
GOWIN=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def require(x,message):
    if not x:raise ValueError(message)

def prepare(args):
    donor=args.donor.resolve()
    trial=ROOT/args.name
    trial.mkdir()
    fixture=trial/'fixture'
    vg=Path('impl/gwsynthesis')/(TOP+'.vg')
    (fixture/vg).parent.mkdir(parents=True)
    donor_hashes={str(n):sha(donor/n) for n in [vg,Path(TOP+'.gprj'),Path(TOP+'.cst'),Path(TOP+'.sdc')]}
    for n in [vg,Path(TOP+'.cst'),Path(TOP+'.sdc')]:shutil.copyfile(donor/n,fixture/n)
    project=ET.parse(donor/(TOP+'.gprj')).getroot()
    files=project.find('FileList');require(files is not None,'No FileList')
    files.clear()
    for name,kind in [(str(vg).replace('\\','/'),'file.netlist'),(TOP+'.cst','file.cst'),(TOP+'.sdc','file.sdc')]:
        ET.SubElement(files,'File',dict(path=name,type=kind,enable='1'))
    (fixture/(TOP+'.gprj')).write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(project,encoding='utf-8'))
    require((fixture/(TOP+'.sdc')).read_text().strip()=='create_clock -name clk50 -period 19.500 [get_ports {clk50}]','Clock must remain19.5ns')
    cst=(fixture/(TOP+'.cst')).read_text()
    pins=dict(re.findall(r'IO_LOC "([^"]+)" (\w+);',cst))
    require(len(pins)==17,'Expected17 pins')
    amendment=''
    if args.matrix_global:
        # These are physical routing directives; no logic, clock or latency edits.
        netlist=(fixture/vg).read_text()
        require(r'\matrix[8]_1_7 ' in netlist,'Exact matrix enable not found')
        require('pose_update' in netlist,'Pose update not found')
        amendment='\nCLOCK_LOC "pose_update" LOCAL_CLOCK;\nCLOCK_LOC "core/imu/estimator/matrix[8]_1_7" BUFG = CE;\n'
    (fixture/(TOP+'.cst')).write_text(cst+amendment)
    tcl='open_project '+TOP+'.gprj\n'
    options=dict(top_module=TOP,output_base_name=TOP,user_code='0000B0B2',place_option=args.place,route_option=args.route,
        timing_driven=1,replicate_resources=0,map_option=2,global_freq=50,max_fanout=200,opt_goal='area',route_maxfan=23)
    tcl+=''.join(f'set_option -{k} {v}\n'for k,v in options.items())+'run pnr\nexit\n'
    (fixture/'build.tcl').write_text(tcl)
    contract=dict(created_utc=datetime.now(timezone.utc).isoformat(),donor=str(donor),donor_sha256=donor_hashes,
        files_sha256={str(p.relative_to(fixture)):sha(p)for p in fixture.rglob('*')if p.is_file()},
        options=options,pins=pins,amendment=amendment,runner_sha256=sha(Path(__file__)),netlist_sha256=sha(fixture/vg),
        hardware_accessed=False,flight_ready=False,release_eligible=False)
    save(trial/'contract.json',contract)
    (trial/'DO_NOT_PROGRAM').write_text('Unqualified physical experiment. Independent functional and installation gates still apply.\n')
    return trial

def verify(trial):
    c=json.loads((trial/'contract.json').read_text());fixture=trial/'fixture'
    require(sha(Path(__file__))==c['runner_sha256'],'Runner changed')
    for n,h in c['donor_sha256'].items():require(sha(Path(c['donor'])/n)==h,'Donor changed:'+n)
    for n,h in c['files_sha256'].items():require(sha(fixture/n)==h,'Input changed:'+n)
    return c

def collect(trial):
    c=verify(trial);fixture=trial/'fixture';pnr=fixture/'impl/pnr'
    state=json.loads((trial/'run_state.json').read_text())
    console=(trial/'console.log').read_text(errors='replace')
    rpt=(pnr/(TOP+'.rpt.txt')).read_text(errors='replace')if(pnr/(TOP+'.rpt.txt')).exists()else''
    timing=(pnr/(TOP+'.tr')).read_text(errors='replace')if(pnr/(TOP+'.tr')).exists()else''
    if 'Note:Core Timing Report'in timing:timing=timing.split('Note:Core Timing Report',1)[1]
    errors=re.findall(r'^.*ERROR[^\r\n]*',console+'\n'+rpt,re.M)
    un=re.search(r'total\s+(\d+)\s+unrouted nets',rpt)
    routed=state['returncode']==0 and not errors and not(un and int(un[1]))and all(s in console for s in ('Placement and routing completed','Bitstream generation completed'))
    freq=re.search(r'clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',timing)
    summaries={}
    for kind in ('setup','hold'):
        m=re.search(r'clk50\s+'+kind+r'\s+(-?[\d.]+)\s+(\d+)',timing)
        summaries[kind]=dict(tns_ns=float(m[1]),violated_endpoints=int(m[2]))if m else None
    timed=bool(freq and float(freq[2])>=1000/19.5 and all(v==dict(tns_ns=0.0,violated_endpoints=0)for v in summaries.values()))
    actual_pins=dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|',rpt,re.M))
    fs=pnr/(TOP+'.fs')
    identity=False
    if fs.exists():
        with fs.open()as f:header=''.join(next(f,'')for _ in range(15))
        identity=bool(re.search(r'UserCode:\s*0x0000b0b2\b',header,re.I))
    result=dict(routing_passed=routed,unrouted_nets=int(un[1])if un else 0 if routed else None,
        timing_summary_passed=timed,fmax_mhz=float(freq[2])if freq else None,summaries=summaries,
        pins_passed=actual_pins==c['pins'],identity_passed=identity,errors=errors,
        vendor_returncode=state['returncode'],netlist_sha256=c['netlist_sha256'],
        outputs_sha256={str(p.relative_to(trial)):sha(p)for p in pnr.glob('*')if p.is_file()},
        hardware_accessed=False,flight_ready=False,release_eligible=False,
        scope='Physical feasibility only; complete STA audit and functional/source binding required separately')
    if fs.exists():result['bitstream']=dict(path=str(fs),sha256=sha(fs))
    save(trial/'result.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='outputs_sha256'}),flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('name');ap.add_argument('--donor',type=Path);ap.add_argument('--place',type=int,choices=range(5),default=2)
    ap.add_argument('--route',type=int,choices=(0,1,2),default=2);ap.add_argument('--matrix-global',action='store_true');ap.add_argument('--collect',action='store_true')
    args=ap.parse_args();require(bool(re.fullmatch('[a-z0-9_]+',args.name)),'Invalid name')
    if args.collect:collect(ROOT/args.name);return
    trial=prepare(args);verify(trial)
    state=dict(started_epoch=time.time(),hardware_accessed=False)
    with(trial/'console.log').open('w')as log:
        p=subprocess.Popen([str(GOWIN),'build.tcl'],cwd=trial/'fixture',stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        state['owned_pid']=p.pid;save(trial/'run_state.json',state)
        print(json.dumps(dict(trial=str(trial),pid=p.pid)),flush=True)
        p.wait();state.update(returncode=p.returncode,finished_epoch=time.time());save(trial/'run_state.json',state)
    collect(trial)

if __name__=='__main__':main()
