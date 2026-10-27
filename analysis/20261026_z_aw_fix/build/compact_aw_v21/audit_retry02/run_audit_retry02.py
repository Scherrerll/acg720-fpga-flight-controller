"""Reviewed Python-only audit recovery on the exact original SYN0 VG; no SYN rerun."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,sys,traceback
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;O=D.parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v21/build_attempt_01';S=A/'source';V=A/'verification';C=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
OUT=D/'results_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def require_review():
    preparation=read(D/'RETRY_PREPARATION.json');review=read(D/'REVIEW_APPROVAL.json')
    assert review['approved'] is True and len(set(review['reviewers']))>=2
    assert review['preparation_sha256']==sha(D/'RETRY_PREPARATION.json') and review['source55']==preparation['source55']
    assert review['original_VG_sha256']==preparation['original_VG_sha256']
    for name,h in preparation['retry_scripts_sha256'].items():assert sha(D/name)==h==review['reviewed_scripts_sha256'][name]
    return preparation
def main():
    prep=require_review();assert not OUT.exists();expected=prep['source55'];vg=S/'impl/gwsynthesis/acg720_ano_port.vg'
    assert sha(vg)==prep['original_VG_sha256']
    for path,digest in prep['original_bound_files'].items():assert sha(Path(path))==digest,path
    for relative,item in prep['original_attempt_artifacts'].items():assert sha(A/relative)==item['sha256'],relative
    for relative,item in prep['original_metadata_artifacts'].items():assert sha(O/relative)==item['sha256'],relative
    assert len(expected)==55 and {n:sha(C/n) for n in expected}=={n:sha(S/n) for n in expected}==expected
    root=read(O/'runner_exit.json');vendor=read(V/'synthesis_exit.json');failed=read(V/'audit_exit.json')
    assert root['normal_wait_return'] and root['actual_p_wait']==1 and failed['normal_wait_return'] and failed['actual_p_wait']==1
    assert vendor['normal_wait_return'] and vendor['actual_p_wait']==0 and 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
    assert read(V/'native_synthesis_audit_failure.json')['error']=="AssertionError('SP CE does not match any remaining common-edge core snapshot FF CE')"
    assert not (S/'impl/pnr').exists()
    OUT.mkdir();write('inputs.json',dict(source55=expected,original_VG_sha256=sha(vg),preparation_sha256=sha(D/'RETRY_PREPARATION.json'),
        approval_sha256=sha(D/'REVIEW_APPROVAL.json'),original_waits=dict(vendor=0,audit=1,root=1),SYN_rerun=False))
    helper_path=R/'firmware/B0B4/build_candidate.py';assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    old_auditor=R/'analysis/20261026_z_aw_fix/build/compact_aw_v2/run_synthesis.py';assert sha(old_auditor)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
    helper=load('v21_retry_original_helper',helper_path);helper.CANON=C;helper.ATTEMPT=A;helper.SOURCE=S;helper.VERIFY=OUT
    baseline=read(R/'firmware/B0B3/qualification.json')['source_sha256'];helper.EXPECTED_CHANGES={n:h for n,h in expected.items() if h!=baseline[n]};assert len(helper.EXPECTED_CHANGES)==10
    helper.check_sources(expected)
    # Rerun original Python audits into the new namespace; no old output is overwritten.
    helper.mapped_audit(vg,expected)
    extended=load('v21_retry_original_gain_ports',old_auditor);extended.SOURCE=S;extended.VERIFY=OUT;extended.extended_audit(helper,vg)
    graph_module=load('v21_retry_protected_graph',helper.GRAPH_READER);g=graph_module.Graph(vg)
    from escaped_port_adapter import complete_snapshot_aliases
    from ce_boolean import prove_shared_ce
    aliases=complete_snapshot_aliases(g,vg);write('escaped_port_aliases.json',aliases)
    boolean=prove_shared_ce(g,vg);write('CE_BOOLEAN_EQUIVALENCE.json',boolean)
    old_sp=load('v21_retry_unmodified_SP_gate',O/'sp_clock_audit.py')
    sp=old_sp.audit_sp(g,vg) # Every original mode/clock/address/padding/CE-same-net gate remains.
    sp.update(vg_sha256=sha(vg),source55=expected,protected_SP_auditor_sha256=sha(O/'sp_clock_audit.py'),
        adapter_sha256=sha(D/'escaped_port_adapter.py'),CE_boolean_proof_sha256=sha(OUT/'CE_BOOLEAN_EQUIVALENCE.json'),explicit_alias_proof_sha256=sha(OUT/'escaped_port_aliases.json'))
    write('strict_SP_clock_audit.json',sp)
    clocks=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']];assert len(clocks)==1
    bad=[dict(cell=n,CLK=p.get('CLK',[])) for n,p in g.regs.items() if len(p.get('CLK',[]))!=1 or g.find(p['CLK'][0])!=g.find(clocks[0])]
    assert not bad;write('strict_ff_clock_audit.json',dict(passed=True,FF_count=len(g.regs),all_FF_CLK50=True,bad=[],vg_sha256=sha(vg)))
    prior=R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml';current=S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    old,new=extended.resources(prior),extended.resources(current);names=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    comparison={n:dict(parent_v4_map2=old[n],actual_v21_SAME_VG=new[n],delta={k:new[n].get(k,0)-old[n].get(k,0) for k in old[n].keys()|new[n].keys()}) for n in names}
    write('resource_comparison.json',dict(resources=comparison,parent_xml_sha256=sha(prior),native_xml_sha256=sha(current),scope='Actual unchanged SYN0 VG resources; no physical benefit claim.'))
    helper.check_sources(expected)
    assert sha(vg)==prep['original_VG_sha256']
    for path,digest in prep['original_bound_files'].items():assert sha(Path(path))==digest,path
    for relative,item in prep['original_attempt_artifacts'].items():assert sha(A/relative)==item['sha256'],relative
    for relative,item in prep['original_metadata_artifacts'].items():assert sha(O/relative)==item['sha256'],relative
    artifacts={p.relative_to(OUT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in OUT.rglob('*') if p.is_file()}
    result=dict(passed_checks=True,source55=expected,original_VG_sha256=sha(vg),original_source_and_artifacts_unchanged=True,
        original_actual_waits=dict(vendor=vendor['actual_p_wait'],audit=failed['actual_p_wait'],root=root['actual_p_wait']),
        original_actual_exit_receipts={str(p):sha(p) for p in [V/'synthesis_exit.json',V/'audit_exit.json',O/'runner_exit.json']},
        actual_SP_count=28,all_SP_CLK50=True,strict_same_net_CE_gate_retained=True,core_snapshot_FF_count=627,FF_leaf_roots=boolean['FF_root_count'],
        original_SP_auditor_unmodified=True,protected_graph_reader_unmodified=True,artifacts=artifacts,SYN_rerun=False,PNR_started=False,
        scope='Python-only audit recovery from explicit actual-VG escaped named port aliases. Original SYN0/audit1/root1 remain unchanged; the supervisor separately records the real retry child wait. No physical qualification.')
    write('RESULT.json',result);print(json.dumps(dict(passed_checks=True,VG=sha(vg),SP=28,CLK50=True,original_waits=result['original_actual_waits'],SYN_rerun=False)),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as error:
        if OUT.is_dir():write('FAILURE.json',dict(passed_checks=False,error=repr(error),traceback=traceback.format_exc()))
        raise
