"""Export a manually reviewed, genuinely qualified B0B4 run. Never programs hardware."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,importlib.util,json,re,shutil,sys

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('b4_release_evidence',REPO/'firmware/B0B4/verify_release.py')
validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)
sha=validation.sha
def read(path):
    validation.safe_local(path,REPO)
    return json.loads(Path(path).read_text(encoding='utf8',errors='strict'))


class EvidenceCollector:
    """Plan and verify immutable inputs before promotion; archive exact bytes later."""
    def __init__(self, source, expected, origins):
        self.source,self.expected=Path(source),expected
        self.origins={k:validation.evidence_key(v) for k,v in origins.items()}
        self.files,self.tools,self.written,self.versions={},{},set(),{}
        self.invalid_failed_inputs={}
        self.repo=Path(self.origins['repo']).resolve()

    def in_repo(self,path):
        validation.evidence_key(path)
        # Windows Path containment compares normalized path components, including case.
        return Path(path).resolve().is_relative_to(self.repo)

    def prerequisite(self,path,digest):
        key=validation.evidence_key(path)
        assert not self.in_repo(key),'Repository dependencies must be archived and hashed'
        assert validation.original_identity(key) in validation.known_toolchain(self.origins['repo']),('Unknown toolchain prerequisite',key)
        original=validation.safe_local(Path(key),Path(Path(key).anchor))
        assert original.is_file() and sha(original)==digest,('Original toolchain prerequisite changed',key)
        if key in self.tools:assert self.tools[key]['sha256']==digest
        self.tools[key]={'sha256':digest,'bytes':original.stat().st_size,'scope':'Explicit original toolchain prerequisite; not bundled or executed by release verification'}

    def check(self,path,digest):
        key=validation.evidence_key(path)
        if self.in_repo(key):
            assert Path(key).suffix.lower() not in {'.exe','.dll'},'Repository tool binaries cannot be bundled'
            self.blob(key,digest)
        elif validation.original_identity(key) in validation.known_external_data(self.origins['repo']):self.blob(key,digest)
        else:self.prerequisite(key,digest)

    def historical(self,original,saved,digest):
        original,saved=validation.evidence_key(original),validation.evidence_key(saved)
        assert self.in_repo(original) and self.in_repo(saved),'Historical versions must stay in repository'
        self.blob(saved,digest)
        self.versions.setdefault(original,{})[digest]=saved

    def blob(self,path,expected=None):
        key=validation.evidence_key(path)
        if expected is not None:key=self.versions.get(key,{}).get(expected,key)
        external=not self.in_repo(key)
        assert not external or validation.original_identity(key) in validation.known_external_data(self.origins['repo']),('Unknown external archived data',key)
        original=validation.safe_local(Path(key),Path(Path(key).anchor) if external else REPO)
        assert original.is_file(),('Missing required evidence',key)
        digest=sha(original)
        if expected is not None:assert digest==expected,('Declared evidence changed',key)
        if key in self.files:
            assert self.files[key]['sha256']==digest,('Evidence changed during preflight',key)
        else:
            compression='gzip' if original.suffix.lower() in {'.vg','.tr','.pr','.log','.txt','.p','.csv','.vvp'} else 'none'
            # Short content-addressed names also work below long Windows checkouts.
            # A truncated-name collision is rejected by the full SHA256 in _write.
            archive='evidence/selected/objects/'+digest[:24]+('.gz' if compression=='gzip' else '')
            if '/source/' in key:
                name=key.rsplit('/source/',1)[1]
                if self.expected.get(name)==digest:archive='source/'+name;compression='none'
            self.files[key]={'archive_path':archive,'sha256':digest,'bytes':original.stat().st_size,'compression':compression}
        return original.read_bytes()

    def read(self,path,expected=None):return json.loads(self.blob(path,expected).decode('utf8'))

    def size(self,path,expected=None):
        key=validation.evidence_key(path)
        if expected is not None:key=self.versions.get(key,{}).get(expected,key)
        return self.tools[key]['bytes'] if key in self.tools else len(self.blob(key))

    def tree(self,root):
        root=validation.safe_local(root,REPO)
        assert root.is_dir(),('Missing evidence directory',str(root))
        for path in sorted(root.rglob('*')):
            # Names are screened before is_file, read or hash; caches are not evidence.
            try:validation.evidence_key(path)
            except SystemExit:continue
            if any(p in {'tmp','fsm_tmp','__pycache__'} for p in path.relative_to(root).parts):continue
            validation.safe_local(path,REPO)
            if path.is_file():self.blob(path)

    def close_dependencies(self):
        """Collect declared hash inventories and executed script inputs to a fixed point."""
        done=set()
        while set(self.files)-done:
            for key in list(set(self.files)-done):
                done.add(key)
                if not key.endswith('.json'):continue
                data=self.read(key);base=key.rsplit('/',1)[0]
                inventory_key=key
                if '/terminal_receipts/' in key:
                    terminal=key.split('/terminal_receipts/',1)[0]+'/TERMINAL_MANIFEST.json'
                    manifest=self.read(terminal)
                    matches=[]
                    for original,item in manifest['artifacts'].items():
                        saved=validation.original_join(self.origins['repo'],item['preserved'])
                        if validation.original_identity(saved)==validation.original_identity(key):
                            self.check(key,item['preserved_sha256'])
                            actual=validation.original_join(self.origins['repo'],original)
                            self.check(actual,item['sha256']);matches.append(actual)
                    assert len(matches)==1,('Saved terminal JSON lacks an exact original artifact binding',key)
                    inventory_key=matches[0];base=inventory_key.rsplit('/',1)[0]
                def walk(value):
                    if isinstance(value,list):
                        for child in value:walk(child)
                        return
                    if not isinstance(value,dict):return
                    for field in ['bound_files','bound_inputs','tools','scripts','input_sha256']:
                        items=value.get(field)
                        if isinstance(items,dict):
                            if field=='bound_inputs' and value is data and key==validation.original_join(self.origins['metadata'],'proofs_attempt01/inputs.json') and Path(self.origins['metadata']).name=='compact_aw_v22':
                                items=validation.validate_v22_failed_inputs(self)
                            if field=='bound_inputs' and value is data and key==validation.original_join(self.origins['metadata'],'proofs_completion02/inputs.json') and Path(self.origins['metadata']).name=='compact_aw_v22':
                                validation.check_v22_inventory(self,self.origins['metadata'],validation.original_join(self.origins['metadata'],'proofs_attempt01'),items)
                                continue
                            inventory_base=self.origins['repo'] if field=='input_sha256' else base
                            validation.check_inventory(self,inventory_base,items)
                    if value is data and isinstance(value.get('evidence_sha256'),dict):
                        inventory_base=base.rsplit('/',1)[0] if inventory_key.endswith('/verification/physical_audit.json') else base
                        validation.check_inventory(self,inventory_base,value['evidence_sha256'])
                    if isinstance(value.get('artifacts'),dict):
                        if value is data and key==validation.original_join(self.origins['metadata'],'proofs_completion02/RESULT.json') and Path(self.origins['metadata']).name=='compact_aw_v22':
                            validation.check_v22_inventory(self,self.origins['metadata'],validation.original_join(self.origins['metadata'],'proofs_attempt01'),value['artifacts'])
                        else:
                            inventory_base=self.origins['repo'] if key.endswith('/TERMINAL_MANIFEST.json') else base
                            validation.check_inventory(self,inventory_base,value['artifacts'])
                    if isinstance(value.get('raw_sha256'),dict):validation.check_inventory(self,self.origins['repo'],value['raw_sha256'])
                    if isinstance(value.get('source_roots'),dict):
                        for label,root in value['source_roots'].items():
                            if label+'_source55' in value:validation.check_inventory(self,root,value[label+'_source55'])
                    if isinstance(value.get('source_root'),str) and isinstance(value.get('source55'),dict):
                        validation.check_inventory(self,value['source_root'],value['source55'])
                    # Boundary source inventories use absolute source-root keys.
                    for name,child in value.items():
                        if isinstance(child,dict) and len(child)==55 and re.match(r'^[A-Za-z]:[/\\]',str(name)):
                            validation.check_inventory(self,name,child)
                    command=value.get('command',[])
                    for position,arg in enumerate(command):
                        # A failed compiler may never create its -o destination.
                        # Successful executables are bound by their simulation input.
                        if position and command[position-1]=='-o':continue
                        if isinstance(arg,str) and re.match(r'^[A-Za-z]:[/\\]',arg):
                            candidate=validation.evidence_key(arg)
                            if self.in_repo(candidate) and Path(candidate).suffix.lower() in {'.py','.tcl','.v','.vh','.vvp','.cjs'}:
                                self.blob(candidate)
                    if 'log_sha256' in value and isinstance(value.get('log'),str):self.check(value['log'],value['log_sha256'])
                    for child in value.values():walk(child)
                walk(data)

    def export(self,path,package,name=None):
        key=validation.evidence_key(path);self.blob(key)
        item=self.files[key]
        preferred='evidence/selected/'+(name or Path(key).name)
        if item['compression']=='gzip':preferred+='.gz'
        if key not in self.written:item['archive_path']=preferred
        self._write(key,package,item['archive_path'])
        if preferred!=item['archive_path']:self._write(key,package,preferred)
        return Path(package)/preferred

    def _write(self,key,package,relative):
        item=self.files[key];source=validation.safe_local(Path(key),REPO if self.in_repo(key) else Path(Path(key).anchor))
        assert sha(source)==item['sha256'],('Evidence changed before archiving',key)
        dest=validation.safe_file(Path(package),relative);dest.parent.mkdir(parents=True,exist_ok=True)
        if relative.startswith('source/'):
            assert sha(dest)==item['sha256']
        elif dest.exists():
            opener=gzip.open if item['compression']=='gzip' else open
            with opener(dest,'rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==item['sha256']
        elif item['compression']=='gzip':
            with source.open('rb') as input,gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as output:shutil.copyfileobj(input,output)
        else:shutil.copy2(source,dest)
        if relative==item['archive_path']:
            item['archive_sha256']=sha(dest);self.written.add(key)

    def finish(self,package):
        for key in sorted(self.files):
            if key not in self.written:self._write(key,package,self.files[key]['archive_path'])
        index={'version':1,'scope':'Exact immutable evidence bytes; original paths resolve only through this index. Tool binaries are prerequisites.',
               'origins':self.origins,'files':self.files,'toolchain_prerequisites':self.tools,'historical_versions':self.versions,
               'invalid_failed_input_references':self.invalid_failed_inputs}
        dest=Path(package)/'evidence/selected/EVIDENCE_INDEX.json'
        assert not dest.exists();dest.write_text(json.dumps(index,indent=2)+'\n',encoding='utf8')
        return dest


def register_family_history(collector,meta,family):
    if family=='v22':
        register_family_history(collector,HERE/'compact_aw_v20','v20')
    elif family=='v20':
        correction=collector.read(meta/'FUNCTIONAL_CORRECTION_02.json')
        for original,item in correction['changed_original_input_snapshots'].items():
            collector.historical(original,item['preserved_path'],item['sha256'])


def register_prepared_history(collector,meta):
    for manifest in sorted((meta/'prepared_revisions').glob('revision_*/REVISION_MANIFEST.json')):
        record=collector.read(manifest)
        for name,item in record['immutable_saved_files'].items():
            collector.historical(item['original_path'],manifest.parent/name,item['sha256'])


def selected_proof_directory(meta,proof,family):
    if family in {'v20','v21','v22'}:return Path(validation.proof_directory(meta,proof['proof_directory']))
    return meta/('proofs_retry02' if family=='v15' else 'proofs')


def prepare_evidence(meta,attempt,source,donor,proof_directory,expected,variant,physical,manifest,functional_meta=None):
    functional_meta=functional_meta or meta
    family=variant.split('_')[0]
    collector=EvidenceCollector(source,expected,dict(repo=REPO,metadata=functional_meta,physical_metadata=meta,report=meta/attempt.name,
        attempt=attempt,source=source,donor=donor,proofs=proof_directory,parent_proofs=HERE/'v4_release_proofs'))
    register_family_history(collector,functional_meta,family)
    for directory in set([meta,functional_meta]):register_prepared_history(collector,directory)
    collector.blob(Path(__file__));collector.blob(REPO/'firmware/B0B4/verify_release.py')
    for root in [proof_directory,HERE/'v4_release_proofs',donor/'verification',meta/attempt.name]:collector.tree(root)
    if family in {'v20','v21','v22'}:
        if family=='v22':
            collector.tree(functional_meta/'proofs_attempt01');collector.tree(functional_meta/'proofs_alias_retry02')
            collector.tree(HERE/'compact_aw_v20/proofs');collector.tree(HERE/'compact_aw_v20/proofs_retry02')
        else:collector.tree(functional_meta/'proofs')
        collector.tree(HERE/'compact_aw_v18/proofs')
    if family=='v21':collector.tree(functional_meta/'audit_retry02')
    for directory in set([meta,functional_meta]):
        for path in sorted(directory.iterdir()):
            try:validation.evidence_key(path)
            except SystemExit:continue
            validation.safe_local(path,REPO)
            if path.is_file() and path.suffix.lower() in {'.py','.json','.md','.diff','.log'}:collector.blob(path)
    for name in ['PROOF_BINDING.json','REUSED_BINDINGS_RECHECK.json','source_freeze.json','SOURCE_CHANGES.json' if family=='v22' else 'SOURCE_EQUIVALENCE_BASIS.json','source_review.md',
                 'run_proofs_retry02.py' if family in {'v15','v20','v21'} else 'run_proofs.py','run_synthesis.py','audit_synthesis_only.py','run_physical.py',
                 'runner_exit.json','runner_process.json','runner.stdout.log','runner.stderr.log','independent_raw_review.py','seal_terminal.py']:
        collector.blob(functional_meta/name)
    for name in ['run_physical.py','launch_physical_hidden.py','independent_raw_review.py','seal_terminal.py']:
        collector.blob(meta/name)
    freeze=functional_meta/'audit_retry02/completion_manifest.json' if family=='v21' else donor/'synthesis_freeze_manifest_final.json'
    for path in [freeze,donor/'synth_only.tcl',donor/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml']:
        collector.blob(path)
    parent_inputs=collector.read(HERE/'v4_release_proofs/inputs.json')
    controller=Path(parent_inputs['reused_controller_proofs']);collector.tree(controller)
    # Preserve the older guard evidence referenced by the reused controller result.
    prior=HERE/'compact_aw_v8/proofs_completion02';collector.tree(prior)
    collector.tree(REPO/'ground/B0B4/test_results')
    if family in {'v18','v20','v21','v22'}:
        vy_meta=functional_meta if family=='v18' else HERE/'compact_aw_v18'
        collector.blob(vy_meta/'VY_BINDING.json');collector.tree(vy_meta/'vy_proofs')
    qualification=dict(source_sha256=expected,netlist_sha256=manifest['vg_sha256'],bitstream_sha256=sha(source/'impl/pnr/acg720_ano_port.fs'),
                       functional_binding_sha256=sha(functional_meta/'PROOF_BINDING.json'),physical=physical,variant=variant,profile=attempt.name)
    if family=='v21':
        qualification.update(synthesis_completion_sha256=sha(functional_meta/'audit_retry02/completion_result.json'),
                             synthesis_completion_manifest_sha256=sha(functional_meta/'audit_retry02/completion_manifest.json'))
    validation.validate_standard_evidence(collector,qualification)
    collector.close_dependencies()
    return collector
profiles={
 'v22_dsp_p3':('compact_aw_v22_dsp_followup','compact_aw_v22','physical_p3r0_dsploc_01'),
 'v22_p3':('compact_aw_v22','compact_aw_v22','physical_p3r0_01'),
 'v20_dsp_p3':('compact_aw_v20_dsp_followup','compact_aw_v20','physical_p3r0_dsploc_01'),
 'v20_p3':('compact_aw_v20','compact_aw_v20','physical_p3r0_01'),
 'v21_p3':('compact_aw_v21','compact_aw_v21','physical_p3r0_01'),
 'v18_dsp_p3':('compact_aw_v18_dsp_followup','compact_aw_v18','physical_p3r0_dsploc_01'),
 'v18_p3':('compact_aw_v18','compact_aw_v18','physical_p3r0_01'),
 'v18_p2':('compact_aw_v18','compact_aw_v18','physical_p2r0_01'),
 'v17_p3':('compact_aw_v17','compact_aw_v17','physical_p3r0_01'),
 'v17_p2':('compact_aw_v17','compact_aw_v17','physical_p2r0_01'),
 'v16_p3':('compact_aw_v16','compact_aw_v16','physical_p3r0_01'),
 'v16_p2':('compact_aw_v16','compact_aw_v16','physical_p2r0_01'),
 'v15_p3':('compact_aw_v15','compact_aw_v15','physical_p3r0_01'),
 'v15_p2':('compact_aw_v15','compact_aw_v15','physical_p2r0_01'),
 'v14_p3':('compact_aw_v14','compact_aw_v14','physical_p3r0_01'),
 'v14_p2':('compact_aw_v14','compact_aw_v14','physical_p2r0_01'),
 'rep1':('compact_aw_v4_rep1_followup','compact_aw_v4','physical_p3r0_rep1_01'),
 'v13_map1_p3':('compact_aw_v13_map1','compact_aw_v13_map1','physical_p3r0_01'),
 'v13_map1_p2':('compact_aw_v13_map1','compact_aw_v13_map1','physical_p2r0_01'),
 'v13_p3':('compact_aw_v13','compact_aw_v13','physical_p3r0_01'),
 'v13_p2':('compact_aw_v13','compact_aw_v13','physical_p2r0_01'),
 'v12_p3':('compact_aw_v12','compact_aw_v12','physical_p3r0_01'),
 'v12_p2':('compact_aw_v12','compact_aw_v12','physical_p2r0_01'),
 'clockbuf1':('compact_aw_v4_clockbuf1_followup','compact_aw_v4','physical_p3r0_clkbuf1_01'),
 'v11_p3':('compact_aw_v11','compact_aw_v11','physical_p3r0_01'),
 'v11_p2':('compact_aw_v11','compact_aw_v11','physical_p2r0_01'),
 'data_route_p2':('compact_aw_v4_data_routing_followup','compact_aw_v4','physical_p2r0_data_route_01'),
 'data_route':('compact_aw_v4_data_routing_followup','compact_aw_v4','physical_p3r0_data_route_01'),
 'partial':('compact_aw_v4_partial_floorplan_followup','compact_aw_v4','physical_p3r0_partial_01'),
 'p1':('compact_aw_v4_p1_followup','compact_aw_v4','physical_p1r0_01'),
 'timing':('compact_aw_v4_timing','compact_aw_v4_timing','physical_p3r0_01'),
 'loc3':('compact_aw_v4_loc3_followup','compact_aw_v4','physical_p3r0_inc_loc3_01'),
 'incplace_loc3':('compact_aw_v4_incplace_loc3_followup','compact_aw_v4','physical_p3r0_incplace_loc3_01')}


def functional_metadata(variant,physical_meta):
    if variant==validation.DSP22_VARIANT:return HERE/'compact_aw_v22'
    if variant==validation.DSP20_VARIANT:return HERE/'compact_aw_v20'
    return HERE/'compact_aw_v18' if variant==validation.DSP_VARIANT else physical_meta

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant',choices=profiles)
    parser.add_argument('--independent-review-sha256',required=True)
    args=parser.parse_args()
    meta,variant,label=profiles[args.variant];M=HERE/meta;A=REPO/'out/z_aw_fix_20261026'/variant/label
    F=functional_metadata(args.variant,M)
    family=args.variant.split('_')[0];new_schema=family in {'v20','v21','v22'}
    report=M/label;V=A/'verification';S=A/'source';B4=REPO/'firmware/B0B4'
    manifest=read(report/'TERMINAL_MANIFEST.json');review=read(report/'INDEPENDENT_RAW_REVIEW.json')
    assert sha(report/'INDEPENDENT_RAW_REVIEW.json')==args.independent_review_sha256
    assert manifest['passed'] and review['passed'] and all(review['checks'].values())
    assert manifest['vendor_actual_p_wait']==manifest['runner_actual_p_wait']==0
    physical=read(V/'physical_audit.json');expected=manifest['source55']
    assert physical['passed'] and all(physical['criteria'].values())
    assert physical['period_ns']==20 and physical['fmax_mhz']>=50
    assert physical['setup_violated_endpoints']==physical['hold_violated_endpoints']==0
    assert all(x['worst_slack_ns']>=0 for x in physical['checks'].values())
    assert len(expected)==55 and {p:sha(S/p) for p in expected}==expected
    assert sha(S/'impl/gwsynthesis/acg720_ano_port.vg')==manifest['vg_sha256']
    for name,digest in review['raw_sha256'].items():
        path=REPO/name
        assert path.is_relative_to(REPO) and path.name.lower()!='deployment.env' and '.env' not in path.suffixes
        assert path.is_file() and sha(path)==digest,('Independent raw evidence changed',name)
    for name,item in manifest['artifacts'].items():
        path=REPO/name
        assert path.is_relative_to(REPO) and path.name.lower()!='deployment.env' and '.env' not in path.suffixes
        assert path.is_file() and sha(path)==item['sha256'],('Sealed artifact changed',name)
    donor=Path(read(V/'build_input.json')['donor'])
    needed=[V/n for n in ['physical_audit.json','physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log','project_serialization_check.json','donor_evidence_binding.json','build_result.json']]
    needed += [donor/'verification'/n for n in (['synthesis_exit.json'] if family=='v21' else ['synthesis_summary.json','synthesis_exit.json','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json'])]
    if family=='v21':needed += [F/'audit_retry02'/n for n in ['completion_result.json','completion_manifest.json','successful_audit_exit.json','completion_runner_exit.json','results_01/RESULT.json','results_01/strict_SP_clock_audit.json']]
    needed += [S/'impl/pnr'/n for n in ['acg720_ano_port.fs','acg720_ano_port.tr','acg720_ano_port.rpt.txt','device.cfg']]
    assert all(p.is_file() for p in needed)
    assert shutil.disk_usage(B4).free>256*1024*1024
    functional= F/'PROOF_BINDING.json' if args.variant.startswith(('v11_','v12_','v13_','v14_','v15_','v16_','v17_','v18_','v20_','v21_','v22_')) else HERE/'v4_release_proofs/RESULT.json'
    proof=read(functional);assert proof['passed'] and proof['source55']==expected
    modern=args.variant.startswith(('v11_','v12_','v13_','v14_','v15_','v16_','v17_','v18_','v20_','v21_','v22_'))
    local_hints=args.variant.startswith(('v14_','v15_','v16_','v17_','v18_'))
    landing_compare=args.variant.startswith(('v15_','v16_','v17_','v18_'))
    proof_origin=HERE/'compact_aw_v13' if args.variant.startswith('v13_map1_') else F
    proof_directory=selected_proof_directory(proof_origin,proof,family)
    mapped_review_name='MAPPED_LANDING_COMPARISON.json' if landing_compare else 'MAPPED_FANOUT_COMPARISON.json'
    if modern:
        origin=read(proof_origin/'PROOF_BINDING.json')
        assert origin['passed'] and origin['source55']==expected and origin['actual_proof_runner_wait']==0
        if proof_origin!=F:assert proof['parent_proof_sha256']==sha(proof_origin/'PROOF_BINDING.json')
        top_name='top_safety_results.json' if local_hints else 'top/top_safety_results.json'
        top_exit_name='runner_exit.json' if local_hints else 'top13_exit.json'
        extra=[proof_directory/n for n in (['inputs.json','RESULT.json'] if new_schema else ['inputs.json','runner_exit.json',top_name,top_exit_name])]
        if new_schema:
            recheck=read(F/'REUSED_BINDINGS_RECHECK.json')
            assert recheck['passed'] and recheck['source55']==expected and recheck['new_'+family+'_proof_binding_sha256']==sha(functional)
        if local_hints and not new_schema:
            recheck=read(F/'REUSED_BINDINGS_RECHECK.json')
            proof_key='new_'+args.variant.split('_')[0]+'_proof_binding_sha256'
            assert recheck['passed'] and recheck['source55']==expected and recheck[proof_key]==sha(functional)
            extra += [F/name for name in ['REUSED_BINDINGS_RECHECK.json','SOURCE_EQUIVALENCE_BASIS.json','source_review.md','source_freeze.json',mapped_review_name]]
            extra += [proof_directory/name for name in ['compile_exit.json','vvp_exit.json']]
            if landing_compare:
                assert proof['flight_state_miter']['passed'] and proof['flight_state_miter']['threshold_vectors']==2097152
                for phase in ['fsm_compile','fsm_vvp']:
                    phase_exit=read(proof_directory/(phase+'_exit.json'))
                    assert phase_exit['normal_wait_return'] and phase_exit['actual_p_wait']==0
                extra += [proof_directory/name for name in ['fsm_compile_exit.json','fsm_vvp_exit.json','flight_state_miter.v','legacy_ano_flight_state.v','fsm_compile.stderr.log','fsm_vvp.stdout.log','run_top13.py']]
        extra += [donor/'synth_only.tcl',donor/'verification/build_input.json',donor/'verification/synthesis_input.json',
                  donor/'verification/synthesis_process.json',donor/'verification/synthesis.log',F/'runner_exit.json',F/'runner_process.json']
        assert all(p.is_file() for p in extra),'Missing actual synthesis/proof-origin evidence'
    # Every physical runner owned by this continuation must have ended before promotion.
    state=read(HERE.parent/'CONTINUATION_STATE.json')
    assert not any(x['status']=='running' for x in state['runs'])
    for tag in ['compact_aw_v4_timing','compact_aw_v4_loc3_followup','compact_aw_v4_incplace_loc3_followup','compact_aw_v4_p1_followup','compact_aw_v4_partial_floorplan_followup','compact_aw_v4_data_routing_followup','compact_aw_v11','compact_aw_v12','compact_aw_v13','compact_aw_v13_map1','compact_aw_v13_native','compact_aw_v4_native','compact_aw_v4_clockbuf1_followup','compact_aw_v4_rep1_followup','compact_aw_v4_fan100_native','compact_aw_v14','compact_aw_v4_incplace_native','compact_aw_v15','compact_aw_v16','compact_aw_v17','compact_aw_v18','compact_aw_v18_dsp_followup','compact_aw_v20','compact_aw_v20_dsp_followup','compact_aw_v21','compact_aw_v22','compact_aw_v22_dsp_followup']:
        base=HERE/tag
        if not base.exists():continue
        if (base/'runner_process.json').is_file():assert (base/'runner_exit.json').is_file(),'A source-bound SYN runner still active: '+tag
        for proc in base.glob('physical_*/runner_process.json'):
            assert (proc.parent/'runner_exit.json').is_file(),str(proc)
    frozen=read(HERE.parent/'handoff_20261026/SOURCE_BINDINGS.json')
    matches=[v for k,v in frozen['source_sha256'].items() if Path(frozen['roots'][k]).resolve()==(B4/'source').resolve()]
    assert len(matches)==1
    before=matches[0];assert {p:sha(B4/'source'/p) for p in before}==before
    release=B4/'release';evidence=B4/'evidence/selected';backup=HERE.parent/'implementation_history/B4_initial_prototype_full55'
    assert not release.exists() and not evidence.exists() and not backup.exists()
    assert not (B4/'qualification.json').exists() and not (HERE.parent/'PROMOTION.json').exists()
    # Resolve and validate the complete immutable evidence closure before changing B4.
    collector=prepare_evidence(M,A,S,donor,proof_directory,expected,args.variant,physical,manifest,F) if landing_compare or new_schema else None
    # Keep every initial prototype byte before promoting the exact selected source55.
    backup.mkdir(parents=True)
    for p in before:
        dest=backup/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B4/'source'/p,dest)
    assert {p:sha(backup/p) for p in before}==before
    for p in expected:shutil.copy2(S/p,B4/'source'/p)
    assert {p:sha(B4/'source'/p) for p in expected}==expected
    release.mkdir();evidence.mkdir(parents=True)
    compressed=[]
    def preserve(source,name=None):
        if collector is not None:
            dest=collector.export(source,B4,name)
            if dest.suffix=='.gz':compressed.append({'path':dest.relative_to(B4).as_posix(),'uncompressed_sha256':sha(source)})
            return dest
        assert source.is_file(),str(source)
        dest=evidence/(name or source.name);assert not dest.exists()
        if source.suffix in ['.vg','.tr','.pr','.log','.txt','.p']:
            dest=dest.with_name(dest.name+'.gz')
            with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as output:output.write(source.read_bytes())
            compressed.append({'path':str(dest.relative_to(B4)).replace('\\','/'),'uncompressed_sha256':sha(source)})
        else:shutil.copy2(source,dest)
        return dest
    fs=S/'impl/pnr/acg720_ano_port.fs';shutil.copy2(fs,release/'acg720_ano_port.fs')
    for name in ['physical_audit.json','physical_exit.json','physical_process.json','physical_input.json','build_input.json','physical.log','project_serialization_check.json','donor_evidence_binding.json','build_result.json']:
        preserve(V/name)
    for name in ['TERMINAL_MANIFEST.json','INDEPENDENT_RAW_REVIEW.json','runner_exit.json','runner_process.json']:
        preserve(report/name)
    for path in [A/'physical.tcl',S/'physical.gprj',S/'impl/gwsynthesis/acg720_ano_port.vg',S/'impl/pnr/acg720_ano_port.tr',S/'impl/pnr/acg720_ano_port.rpt.txt',S/'impl/pnr/acg720_ano_port.pr',S/'impl/pnr/device.cfg']:
        preserve(path)
    if (S/'physical_constraints.cst').exists():
        preserve(S/'physical_constraints.cst')
        for name in ['placement_constraint_binding.json','data_routing_binding.json','clock_route_binding.json']:
            if (V/name).is_file():preserve(V/name)
        for name in ['FLOORPLAN_FROM_RAW.json','DATA_ROUTE_DECLARATION.json']:
            if (M/name).is_file():preserve(M/name)
        if args.variant in validation.DSP_VARIANTS:
            preserve(M/'PORTABLE_CONSTRAINT_BINDING.json')
            preserve(V/'portable_constraint_binding.json')
            # Exact-byte alias consumed by the unchanged replay wrapper's CST receipt lookup.
            preserve(V/'portable_constraint_binding.json','placement_constraint_binding.json')
    seed_index=[]
    for seed in (A/'donor').glob('*') if (A/'donor').exists() else []:
        item={'path':str(seed),'sha256':sha(seed),'bytes':seed.stat().st_size}
        if seed.suffix=='.p':item['preserved']=str(preserve(seed).relative_to(B4))
        else:item['retained_local_only']=True
        seed_index.append(item)
    if family=='v21':
        preserve(donor/'verification/synthesis_exit.json')
        for name in ['completion_result.json','completion_manifest.json','successful_audit_exit.json','completion_runner_exit.json']:
            preserve(F/'audit_retry02'/name,'SYN_'+name)
        for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','strict_SP_clock_audit.json']:
            preserve(F/'audit_retry02/results_01'/name)
    else:
        for name in ['synthesis_summary.json','synthesis_exit.json','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
            preserve(donor/'verification'/name)
    if modern:
        preserve(donor/'synth_only.tcl')
        preserve(donor/'verification/build_input.json','SYN_build_input.json')
        for name in ['synthesis_input.json','synthesis_process.json','synthesis.log']:preserve(donor/'verification'/name)
        for name in ['runner_exit.json','runner_process.json']:preserve(F/name,'SYN_'+name)
    preserve(functional,'functional_proof_binding.json')
    if new_schema:
        preserve(proof_directory/'inputs.json','functional_proof_inputs.json')
        if family=='v20':
            top_directory=Path(proof['fresh_top13']['directory'])
            preserve(proof_directory/'functional_runner_exit.json','functional_proof_runner_exit.json')
            preserve(Path(proof['fresh_top13']['root_exit_path']),'top13_runner_exit.json')
            preserve(top_directory/'top_safety_results.json','top13_results.json')
            for name in ['compile_exit.json','vvp_exit.json']:preserve(top_directory/name,'top13_'+name)
        elif family=='v21':
            preserve(F/'proof_retry02_runner_exit.json','functional_proof_runner_exit.json')
            preserve(F/'proof_retry02_runner_exit.json','top13_runner_exit.json')
            preserve(proof_directory/'top_safety_results.json','top13_results.json')
        else:
            top_directory=Path(proof['fresh_top13']['directory'])
            preserve(proof_directory/'functional_runner_exit.json','functional_proof_runner_exit.json')
            preserve(Path(proof['fresh_proof_directory'])/'top13_exit.json','top13_runner_exit.json')
            preserve(top_directory/'top_safety_results.json','top13_results.json')
            preserve(donor/'verification/local_hint_effect_audit.json')
        for name in ['REUSED_BINDINGS_RECHECK.json','SOURCE_CHANGES.json' if family=='v22' else 'SOURCE_EQUIVALENCE_BASIS.json','source_review.md','source_freeze.json']:preserve(F/name)
    elif modern:
        if proof_origin!=F:preserve(proof_origin/'PROOF_BINDING.json','functional_origin_proof_binding.json')
        preserve(proof_directory/'inputs.json','functional_proof_inputs.json')
        preserve(proof_directory/'runner_exit.json','functional_proof_runner_exit.json')
        preserve(proof_directory/top_name,'top13_results.json')
        preserve(proof_directory/top_exit_name,'top13_runner_exit.json')
        if local_hints:
            for name in ['REUSED_BINDINGS_RECHECK.json','SOURCE_EQUIVALENCE_BASIS.json','source_review.md','source_freeze.json',mapped_review_name]:preserve(F/name)
            for name in ['compile_exit.json','vvp_exit.json']:preserve(proof_directory/name,'top13_'+name)
            if landing_compare:
                for name in ['fsm_compile_exit.json','fsm_vvp_exit.json','flight_state_miter.v','legacy_ano_flight_state.v','fsm_compile.stderr.log','fsm_vvp.stdout.log','run_top13.py']:preserve(proof_directory/name,'landing_'+name)
    else:
        preserve(HERE/'v4_release_proofs/inputs.json','functional_proof_inputs.json')
        preserve(HERE/'v4_release_proofs/runner_exit.json','top13_runner_exit.json')
        preserve(HERE/'v4_release_proofs/top_safety_results.json','top13_results.json')
    promotion={'promoted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variant':args.variant,'profile':label,
        'selected_attempt':str(A),'selected_terminal_manifest_sha256':sha(report/'TERMINAL_MANIFEST.json'),
        'independent_review_sha256':args.independent_review_sha256,'source55_before':before,'source55_after':expected,
        'initial_prototype_backup':str(backup),'installed_B0B4':False,'hardware_confirmation_required':True}
    qualification={'passed':True,'scope':'Offline source/behavior/full physical qualification only. Hardware installation, cold boot and flight are separate.',
        'source_sha256':expected,'physical':physical,'profile':label,'variant':args.variant,
        'netlist_sha256':manifest['vg_sha256'],'release_bitstream':'release/acg720_ano_port.fs','bitstream_sha256':sha(fs),
        'compressed_artifacts':compressed,'external_build_inputs':{str(A/'physical.tcl'):sha(A/'physical.tcl'),str(fs):sha(fs)},
        'seed_artifacts':seed_index,'installed_B0B4':False,'true_cold_boot_verified':False,
        'functional_binding_sha256':sha(functional),
        'effective_build_recipe':'evidence/selected/physical.tcl','canonical_build_tcl_note':'Immutable source55 build.tcl is the synthesis baseline; selected physical Tcl/project and any additional CST record actual options. Do not silently rewrite accepted source55.'}
    if collector is not None:
        if family=='v21':
            qualification.update(synthesis_completion_sha256=sha(F/'audit_retry02/completion_result.json'),
                                 synthesis_completion_manifest_sha256=sha(F/'audit_retry02/completion_manifest.json'))
        index=collector.finish(B4);qualification['evidence_index_sha256']=sha(index)
        validation.validate_standard_evidence(validation.ArchivedEvidence(B4,read(index)),qualification)
    (HERE.parent/'PROMOTION.json').write_text(json.dumps(promotion,indent=2)+'\n')
    (B4/'qualification.json').write_text(json.dumps(qualification,indent=2)+'\n')
    print(json.dumps({'exported':True,'source_files':55,'fmax_mhz':physical['fmax_mhz'],'installed':False,'release_manifest_next':'Update final docs, then seal all exported files and run verify_release.py.'}))

if __name__=='__main__':main()
