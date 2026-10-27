"""Export a genuinely qualified native RTL-project B0B4 run; never program hardware."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[2];B4=R/'firmware/B0B4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def safe(path):
    assert path.resolve().is_relative_to(R) and not path.name.lower().startswith('.env') and not path.name.lower().endswith('.env') and '.env' not in [x.lower() for x in path.suffixes]
    return path
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant',choices=['v13_native_p3','v13_native_p2','v4_native_p3','v4_native_p2','v4_fan100_native_p3','v4_fan100_native_p2'])
    parser.add_argument('--independent-review-sha256',required=True);args=parser.parse_args()
    tag,place=args.variant.rsplit('_p',1);label=f'physical_p{place}r0_01';M=O/('compact_aw_'+tag)
    A=R/'out/z_aw_fix_20261026'/('compact_aw_'+tag)/label;S=A/'source';V=A/'verification';D=M/label
    terminal=read(D/'TERMINAL_MANIFEST.json');review=read(D/'INDEPENDENT_RAW_REVIEW.json');physical=read(V/'physical_audit.json')
    assert sha(D/'INDEPENDENT_RAW_REVIEW.json')==args.independent_review_sha256
    assert terminal['passed'] and terminal['vendor_actual_p_wait']==terminal['runner_actual_p_wait']==0
    assert review['passed'] and all(review['checks'].values()) and physical['passed'] and all(physical['criteria'].values())
    assert physical['period_ns']==review['period_ns']==20 and physical['fmax_mhz']>=50 and review['fmax_mhz']>=50
    assert physical['setup_violated_endpoints']==physical['hold_violated_endpoints']==0
    assert review['violated_endpoints']=={'setup':0,'hold':0}
    assert set(physical['checks'])=={'setup','hold','recovery','removal','minimum_pulse_width'}
    assert all(x['worst_slack_ns']>=0 for x in physical['checks'].values()) and all(x>=0 for x in review['slacks_ns'].values())
    expected=terminal['source55'];assert len(expected)==55 and {n:sha(S/n) for n in expected}==expected
    assert {n:sha(R/'out/z_aw_fix_20261026'/('compact_aw_'+tag)/'canonical/source'/n) for n in expected}==expected
    for name,digest in review['raw_sha256'].items():assert sha(safe(R/name))==digest
    for name,item in terminal['artifacts'].items():assert sha(safe(R/name))==item['sha256']
    syn=read(V/'native_synthesis_audit.json');assert syn['passed'] and syn['source55']==expected
    assert sha(S/'impl/gwsynthesis/acg720_ano_port.vg')==syn['netlist_sha256']==terminal['vg_sha256']
    proof=read(M/'PROOF_BINDING.json');assert proof['passed'] and proof['source55']==expected and proof['actual_proof_runner_wait']==0
    family='v4' if tag.startswith('v4_') else 'v13'
    origin=O/'v4_release_proofs' if family=='v4' else O/'compact_aw_v13/proofs'
    origin_binding=O/'v4_release_proofs/RESULT.json' if family=='v4' else O/'compact_aw_v13/PROOF_BINDING.json'
    assert sha(origin_binding)==proof['parent_proof_sha256'] and read(origin_binding)['source55']==expected
    origin_exit=read(origin/'runner_exit.json');assert origin_exit['normal_wait_return'] and origin_exit['actual_p_wait']==0
    top_result=origin/'top_safety_results.json' if family=='v4' else origin/'top/top_safety_results.json'
    assert read(top_result)['passed']
    runtime=R.parents[1]/'runtime_xy_pi_20261026'
    graph=runtime/'tools/read_cones.py';baseline=runtime/'candidates/idle_gain_integral_ce/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    parent_xml=R/f'out/z_aw_fix_20261026/compact_aw_{family}/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    gain=R/'analysis/20261026_z_aw_fix/build/compact_aw_v2/run_synthesis.py'
    mapped=read(V/'mapped_audit.json');resources=read(V/'resource_comparison.json')
    assert sha(graph)==mapped['graph_reader_sha256']=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
    assert sha(baseline)==mapped['reference_resources_sha256'] and sha(parent_xml)==resources['parent_xml_sha256']
    assert sha(gain)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
    state=read(O.parent/'CONTINUATION_STATE.json')
    assert (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(state['updated_utc'])).total_seconds()<120
    assert not any(x['status']=='running' for x in state['runs']) and all(state['protected_source55_match'].values())
    current_families=['v8','v9','v10','v4_timing','v4_loc3_followup','v4_incplace_loc3_followup','v4_p1_followup',
        'v4_partial_floorplan_followup','v4_data_routing_followup','v4_clockbuf1_followup','v11','v12','v13','v13_map1','v13_native','v4_native','v4_rep1_followup','v4_fan100_native','v14']
    for base in [O/('compact_aw_'+tag) for tag in current_families]:
        # Historical missing exits stay unknown; no retrospective process receipt is invented.
        if (base/'runner_process.json').is_file():assert (base/'runner_exit.json').is_file(),str(base)
        for process in base.glob('physical_*/runner_process.json'):assert (process.parent/'runner_exit.json').is_file(),str(process)
    initial=read(O.parent/'handoff_20261026/SOURCE_BINDINGS.json')['source_sha256']['B0B4_unpromoted_prototype']
    assert {n:sha(B4/'source'/n) for n in initial}==initial
    vendor_names=['physical_audit.json','physical_exit.json','physical_process.json','physical_input.json','build_input.json',
        'physical.log','build_result.json','native_synthesis_audit.json','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json',
        'resource_comparison.json','project_serialization_check.json','donor_evidence_binding.json']
    required=[V/n for n in vendor_names]
    required += [D/n for n in ['TERMINAL_MANIFEST.json','INDEPENDENT_RAW_REVIEW.json','runner_exit.json','runner_process.json']]
    required += [M/n for n in ['PROOF_BINDING.json','source_freeze.json','GATE_ADAPTATION.json','audit_synthesis.py','native_physical_audit.py','run_physical.py']]
    required += [A/'physical.tcl',S/'acg720_ano_port.gprj',S/'impl/gwsynthesis/acg720_ano_port.vg',S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']
    required += [S/'impl/pnr'/n for n in ['acg720_ano_port.fs','acg720_ano_port.tr','acg720_ano_port.rpt.txt','device.cfg']]
    required += [origin_binding,origin/'inputs.json',origin/'runner_exit.json',top_result,graph,baseline,parent_xml,gain]
    assert all(p.is_file() for p in required) and shutil.disk_usage(B4).free>512*1024*1024
    release=B4/'release';evidence=B4/'evidence/selected';backup=O.parent/'implementation_history/B4_initial_prototype_full55'
    assert not any(p.exists() for p in [release,evidence,backup,B4/'qualification.json',O.parent/'PROMOTION.json'])
    # Everything above is read-only. Preserve the complete initial prototype before promotion.
    backup.mkdir(parents=True)
    for name in initial:
        dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B4/'source'/name,dest)
    assert {n:sha(backup/n) for n in initial}==initial
    for name in expected:shutil.copy2(S/name,B4/'source'/name)
    assert {n:sha(B4/'source'/n) for n in expected}==expected
    release.mkdir();evidence.mkdir(parents=True);compressed=[]
    def preserve(path,name=None):
        dest=evidence/(name or path.name);assert not dest.exists()
        if path.suffix in ['.vg','.tr','.txt','.log','.xml']:
            dest=dest.with_name(dest.name+'.gz')
            with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as stream:stream.write(path.read_bytes())
            compressed.append({'path':dest.relative_to(B4).as_posix(),'uncompressed_sha256':sha(path)})
        else:shutil.copy2(path,dest)
    fs=S/'impl/pnr/acg720_ano_port.fs';shutil.copy2(fs,release/'acg720_ano_port.fs')
    for name in vendor_names:preserve(V/name)
    # Explicit remaining names avoid collisions between physical and functional runner receipts.
    for name in ['TERMINAL_MANIFEST.json','INDEPENDENT_RAW_REVIEW.json','runner_exit.json','runner_process.json']:preserve(D/name)
    for name in ['source_freeze.json','GATE_ADAPTATION.json','audit_synthesis.py','native_physical_audit.py','run_physical.py']:preserve(M/name)
    for path in [A/'physical.tcl',S/'acg720_ano_port.gprj',S/'impl/gwsynthesis/acg720_ano_port.vg',S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml',
                 S/'impl/pnr/acg720_ano_port.tr',S/'impl/pnr/acg720_ano_port.rpt.txt',S/'impl/pnr/device.cfg']:preserve(path)
    preserve(M/'PROOF_BINDING.json','functional_proof_binding.json');preserve(origin_binding,'functional_origin_proof_binding.json')
    preserve(origin/'inputs.json','functional_proof_inputs.json');preserve(origin/'runner_exit.json','functional_proof_runner_exit.json')
    preserve(top_result,'top13_results.json');preserve(graph,'read_cones.py');preserve(gain,'gain_port_auditor.py')
    reference=evidence/'replay_reference';baseline_dest=reference/'candidates/idle_gain_integral_ce/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    baseline_dest.parent.mkdir(parents=True);shutil.copy2(baseline,baseline_dest)
    parent_dest=reference/'parent_resource.xml';shutil.copy2(parent_xml,parent_dest)
    replay={'graph_reader':'evidence/selected/read_cones.py','gain_auditor':'evidence/selected/gain_port_auditor.py',
        'runtime_reference_root':'evidence/selected/replay_reference','parent_resource_xml':'evidence/selected/replay_reference/parent_resource.xml',
        'original_parent_resource_path':str(parent_xml),'parent_resource_repo_relative':parent_xml.relative_to(R).as_posix(),
        'graph_sha256':sha(graph),'gain_auditor_sha256':sha(gain),
        'reference_resource_sha256':sha(baseline),'parent_resource_sha256':sha(parent_xml),'place':int(place)}
    promotion={'promoted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variant':args.variant,'profile':label,'selected_attempt':str(A),
        'selected_terminal_manifest_sha256':sha(D/'TERMINAL_MANIFEST.json'),'independent_review_sha256':args.independent_review_sha256,
        'source55_before':initial,'source55_after':expected,'initial_prototype_backup':str(backup),'installed_B0B4':False,'hardware_confirmation_required':True,
        'exporter_sha256':sha(Path(__file__))}
    (O.parent/'PROMOTION.json').write_text(json.dumps(promotion,indent=2)+'\n',encoding='utf8')
    qualification={'passed':True,'workflow':'native_RTL_project_SYN_audit_PNR_one_vendor_process',
        'scope':'Offline functional/source/full physical acceptance only; hardware installation/cold boot/flight separate.',
        'source_sha256':expected,'physical':physical,'variant':args.variant,'profile':label,'netlist_sha256':syn['netlist_sha256'],
        'release_bitstream':'release/acg720_ano_port.fs','bitstream_sha256':sha(fs),'compressed_artifacts':compressed,
        'external_build_inputs':{str(p):sha(p) for p in [A/'physical.tcl',fs,S/'impl/gwsynthesis/acg720_ano_port.vg']},
        'installed_B0B4':False,'true_cold_boot_verified':False,'hardware_activity_started':False,'replay_support':replay,
        'tools':read(V/'build_input.json')['tools'],
        'combined_vendor_actual_wait':0,'runner_actual_wait':0,'standalone_SYN_p_wait_claimed':False,
        'functional_binding_sha256':sha(M/'PROOF_BINDING.json'),'effective_build_recipe':'evidence/selected/physical.tcl',
        'canonical_build_tcl_note':'Immutable source55 build.tcl is the authored baseline. Actual native Tcl and executed audit hook are archived separately; no source inputs were rewritten.'}
    (B4/'qualification.json').write_text(json.dumps(qualification,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'exported':True,'workflow':qualification['workflow'],'source_files':55,'fmax_mhz':physical['fmax_mhz'],'installed':False,
                      'next':'Update final docs, seal manifest, verify package before any fresh hardware-state request.'}))
if __name__=='__main__':main()
