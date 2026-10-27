"""Add own-child cancellation only if .p flow falls back to the same existing LOC run."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_incplace_loc3_followup'
assert not (O/'physical_p3r0_incplace_loc3_01/runner_process.json').exists()
p=O/'run_physical.py';t=p.read_text();before=hashlib.sha256(p.read_bytes()).hexdigest()
extra=r'''
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
'''
assert t.count('def main():\n')==1;t=t.replace('def main():\n',extra+'\ndef main():\n')
old="helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)";assert t.count(old)==1
t=t.replace(old,"monitored_run_phase(helper,[str(helper.GOWIN),str(execution)],SOURCE,expected)");ast.parse(t);p.write_text(t)
p=O/'seal_terminal.py';t=p.read_text();marker="paths=[REPORT/'runner_exit.json'";assert t.count(marker)==1
t=t.replace(marker,"if (V/'incremental_fallback_cancel.json').exists():classification='cancelled_incremental_fallback'\n"+marker)
t=t.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()","paths += [V/n for n in ['incremental_fallback_cancel.json','incremental_flow_observation.json']]\npaths=[p for p in paths if p.is_file()];copies.mkdir()");ast.parse(t);p.write_text(t)
(O/'MONITOR_PREPARATION.json').write_text(json.dumps({'scope':'Own live Popen child only; reject duplicate ordinary fallback after .p interface test. Preserve actual waits; no other process touched.',
    'runner_before_sha256':before,'runner_after_sha256':hashlib.sha256((O/'run_physical.py').read_bytes()).hexdigest(),
    'seal_script_sha256':hashlib.sha256((O/'seal_terminal.py').read_bytes()).hexdigest(),'PNR_started':False},indent=2)+'\n')
print('Own-child duplicate fallback monitor prepared; not launched.')
