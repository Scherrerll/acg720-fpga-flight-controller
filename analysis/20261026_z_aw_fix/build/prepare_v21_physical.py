"""One-shot v21 physical preparation, allowed only after actual successful sealed SYN.

This file can be AST-inspected while SYN runs. It never launches vendor tools.
Schema status: the original audit/root attempt actually failed with wait1 at the
strict SP CE net-identity gate. This draft deliberately rejects that state and
must not be run to generate files yet. Main must confirm any real audit_retry
completion schema before this preparer is adapted; original failures stay intact.
No CE gate is removed or relaxed here. Under its initial all0-sealed schema,
running it later creates only new physical scripts/metadata after all donor gates.
"""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,re,subprocess,sys

CONTRACT_SOURCE=r'''"""Read-only v21 actual9 proof/SP28/sealed-SYN donor contract; no vendor calls."""
from pathlib import Path
import hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent;R=O.parents[3]
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v21';C=ROOT/'canonical/source';A=ROOT/'build_attempt_01';V=A/'verification'
P18=O.parent/'compact_aw_v18';S18=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
def safe(path,root=None):
    p=Path(path)
    for part in p.parts:
        name=part.lower().rstrip(' .')
        assert not name.startswith('.env') and not name.endswith('.env') and '.env' not in [s.lower() for s in Path(name).suffixes],str(p)
    if root is not None:assert p.resolve().is_relative_to(Path(root).resolve()),str(p)
    for ancestor in [p,*p.parents]:
        assert not ancestor.is_symlink() and not (hasattr(ancestor,'is_junction') and ancestor.is_junction()),str(p)
    return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe(p).read_text(encoding='utf8'))
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate21(require_preparation=True):
    # No output or runtime physical directory is created by this validator.
    freeze=read(O/'source_freeze.json');expected=freeze['source55'];before=freeze['baseline_source55']
    assert len(expected)==len(before)==55 and {n:sha(C/n) for n in expected}==expected
    assert {n:sha(S18/n) for n in before}==before==read(P18/'source_freeze.json')['source55']
    assert sha(P18/'source_freeze.json')==freeze['baseline_source_freeze_sha256']
    assert [n for n in expected if expected[n]!=before[n]]==['acg720_ano_port.v']
    for name,key in [('source_review.md','source_review_sha256'),('SOURCE_EQUIVALENCE_BASIS.json','source_equivalence_basis_sha256'),('source_changes.diff','source_changes_diff_sha256')]:assert sha(O/name)==freeze[key]
    bound={}
    def bind(p,h=None):
        p=safe(p);actual=sha(p);assert h is None or actual==h,(str(p),h,actual);bound[str(p)]=actual
    proof=read(O/'PROOF_BINDING.json');reuse=read(O/'REUSED_BINDINGS_RECHECK.json')
    assert proof['passed'] and proof['source55']==expected and proof['baseline_source55']==before and proof['actual_proof_runner_wait']==0
    assert proof['proof_directory']=='proofs_retry02' and len(proof['exit_receipts'])==9
    assert reuse['passed'] and reuse['source55']==expected and reuse['parent_v18_source55']==before and reuse['full_source55_differs']
    assert reuse['new_v21_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
    for p,h in reuse['bound_files'].items():bind(p,h)
    D=O/proof['proof_directory'];inputs=read(D/'inputs.json');result=read(D/'RESULT.json')
    bind(D/'inputs.json',proof['inputs_sha256']);bind(D/'RESULT.json',proof['new_proof_results_sha256'])
    assert inputs['source55']==expected and inputs['baseline_source55']==before and result['passed']
    assert result['source55']==expected and result['baseline_source55']==before
    for p,h in inputs['bound_files'].items():bind(p,h)
    receipts=[]
    for rel,h in proof['exit_receipts'].items():
        p=safe(O/rel,O);bind(p,h);j=read(p)
        assert j['normal_wait_return'] and j['actual_p_wait']==0 and not j.get('terminated_after_timeout'),rel
        prefix=p.name.removesuffix('_exit.json')
        for channel in ['stdout','stderr']:bind(p.parent/(prefix+'.'+channel+'.log'),j[channel+'_sha256'])
        receipts.append({'path':str(p),'sha256':sha(p),'actual_p_wait':j['actual_p_wait']})
    root=read(O/'proof_retry02_runner_exit.json')
    bind(O/'run_proofs_retry02.py',root['runner_sha256']);bind(O/'supervise_proofs_retry02.py',root['supervisor_script_sha256'])
    assert proof['new_vendor_SP_integration']['passed'] and proof['new_vendor_SP_integration']['actual_SP_instances']==28
    assert proof['new_vendor_SP_integration']['periods']==[8,12000] and proof['new_vendor_SP_integration']['extension_bits']==888
    assert proof['new_vendor_SP_integration']['no_internal_state_force_or_preload'] and proof['new_vendor_SP_integration']['hold_and_serializer_scheduling_natural']
    assert len(result['framing'])==6 and all(x['independent_checksums_crc'] and x['bytes']==644 and x['frames']==7 for x in result['framing'])
    assert len(result['integration'])==2 and all(x['elaboration']['actual_SP_instances']==28 and x['elaboration']['actual_GSR_instances']==1 and not x['elaboration']['portable_FF_branch'] for x in result['integration'])
    for label,want_sp in [('top13_default',0),('top13_vendor',28)]:
        top=proof[label];assert top['passed'] and top['cases']==13 and top['original_stimulus_byte_identical']
        assert top['elaboration']['actual_SP_instances']==want_sp and top['elaboration']['actual_GSR_instances']==1
        assert top['stimulus_sha256']==sha(O.parent/'v4_release_proofs/top_safety_tb.v')
    assert proof['reused_core_FSM']['source_dependencies']==reuse['reused_core_FSM_dependencies']
    assert proof['reused_VY_components']['source_dependencies']==reuse['reused_VY_component_dependencies']
    for field in ['reused_core_FSM_dependencies','reused_VY_component_dependencies','six_exact_controller_dependencies']:
        for n,h in reuse[field].items():assert sha(C/n)==sha(S18/n)==h
    failed=proof['preserved_failed_attempt'];bind(O/'proof_runner_exit.json',failed['root_exit_sha256'])
    assert failed['actual_root_wait']==read(O/'proof_runner_exit.json')['actual_p_wait']==1
    # Successful sealed SYN is mandatory; mere presence of VG or partial audit is insufficient.
    syn=read(O/'SYNTHESIS_RESULT.json');manifest_path=A/'synthesis_freeze_manifest_final.json';manifest=read(manifest_path)
    summary=read(V/'synthesis_summary.json');vendor=read(V/'synthesis_exit.json');audit=read(V/'audit_exit.json');synroot=read(O/'runner_exit.json')
    assert syn['passed_SYN_only'] and syn['source55']==expected and syn['vendor_actual_wait']==syn['runner_actual_wait']==syn['audit_actual_wait']==0
    assert manifest['source_sha256']==expected and manifest['runner_actual_wait']==manifest['vendor_actual_wait']==manifest['audit_actual_wait']==0
    assert manifest['actual_SP_count']==28 and manifest['all_SP_CLK50']
    bind(manifest_path,syn['synthesis_freeze_sha256']);bind(V/'synthesis_summary.json',syn['synthesis_summary_sha256']);bind(O/'runner_exit.json',syn['root_exit_sha256'])
    for j in [vendor,audit,synroot]:assert j['normal_wait_return'] and j['actual_p_wait']==0 and not j.get('terminated_after_timeout')
    for channel in ['stdout','stderr']:bind(O/('runner.'+channel+'.log'),synroot[channel+'_sha256'])
    for j,name in [(vendor,'synthesis'),(audit,'audit')]:bind(V/(name+'.log'),j['log_sha256'])
    assert summary['passed'] and summary['source_sha256']==expected and summary['actual_p_wait']==summary['audit_actual_p_wait']==0
    vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg';vg_sha=sha(vg)
    assert re.fullmatch(r'[0-9a-f]{64}',vg_sha) and vg_sha==summary['netlist_sha256']==syn['netlist_sha256']==manifest['netlist_sha256']
    assert {n:sha(A/'source'/n) for n in expected}==expected and not (A/'source/impl/pnr').exists()
    for rel,info in manifest['artifacts'].items():bind(safe(A/rel,A),info['sha256'])
    for p,h in manifest['bound_metadata'].items():bind(p,h)
    for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('strict_SP_clock_audit.json','strict_SP_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256')]:bind(V/name,summary[key])
    sp=read(V/'strict_SP_clock_audit.json')
    assert sp['passed'] and sp['actual_SP_count']==28 and sp['all_SP_CLK50'] and sp['source55']==expected and sp['vg_sha256']==vg_sha
    assert sp['bank_indices']==list(range(28)) and len(sp['cells'])==28 and sp['READ_MODE']==0 and sp['WRITE_MODE']==1 and sp['BIT_WIDTH']==32
    assert sp['byte_enable_address']=='000f' and sp['reset_constant_zero'] and sp['all_declared_INIT_RAM_zero'] and sp['last_bank_padding_zero']
    assert sp['common_CE_matches_remaining_core_snapshot'] and sp['remaining_extension_FF']==[]
    bind(O/'sp_clock_audit.py',sp['auditor_sha256'])
    reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py';bind(reader,'a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc')
    graph=load('v21_physical_original_graph',reader).Graph(vg)
    recomputed=load('v21_physical_bound_SP_auditor',O/'sp_clock_audit.py').audit_sp(graph,vg)
    assert all(sp[k]==value for k,value in recomputed.items())
    helper=R/'firmware/B0B4/build_candidate.py';bind(helper,'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84')
    for n in ['source_freeze.json','PROOF_BINDING.json','REUSED_BINDINGS_RECHECK.json','SYNTHESIS_RESULT.json','SYNTHESIS_REVIEW_APPROVAL.json','SYNTHESIS_PREPARATION.json','source_review.md','SOURCE_EQUIVALENCE_BASIS.json']:bind(O/n)
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];changes={n:h for n,h in expected.items() if h!=b3[n]};assert len(changes)==10
    result={'passed':True,'source55':expected,'parent_v18_source55':before,'VG_sha256':vg_sha,'bound_inputs':bound,'actual_proof_receipts':receipts,
        'actual_SP_count':28,'all_SP_CLK50':True,'READ_MODE':0,'WRITE_MODE':1,'BIT_WIDTH':32,'byte_enable_address':'000f','common_CE_matches_core':True,'last_bank_padding_zero':True,
        'functional_scope':proof['scope'],'forced_boundaries':inputs['integration_forced_boundaries'],'baseline':'Exact frozen v18 full source55; complete v21 differs only at top, with full parent dependency proof reuse limited to unchanged files.'}
    if require_preparation:
        preparation=read(O/'PHYSICAL_PREPARATION.json');assert preparation['VG_sha256']==vg_sha and preparation['source55']==expected
        assert preparation['input_binding_sha256']==sha(O/'PHYSICAL_INPUT_BINDING.json')
        frozen=read(O/'PHYSICAL_INPUT_BINDING.json');assert frozen['validation']==result
        for name,h in preparation['new_scripts_sha256'].items():assert sha(O/name)==h
    return result
'''

B=Path(__file__).resolve().parent;R=B.parents[2];O=B/'compact_aw_v21';P=B/'compact_aw_v19'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v21';PROFILE='physical_p3r0_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
def one(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)

def main():
    # The required gates run before the first write into v21 metadata.
    assert (O/'SYNTHESIS_RESULT.json').is_file() and (ROOT/'build_attempt_01/synthesis_freeze_manifest_final.json').is_file(),'Wait for actual vendor/root/audit0 and seal_synthesis.py'
    namespace={'__file__':str(O/'physical_input_contract.py'),'__name__':'v21_preparation_readonly_contract'}
    exec(compile(CONTRACT_SOURCE,str(O/'physical_input_contract.py'),'exec'),namespace)
    validation=namespace['validate21'](require_preparation=False);vg=validation['VG_sha256']
    assert not (ROOT/PROFILE).exists() and not (O/PROFILE).exists()
    names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']
    new_names=names+['physical_input_contract.py']
    assert not any((O/n).exists() for n in new_names) and not (O/'PHYSICAL_PREPARATION.json').exists() and not (O/'PHYSICAL_INPUT_BINDING.json').exists()
    parents={n:sha(P/n) for n in names};parent_vg=read(P/'SYNTHESIS_RESULT.json')['netlist_sha256']
    (O/'physical_input_contract.py').write_text(CONTRACT_SOURCE,encoding='utf8',newline='\n')
    text=(P/'run_physical.py').read_text(encoding='utf8').replace('compact_aw_v19','compact_aw_v21').replace(parent_vg,vg)
    text=one(text,"PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'")
    text=one(text,'from validation_contract import verify_contract','from physical_input_contract import validate21')
    text=text.replace('verify_contract(check_proof=True)','validate21(require_preparation=True)')
    text=one(text,"proof['guard_binding_sha256']==functional_contract['guard_binding_sha256']","len(proof['exit_receipts'])==9 and functional_contract['actual_SP_count']==28")
    a=text.index("    evidence += [O/n for n in ['SYNTHESIS_RESULT.json'")
    b=text.index("    bound={str(p):",a)
    text=text[:a]+"    evidence += [Path(p) for p in functional_contract['bound_inputs']]\n    evidence += [O/'physical_input_contract.py',O/'PHYSICAL_INPUT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']\n    evidence=list(dict.fromkeys(evidence))\n"+text[b:]
    a=text.index("    write('functional_evidence_binding.json',")
    b=text.index("    tmp=VERIFY/'tmp';",a)
    text=text[:a]+"    write('functional_evidence_binding.json',{'passed':True,'schema':'Real v21 nine proof receipts, inputs and actual vendor-SP integration; parent v18 dependency reuse retains its original full source55','proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'input_binding_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'actual_proof_receipts':functional_contract['actual_proof_receipts'],'actual_SP_count':28,'all_SP_CLK50':True,'READ_MODE':0,'WRITE_MODE':1,'common_CE_matches_core':True,'last_bank_padding_zero':True,'scope':functional_contract['functional_scope'],'forced_boundaries':functional_contract['forced_boundaries']})\n"+text[b:]
    text=text.replace("'v4_source55':prior","'parent_v18_source55':prior").replace("'v4_source55_unchanged':True","'parent_v18_source55_unchanged':True")
    text=text.replace('Deferred exact-v19 map2 P3/R0','Deferred sealed exact-v21 map2 P3/R0').replace('Fresh exact-v19 VG','Fresh sealed exact-v21 VG').replace('compact_aw_v21 exact-VG P3/R0','compact_aw_v21 sealed exact-VG P3/R0')
    assert "sys.argv[1] in ['3']" in text and 'retiming_resource' not in text and 'physical_constraints.cst' not in text
    (O/'run_physical.py').write_text(text,encoding='utf8',newline='\n')
    for name in ['launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']:
        text=(P/name).read_text(encoding='utf8').replace('compact_aw_v19','compact_aw_v21').replace(parent_vg,vg)
        if name=='seal_terminal.py':
            text=one(text,'from validation_contract import verify_contract','from physical_input_contract import validate21')
            text=text.replace('verify_contract(check_proof=True)','validate21(require_preparation=True)')
        elif name=='independent_raw_review.py':
            a=text.index("proof=read(O/'PROOF_BINDING.json');")
            b=text.index("log=(V/'physical.log').read_text",a)
            text=text[:a]+"proof=read(O/'PROOF_BINDING.json');sp=read(R/'out/z_aw_fix_20261026/compact_aw_v21/build_attempt_01/verification/strict_SP_clock_audit.json');binding=read(O/'PHYSICAL_INPUT_BINDING.json')\nchecks['v21_nine_actual_proof_receipts']=proof['passed'] and proof['source55']==expected and len(proof['exit_receipts'])==9 and all(sha(O/n)==h and read(O/n)['normal_wait_return'] and read(O/n)['actual_p_wait']==0 for n,h in proof['exit_receipts'].items())\nchecks['sealed_actual28SP_CLK50_modes_CE_padding']=sp['passed'] and sp['actual_SP_count']==28 and sp['all_SP_CLK50'] and sp['READ_MODE']==0 and sp['WRITE_MODE']==1 and sp['BIT_WIDTH']==32 and sp['common_CE_matches_remaining_core_snapshot'] and sp['last_bank_padding_zero'] and sp['vg_sha256']==binding['validation']['VG_sha256']\nchecks['unchanged_bound_inputs']=all(sha(Path(p))==h for p,h in binding['validation']['bound_inputs'].items())\n"+text[b:]
        (O/name).write_text(text,encoding='utf8',newline='\n')
    (O/PROFILE).mkdir()
    for name in new_names:ast.parse((O/name).read_text(encoding='utf8'),filename=str(O/name))
    write(O/'PHYSICAL_INPUT_BINDING.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Actual sealed SYN and strict SP audit + actual nine successful proof receipt/log/input bindings; no physical qualification','preparer_path':str(Path(__file__)),'preparer_sha256':sha(Path(__file__)),'validation':validation})
    cp=subprocess.run([sys.executable,'-B','-X','utf8',str(O/'preflight_physical_recipe.py')],stdin=subprocess.DEVNULL,capture_output=True,text=True)
    (O/'physical_preflight.stdout.log').write_text(cp.stdout,encoding='utf8',newline='\n');(O/'physical_preflight.stderr.log').write_text(cp.stderr,encoding='utf8',newline='\n')
    write(O/'PHYSICAL_PREFLIGHT_EXIT.json',{'actual_completedprocess_returncode':cp.returncode,'normal_return':True,'command':cp.args,'stdout_sha256':sha(O/'physical_preflight.stdout.log'),'stderr_sha256':sha(O/'physical_preflight.stderr.log')})
    assert cp.returncode==0,(cp.stdout,cp.stderr)
    diff=''
    for name in names:diff+=''.join(difflib.unified_diff((P/name).read_text(encoding='utf8').splitlines(True),(O/name).read_text(encoding='utf8').splitlines(True),fromfile='v19/'+name,tofile='v21/'+name))
    (O/'PHYSICAL_SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
    write(O/'PHYSICAL_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Sealed actual-v21 standard single-slot P3/R0 physical-only preparation. No vendor started by this preparer; main alone controls physical scheduling.',
        'profile':PROFILE,'ROOT':str(ROOT),'CANON':str(ROOT/'canonical/source'),'DONOR':str(ROOT/'build_attempt_01'),'ATTEMPT':str(ROOT/PROFILE),'receipt_directory':str(O/PROFILE),
        'source55':validation['source55'],'parent_v18_source55':validation['parent_v18_source55'],'VG_sha256':vg,'actual_SYN_vendor_wait':0,'actual_SYN_runner_wait':0,'actual_audit_wait':0,
        'actual_SP_count':28,'all_SP_CLK50':True,'READ_MODE':0,'WRITE_MODE':1,'BIT_WIDTH':32,'same_CE_and_last_bank_padding_bound':True,
        'input_binding_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'strict_SP_clock_audit_sha256':sha(ROOT/'build_attempt_01/verification/strict_SP_clock_audit.json'),
        'actual_proof_receipt_count':9,'functional_scope':validation['functional_scope'],'forced_boundaries':validation['forced_boundaries'],
        'parent_scripts_sha256':parents,'new_scripts_sha256':{n:sha(O/n) for n in new_names},'derivation_sha256':sha(O/'PHYSICAL_SCRIPT_DERIVATION.diff'),'preflight_actual_returncode':cp.returncode,'physical_Tcl_preflight_sha256':sha(O/'PHYSICAL_TCL_PREFLIGHT.json'),'AST_parse_passed':True,
        'unchanged':'Complete original frozen CST (including observer_reset CLOCK_LOC), SDC, source55, exact sealed VG, P3/R0/map2/replicate0/route_maxfan23/usercode0000B0B4; no DSP-location, retiming, clock, logic or threshold option added.',
        'strict_gates':['fullroute','real20ns/50MHz','all5 slacks nonnegative','setup and hold endpoints0','18pins and B4 identity','actual vendor and runner normal waits0'],
        'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3'],'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})
    contract=namespace['validate21'](require_preparation=True)
    assert contract['passed'] and not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
    assert all(sha(P/n)==h for n,h in parents.items())
    print(json.dumps({'prepared':True,'profile':PROFILE,'actual_sealed_VG_sha256':vg,'SP_count':28,'actual_proof_receipts':9,'Tcl_preflight_actual_returncode':cp.returncode,'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'vendor_started':False,'runtime_attempt_created':False}))

if __name__=='__main__':main()
