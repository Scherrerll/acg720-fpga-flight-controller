"""Fresh exact-VG compact P3/R0 physical trial, explicitly authorized by root."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,shutil,traceback,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v1'
CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01';ATTEMPT=ROOT/'physical_p3r0_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
ORIGINAL=R/'firmware/B0B4/source';HELPER=R/'firmware/B0B4/build_candidate.py'
VG_SHA='b7691fd2d04abfc95e1fa458b0cb22e1c8ebcb2eb810db16e7a706fa8e73a87b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
    assert not ATTEMPT.exists(),'Never overwrite physical evidence'
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['variant_source55'];old=freeze['base_source55']
    assert len(expected)==55 and expected['position/mtf_xyz_hold_control.v']=='479f757149a57ac0b5f9e0334dab80cae475a5345b834fde9c5130c701057ac3'
    assert all(sha(CANON/n)==h for n,h in expected.items()) and all(sha(ORIGINAL/n)==h for n,h in old.items())
    summary=json.loads((DONOR/'verification/synthesis_summary.json').read_text())
    exit_receipt=json.loads((DONOR/'verification/synthesis_exit.json').read_text())
    mapped=json.loads((DONOR/'verification/mapped_audit.json').read_text())
    assert summary['passed'] is True and summary['actual_p_wait']==exit_receipt['actual_p_wait']==0
    assert summary['source_sha256']==expected and mapped['passed'] is True and mapped['source_sha256']==expected
    assert sha(DONOR/'verification/synthesis_exit.json')==summary['synthesis_exit_sha256']
    assert sha(DONOR/'verification/mapped_audit.json')==summary['mapped_audit_sha256']
    assert sha(DONOR/'verification/synthesis.log')==exit_receipt['log_sha256']
    assert all(sha(DONOR/'source'/n)==h for n,h in expected.items())
    donor_vg=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg'
    assert sha(donor_vg)==summary['netlist_sha256']==mapped['netlist_sha256']==VG_SHA
    spec=importlib.util.spec_from_file_location('compact_aw_physical_helper',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    ATTEMPT.mkdir(parents=True);shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';vg.parent.mkdir(parents=True);shutil.copy2(donor_vg,vg)
    assert sha(vg)==VG_SHA
    project=ET.parse(SOURCE/'acg720_ano_port.gprj');root=project.getroot();filelist=root.find('FileList');filelist.clear()
    for path,kind in [('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]:ET.SubElement(filelist,'File',dict(path=path,type=kind,enable='1'))
    (SOURCE/'physical.gprj').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf8'))
    tcl=(SOURCE/'build.tcl').read_text();assert tcl.count('run all')==1 and tcl.count('open_project acg720_ano_port.gprj')==1
    tcl='\n'.join(x for x in tcl.splitlines() if x.strip()!='exit')+'\n'
    tcl=tcl.replace('open_project acg720_ano_port.gprj','open_project physical.gprj').replace('run all','run pnr')+'puts PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
    for option,value in [('place_option','3'),('route_option','0'),('map_option','2'),('replicate_resources','0'),('user_code','0000B0B4')]:
        assert re.findall(r'^set_option -'+option+r'\s+(\S+)\s*$',tcl,re.M)==[value]
    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')
    write('build_input.json',{'scope':'Fresh compact exact-VG physical-only trial; source variant override, no resynthesis or hardware.',
       'started_utc':utc(),'canonical_override':str(CANON),'source_sha256':expected,'original_B4_source55':old,
       'source_freeze_sha256':sha(O/'source_freeze.json'),'runner_sha256':sha(Path(__file__)),
       'imported_helper':str(HELPER),'imported_helper_sha256':sha(HELPER),
       'donor':str(DONOR),'donor_vg_sha256':VG_SHA,'donor_synthesis_summary_sha256':sha(DONOR/'verification/synthesis_summary.json'),
       'donor_synthesis_exit_sha256':sha(DONOR/'verification/synthesis_exit.json'),'donor_mapped_audit_sha256':sha(DONOR/'verification/mapped_audit.json'),
       'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0},'period_ns':20,'usercode':'0000B0B4'})
    write('physical_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'donor_netlist_sha256':VG_SHA,
       'project_sha256':sha(SOURCE/'physical.gprj'),'tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)
    assert all(sha(ORIGINAL/n)==h for n,h in old.items()) and sha(donor_vg)==VG_SHA
    write('build_result.json',{'passed':True,'scope':'Physical artifact gate only; functional equivalence and hardware acceptance are separate.',
       'completed_utc':utc(),'source_sha256':expected,'canonical_override':str(CANON),'original_B4_source55_unchanged':True,
       'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0},'netlist_sha256':VG_SHA,
       'physical_audit_sha256':sha(VERIFY/'physical_audit.json'),'physical_exit_sha256':sha(VERIFY/'physical_exit.json'),
       'bitstream_sha256':sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),'checks':result['checks'],'fmax_mhz':result['fmax_mhz']})
    print('Compact exact-VG P3/R0 full physical gate PASS',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if VERIFY.exists():write('build_failure.json',{'passed':False,'utc':utc(),'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
