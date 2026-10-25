"""Fail-closed input, routing and complete STA audit for policy v3. No hardware."""
import argparse, hashlib, importlib.util, json, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent/'github_publish/acg720-fpga-flight-controller'
TOP='acg720_ano_port'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def verify_inputs(trial):
    binding=json.loads((ROOT/'synthesis_final_binding.json').read_text())
    require(binding['passed'],'Missing synthesis qualification')
    for p,h in binding['evidence_sha256'].items():require(sha(Path(p))==h,'Evidence changed: '+p)
    for n,h in binding['source_sha256'].items():
        for source in [ROOT/'candidate',ROOT/'synthesis_final/fixture']:
            require(sha(source/n)==h,'Source changed: '+str(source/n))
    for source,extra in [(ROOT/'candidate',set())]:
        actual={p.relative_to(source).as_posix()for p in source.rglob('*')if p.is_file()}
        require(actual==set(binding['source_sha256'])|extra,'Unexpected source file coverage')
    for name in ['behavior_verification.json','protocol_verification.json']:
        proof=json.loads((ROOT/name).read_text())
        require(proof['passed'] and proof['source_sha256']==binding['source_sha256'],'Proof source mismatch')
        for p,h in proof.get('evidence_sha256',{}).items():require(sha(Path(p))==h,'Proof dependency changed: '+p)
    proof=json.loads((ROOT/'behavior_verification.json').read_text())
    for name,result in proof['tests'].items():
        require(result['passed'],'Behavior test failed')
        require(sha(ROOT/(name+'_commands.json'))==result['commands_sha256'],'Behavior commands changed')
        require(sha(ROOT/(name+'.log'))==result['log_sha256'],'Behavior output changed')
    c=json.loads((trial/'contract.json').read_text());f=trial/'fixture'
    replication=c['options']['replicate_resources']
    require(type(replication)is int and replication in [0,1],'Unknown replication option')
    runner=ROOT/('physical_replicated.py'if replication else'physical_trial.py')
    require(c['runner_sha256']==sha(runner),'Physical runner changed')
    donor=Path(c['donor']).resolve()
    require(donor in [(ROOT/n).resolve()for n in ['physical_donor_final','physical_donor_logic_globals','physical_donor_live_globals']],'Unexpected donor')
    for n,h in binding['donor_sha256'].items():require(sha(ROOT/'physical_donor_final'/n)==h,'Base donor changed')
    expected_donor=dict(binding['donor_sha256'])
    if donor.name in ['physical_donor_logic_globals','physical_donor_live_globals']:
        first=('LUT4','pose_valid_s','F','pose_valid')if donor.name=='physical_donor_live_globals'else('DFFSE','tilt4500_ok_s0','Q','body_tilt4500_ok')
        extra='\nCLOCK_LOC "nav_vertical_ready" BUFG = LOGIC;\nCLOCK_LOC "'+first[3]+'" BUFG = LOGIC;\n'
        require((donor/(TOP+'.cst')).read_text()==(ROOT/'physical_donor_final'/(TOP+'.cst')).read_text()+extra,'Unexpected logic global constraints')
        text=(donor/'impl/gwsynthesis'/f'{TOP}.vg').read_text()
        for kind,name,output,net in [first,('LUT4','nav_vertical_ready_s','F','nav_vertical_ready')]:
            matches=list(re.finditer(r'\b'+kind+r'\s+'+name+r'\s*\([\s\S]*?\);',text))
            require(len(matches)==1 and f'.{output}({net})'in matches[0][0],'Missing unique global driver')
        expected_donor[TOP+'.cst']=sha(donor/(TOP+'.cst'))
    require(c['donor_sha256']==expected_donor,'Donor contract mismatch')
    for n,h in c['donor_sha256'].items():require(sha(Path(c['donor'])/n)==h,'Donor changed')
    for n,h in c['files_sha256'].items():require(sha(f/n)==h,'Physical input changed: '+n)
    require(c['netlist_sha256']==binding['actual_netlist_sha256']==sha(f/'impl/gwsynthesis'/f'{TOP}.vg'),'Wrong exact netlist')
    require(c['pins']==binding['pins'] and c['amendment']=='','Unexpected pin/global amendment')
    expected=dict(top_module=TOP,output_base_name=TOP,user_code='0000B0B2',place_option=c['options']['place_option'],route_option=c['options']['route_option'],timing_driven=1,replicate_resources=replication,map_option=2,global_freq=50,max_fanout=200,opt_goal='area',route_maxfan=23)
    require(c['options']==expected and expected['place_option']in range(5)and expected['route_option']in range(3),'Unexpected physical options')
    tcl='open_project '+TOP+'.gprj\n'+''.join(f'set_option -{k} {v}\n'for k,v in expected.items())+'run pnr\nexit\n'
    require((f/'build.tcl').read_text()==tcl,'Unexpected build commands')
    project=ET.parse(f/(TOP+'.gprj')).getroot();dev=project.find('Device')
    require(dev is not None and dev.attrib==dict(name='GW5AT-60B',pn='GW5AT-LV60PG484AC1/I0')and dev.text=='gw5at60b-002','Unexpected device')
    files=project.findall('.//File')
    require([x.attrib for x in files]==[dict(path=p,type=t,enable='1')for p,t in [('impl/gwsynthesis/'+TOP+'.vg','file.netlist'),(TOP+'.cst','file.cst'),(TOP+'.sdc','file.sdc')]],'Unexpected project inputs')
    require((f/(TOP+'.sdc')).read_text().strip()=='create_clock -name clk50 -period 19.500 [get_ports {clk50}]','Clock or exceptions changed')
    return binding,c

def audit(trial):
    b,c=verify_inputs(trial);f=trial/'fixture';pnr=f/'impl/pnr'
    canonical=REPO/'firmware/B0B2/source'
    canonical_files={p.relative_to(canonical).as_posix()for p in canonical.rglob('*')if p.is_file()}
    canonical_match=canonical_files==set(b['source_sha256'])|{'build.tcl'} and all(sha(canonical/n)==h for n,h in b['source_sha256'].items())
    state=json.loads((trial/'run_state.json').read_text());require('returncode'in state,'Run is unfinished')
    console=(trial/'console.log').read_text(errors='replace')
    rpt=pnr/(TOP+'.rpt.txt');report=rpt.read_text(errors='replace')if rpt.exists()else''
    errors=re.findall(r'^.*ERROR[^\r\n]*',console+'\n'+report,re.M)
    un=re.search(r'total\s+(\d+)\s+unrouted nets',report)
    actual_pins=dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|',report,re.M))
    part=bool(re.search(r'<Part Number>:\s*GW5AT-LV60PG484AC1/I0\s',report)and re.search(r'<Device>:\s*GW5AT-60\s',report)and re.search(r'<Device Version>:\s*B\s',report))
    fs=pnr/(TOP+'.fs');identity=False
    if fs.exists():
        with fs.open()as stream:head=''.join(next(stream,'')for _ in range(16))
        identity=all(re.search(p,head,re.I)for p in [r'//UserCode: 0x0000b0b2\b',r'//Part Number: GW5AT-LV60PG484AC1/I0',r'//Device-package: GW5AT-60B-PBGA484A\b'])
    routing=bool(state['returncode']==0 and not errors and not(un and int(un[1])) and all(x in console for x in ['Skip synthesis, because there is only one netlist file','Placement and routing completed','Bitstream generation completed'])and fs.exists())
    fresh=all(p.stat().st_mtime>=state['started_epoch']-2 for p in pnr.glob('*')if p.is_file())if pnr.exists()else False
    sta=None;sta_error=None
    if(pnr/(TOP+'.tr')).exists():
        # The imported auditor checks setup, hold, recovery, removal and pulse width.
        # Its older >=50MHz acceptance is tightened below to the actual19.5ns limit.
        (f/'console.txt').write_bytes((trial/'console.log').read_bytes())
        path=ROOT.parent/'routing_closure_20261024/audit_physical.py'
        spec=importlib.util.spec_from_file_location('full_sta',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        try:sta=module.audit(f)
        except(Exception)as e:sta_error=str(e)
    timing=bool(sta and sta['passed']and sta['constraint_period_ns']==19.5 and sta['fmax_mhz']>=51.282)
    physical_ready=bool(routing and timing and actual_pins==b['pins'] and part and identity and fresh)
    passed=physical_ready and canonical_match
    files=[ROOT/'synthesis_final_binding.json',ROOT/'audit_final_policy.py',ROOT.parent/'routing_closure_20261024/audit_physical.py',trial/'contract.json',trial/'run_state.json',trial/'console.log']+sorted(p for p in pnr.glob('*')if p.is_file())
    return dict(passed=passed,checked_utc=datetime.now(timezone.utc).isoformat(),inputs_passed=True,canonical_source_matches=canonical_match,offline_physical_ready=physical_ready,netlist_sha256=b['actual_netlist_sha256'],vendor_returncode=state['returncode'],routing_passed=routing,unrouted_nets=int(un[1])if un else 0 if routing else None,part_passed=part,pins_passed=actual_pins==b['pins'],identity_passed=bool(identity),output_freshness_passed=fresh,full_timing_passed=timing,sta=sta,sta_error=sta_error,errors=errors,evidence_sha256={str(p):sha(p)for p in files},hardware_accessed=False,flight_ready=False,scope='Offline source/protocol/behavior binding and physical timing only; no installation or flight authorization')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('trial',type=Path);args=ap.parse_args()
    trial=args.trial.resolve()
    try:result=audit(trial)
    except(Exception)as e:result=dict(passed=False,inputs_passed=False,error=str(e),hardware_accessed=False)
    (trial/'final_policy_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['evidence_sha256','sta']},indent=2))
    raise SystemExit(0 if result['passed']else 1)
