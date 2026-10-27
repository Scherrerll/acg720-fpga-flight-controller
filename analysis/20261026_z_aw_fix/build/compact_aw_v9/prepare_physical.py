"""Two targeted v9 trials: fresh P3R0 and copied-v4 incremental P3R0."""
from pathlib import Path
import ast,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
summary=read(R/'out/z_aw_fix_20261026/compact_aw_v9/build_attempt_01/verification/synthesis_summary.json')
sx=read(O/'runner_exit.json');px=read(O/'proofs_retry02/runner_exit.json');proof=read(O/'proofs_retry02/results.json')
assert summary['passed'] and sx['actual_p_wait']==px['actual_p_wait']==0 and sx['normal_wait_return'] and px['normal_wait_return']
assert proof['passed'] and proof['source55']==summary['source_sha256']
vg=summary['netlist_sha256'];oldvg='5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e'
items={};texts={}
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    donor=O.parent/'compact_aw_v8'/name
    text=donor.read_text().replace('v8','v9').replace('v7','v4').replace(oldvg,vg)
    text=text.replace('2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad','ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642')
    text=text.replace('proofs_completion02','proofs_retry02').replace("proof['source55']['v9']","proof['source55']")
    if name=='physical_snapshot.py':
        needle="for place in [3,2]:\n    label=f'physical_p{place}r0_01';"
        assert text.count(needle)==1
        text=text.replace(needle,"for label in ['physical_p3r0_01','physical_p3r0_inc_v4_01']:\n    ")
    ast.parse(text);dest=O/name;assert not dest.exists();dest.write_text(text);texts[name]=text
    items[name]={'donor_sha256':sha(donor),'derived_sha256':sha(dest)}

inc=texts['run_physical.py']
inc,n=re.subn(r"assert len\(sys.argv\)==2[^\n]+;PLACE=int\(sys.argv\[1\]\)","assert len(sys.argv)==1;PLACE=3",inc,count=1);assert n==1
inc=inc.replace("LABEL=f'physical_p{PLACE}r0_01'","LABEL='physical_p3r0_inc_v4_01'")
extra=r'''
SEED_ORIGINAL=R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.pr'
SEED_SHA='ba20959930d4ddac2f4841d3ce4962d4ee1c84c2b65feaf004b9def3a6f76a1e'
SEED=ATTEMPT/'donor/v4_P3R0.pr'
SEED_AUDIT=R/'analysis/20261026_z_aw_fix/build/raw_terminal_receipts/frozen_11_terminal_20261026/compact_v4_p3r0/physical_audit.json'

def monitored_run_phase(helper,command,cwd,expected):
    # The live Popen handle identifies exactly the vendor child created here.
    # Cancellation never performs a broad PID/name lookup.
    import subprocess,time
    helper.check_sources(expected);log=VERIFY/'physical.log'
    record={'stage':'physical','command':command,'cwd':str(cwd),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'stdin':'DEVNULL','create_no_window':True,'log':str(log),'runner_sha256':sha(Path(__file__)),'parent_pid':os.getpid()}
    cancelled=False
    with log.open('wb') as output:
        proc=subprocess.Popen(command,cwd=cwd,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        record['pid']=proc.pid;write('physical_process.json',record)
        print('incremental vendor PID',proc.pid,flush=True)
        while proc.poll() is None:
            time.sleep(.5)
            current=log.read_text(errors='replace')
            if 'PA2136' in current:
                fresh=ROOT/'physical_p3r0_01/verification/physical_input.json'
                fin=json.loads(fresh.read_text())
                assert fin['donor_netlist_sha256']==VG_SHA and fin['source_sha256']==expected and fin['period_ns']==20
                cancellation={'requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Vendor PA2136 below80 matching automatically falls back to the same already-launched fresh P3R0 trial.',
                    'pid':proc.pid,'parent_pid':os.getpid(),'exact_command':command,'process_identity':'Live handle of this runner own Popen child; no PID/name lookup.',
                    'vendor_message':[line for line in current.splitlines() if 'PA2136' in line],
                    'fresh_input':str(fresh),'fresh_input_sha256':sha(fresh),'log_prefix_sha256':sha(log)}
                if proc.poll() is None:
                    write('incremental_fallback_cancel.json',cancellation);proc.terminate();cancelled=True
                break
        code=proc.wait()
    record.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_p_wait=code,normal_wait_return=True,
        log_sha256=sha(log),cancelled_duplicate_fallback=cancelled)
    write('physical_exit.json',record)
    text=log.read_text(errors='replace');ratios=[float(x) for x in re.findall(r'matching\(([\d.]+)\)',text,re.I)]
    write('incremental_flow_observation.json',{'requested':True,'matching_percent_reports':ratios,
        'fallback_detected':'PA2136' in text,'incremental_use_proven':bool(ratios and min(ratios)>=80 and 'PA2136' not in text),
        'seed_read_reported':str(SEED.as_posix()) in text or str(SEED) in text,'actual_vendor_wait':code,
        'source_seed_unchanged':sha(SEED_ORIGINAL)==SEED_SHA,'copied_seed_unchanged':sha(SEED)==SEED_SHA,
        'note':'Physical qualification depends on fresh actual route/STA gates even when flow effect is unproven.'})
    print('incremental actual vendor wait',code,'cancelled fallback',cancelled,flush=True)
    assert code==0 and 'PA2136' not in text,('incremental vendor nonzero/cancelled fallback',code,cancelled)
    helper.check_sources(expected)
'''
marker='def main():\n';assert inc.count(marker)==1;inc=inc.replace(marker,extra+'\n'+marker)
marker="    evidence += [O/'proofs_retry02/results.json',O/'proofs_retry02/runner_exit.json']\n"
assert inc.count(marker)==1
inc=inc.replace(marker,marker+"    seed_audit=json.loads(SEED_AUDIT.read_text())\n    assert seed_audit['criteria']['full_route'] and seed_audit['period_ns']==20 and seed_audit['fmax_mhz']==49.456 and seed_audit['source_sha256']==prior\n    assert sha(SEED_ORIGINAL)==SEED_SHA==seed_audit['evidence_sha256']['source\\\\impl\\\\pnr\\\\acg720_ano_port.pr']\n    evidence += [SEED_ORIGINAL,SEED_AUDIT]\n")
marker='    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n';assert inc.count(marker)==1
inc=inc.replace(marker,marker+"    SEED.parent.mkdir();shutil.copy2(SEED_ORIGINAL,SEED);assert sha(SEED)==SEED_SHA\n    write('incremental_seed_before.json',{'original':str(SEED_ORIGINAL),'copied':str(SEED),'sha256':SEED_SHA,'seed_audit_sha256':sha(SEED_AUDIT),'seed_is_timing_failed_reference_only':True})\n")
marker="    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')\n";assert inc.count(marker)==1
inc=inc.replace(marker,"    assert not any(c in SEED.as_posix() for c in '{}[]$;')\n    tcl=tcl.replace('run pnr\\n','set_option -inc_pnr {'+SEED.as_posix()+'}\\nrun pnr\\n');assert tcl.count('set_option -inc_pnr ')==1\n"+marker)
inc=inc.replace("    write('build_input.json',common);write('physical_input.json',common)","    common.update(incremental_seed=str(SEED),incremental_seed_sha256=SEED_SHA,seed_audit_sha256=sha(SEED_AUDIT))\n    write('build_input.json',common);write('physical_input.json',common)")
marker="helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)";assert inc.count(marker)==1
inc=inc.replace(marker,"monitored_run_phase(helper,[str(helper.GOWIN),str(execution)],SOURCE,expected)")
inc=inc.replace('Fresh exact-VG v9 physical-only trial','v9 exact-VG incremental physical trial with copied v4 seed')
ast.parse(inc);(O/'run_incremental.py').write_text(inc)

sup=texts['launch_physical_hidden.py']
sup=sup.replace("assert len(sys.argv)==2 and sys.argv[1] in ['2','3']","assert len(sys.argv)==1")
sup=sup.replace("PLACE=sys.argv[1];O=BASE/f'physical_p{PLACE}r0_01'","PLACE='3';O=BASE/'physical_p3r0_inc_v4_01'")
sup=sup.replace("BASE/'run_physical.py'","BASE/'run_incremental.py'").replace("str(runner),PLACE]","str(runner)]")
ast.parse(sup);(O/'launch_incremental_hidden.py').write_text(sup)

for source,destination in [('seal_terminal.py','seal_incremental.py'),('independent_raw_review.py','independent_incremental_raw_review.py')]:
    text=texts[source]
    if source=='seal_terminal.py':
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'"
        assert text.count(old)==1;text=text.replace(old,"assert len(sys.argv)==1;label='physical_p3r0_inc_v4_01'")
        marker="paths=[REPORT/'runner_exit.json'";assert text.count(marker)==1
        text=text.replace(marker,"if (V/'incremental_fallback_cancel.json').exists():classification='cancelled_incremental_fallback'\n"+marker)
        text=text.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()", "paths += [V/n for n in ['incremental_seed_before.json','incremental_flow_observation.json','incremental_fallback_cancel.json']]\npaths=[p for p in paths if p.is_file()];copies.mkdir()")
    else:
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3']\nlabel=f'physical_p{sys.argv[1]}r0_01'"
        assert text.count(old)==1;text=text.replace(old,"assert len(sys.argv)==1\nlabel='physical_p3r0_inc_v4_01'")
    ast.parse(text);(O/destination).write_text(text)
items.update({name:{'derived_sha256':sha(O/name)} for name in ['run_incremental.py','launch_incremental_hidden.py','seal_incremental.py','independent_incremental_raw_review.py']})
(O/'physical_runner_derivation.json').write_text(json.dumps({'scope':'Same physical gates. Two targeted trials, no clock/exception changes. PA2136 fallback is cancelled via the exact own Popen handle, with actual waits preserved.',
    'source55':summary['source_sha256'],'VG_sha256':vg,'seed_sha256':'ba20959930d4ddac2f4841d3ce4962d4ee1c84c2b65feaf004b9def3a6f76a1e','items':items},indent=2)+'\n')
print(json.dumps({'VG_sha256':vg,'prepared':['fresh_P3R0','copied_v4_incremental_P3R0'],'PNR_launched':False},indent=2))
