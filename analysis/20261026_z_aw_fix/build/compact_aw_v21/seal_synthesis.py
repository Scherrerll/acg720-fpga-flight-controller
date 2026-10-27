"""Seal actual completed v21 SYN_ONLY/28SP evidence; never infer process exits."""
from pathlib import Path
import datetime,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v21/build_attempt_01';S=A/'source';V=A/'verification'
C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
def safe(path,root=None):
    p=Path(path)
    for part in p.parts:
        name=part.lower().rstrip(' .')
        assert not name.startswith('.env') and not name.endswith('.env') and '.env' not in [s.lower() for s in Path(name).suffixes],str(p)
    if root is not None:assert p.resolve().is_relative_to(Path(root).resolve()),str(p)
    for ancestor in [p,*p.parents]:
        assert not ancestor.is_symlink() and not (hasattr(ancestor,'is_junction') and ancestor.is_junction()),str(p)
    return p
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def read(path):return json.loads(safe(path).read_text(encoding='utf8'))
manifest=A/'synthesis_freeze_manifest_final.json';result_path=O/'SYNTHESIS_RESULT.json'
assert not manifest.exists() and not result_path.exists() and not (S/'impl/pnr').exists()
root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json');summary=read(V/'synthesis_summary.json')
for receipt in [root,vendor,audit]:
    assert receipt['normal_wait_return'] is True and receipt['actual_p_wait']==0 and not receipt.get('terminated_after_timeout')
assert summary['passed'] is True and summary['actual_p_wait']==vendor['actual_p_wait'] and summary['audit_actual_p_wait']==audit['actual_p_wait']
for channel in ['stdout','stderr']:assert root[channel+'_sha256']==sha(O/('runner.'+channel+'.log'))
for receipt,name in [(vendor,'synthesis'),(audit,'audit')]:
    assert safe(receipt['log']).resolve()==(V/(name+'.log')).resolve()
    assert receipt['log_sha256']==sha(V/(name+'.log'))
assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
assert root['runner_sha256']==sha(O/'run_synthesis.py') and root['supervisor_sha256']==sha(O/'launch_synthesis_hidden.py')
assert root['seal_synthesis_sha256']==sha(Path(__file__))
approval=read(O/'SYNTHESIS_REVIEW_APPROVAL.json');expected=read(O/'source_freeze.json')['source55']
assert len(expected)==55 and root['source55']==expected and approval['approved'] is True and approval['source55']==expected and len(set(approval['reviewers']))>=2
for name,key in [('source_freeze.json','source_freeze_sha256'),('PROOF_BINDING.json','proof_binding_sha256'),('REUSED_BINDINGS_RECHECK.json','reused_bindings_sha256'),('SYNTHESIS_REVIEW_APPROVAL.json','review_approval_sha256')]:assert sha(O/name)==root[key]
assert approval['run_synthesis_sha256']==sha(O/'run_synthesis.py') and approval['audit_synthesis_only_sha256']==sha(O/'audit_synthesis_only.py') and approval['sp_clock_audit_sha256']==sha(O/'sp_clock_audit.py')
assert summary['source_sha256']==expected and {n:sha(S/n) for n in expected}=={n:sha(C/n) for n in expected}==expected
assert {p.relative_to(C).as_posix() for p in C.rglob('*') if safe(p,C).is_file()}==set(expected)
vg=S/'impl/gwsynthesis/acg720_ano_port.vg';vg_sha=sha(vg);assert summary['netlist_sha256']==vg_sha
checks=[('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),
        ('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('strict_SP_clock_audit.json','strict_SP_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256')]
for name,key in checks:assert sha(V/name)==summary[key],(name,key)
native=read(V/'native_synthesis_audit.json');mapped=read(V/'mapped_audit.json');gain=read(V/'gain_port_audit.json');ff=read(V/'strict_ff_clock_audit.json');sp=read(V/'strict_SP_clock_audit.json')
assert native['passed'] is True and native['source55']==expected and native['netlist_sha256']==vg_sha and native['project_sha256']==sha(S/'acg720_ano_port.gprj')
assert native['hook_sha256']==sha(O/'audit_synthesis_only.py')
for name,key in checks[1:]:assert native[key]==summary[key],(name,key)
assert mapped['passed'] is True and mapped['source_sha256']==expected and mapped['netlist_sha256']==vg_sha
assert mapped['resource_xml_sha256']==sha(S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml')
assert gain['passed'] is True and gain['netlist_sha256']==vg_sha and len(gain['top_ports'])==18
assert gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
assert ff['passed'] is True and ff['all_FF_CLK50'] is True and not ff['bad'] and ff['vg_sha256']==vg_sha
assert sp['passed'] is True and sp['actual_SP_count']==28 and sp['all_SP_CLK50'] is True and sp['source55']==expected and sp['vg_sha256']==vg_sha
assert sp['auditor_sha256']==sha(O/'sp_clock_audit.py') and sp['bank_indices']==list(range(28)) and len(sp['cells'])==28
assert sp['READ_MODE']==0 and sp['WRITE_MODE']==1 and sp['BIT_WIDTH']==32 and sp['byte_enable_address']=='000f'
assert sp['reset_constant_zero'] is True and sp['all_declared_INIT_RAM_zero'] is True and sp['last_bank_padding_zero'] is True
assert sp['common_CE_matches_remaining_core_snapshot'] is True and sp['remaining_extension_FF']==[]
build_input=read(V/'build_input.json');execution=read(V/'synthesis_input.json')
assert build_input['source_sha256']==execution['source_sha256']==expected
for inventory in ['bound_inputs','tools']:
    for path,digest in build_input[inventory].items():assert sha(path)==digest,path
assert execution['runner_sha256']==sha(O/'run_synthesis.py') and execution['execution_tcl_sha256']==sha(A/'synth_only.tcl')
tcl=(A/'synth_only.tcl').read_text(encoding='utf8')
assert len(re.findall(r'^run syn\s*$',tcl,re.M))==1 and not re.search(r'^run\s+(?:all|pnr)\b',tcl,re.M)
assert sha(V/'executed_run_synthesis.py')==sha(O/'run_synthesis.py') and sha(V/'executed_audit_synthesis_only.py')==sha(O/'audit_synthesis_only.py')
items={}
for p in sorted(A.rglob('*')):
    relative=p.relative_to(A)
    safe(p,A) # Screen every component before is_file/read/hash.
    if 'tmp' in relative.parts or not p.is_file():continue
    items[relative.as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
bound_metadata={str(O/n):sha(O/n) for n in ['runner_exit.json','runner_process.json','runner.stdout.log','runner.stderr.log','source_freeze.json','PROOF_BINDING.json',
    'REUSED_BINDINGS_RECHECK.json','SYNTHESIS_REVIEW_APPROVAL.json','run_synthesis.py','audit_synthesis_only.py','sp_clock_audit.py','launch_synthesis_hidden.py','seal_synthesis.py']}
manifest.write_text(json.dumps(dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Actual v21 successful SYN_ONLY, original strict mapped/gain/18port/FF clock gates and added actual28SP CLK50 audit; compiler scratch excluded. No PNR/physical qualification.',
    source_sha256=expected,netlist_sha256=vg_sha,artifacts=items,bound_metadata=bound_metadata,
    runner_actual_wait=root['actual_p_wait'],vendor_actual_wait=vendor['actual_p_wait'],audit_actual_wait=audit['actual_p_wait'],root_exit_sha256=sha(O/'runner_exit.json'),
    strict_SP_clock_audit_sha256=sha(V/'strict_SP_clock_audit.json'),actual_SP_count=28,all_SP_CLK50=True),indent=2)+'\n',encoding='utf8')
result_path.write_text(json.dumps(dict(passed_SYN_only=True,source55=expected,netlist_sha256=vg_sha,vendor_actual_wait=vendor['actual_p_wait'],runner_actual_wait=root['actual_p_wait'],audit_actual_wait=audit['actual_p_wait'],
    synthesis_summary_sha256=sha(V/'synthesis_summary.json'),synthesis_freeze_sha256=sha(manifest),strict_SP_clock_audit_sha256=sha(V/'strict_SP_clock_audit.json'),
    actual_SP_count=28,all_SP_CLK50=True,root_exit_sha256=sha(O/'runner_exit.json'),PNR_started=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(sealed=True,vendor_actual_wait=0,runner_actual_wait=0,audit_actual_wait=0,VG=vg_sha,SP_count=28,all_SP_CLK50=True,PNR_started=False)))
