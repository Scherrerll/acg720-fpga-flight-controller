from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inp=json.loads((O/'inputs.json').read_text());out=json.loads((O/'final_results.json').read_text())
assert out['passed'] is True and out['case_count']==5
for name in ['B3','B4']:
    root=Path(inp['source_roots'][name]);expected=inp[name+'_source55']
    assert len(expected)==55 and all(sha(root/p)==h for p,h in expected.items())
assert sha(O/'results.json')==out['first_attempt_results_sha256']
assert sha(O/'xy_i0_attempt02/results.json')==out['retry_results_sha256']
assert sha(O/'source_stability.json')==out['source_stability_sha256']
for row in out['successful_cases'][:4]:
    assert row['exit_code']==0
    d=O/row['name'];assert sha(d/'simulation.log')==row['log_sha256'] and sha(d/'trace.csv')==row['trace_sha256']
row=out['successful_cases'][4];d=O/'xy_i0_attempt02/corrected_xy_i0'
assert row['actual_exit_code']==0 and sha(d/'simulation.log')==row['log_sha256'] and sha(d/'trace.csv')==row['trace_sha256']
diag=out['diagnosed_failure'];assert diag['actual_exit_code']==1 and diag['expected_exit_code']==1
assert sha(O/'xy_i0_attempt02/diagnose_original_cadence/simulation.log')==diag['log_sha256']
omitted=[{'path':str(p.relative_to(O)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p),'required_for_archive_verification':False} for p in sorted(O.rglob('*.vvp'))]
(O/'omitted_compiled.json').write_text(json.dumps({'scope':'Optional local rebuildable binaries, excluded from the retained-file manifest and upload.','files':omitted},indent=2)+'\n')
files=[p for p in sorted(O.rglob('*')) if p.is_file() and p.suffix!='.vvp' and 'tmp' not in p.relative_to(O).parts and '__pycache__' not in p.relative_to(O).parts and p.name!='MANIFEST.json']
manifest={'scope':'Frozen bounded Z antiwindup regressions only. Cases1-4 plus corrected-cadenceCASE5PASS; artificial-overrun failures retained. No source changes or hardware. Excludes *.vvp, tmp and caches.',
 'files':[{'path':str(p.relative_to(O)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
(O/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for r in manifest['files']:assert (O/r['path']).stat().st_size==r['bytes'] and sha(O/r['path'])==r['sha256']
print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in manifest['files']),'manifest_sha256':sha(O/'MANIFEST.json'),
 'final_results_sha256':sha(O/'final_results.json'),'report_sha256':sha(O/'REGRESSION_REPORT.md'),'inputs_sha256':sha(O/'inputs.json')},indent=2))
