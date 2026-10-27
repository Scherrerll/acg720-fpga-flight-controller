"""Actual v18 FF/v21 SP top integration and byte-identical original top13."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,time,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs_retry02'
C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source';OLD=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
freeze=read(O/'source_freeze.json');expected=freeze['source55'];before=freeze['baseline_source55']
assert not D.exists();D.mkdir();(D/'tmp').mkdir()
assert len(expected)==55 and all(sha(C/n)==h for n,h in expected.items()) and all(sha(OLD/n)==h for n,h in before.items())
assert [n for n in expected if expected[n]!=before[n]]==['acg720_ano_port.v']
basis=read(O/'SOURCE_EQUIVALENCE_BASIS.json');a,b=basis['transformations']['acg720_ano_port.v']['edits'][0]
assert (C/'acg720_ano_port.v').read_bytes().replace(b.encode(),a.encode())==(OLD/'acg720_ano_port.v').read_bytes()
assert sha(O/'source_review.md')==freeze['source_review_sha256'] and sha(O/'SOURCE_EQUIVALENCE_BASIS.json')==freeze['source_equivalence_basis_sha256']
B=R.parents[1]/'.tools/iverilog/app/bin';IV=B/'iverilog.exe';VVP=B/'vvp.exe'
MODEL=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
assert sha(MODEL)=='7109c2568188627465d218bc099cf72f12e90807c21d4d862d2335b499043544'
oldtop=(OLD/'acg720_ano_port.v').read_bytes();needle=b'module acg720_ano_port('
assert oldtop.count(needle)==1
old_fixture=oldtop.replace(needle,b'module acg720_ano_port_before(')
assert old_fixture.count(b'module nav_control_handoff(')==1
old_fixture=re.sub(rb'\bnav_control_handoff\b',b'nav_control_handoff_before',old_fixture)
(D/'top_before.v').write_bytes(old_fixture)
(D/'extension_top_miter.v').write_bytes((O/'extension_top_miter.v').read_bytes())
original_tb=O.parent/'v4_release_proofs/top_safety_tb.v'
assert sha(original_tb)==sha(O.parent/'compact_aw_v18/proofs/top_safety_tb.v')
(D/'top_safety_tb.v').write_bytes(original_tb.read_bytes())
root=r'''`timescale 1ns/1ps
module top13_root;
 GSR GSR(.GSRI(1'b1));
 tb original();
 initial begin
  #1;
`ifdef GW5_USE_VENDOR_BRAM
  if(original.dut.staged_telemetry.extension_storage.SIMULATION_BYPASS!==0)$fatal(1,"Vendor top13 FF bypass");
`else
  if(original.dut.staged_telemetry.extension_storage.SIMULATION_BYPASS!==1)$fatal(1,"Default top13 branch differs");
`endif
 end
endmodule
'''
(D/'top13_root.v').write_text(root,encoding='utf8')
files=[C/f.attrib['path'] for f in ET.parse(C/'acg720_ano_port.gprj').findall('.//File') if f.attrib.get('type')=='file.verilog' and f.attrib.get('enable')=='1']
assert C/'gw5_snapshot_bram.v' in files and C/'acg720_ano_port.v' in files
bound={str(p):sha(p) for p in [Path(__file__),O/'supervise_proofs_retry02.py',O/'extension_top_miter.v',O/'source_freeze.json',O/'SOURCE_EQUIVALENCE_BASIS.json',O/'source_review.md',O/'source_changes.diff',original_tb,MODEL,IV,VVP,Path(sys.executable),*D.glob('*.v')]}
inputs=dict(source55=expected,baseline_source55=before,bound_files=bound,model=str(MODEL),model_sha256=sha(MODEL),
    original_top13_stimulus_sha256=sha(original_tb),integration_forced_boundaries=['old/revised.extension source payload','old/revised.telemetry.busy byte acknowledgment'],
    integration_no_boot_reset_hold_state_ticks_index_cache_or_storage_force=True,
    scope='New actual-top extension888 SP/FF integration with natural snapshot/serializer scheduling and byte-ack fixture, plus untouched original top13 stimulus separately in default and vendor branches. Existing top13 safety/RX/control forces are inherited unchanged; no physical UART/whole-flight/STA claim.')
(D/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8')
env=dict(os.environ);env.update(TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
stages=[]
def run(name,command,cwd=D,timeout=300):
    assert not (D/(name+'_exit.json')).exists()
    rec=dict(command=command,cwd=str(cwd),started_utc=utc(),parent_pid=os.getpid());start=time.monotonic()
    with (D/(name+'.stdout.log')).open('wb') as out,(D/(name+'.stderr.log')).open('wb') as err:
        p=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        rec['pid']=p.pid;(D/(name+'_process.json')).write_text(json.dumps(rec,indent=2)+'\n',encoding='utf8')
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.terminate();code=p.wait();rec['terminated_after_timeout']=True
    rec.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),seconds=time.monotonic()-start,stdout_sha256=sha(D/(name+'.stdout.log')),stderr_sha256=sha(D/(name+'.stderr.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(rec,indent=2)+'\n',encoding='utf8');stages.append(rec)
    print(json.dumps(dict(stage=name,actual_p_wait=code,seconds=rec['seconds'])),flush=True)
    assert code==0 and not rec.get('terminated_after_timeout'),(name,code,(D/(name+'.stdout.log')).read_text(errors='replace'),(D/(name+'.stderr.log')).read_text(errors='replace'))
    return (D/(name+'.stdout.log')).read_text(encoding='utf8',errors='replace')
def elaboration(exe,banks):
    s=exe.read_text(encoding='utf8');n=len(re.findall(r'\.scope module,\s*"memory"\s*"SP"',s))
    g=len(re.findall(r'\.scope module,\s*"GSR"\s*"GSR"',s));assert n==banks and g==1,(exe,n,g,banks)
    if banks:assert 'portable_simulation' not in s
    else:assert 'portable_simulation' in s
    return dict(actual_SP_instances=n,actual_GSR_instances=g,portable_FF_branch=(banks==0),vvp_sha256=sha(exe))
def crc16(data):
    c=65535
    for b in data:
        c^=b<<8
        for _ in range(8):c=((c<<1)^0x1021)&65535 if c&0x8000 else (c<<1)&65535
    return c
framing=[];integration=[]
for period in [8,12000]:
    mode=D/f'period{period}';mode.mkdir();exe=mode/'top.vvp';tag=f'integration{period}'
    run(tag+'_compile',[str(IV),'-g2012','-DGW5_USE_VENDOR_BRAM','-I',str(C),'-s','extension_top_miter','-P',f'extension_top_miter.TEST_PERIOD={period}','-o',str(exe),str(D/'extension_top_miter.v'),str(D/'top_before.v'),*map(str,files),str(MODEL)],mode)
    el=elaboration(exe,28);log=run(tag+'_vvp',[str(VVP),str(exe)],mode)
    assert 'PASS actual_v18_FF_vs_v21_vendor_SP extension888=1 SP=28' in log
    wire=mode/'wire.hex';raw=bytes(int(x,16) for x in wire.read_text(encoding='ascii').split());assert len(raw)==1932
    base_sequence=int.from_bytes(raw[2:4],'big')
    for group in range(3):
        offset=group*644
        for header,length,check in [(0xa586,224,'xor'),(0xa587,32,'xor'),(0xa588,40,'crc'),(0xa581,128,'crc'),(0xa582,96,'crc'),(0xa589,48,'crc'),(0xa585,76,'crc')]:
            frame=raw[offset:offset+length];assert int.from_bytes(frame[:2],'big')==header,(period,group,offset,header,frame[:6])
            seq=frame[4:6] if header==0xa585 else frame[2:4];assert int.from_bytes(seq,'big')==(base_sequence+group)&65535
            if check=='xor':
                c=0
                for b in frame[2:-1]:c^=b
                assert frame[-1]==c
            else:assert int.from_bytes(frame[-2:],'big')==crc16(frame[2:-2])
            offset+=length
        framing.append(dict(period=period,group=group,sequence=(base_sequence+group)&65535,bytes=644,frames=7,independent_checksums_crc=True))
    integration.append(dict(period=period,elaboration=el,wire_sha256=sha(wire),pass_lines=[s for s in log.splitlines() if s.startswith('PASS ')]))
top13=[]
for vendor in [False,True]:
    tag='top13_vendor' if vendor else 'top13_default';mode=D/tag;mode.mkdir();exe=mode/'top.vvp'
    defines=['-DGW5_USE_VENDOR_BRAM'] if vendor else []
    run(tag+'_compile',[str(IV),'-g2012',*defines,'-I',str(C),'-s','top13_root','-o',str(exe),str(D/'top_safety_tb.v'),str(D/'top13_root.v'),*map(str,files),str(MODEL)],mode)
    el=elaboration(exe,28 if vendor else 0);log=run(tag+'_vvp',[str(VVP),str(exe)],mode)
    assert 'PASS actual top/core stopped-width arm/controller/fresh/takeoff gates;' in log
    top13.append(dict(passed=True,cases=13,vendor_branch=vendor,original_stimulus_byte_identical=True,stimulus_sha256=sha(D/'top_safety_tb.v'),elaboration=el,pass_lines=[s for s in log.splitlines() if s.startswith('PASS ')]))
assert all(sha(Path(p))==h for p,h in bound.items()) and all(sha(C/n)==h for n,h in expected.items()) and all(sha(OLD/n)==h for n,h in before.items())
result=dict(passed=True,source55=expected,baseline_source55=before,inputs_sha256=sha(D/'inputs.json'),integration=integration,framing=framing,top13=top13,
    original_top13_stimulus_unchanged=True,source_fixture_tool_model_bindings_unchanged=True,stages=stages,
    exit_receipts={p.relative_to(D).as_posix():sha(p) for p in D.glob('*_exit.json')},scope=inputs['scope'])
(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,integration_periods=[8,12000],SP_instances=28,top13_default_and_vendor=True,frames=42)),flush=True)
