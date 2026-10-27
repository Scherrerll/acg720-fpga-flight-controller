"""Freeze read-only investigation and audit-only retry inputs; never execute retry."""
from pathlib import Path
import ast,datetime,hashlib,json
D=Path(__file__).resolve().parent;O=D.parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v21/build_attempt_01';V=A/'verification';C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
def safe(path):
    p=Path(path)
    for part in p.parts:
        name=part.lower().rstrip(' .')
        assert not name.startswith('.env') and not name.endswith('.env') and '.env' not in [s.lower() for s in Path(name).suffixes]
    for q in [p,*p.parents]:assert not q.is_symlink() and not (hasattr(q,'is_junction') and q.is_junction())
    return p
sha=lambda p:hashlib.sha256(safe(p).read_bytes()).hexdigest()
read=lambda p:json.loads(safe(p).read_text(encoding='utf8'))
assert not (D/'RETRY_PREPARATION.json').exists() and not (D/'REVIEW_APPROVAL.json').exists() and not (D/'results_01').exists()
expected=read(O/'source_freeze.json')['source55'];assert len(expected)==55
assert all(sha(C/n)==sha(A/'source'/n)==h for n,h in expected.items())
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');failed=read(V/'audit_exit.json')
assert root['normal_wait_return'] and root['actual_p_wait']==1 and vendor['normal_wait_return'] and vendor['actual_p_wait']==0 and failed['normal_wait_return'] and failed['actual_p_wait']==1
assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
assert read(V/'native_synthesis_audit_failure.json')['error']=="AssertionError('SP CE does not match any remaining common-edge core snapshot FF CE')"
investigation=read(D/'CE_TOPOLOGY_INVESTIGATION.json');assert investigation['cause_confirmed'] and not investigation['audit_retry_executed']
for p,h in investigation['bound_files'].items():assert sha(Path(p))==h,p
scripts=['run_audit_retry02.py','complete_audit_retry02.py','launch_audit_retry02_hidden.py','escaped_port_adapter.py','ce_boolean.py']
for name in scripts:ast.parse((D/name).read_text())
originals=[O/n for n in ['run_synthesis.py','audit_synthesis_only.py','sp_clock_audit.py','launch_synthesis_hidden.py','seal_synthesis.py','source_freeze.json','source_review.md','SOURCE_EQUIVALENCE_BASIS.json','PROOF_BINDING.json','REUSED_BINDINGS_RECHECK.json','SYNTHESIS_REVIEW_APPROVAL.json','runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log']]
originals += [R/'firmware/B0B4/build_candidate.py',R/'analysis/20261026_z_aw_fix/build/compact_aw_v2/run_synthesis.py',R/'firmware/B0B3/qualification.json',R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
originals += [Path(p) for p in read(V/'build_input.json')['tools']]
original_bound={str(p):sha(p) for p in originals}
for p,h in read(V/'build_input.json')['bound_inputs'].items():assert sha(Path(p))==h;original_bound[p]=h
artifacts={}
for p in sorted(A.rglob('*')):
    safe(p);relative=p.relative_to(A)
    if 'tmp' in relative.parts or not p.is_file():continue
    artifacts[relative.as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
metadata={}
for p in sorted(O.rglob('*')):
    relative=p.relative_to(O)
    if 'audit_retry02' in relative.parts or 'tmp' in relative.parts or 'fsm_tmp' in relative.parts or '__pycache__' in relative.parts:continue
    safe(p)
    if p.is_file():metadata[relative.as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
record=dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepared_only=True,source55=expected,
    original_VG_sha256=sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg'),original_actual_waits=dict(vendor=0,audit=1,root=1),
    original_bound_files=original_bound,original_attempt_artifacts=artifacts,original_metadata_artifacts=metadata,retry_scripts_sha256={name:sha(D/name) for name in scripts},
    investigation_sha256=sha(D/'CE_TOPOLOGY_INVESTIGATION.json'),prepare_script_sha256=sha(Path(__file__)),
    correction='Strict local lexer completion only for explicitly declared wrapper CE input and DO output named ports with legal escaped-identifier terminating whitespace. Original protected Graph and SP auditor remain unchanged; original CE-same-net gate is rerun after explicit actual-port aliases.',
    retained_CE_gate='All28 actual SP CE pins and all627 remaining core snapshot FF CE pins must still resolve to the identical actual parent net. Exact LUT INIT/shared39 FF-Q BDD proof is additional evidence, not a waiver.',
    SYN_rerun=False,audit_retry_executed=False,PNR_started=False,
    scope='Prepared Python-only audit retry, preserving original SYN0/audit1/root1 and exact source55/VG/artifacts. Requires main and independent review before execution. Physical evaluation is separate and deprioritized.')
(D/'RETRY_PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
requirements=dict(scope='Requirements only; not an execution approval. Main creates REVIEW_APPROVAL.json after main and independent review.',
    actual_approval_file=str(D/'REVIEW_APPROVAL.json'),approved=False,reviewers=[],source55=expected,
    preparation_sha256=sha(D/'RETRY_PREPARATION.json'),original_VG_sha256=record['original_VG_sha256'],reviewed_scripts_sha256=record['retry_scripts_sha256'],
    minimum_distinct_reviewers=2,no_vendor_or_SYN_rerun=True)
(D/'REVIEW_REQUIREMENTS.json').write_text(json.dumps(requirements,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared_only=True,old_artifacts_bound=len(artifacts),old_metadata_tools_bound=len(original_bound),source55=55,original_waits=record['original_actual_waits'],audit_retry_executed=False)))
