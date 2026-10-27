"""One isolated native-project incremental-placement experiment; unchanged real50MHz gates."""
from pathlib import Path
import ast, datetime, hashlib, json, shutil, subprocess, sys
O=Path(__file__).resolve().parent; R=O.parents[2]
OLD=O/'compact_aw_v4_native'; NEW=O/'compact_aw_v4_incplace_native'
OLDROOT=R/'out/z_aw_fix_20261026/compact_aw_v4_native'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v4_incplace_native'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not NEW.exists() and not ROOT.exists()
NEW.mkdir(); ROOT.mkdir(parents=True)
expected=json.loads((OLD/'source_freeze.json').read_text(encoding='utf8'))['source55']
assert len(expected)==55 and all(sha(OLDROOT/'canonical/source'/n)==h for n,h in expected.items())
for n in expected:
    p=ROOT/'canonical/source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(OLDROOT/'canonical/source'/n,p)
for n in ['source_freeze.json','source_review.md','PROOF_BINDING.json','GATE_ADAPTATION.json']:
    shutil.copy2(OLD/n,NEW/n)
names=['run_physical.py','audit_synthesis.py','native_physical_audit.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']
originals={}
for n in names:
    text=(OLD/n).read_text(encoding='utf8');originals[n]=sha(OLD/n)
    text=text.replace('compact_aw_v4_native','compact_aw_v4_incplace_native')
    if n=='run_physical.py':
        text=text.replace('OWNED=False','''OWNED=False
SEED_ORIGINAL=R/'out/z_aw_fix_20261026/compact_aw_v4_native/physical_p3r0_01/source/impl/pnr/acg720_ano_port.p'
SEED_SHA='9a1a9ece54fc617dd20391ab23349a4c6ee4b7934bb717a88bcea537aed9f990'
SEED=A/'donor/native_v4_P3R0.p'

def monitored_native_run(helper, command, cwd, expected):
    import datetime, re, subprocess, time
    helper.check_sources(expected)
    log=V/'physical.log'
    record=dict(stage='physical',command=command,cwd=str(cwd),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=os.getpid(),stdin='DEVNULL',create_no_window=True,log=str(log),runner_sha256=sha(Path(__file__)))
    cancelled=False; fallback=[]
    with log.open('wb') as output:
        proc=subprocess.Popen(command,cwd=cwd,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        record['pid']=proc.pid;write('physical_process.json',record)
        while proc.poll() is None:
            time.sleep(.5)
            current=log.read_text(errors='replace')
            fallback=[line for line in current.splitlines() if 'matching(' in line and 'threshold' in line and 'default' in line]
            if fallback:
                parent=R/'out/z_aw_fix_20261026/compact_aw_v4_native/physical_p3r0_01/verification'
                old=read(parent/'build_input.json')
                assert old['source_sha256']==expected and old['period_ns']==20
                assert old['physical_options']==dict(place=3,route=0,map_option=2,replicate_resources=0,timing_driven=1)
                assert read(V/'native_synthesis_audit.json')['netlist_sha256']==read(parent/'native_synthesis_audit.json')['netlist_sha256']
                assert 'SYNTHESIS_AUDIT_RETURNED_EOF' in current and PLACE==3
                receipt=dict(reason='Native context incremental matching fell back to already completed identical native v4 SYN/PNR; cancel only this own child via live Popen handle.',vendor_message=fallback,pid=proc.pid,parent_pid=os.getpid(),exact_command=command,parent_input_sha256=sha(parent/'build_input.json'),log_prefix_sha256=sha(log))
                if proc.poll() is None:
                    write('incremental_fallback_cancel.json',receipt);proc.terminate();cancelled=True
                break
        code=proc.wait();output.flush()
    record.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_p_wait=code,normal_wait_return=True,log_sha256=sha(log))
    write('physical_exit.json',record)
    current=log.read_text(errors='replace')
    ratios=[float(x) for x in re.findall(r'matching\\(([\\d.]+)\\)',current,re.I)]
    write('incremental_flow_observation.json',dict(requested_interface='native original RTL project, run syn then inc_place .p then run pnr',matching_percent_reports=ratios,fallback_detected=bool(fallback),incremental_use_proven=bool(ratios and min(ratios)>=80 and not fallback),cancelled_duplicate_fallback=cancelled,actual_vendor_wait=code,original_seed_unchanged=sha(SEED_ORIGINAL)==SEED_SHA,copied_seed_unchanged=sha(SEED)==SEED_SHA))
    assert code==0 and not cancelled,('Actual vendor nonzero/cancelled duplicate fallback',code,cancelled)
    helper.check_sources(expected)
''')
        text=text.replace("'puts SYNTHESIS_AUDIT_RETURNED_EOF','flush stdout','run pnr',", "'puts SYNTHESIS_AUDIT_RETURNED_EOF','flush stdout',f'set_option -inc_place {{{SEED.as_posix()}}}','run pnr',")
        text=text.replace("evidence += [parent,helper_path]", "assert sha(SEED_ORIGINAL)==SEED_SHA\n    evidence += [parent,helper_path,SEED_ORIGINAL]")
        text=text.replace("A.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,S);V.mkdir()", "A.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,S);V.mkdir()\n    SEED.parent.mkdir();shutil.copy2(SEED_ORIGINAL,SEED);assert sha(SEED)==SEED_SHA")
        text=text.replace("helper.run_phase('physical',[str(helper.GOWIN),str(execution)],S,expected)","monitored_native_run(helper,[str(helper.GOWIN),str(execution)],S,expected)")
        text=text.replace("'project_sha256':sha(S/'acg720_ano_port.gprj'),'tcl_sha256'", "'incremental_seed_sha256':SEED_SHA,'incremental_seed_source':str(SEED_ORIGINAL),'project_sha256':sha(S/'acg720_ano_port.gprj'),'tcl_sha256'")
    if n=='seal_terminal.py':
        text=text.replace("classification='full_gate_pass'", "classification='cancelled_duplicate_incremental_fallback' if (V/'incremental_fallback_cancel.json').is_file() else 'full_gate_pass'")
        text=text.replace("'physical_audit.json','build_result.json'", "'incremental_flow_observation.json','incremental_fallback_cancel.json','physical_audit.json','build_result.json'")
    ast.parse(text);(NEW/n).write_text(text,encoding='utf8')
for place in ['2','3']:(NEW/f'physical_p{place}r0_01').mkdir()
# Evaluate only the pure Tcl constructor, not build/dispatch code.
tree=ast.parse((NEW/'run_physical.py').read_text(encoding='utf8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build_tcl')
env=dict(Path=Path,sys=sys,O=NEW,SEED=ROOT/'physical_p3r0_01/donor/native_v4_P3R0.p')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<tcl-constructor>','exec'),env)
tcl=env['build_tcl']((ROOT/'canonical/source/build.tcl').read_text(encoding='utf8').splitlines(),3)
assert tcl.count('set_option -inc_place ')==1 and tcl.index('run syn')<tcl.index('SYNTHESIS_AUDIT_RETURNED_EOF')<tcl.index('set_option -inc_place ')<tcl.index('run pnr')
assert 'set_option -global_freq 50' in tcl and 'set_option -place_option 3' in tcl
syntax=subprocess.run([sys.executable,'-B','-X','utf8','-c','import sys; import tkinter; t=tkinter.Tcl(); assert t.call("info","complete",sys.stdin.read())==1'],input=tcl,text=True,capture_output=True)
assert syntax.returncode==0,syntax.stderr
out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Only native context plus inc_place .p; exact v4 source55, original20ns/50MHz timing/pin/identity gates, no LOC additions',source55=expected,parent_scripts_sha256=originals,new_scripts_sha256={n:sha(NEW/n) for n in names},native_physical_auditor_byte_unchanged=sha(NEW/'native_physical_audit.py')==sha(OLD/'native_physical_audit.py'),Tcl_info_complete=True,Tcl_preflight=tcl,incremental_seed_sha256=sha(OLDROOT/'physical_p3r0_01/source/impl/pnr/acg720_ano_port.p'),duplicate_fallback_cancel='Only exact-own live vendor handle after successful SYN hook and verified identical prior failed native flow')
(NEW/'PREPARATION.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,scripts=len(names),source_files=len(expected),Tcl_info_complete=True,native_physical_auditor_byte_unchanged=out['native_physical_auditor_byte_unchanged'])))
