"""Seal only the owned replication1 attempt after real normal physical termination."""
from pathlib import Path
import datetime,gzip,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v5/physical_p3r0_repl1_01';V=A/'verification';D=A.parent/'build_attempt_01';F=O/'final'
VG='2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9'
HELPER='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(data,indent=2)+'\n')
def main():
    assert not F.exists(),'Never overwrite terminal seal'
    inp=json.loads((V/'build_input.json').read_bytes());expected=inp['source_sha256'];ex=json.loads((V/'physical_exit.json').read_bytes())
    assert ex['normal_wait_return'] is True and ex['ended_utc'] and ex['actual_p_wait'] in [0,1]
    assert ex['pid']==13152 and ex['parent_pid']==39312
    assert sha(V/'physical.log')==ex['log_sha256']
    assert expected['position/mtf_xyz_hold_control.v']=='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
    assert inp['physical_options']=={'place':3,'route':0,'map_option':2,'replicate_resources':1,'timing_driven':1}
    sourcechecks=[]
    for root,values in [(Path(inp['canonical_override']),expected),(A/'source',expected),(D/'source',expected),(R/'firmware/B0B4/source',inp['original_B4_source55']),(R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source',inp['v4_source55'])]:
        assert len(values)==55 and all(sha(root/p)==h for p,h in values.items()),str(root)
        sourcechecks.append({'path':str(root),'file_count':55,'all_bound_hashes_match':True})
    assert sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg')==sha(D/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
    assert sha(R/'firmware/B0B4/build_candidate.py')==HELPER
    din=json.loads((D/'verification/build_input.json').read_bytes());assert din['synthesis_options']=={'map_option':2,'replicate_resources':0}
    for name,key in [('synthesis_summary.json','donor_synthesis_summary_sha256'),('synthesis_exit.json','donor_synthesis_exit_sha256'),('mapped_audit.json','donor_mapped_audit_sha256'),('gain_port_audit.json','donor_gain_port_audit_sha256'),('strict_ff_clock_audit.json','donor_strict_ff_clock_audit_sha256')]:assert sha(D/'verification'/name)==inp[key]
    baseline=(A.parent/'physical_p3r0_01/physical.tcl').read_bytes();executed=(A/'physical.tcl').read_bytes()
    assert executed.replace(b'set_option -replicate_resources 1',b'set_option -replicate_resources 0')==baseline
    assert b'set_option -global_freq 50' in executed
    pin=json.loads((V/'physical_input.json').read_bytes());assert sha(A/'physical.tcl')==pin['tcl_sha256']
    log=(V/'physical.log').read_text(errors='replace')
    values=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log,re.I)]
    audit=json.loads((V/'physical_audit.json').read_bytes()) if (V/'physical_audit.json').exists() else None
    passed=ex['actual_p_wait']==0 and audit is not None and audit['passed'] is True
    if ex['actual_p_wait']==1:
        assert (V/'build_failure.json').is_file()
        if values and any(values):classification='routefail'
        elif 'open_project' in log and ('XML' in log or 'project file' in log):classification='xml_startupfail'
        else:raise AssertionError('Unexpected command failure: preserve and ask root before sealing')
    else:
        assert audit is not None,'Unexpected missing audit after normal wait0: preserve and ask root'
        for rel,h in audit['evidence_sha256'].items():assert sha(A/rel)==h,rel
        if passed:
            assert (V/'build_result.json').is_file();classification='physical_gate_pass'
            assert all(audit['criteria'].values()) and audit['period_ns']==20 and audit['fmax_mhz']>=50
            assert audit['setup_violated_endpoints']==audit['hold_violated_endpoints']==0
            assert all(x['worst_slack_ns']>=0 for x in audit['checks'].values())
        else:
            assert (V/'build_failure.json').is_file() and audit['criteria']['full_route'] is True
            failed={k for k,v in audit['criteria'].items() if not v}
            assert failed <= {'fmax_at_least_50','setup_hold_endpoints_zero','all_five_nonnegative'},'Unexpected dependency gate failure: ask root'
            classification='fullroute_timingfail'
    rawpaths=[V/n for n in ['build_input.json','physical_input.json','physical_process.json','physical_exit.json','physical.log','project_serialization_check.json']]
    rawpaths += [V/n for n in ['physical_audit.json','build_result.json','build_failure.json'] if (V/n).is_file()]
    rawpaths += [A/'physical.tcl',A/'source/physical.gprj',A/'source/acg720_ano_port.sdc',A/'source/acg720_ano_port.cst']
    rawpaths += [A/'source/impl/pnr'/('acg720_ano_port.'+s) for s in ['tr','rpt.txt'] if (A/'source/impl/pnr'/('acg720_ano_port.'+s)).is_file()]
    provenance=[O/n for n in ['run_physical_p3r0_repl1.py','source_freeze.json','runner_changes.diff','TRIAL_PROVENANCE.json','EXECUTION_CHECK.json','runner_process.json','runner.stdout.log','runner.stderr.log','seal_terminal.py']]
    external=rawpaths+[A/'source/impl/gwsynthesis/acg720_ano_port.vg',D/'source/impl/gwsynthesis/acg720_ano_port.vg',R/'firmware/B0B4/build_candidate.py']+provenance
    external += [D/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']]
    external += [A/'source/impl/pnr'/n for n in ['acg720_ano_port.fs','acg720_ano_port.pr','device.cfg','acg720_ano_port.pin.html'] if (A/'source/impl/pnr'/n).is_file()]
    originals={str(p):(p.stat().st_size,p.stat().st_mtime_ns,sha(p)) for p in external}
    F.mkdir();(F/'raw').mkdir()
    archives=[]
    for p in rawpaths:
        raw=p.read_bytes();z=p.suffix in {'.tr'} or p.name.endswith('.rpt.txt');name=p.name+('.gz' if z else '')
        archived=gzip.compress(raw,mtime=0) if z else raw
        target=F/'raw'/name
        with target.open('xb') as f:f.write(archived)
        assert (gzip.decompress(target.read_bytes()) if z else target.read_bytes())==raw
        archives.append({'original_absolute_path':str(p),'original_repository_relative_path':p.relative_to(R).as_posix(),'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'archived_path':target.relative_to(F).as_posix(),'archived_bytes':len(archived),'archived_sha256':sha(target),'compression':'gzip.compress(bytes,mtime=0)' if z else 'none'})
    for p in external:
        size,mtime,h=originals[str(p)];assert (p.stat().st_size,p.stat().st_mtime_ns,sha(p))==(size,mtime,h),'Raw source changed during seal: '+str(p)
    data={'scope':'Frozen owned v5 P3/R0 replication1 actual terminal; physical gate only, no delivery/hardware acceptance.','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':classification,'actual_p_wait':ex['actual_p_wait'],'normal_wait_return':ex['normal_wait_return'],'physical_started_utc':ex['started_utc'],'physical_ended_utc':ex['ended_utc'],'vendor_pid':ex['pid'],'helper_pid':ex['parent_pid'],'qualified_physical':passed,'accepted_for_delivery':False,'physical_options':inp['physical_options'],'donor_synthesis_options':din['synthesis_options'],'only_tcl_delta':'replicate_resources0->1','actual_tcl_sha256':sha(A/'physical.tcl'),'helper_sha256':HELPER,'exact_donor_vg_sha256':VG,'source55':expected,'source55_checks':sourcechecks,'unrouted_reports':values,'archived_raw_files':archives,'external_evidence':{p.relative_to(R).as_posix():{'bytes':originals[str(p)][0],'sha256':originals[str(p)][2]} for p in external},'raw_sources_verified_stable_after_copy':True,'FS_PR_VG_not_copied':True}
    data.update(TR_exists=(A/'source/impl/pnr/acg720_ano_port.tr').is_file(),FS_exists=(A/'source/impl/pnr/acg720_ano_port.fs').is_file(),physical_audit_exists=audit is not None,physical_command_returned_EOF='PHYSICAL_COMMAND_RETURNED_EOF' in log,elapsed_seconds=(datetime.datetime.fromisoformat(ex['ended_utc'])-datetime.datetime.fromisoformat(ex['started_utc'])).total_seconds())
    if classification=='routefail':assert data['TR_exists'] is False and data['FS_exists'] is False
    if audit:data.update(period_ns=audit['period_ns'],fmax_mhz=audit['fmax_mhz'],slacks_ns={n:x['worst_slack_ns'] for n,x in audit['checks'].items()},setup_violated_endpoints=audit['setup_violated_endpoints'],hold_violated_endpoints=audit['hold_violated_endpoints'],all_criteria=audit['criteria'])
    dump(F/'FINAL_STATUS.json',data)
    summary=f"Actual wait={ex['actual_p_wait']}; classification={classification}; qualified physical={passed}; accepted for delivery=False."
    readme='# V5 P3/R0 replication1 terminal evidence\n\n'+summary+'\n\nThis is the one root-authorized fresh physical-only trial. The exact v5 donor was synthesized at map2/replication0; execution changed only replication0 to1 and kept P3R0, map2, TD1, 20ns/50MHz, the exact helper, VG, source55 and all physical gates unchanged. The installed primary Tcl guide was read before mutation; its provenance is in the runner folder.\n\nFINAL_STATUS.json binds the actual normal exit, terminal log, raw gate evidence and unchanged source/donor hashes. The raw/ subtree preserves exact small receipt bytes; TR and RPT, if present, use deterministic gzip with mtime0. Decompression recovers the original bytes. FS, PR and VG remain external and are only hash-bound. No binary is selected or delivered by this seal. Every terminal classification is based on actual receipts; return0 alone is not qualification.\n\nOriginal absolute and repository paths are workstation provenance, not portable links. Some external evidence and omitted large vendor artifacts remain outside this subtree. This is not a standalone reproducible build fixture. No canonical source, old proof/index/manifest, other job, archived11 data, Git, serial or hardware state was changed. No further profile is authorized.\n'
    with (F/'README.md').open('x',encoding='utf8',newline='\n') as f:f.write(readme)
    files=[p for p in F.rglob('*') if p.is_file()]
    dump(F/'MANIFEST.json',{'scope':'Only this new terminal seal subtree; external raw evidence is bound in FINAL_STATUS.json.','files':[{'path':p.relative_to(F).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)],'manifest_self_hash_policy':'Not included; reported after seal.'})
    print(json.dumps({'classification':classification,'qualified_physical':passed,'actual_p_wait':ex['actual_p_wait'],'final_status_sha256':sha(F/'FINAL_STATUS.json'),'manifest_sha256':sha(F/'MANIFEST.json'),'raw_archive_files':len(archives),'total_files':len(list(p for p in F.rglob('*') if p.is_file()))},indent=2))
if __name__=='__main__':main()
