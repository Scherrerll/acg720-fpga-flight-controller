"""Root-authorized fresh v4 map2 P3/R0 three-source LOC/copied same-VG placement seed physical trial; no resynthesis/hardware."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,shutil,traceback,xml.etree.ElementTree as ET
import sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v4'
CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01';ATTEMPT=ROOT/'physical_p3r0_incplace_loc3_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
ORIGINAL=R/'firmware/B0B4/source';PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v3/canonical/source';HELPER=R/'firmware/B0B4/build_candidate.py'
HELPER_SHA='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
VG_SHA='e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f'
OWNED=False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n')
def hash55(root,paths):return {p:sha(root/p) for p in paths}

SEED_ORIGINAL=ROOT/'physical_p3r0_01/source/impl/pnr/acg720_ano_port.p'
SEED_SHA='f61026f1a52bf700951acaa1997494a39c1753a4c836fd89b2c68de499676bbe'
SEED=ATTEMPT/'donor/v4_P3R0.p'
LOCATIONS={'acc_time/output_az_3_s0':'R34C24[0][A]',
 'mtf/metric/vy_x100_28_s0':'R50C56[3][B]',
 'previous_pose_valid_s0':'R36C78[0][B]'}


def monitored_run_phase(helper,command,cwd,expected):
    import subprocess,time
    helper.check_sources(expected);log=VERIFY/'physical.log'
    record={'stage':'physical','command':command,'cwd':str(cwd),
        'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'parent_pid':os.getpid(),'stdin':'DEVNULL','create_no_window':True,'log':str(log),'runner_sha256':sha(Path(__file__))}
    cancelled=False;fallback=[]
    with log.open('wb') as output:
        proc=subprocess.Popen(command,cwd=cwd,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        record['pid']=proc.pid;write('physical_process.json',record)
        while proc.poll() is None:
            time.sleep(.5);current=log.read_text(errors='replace')
            fallback=[line for line in current.splitlines() if 'matching(' in line and 'threshold' in line and 'default' in line]
            if fallback:
                existing=ROOT/'physical_p3r0_inc_loc3_01/verification/build_input.json'
                prior=json.loads(existing.read_text())
                assert prior['source_sha256']==expected and prior['donor_netlist_sha256']==VG_SHA
                assert prior['locations']==LOCATIONS and prior['period_ns']==20
                assert prior['physical_options']=={'place':3,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23}
                receipt={'requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'reason':'Documented .p incremental placement fell back to the same already-executed ordinary exact-VG/three-LOC/P3/R0 flow. Cancel only this duplicate child.',
                    'pid':proc.pid,'parent_pid':os.getpid(),'exact_command':command,'process_identity':'Live handle of this runner own Popen child; no PID/name lookup.',
                    'vendor_message':fallback,'existing_input':str(existing),'existing_input_sha256':sha(existing),'log_prefix_sha256':sha(log)}
                if proc.poll() is None:write('incremental_fallback_cancel.json',receipt);proc.terminate();cancelled=True
                break
        code=proc.wait();output.flush()
    record.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_p_wait=code,normal_wait_return=True,log_sha256=sha(log))
    write('physical_exit.json',record)
    text=log.read_text(errors='replace');ratios=[float(x) for x in re.findall(r'matching\(([\d.]+)\)',text,re.I)]
    write('incremental_flow_observation.json',{'requested_interface':'inc_place .p','matching_percent_reports':ratios,
        'fallback_detected':bool(fallback),'incremental_use_proven':bool(ratios and min(ratios)>=80 and not fallback),
        'cancelled_duplicate_fallback':cancelled,'actual_vendor_wait':code,'original_seed_unchanged':sha(SEED_ORIGINAL)==SEED_SHA,'copied_seed_unchanged':sha(SEED)==SEED_SHA})
    assert code==0 and not cancelled,('Actual vendor nonzero/cancelled duplicate fallback',code,cancelled)
    helper.check_sources(expected)

def main():
    global OWNED
    assert not ATTEMPT.exists(),'Never overwrite physical evidence'
    assert sha(HELPER)==HELPER_SHA
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['source55']
    assert len(expected)==55 and expected['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
    din=json.loads((DONOR/'verification/build_input.json').read_text());original=din['original_B4_source55'];prior=din['baseline_v3_map2_source55']
    assert hash55(CANON,expected)==expected and hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior
    summary=json.loads((DONOR/'verification/synthesis_summary.json').read_text());ex=json.loads((DONOR/'verification/synthesis_exit.json').read_text())
    mapped=json.loads((DONOR/'verification/mapped_audit.json').read_text());gain=json.loads((DONOR/'verification/gain_port_audit.json').read_text());clock=json.loads((DONOR/'verification/strict_ff_clock_audit.json').read_text())
    assert summary['passed'] is True and summary['actual_p_wait']==ex['actual_p_wait']==0 and summary['source_sha256']==expected
    for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256')]:assert sha(DONOR/'verification'/name)==summary[key]
    assert sha(DONOR/'verification/synthesis.log')==ex['log_sha256']
    assert mapped['passed'] is True and mapped['source_sha256']==expected and mapped['netlist_sha256']==VG_SHA
    assert gain['passed'] is True and gain['netlist_sha256']==VG_SHA and len(gain['top_ports'])==18
    assert gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad'] and clock['vg_sha256']==VG_SHA
    assert din['synthesis_options']=={'map_option':2,'replicate_resources':0} and hash55(DONOR/'source',expected)==expected
    donor_vg=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(donor_vg)==summary['netlist_sha256']==VG_SHA
    evidence=[DONOR/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']]
    evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']
    assert sha(SEED_ORIGINAL)==SEED_SHA
    evidence += [SEED_ORIGINAL]
    bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}
    spec=importlib.util.spec_from_file_location('v4_exact_original_physical_gate',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    SEED.parent.mkdir();shutil.copy2(SEED_ORIGINAL,SEED);assert sha(SEED)==SEED_SHA
    constraints=SOURCE/'physical_constraints.cst'
    original_cst=(SOURCE/'acg720_ano_port.cst').read_bytes()
    extra_cst='\n// Three placement-only source FF constraints; original 18 IO constraints unchanged.\n'+''.join('INS_LOC '+json.dumps(n)+' '+loc+';\n' for n,loc in LOCATIONS.items())
    constraints.write_bytes(original_cst+extra_cst.encode('ascii'))
    assert constraints.read_bytes().startswith(original_cst) and extra_cst.count('INS_LOC ')==3
    write('placement_constraint_binding.json',{'original_cst_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_cst_sha256':sha(constraints),'locations':LOCATIONS,'copied_seed_sha256':sha(SEED),'original_seed_sha256':sha(SEED_ORIGINAL),'only_added_commands':'INS_LOC, three source DFFs from old raw late paths1/3/8; no SDC changes'})
    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')
    write('donor_evidence_binding.json',{'passed':True,'artifacts':bound,'source55':expected,'vg_sha256':VG_SHA})
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';vg.parent.mkdir(parents=True);shutil.copy2(donor_vg,vg);assert sha(vg)==VG_SHA
    project=ET.parse(SOURCE/'acg720_ano_port.gprj');root=project.getroot();filelist=root.find('FileList');filelist.clear()
    entries=[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('physical_constraints.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
    for path,kind in entries:ET.SubElement(filelist,'File',dict(path=path,type=kind,enable='1'))
    physical_project=SOURCE/'physical.gprj';physical_project.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf-8'))
    raw=physical_project.read_bytes();assert raw.count(b'<?xml')==1
    assert [(f.attrib['path'],f.attrib['type']) for f in ET.fromstring(raw).find('FileList')]==entries
    write('project_serialization_check.json',{'passed':True,'xml_declarations':1,'exact_netlist_constraints_project':True,'combined_cst_sha256':sha(constraints),'incremental_seed_sha256':SEED_SHA,'project_sha256':sha(physical_project)})
    lines=(SOURCE/'build.tcl').read_text().splitlines();assert lines.count('run all')==1 and lines.count('exit')==1
    tcl='\n'.join('run pnr' if line=='run all' else 'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else line for line in lines if line.strip()!='exit')+'\nputs PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
    for option,value in [('place_option','3'),('route_option','0'),('map_option','2'),('replicate_resources','0'),('timing_driven','1'),('route_maxfan','23'),('user_code','0000B0B4')]:assert re.findall(r'^set_option -'+option+r'\s+(\S+)\s*$',tcl,re.M)==[value]
    assert 'run syn' not in tcl and 'run all' not in tcl
    assert not any(c in SEED.as_posix() for c in '{}[]$;')
    tcl=tcl.replace('run pnr\n','set_option -inc_place {'+SEED.as_posix()+'}\nrun pnr\n')
    assert tcl.count('set_option -inc_place ')==1
    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')
    write('build_input.json',{'scope':'Fresh exact-VG v4 physical-only trial; no synthesis/hardware; source override is v4.',
      'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_override':str(CANON),'source_sha256':expected,
      'original_B4_source55':original,'v3_source55':prior,'source_freeze_sha256':sha(O/'source_freeze.json'),'runner_sha256':sha(Path(__file__)),
      'imported_helper_sha256':HELPER_SHA,'donor':str(DONOR),'donor_netlist_sha256':VG_SHA,
      'donor_synthesis_summary_sha256':sha(DONOR/'verification/synthesis_summary.json'),'donor_synthesis_exit_sha256':sha(DONOR/'verification/synthesis_exit.json'),
      'donor_mapped_audit_sha256':sha(DONOR/'verification/mapped_audit.json'),'donor_gain_port_audit_sha256':sha(DONOR/'verification/gain_port_audit.json'),
      'donor_strict_ff_clock_audit_sha256':sha(DONOR/'verification/strict_ff_clock_audit.json'),
      'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23},'period_ns':20,'usercode':'0000B0B4','incremental_seed_sha256':SEED_SHA,'combined_cst_sha256':sha(constraints),'locations':LOCATIONS})
    write('physical_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'donor_netlist_sha256':VG_SHA,
      'combined_cst_sha256':sha(constraints),'incremental_seed_sha256':SEED_SHA,'project_sha256':sha(physical_project),'tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    monitored_run_phase(helper,[str(helper.GOWIN),str(execution)],SOURCE,expected)
    assert sha(SEED_ORIGINAL)==sha(SEED)==SEED_SHA
    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)
    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}==bound
    assert hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior and sha(donor_vg)==VG_SHA and sha(HELPER)==HELPER_SHA
    write('build_result.json',{'passed':True,'scope':'Physical artifact gate only; functional equivalence/hardware acceptance separate.',
      'source_sha256':expected,'canonical_override':str(CANON),'netlist_sha256':VG_SHA,'original_B4_source55_unchanged':True,'v3_source55_unchanged':True,
      'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23},'physical_audit_sha256':sha(VERIFY/'physical_audit.json'),
      'physical_exit_sha256':sha(VERIFY/'physical_exit.json'),'bitstream_sha256':sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),'checks':result['checks'],'fmax_mhz':result['fmax_mhz']})
    print('compact_aw_v4 exact-VG P3/R0 three-source LOC/copied same-VG placement seed full physical gate PASS',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():write('build_failure.json',{'passed':False,'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
