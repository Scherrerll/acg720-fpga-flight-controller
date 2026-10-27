"""Proof/SYN archive tests only: never exports a release or runs vendor/hardware tools."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
SCRATCH = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_release_export', REPO / 'analysis/20261026_z_aw_fix/build/export_qualified_v4.py')
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)
verify = export.validation


def live(family):
    meta = export.HERE / ('compact_aw_' + family)
    source = REPO / 'out/z_aw_fix_20261026' / ('compact_aw_' + family) / 'canonical/source'
    proof = export.read(meta / 'PROOF_BINDING.json')
    donor = source.parents[1] / 'build_attempt_01'
    collector = export.EvidenceCollector(source, proof['source55'], dict(
        repo=REPO, metadata=meta, proofs=export.selected_proof_directory(meta, proof, family),
        source=source, donor=donor, parent_proofs=export.HERE / 'v4_release_proofs',
        attempt=source.parents[1] / 'physical_p3r0_01', report=meta / 'physical_p3r0_01'))
    export.register_family_history(collector, meta, family)
    qualification = dict(variant=family + '_p3', source_sha256=proof['source55'],
                         functional_binding_sha256=export.sha(meta / 'PROOF_BINDING.json'))
    return collector, qualification


def altered_vy(mutator):
    """In-memory negative fixture; frozen component records are never rewritten."""
    collector, qualification = live('v18')
    meta = Path(collector.origins['metadata'])
    root = meta / 'vy_proofs'
    binding = export.read(meta / 'VY_BINDING.json')
    result = export.read(root / 'RESULT.json')
    overrides = {}
    def store(path, value):
        data = (json.dumps(value, indent=2) + '\n').encode()
        overrides[verify.evidence_key(path)] = data
        return hashlib.sha256(data).hexdigest()
    mutator(result, root, store)
    binding['result_sha256'] = store(root / 'RESULT.json', result)
    store(meta / 'VY_BINDING.json', binding)
    original_blob = collector.blob
    def blob(path, expected=None):
        key = verify.evidence_key(path)
        if key in overrides:
            data = overrides[key]
            if expected is not None:
                assert hashlib.sha256(data).hexdigest() == expected
            return data
        return original_blob(path, expected)
    collector.blob = blob
    return collector, qualification


def with_synthesis(collector, qualification):
    meta, donor = Path(collector.origins['metadata']), Path(collector.origins['donor'])
    if qualification['variant'] == 'v21_p3':
        directory = meta / 'audit_retry02'
        qualification.update(netlist_sha256=export.read(directory / 'completion_result.json')['original_VG_sha256'],
                             synthesis_completion_sha256=export.sha(directory / 'completion_result.json'),
                             synthesis_completion_manifest_sha256=export.sha(directory / 'completion_manifest.json'))
    else:
        qualification['netlist_sha256'] = export.read(donor / 'verification/synthesis_summary.json')['netlist_sha256']
    return qualification


def new_family_archive(family):
    collector, qualification = live(family)
    with_synthesis(collector, qualification)
    verify.validate_functional(collector, qualification)
    verify.validate_synthesis(collector, qualification)
    meta, donor = Path(collector.origins['metadata']), Path(collector.origins['donor'])
    roots = [Path(collector.origins['proofs']), donor / 'verification', export.HERE / 'v4_release_proofs',
             export.HERE / 'compact_aw_v18/proofs', export.HERE / 'compact_aw_v18/vy_proofs',
             export.HERE / 'compact_aw_v9/proofs_retry02', export.HERE / 'compact_aw_v8/proofs_completion02', REPO / 'ground/B0B4/test_results']
    if family == 'v21':roots.append(meta / 'audit_retry02')
    if family == 'v22':roots += [meta / 'proofs_attempt01', meta / 'proofs_alias_retry02', export.HERE / 'compact_aw_v20/proofs', export.HERE / 'compact_aw_v20/proofs_retry02']
    else:roots.append(meta / 'proofs')
    for root in roots:collector.tree(root)
    collector.close_dependencies()
    package = Path(tempfile.mkdtemp(prefix=family + '_proof_SYN_archive_', dir=SCRATCH))
    for name in qualification['source_sha256']:
        destination = package / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(collector.origins['source']) / name, destination)
    collector.export(donor / 'source/impl/gwsynthesis/acg720_ano_port.vg', package)
    index = json.loads(collector.finish(package).read_text())
    return package, index, qualification


def altered_v22_failed(mutator):
    collector, qualification = live('v22');meta = Path(collector.origins['metadata'])
    old = export.read(meta / 'proofs_attempt01/inputs.json');current = export.read(meta / 'proofs_completion02/inputs.json')
    binding = export.read(meta / 'PROOF_BINDING.json');overrides = {}
    def store(path, value):
        data = (json.dumps(value, indent=2) + '\n').encode();overrides[verify.evidence_key(path)] = data
        return hashlib.sha256(data).hexdigest()
    mutator(old, current, meta)
    path = meta / 'proofs_attempt01/inputs.json';digest = store(path, old)
    keys = [name for name in current['bound_inputs'] if verify.original_identity(verify.v22_reference(meta, meta / 'proofs_attempt01', name)) == verify.original_identity(path)]
    assert len(keys) == 1;current['bound_inputs'][keys[0]] = digest
    binding['inputs_sha256'] = store(meta / 'proofs_completion02/inputs.json', current)
    qualification['functional_binding_sha256'] = store(meta / 'PROOF_BINDING.json', binding)
    original_blob = collector.blob
    def blob(path, expected=None):
        key = verify.evidence_key(path)
        if key in overrides:
            data = overrides[key]
            if expected is not None:assert hashlib.sha256(data).hexdigest() == expected
            return data
        return original_blob(path, expected)
    collector.blob = blob
    return collector, qualification


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper_before = export.sha(REPO / 'firmware/B0B4/build_candidate.py')
        cls.collector, cls.qualification = live('v17')
        donor = Path(cls.collector.origins['donor'])
        cls.qualification['netlist_sha256'] = export.read(donor / 'verification/synthesis_summary.json')['netlist_sha256']
        verify.validate_functional(cls.collector, cls.qualification)
        verify.validate_synthesis(cls.collector, cls.qualification)
        for root in [Path(cls.collector.origins['proofs']), export.HERE / 'v4_release_proofs', donor / 'verification',
                     export.HERE / 'compact_aw_v9/proofs_retry02', export.HERE / 'compact_aw_v8/proofs_completion02',
                     REPO / 'ground/B0B4/test_results']:
            cls.collector.tree(root)
        cls.collector.close_dependencies()
        cls.package = Path(tempfile.mkdtemp(prefix='proof_SYN_archive_', dir=SCRATCH))
        (cls.package / 'source').mkdir(parents=True)
        for name in cls.qualification['source_sha256']:
            destination = cls.package / 'source' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(cls.collector.origins['source']) / name, destination)
        cls.collector.export(donor / 'source/impl/gwsynthesis/acg720_ano_port.vg', cls.package)
        cls.collector.export(Path(cls.collector.origins['proofs']) / 'inputs.json', cls.package, 'functional_proof_inputs.json')
        cls.index_path = cls.collector.finish(cls.package)
        cls.index = json.loads(cls.index_path.read_text())
        cls.new_archives = {family: new_family_archive(family) for family in ['v20', 'v21', 'v22']}

    def test_genuine_v15_v16_v18_functional_chains(self):
        for family in ['v15', 'v16', 'v18']:
            collector, qualification = live(family)
            verify.validate_functional(collector, qualification)

    def test_portable_archive_functional_and_SYN_roundtrip(self):
        evidence = verify.ArchivedEvidence(self.package, self.index)
        for key in evidence.files:
            evidence.blob(key)
        verify.validate_functional(evidence, self.qualification)
        verify.validate_synthesis(evidence, self.qualification)
        self.assertGreater(len(evidence.files), 400)
        self.assertTrue((self.package / 'evidence/selected/acg720_ano_port.vg.gz').is_file())
        self.assertFalse((self.package / 'qualification.json').exists())

    def test_v20_v21_actual_proof_and_SYN_portable_roundtrips(self):
        for family, (package, index, qualification) in self.new_archives.items():
            with self.subTest(family=family):
                evidence = verify.ArchivedEvidence(package, index)
                for key in evidence.files:evidence.blob(key)
                verify.validate_functional(evidence, qualification)
                verify.validate_synthesis(evidence, qualification)
                self.assertFalse((package / 'qualification.json').exists())
                self.assertEqual(len(qualification['source_sha256']), 55)
                self.assertEqual(export.profiles[family + '_p3'], ('compact_aw_' + family, 'compact_aw_' + family, 'physical_p3r0_01'))

    def test_compiled_canonical_source_is_distinct_from_selected_physical_copy(self):
        for family, (package, index, qualification) in self.new_archives.items():
            altered = copy.deepcopy(index)
            altered['origins']['source'] = verify.original_join(index['origins']['repo'], 'out/z_aw_fix_20261026/compact_aw_' + family + '/physical_p3r0_01/source')
            with self.subTest(family=family):
                verify.validate_functional(verify.ArchivedEvidence(package, altered), qualification)

    def test_v20_missing_fresh_and_component_receipts_rejected(self):
        package, original, qualification = self.new_archives['v20']
        meta = original['origins']['metadata']
        component = export.read(Path(meta) / 'COMPONENT_REUSE_BINDING.json')
        paths = [verify.original_join(meta, 'proofs/top13/compile_exit.json'),
                 verify.original_join(meta, 'proofs_retry02/integration_vvp_exit.json'),
                 verify.evidence_key(component['AZ']['actual_compile_sim_receipts'][1]['path'])]
        for missing in paths:
            index = copy.deepcopy(original);del index['files'][missing]
            with self.subTest(missing=missing), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v20_history_requires_preserved_original_fixture_versions(self):
        package, original, qualification = self.new_archives['v20']
        self.assertEqual(len(original['historical_versions']), 2)
        index = copy.deepcopy(original);index['historical_versions'] = {}
        with self.assertRaises(SystemExit):
            verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v20_v21_compile_cannot_replace_simulation(self):
        collector, qualification = live('v20')
        meta = Path(collector.origins['metadata'])
        compile_receipt = export.read(meta / 'proofs_retry02/integration_compile_exit.json')
        with self.assertRaisesRegex(SystemExit, 'command roles differ'):
            verify.check_compile_simulation(collector, compile_receipt, compile_receipt)
        simulation = export.read(meta / 'proofs_retry02/integration_vvp_exit.json')
        wrong = copy.deepcopy(compile_receipt)
        wrong['command'][wrong['command'].index('-o') + 1] = str(meta / 'wrong.vvp')
        with self.assertRaisesRegex(SystemExit, 'executable or top differs'):
            verify.check_compile_simulation(collector, wrong, simulation)

    def test_v21_missing_each_actual_proof_role_rejected(self):
        package, original, qualification = self.new_archives['v21']
        meta = original['origins']['metadata'];binding = export.read(Path(meta) / 'PROOF_BINDING.json')
        for name in binding['exit_receipts']:
            index = copy.deepcopy(original);del index['files'][verify.original_join(meta, name)]
            with self.subTest(missing=name), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v21_standalone_receipt_and_original_failure_log_required(self):
        package, original, qualification = self.new_archives['v21']
        for missing in [verify.original_join(original['origins']['repo'], 'analysis/agent_reviews/extension_bram_20261027/attempt01/vvp_exit.json'),
                        verify.original_join(original['origins']['metadata'], 'proof_runner.stderr.log')]:
            index = copy.deepcopy(original);del index['files'][missing]
            with self.subTest(missing=missing), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v21_original_failures_and_two_successful_retry_waits_preserved(self):
        package, index, qualification = self.new_archives['v21'];evidence = verify.ArchivedEvidence(package, index)
        meta, donor = index['origins']['metadata'], index['origins']['donor']
        self.assertEqual(evidence.read(verify.original_join(meta, 'runner_exit.json'))['actual_p_wait'], 1)
        self.assertEqual(evidence.read(verify.original_join(donor, 'verification/audit_exit.json'))['actual_p_wait'], 1)
        self.assertEqual(evidence.read(verify.original_join(donor, 'verification/synthesis_exit.json'))['actual_p_wait'], 0)
        for name in ['successful_audit_exit.json', 'completion_runner_exit.json']:
            self.assertEqual(evidence.read(verify.original_join(meta, 'audit_retry02', name))['actual_p_wait'], 0)

    def test_v21_completion_and_strict_SP_dependencies_required(self):
        package, original, qualification = self.new_archives['v21'];meta = original['origins']['metadata']
        for name in ['completion_result.json', 'completion_manifest.json', 'successful_audit_exit.json', 'completion_runner_exit.json',
                     'results_01/strict_SP_clock_audit.json', 'results_01/CE_BOOLEAN_EQUIVALENCE.json', 'results_01/escaped_port_aliases.json']:
            index = copy.deepcopy(original);del index['files'][verify.original_join(meta, 'audit_retry02', name)]
            with self.subTest(missing=name), self.assertRaises(SystemExit):
                verify.validate_synthesis(verify.ArchivedEvidence(package, index), qualification)

    def test_v21_wrong_completion_and_VG_hashes_rejected(self):
        package, index, original = self.new_archives['v21']
        for name in ['synthesis_completion_sha256', 'synthesis_completion_manifest_sha256', 'netlist_sha256']:
            qualification = dict(original, **{name: '0' * 64})
            with self.subTest(field=name), self.assertRaises(SystemExit):
                verify.validate_synthesis(verify.ArchivedEvidence(package, index), qualification)

    def test_v22_real_failed_self_outputs_are_preserved_not_claimed_immutable(self):
        package, index, qualification = self.new_archives['v22'];evidence = verify.ArchivedEvidence(package, index)
        verify.validate_functional(evidence, qualification);verify.validate_synthesis(evidence, qualification)
        self.assertEqual(len(evidence.invalid_failed_inputs), 2)
        for path, item in evidence.invalid_failed_inputs.items():
            self.assertEqual(item['declared_sha256'], hashlib.sha256(b'').hexdigest())
            self.assertNotEqual(item['terminal_sha256'], item['declared_sha256'])
            self.assertEqual(hashlib.sha256(evidence.blob(path)).hexdigest(), item['terminal_sha256'])
        self.assertEqual(evidence.read(verify.original_join(index['origins']['metadata'], 'proofs_attempt01/functional_runner_exit.json'))['actual_p_wait'], 1)
        self.assertFalse((package / 'qualification.json').exists())

    def test_v22_invalid_reference_index_cannot_be_omitted_or_extended(self):
        package, original, qualification = self.new_archives['v22']
        for mode in ['omit', 'extra']:
            index = copy.deepcopy(original)
            if mode == 'omit':index['invalid_failed_input_references'] = {}
            else:index['invalid_failed_input_references']['c:/unrelated'] = dict(next(iter(index['invalid_failed_input_references'].values())))
            with self.subTest(mode=mode), self.assertRaisesRegex(SystemExit, 'invalid failed-input reference inventory differs'):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v22_other_wrong_old_input_hash_is_never_waived(self):
        def mutate(old, current, meta):
            key = next(name for name in old['bound_inputs'] if name.endswith('run_proofs.py'))
            old['bound_inputs'][key] = '0' * 64
        collector, qualification = altered_v22_failed(mutate)
        with self.assertRaisesRegex(AssertionError, 'Declared evidence changed'):
            verify.validate_v22_failed_inputs(collector)

    def test_v22_invalid_self_reference_is_exactly_empty_hash_only(self):
        def mutate(old, current, meta):
            key = next(name for name in old['bound_inputs'] if name.endswith('functional_runner.stdout.log'))
            old['bound_inputs'][key] = '0' * 64
        collector, qualification = altered_v22_failed(mutate)
        with self.assertRaisesRegex(SystemExit, 'invalid self-output declaration/real terminal log binding differs'):
            verify.validate_v22_failed_inputs(collector)

    def test_v22_current_terminal_output_hash_is_never_waived(self):
        def mutate(old, current, meta):
            key = next(name for name in current['bound_inputs'] if name.endswith('proofs_attempt01\\functional_runner.stdout.log'))
            current['bound_inputs'][key] = '0' * 64
        collector, qualification = altered_v22_failed(mutate)
        with self.assertRaisesRegex(SystemExit, 'invalid self-output declaration/real terminal log binding differs'):
            verify.validate_v22_failed_inputs(collector)

    def test_v22_only_known_same_family_sibling_spelling_is_allowed(self):
        collector, qualification = live('v22');meta = collector.origins['metadata'];base = verify.original_join(meta, 'proofs_attempt01')
        self.assertEqual(verify.v22_reference(meta, base, '../proofs_alias_retry02/compile_exit.json'), verify.original_join(meta, 'proofs_alias_retry02/compile_exit.json'))
        for path in ['../outside/x', '../../outside', '../proofs_alias_retry02/../../outside', '../proofs_alias_retry02/.env']:
            with self.subTest(path=path), self.assertRaises(SystemExit):verify.v22_reference(meta, base, path)

    def test_v22_each_actual_successful_receipt_is_required(self):
        package, original, qualification = self.new_archives['v22'];meta = original['origins']['metadata'];binding = export.read(Path(meta) / 'PROOF_BINDING.json')
        for item in binding['fresh_actual_exit_receipts']:
            key = verify.v22_reference(meta, verify.original_join(meta, 'proofs_attempt01'), item['path'])
            index = copy.deepcopy(original);del index['files'][key]
            with self.subTest(missing=key), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v22_preserved_TEMP_logs_and_alias_identity_are_required(self):
        package, original, qualification = self.new_archives['v22'];meta = original['origins']['metadata']
        for name in ['proofs_attempt01/functional_runner.stderr.log', 'proofs_attempt01/alias_compile.stderr.log',
                     'proofs_alias_retry02/actual_functions.v', 'proofs_alias_retry02/vvp.stdout.log']:
            index = copy.deepcopy(original);del index['files'][verify.original_join(meta, name)]
            with self.subTest(missing=name), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)

    def test_v22_native_hint_measurement_and_parent_XML_are_required(self):
        package, original, qualification = self.new_archives['v22'];donor = original['origins']['donor']
        paths = [verify.original_join(donor, 'verification/local_hint_effect_audit.json'), verify.original_join(donor, 'verification/native_synthesis_audit.json'),
                 verify.original_join(original['origins']['repo'], 'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml')]
        for path in paths:
            index = copy.deepcopy(original);del index['files'][path]
            with self.subTest(missing=path), self.assertRaises(SystemExit):
                verify.validate_synthesis(verify.ArchivedEvidence(package, index), qualification)

    def test_v20_v21_distinct_source_identity_and_unqualified_physical_rejected(self):
        for family, (package, index, original) in self.new_archives.items():
            qualification = copy.deepcopy(original)
            qualification['source_sha256'] = export.read(export.HERE / 'compact_aw_v18/PROOF_BINDING.json')['source55']
            with self.subTest(family=family), self.assertRaises(SystemExit):
                verify.validate_functional(verify.ArchivedEvidence(package, index), qualification)
            with self.subTest(physical=family), self.assertRaises(SystemExit):
                verify.validate_standard_evidence(verify.ArchivedEvidence(package, index), original)

    def test_missing_archived_ground_input_rejected(self):
        index = copy.deepcopy(self.index)
        verification = export.read(REPO / 'ground/B0B4/test_results/verification.json')
        name = next(name for name in verification['input_sha256'] if name.startswith('ground/B0B4/') and name.endswith('.py'))
        ground = verify.original_join(self.collector.origins['repo'], name)
        del index['files'][ground]
        with self.assertRaises(SystemExit):
            verify.validate_functional(verify.ArchivedEvidence(self.package, index), self.qualification)

    def test_wrong_functional_hash_rejected(self):
        qualification = dict(self.qualification, functional_binding_sha256='0' * 64)
        with self.assertRaises(SystemExit):
            verify.validate_functional(verify.ArchivedEvidence(self.package, self.index), qualification)

    def test_wrong_SYN_source_rejected(self):
        qualification = copy.deepcopy(self.qualification)
        qualification['source_sha256']['core/flight_core.v'] = '0' * 64
        with self.assertRaises(SystemExit):
            verify.validate_synthesis(verify.ArchivedEvidence(self.package, self.index), qualification)

    def test_missing_SYN_actual_audit_receipt_rejected(self):
        index = copy.deepcopy(self.index)
        key = verify.original_join(self.collector.origins['donor'], 'verification/audit_exit.json')
        del index['files'][key]
        with self.assertRaises(SystemExit):
            verify.validate_synthesis(verify.ArchivedEvidence(self.package, index), self.qualification)

    def test_environment_traversal_and_binary_index_rejected(self):
        for name in ['.env', '.env.local', 'deployment.env', 'deployment.env. ', 'deployment.env:stream', 'sub/config.env.local', '../outside']:
            with self.assertRaises(SystemExit):
                verify.evidence_key(name)
        index = copy.deepcopy(self.index)
        item = next(iter(index['files'].values()))
        index['files']['c:/tools/proprietary.exe'] = item
        with self.assertRaises(SystemExit):
            verify.ArchivedEvidence(self.package, index)

    def test_real_failed_v15_remains_rejected(self):
        collector, qualification = live('v15')
        terminal = collector.read(Path(collector.origins['report']) / 'TERMINAL_MANIFEST.json')
        self.assertFalse(terminal['passed'])
        qualification['netlist_sha256'] = terminal['vg_sha256']
        with self.assertRaises(SystemExit):
            verify.validate_standard_evidence(collector, qualification)

    def test_v18_genuine_VY_and_missing_binding_rejected(self):
        meta = export.HERE / 'compact_aw_v18'
        binding = export.read(meta / 'VY_BINDING.json')
        source = REPO / 'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
        collector = export.EvidenceCollector(source, binding['source55'], dict(repo=REPO, metadata=meta))
        verify.validate_vy(collector, verify.evidence_key(meta), binding['source55'])
        original_blob = collector.blob
        def missing_binding(path, expected=None):
            if verify.evidence_key(path).endswith('/VY_BINDING.json'):
                raise SystemExit('Missing required VY binding')
            return original_blob(path, expected)
        collector.blob = missing_binding
        with self.assertRaises(SystemExit):
            verify.validate_vy(collector, verify.evidence_key(meta), binding['source55'])

    def test_case_alias_wrong_SHA_cannot_become_prerequisite(self):
        collector, qualification = live('v18')
        path = Path(collector.origins['metadata']) / 'VY_BINDING.json'
        alias = str(path).swapcase()
        self.assertTrue(collector.in_repo(alias))
        with self.assertRaisesRegex(AssertionError, 'Declared evidence changed'):
            collector.check(alias, '0' * 64)
        self.assertFalse(collector.tools)
        collector.check(alias, export.sha(path))
        self.assertIn(verify.evidence_key(alias), collector.files)
        self.assertFalse(collector.tools)

    def test_repository_alias_is_rejected_in_archive_toolchain(self):
        index = copy.deepcopy(self.index)
        key, item = next(iter(index['files'].items()))
        del index['files'][key]
        index['toolchain_prerequisites'][verify.evidence_key(key.swapcase())] = dict(sha256=item['sha256'], bytes=item['bytes'])
        with self.assertRaisesRegex(SystemExit, 'Unrecognized or repository-local'):
            verify.ArchivedEvidence(self.package, index)

    def test_VY_one_compile_only_missing_eight_roles_rejected(self):
        def mutate(result, root, store):
            key = 'successful_wait_receipts/metric_compile_exit.json'
            result['exit_receipts'] = {key: result['exit_receipts'][key]}
        collector, qualification = altered_vy(mutate)
        with self.assertRaisesRegex(SystemExit, 'root and all eight'):
            verify.validate_vy(collector, collector.origins['metadata'], qualification['source_sha256'])

    def test_VY_missing_each_required_role_rejected(self):
        keys = export.read(export.HERE / 'compact_aw_v18/vy_proofs/RESULT.json')['exit_receipts']
        for missing in keys:
            def mutate(result, root, store):
                del result['exit_receipts'][missing]
            collector, qualification = altered_vy(mutate)
            with self.subTest(missing=missing), self.assertRaisesRegex(SystemExit, 'root and all eight'):
                verify.validate_vy(collector, collector.origins['metadata'], qualification['source_sha256'])

    def test_VY_compile_command_cannot_replace_simulation(self):
        def mutate(result, root, store):
            name = 'successful_wait_receipts/metric_vvp_exit.json'
            adapter = export.read(root / name)
            original_name = adapter['original_receipt']
            actual = export.read(root / original_name)
            actual['command'] = export.read(root / 'attempt01/metric_compile_exit.json')['command']
            result['stages'][1] = actual
            digest = store(root / original_name, actual)
            adapter['original_receipt_sha256'] = digest
            result['original_actual_wait_receipts'][original_name] = digest
            result['exit_receipts'][name] = store(root / name, adapter)
        collector, qualification = altered_vy(mutate)
        with self.assertRaisesRegex(SystemExit, 'simulation role/command differs'):
            verify.validate_vy(collector, collector.origins['metadata'], qualification['source_sha256'])

    def test_VY_original_log_hash_is_checked(self):
        def mutate(result, root, store):
            name = 'successful_wait_receipts/metric_vvp_exit.json'
            adapter = export.read(root / name)
            original_name = adapter['original_receipt']
            actual = export.read(root / original_name)
            actual['stdout_sha256'] = '0' * 64
            result['stages'][1] = actual
            digest = store(root / original_name, actual)
            adapter['original_receipt_sha256'] = digest
            result['original_actual_wait_receipts'][original_name] = digest
            result['exit_receipts'][name] = store(root / name, adapter)
        collector, qualification = altered_vy(mutate)
        with self.assertRaises((AssertionError, SystemExit)):
            verify.validate_vy(collector, collector.origins['metadata'], qualification['source_sha256'])

    def test_DSP_profile_official46_uses_standard_v18_evidence(self):
        collector, qualification = live('v18')
        thin = export.HERE / 'compact_aw_v18_dsp_followup'
        collector.origins['physical_metadata'] = verify.evidence_key(thin)
        qualification.update(variant='v18_dsp_p3', profile=verify.DSP_PROFILE, netlist_sha256=verify.DSP_VG_SHA)
        verify.validate_synthesis(collector, qualification)
        result = verify.validate_portable_preparation(collector, qualification)
        graph = next(path for path in collector.tools if path.endswith('/read_cones.py'))
        verify.check_inventory(collector, collector.origins['repo'], {
            graph: {'sha256': collector.tools[graph]['sha256'], 'bytes': collector.tools[graph]['bytes']}})
        self.assertEqual(export.profiles['v18_dsp_p3'], ('compact_aw_v18_dsp_followup', 'compact_aw_v18', verify.DSP_PROFILE))
        self.assertEqual(export.functional_metadata('v18_dsp_p3', thin), export.HERE / 'compact_aw_v18')
        self.assertEqual(result['validation']['kept'], 46)
        self.assertEqual(result['validation']['DSP'], 44)
        self.assertEqual(result['validation']['BSRAM'], 2)
        self.assertEqual(hashlib.sha256(result['combined']).hexdigest(), '794db7888509514d1394d5f1bc25954445717eeefaabd353464a047713cfadef')
        collector.origins['metadata'] = verify.evidence_key(thin)
        with self.assertRaises(SystemExit):
            verify.validate_portable_preparation(collector, qualification)

    def test_DSP_suffix_rejects_extra_clock_or_timing_directives(self):
        portable = (export.HERE / 'native_v4_DSP_export/portable_v18_dsp_bsram.cst').read_bytes()
        self.assertEqual(len(verify.parse_resource_cst(portable)), 46)
        for extra in [b'CLOCK_LOC "clk50" BUFG;\n', b'set_false_path -from [get_ports {range_rx}]\n']:
            with self.assertRaises(SystemExit):
                verify.parse_resource_cst(portable + extra)

    def test_DSP20_profile_uses_standard_v20_and_exact_official41(self):
        collector, qualification = live('v20');with_synthesis(collector, qualification)
        thin = export.HERE / 'compact_aw_v20_dsp_followup'
        collector.origins['physical_metadata'] = verify.evidence_key(thin)
        qualification.update(variant='v20_dsp_p3', profile=verify.DSP_PROFILE)
        result = verify.validate_portable_preparation(collector, qualification)
        verify.validate_functional(collector, qualification);verify.validate_synthesis(collector, qualification)
        self.assertEqual(export.profiles['v20_dsp_p3'], ('compact_aw_v20_dsp_followup', 'compact_aw_v20', verify.DSP_PROFILE))
        self.assertEqual(export.functional_metadata('v20_dsp_p3', thin), export.HERE / 'compact_aw_v20')
        self.assertEqual((result['validation']['kept'], result['validation']['DSP'], result['validation']['BSRAM']), (41, 39, 2))
        self.assertEqual(len(result['validation']['dropped_rows']), 11)
        self.assertEqual(hashlib.sha256(result['combined']).hexdigest(), '01c8bc50df1c8303b032c1a6d5c891f21c26b3c16da279234bb18e85eb2cdba1')
        original = qualification['netlist_sha256'];qualification['netlist_sha256'] = verify.DSP_VG_SHA
        with self.assertRaises(SystemExit):verify.validate_portable_preparation(collector, qualification)
        qualification['netlist_sha256'] = original;collector.origins['metadata'] = verify.evidence_key(thin)
        with self.assertRaises(SystemExit):verify.validate_portable_preparation(collector, qualification)

    def test_DSP20_current_prepared_revision_archive_closure(self):
        collector, qualification = live('v20');with_synthesis(collector, qualification)
        thin = export.HERE / 'compact_aw_v20_dsp_followup'
        collector.origins['physical_metadata'] = verify.evidence_key(thin)
        qualification.update(variant='v20_dsp_p3', profile=verify.DSP_PROFILE)
        export.register_prepared_history(collector, thin)
        verify.validate_portable_preparation(collector, qualification)
        collector.tree(thin);collector.close_dependencies()
        self.assertGreaterEqual(len(collector.versions), 20)
        self.assertIn(verify.evidence_key(thin / 'prepared_revisions/revision_01/seal_terminal.py'), collector.files)

    def test_DSP22_profile_actual_official33_and_portable_preparation_archive(self):
        collector, qualification = live('v22');with_synthesis(collector, qualification)
        thin = export.HERE / 'compact_aw_v22_dsp_followup'
        collector.origins['physical_metadata'] = verify.evidence_key(thin)
        qualification.update(variant='v22_dsp_p3', profile=verify.DSP_PROFILE)
        export.register_prepared_history(collector, thin)
        result = verify.validate_portable_preparation(collector, qualification)
        verify.validate_functional(collector, qualification);verify.validate_synthesis(collector, qualification)
        self.assertEqual(export.profiles['v22_dsp_p3'], ('compact_aw_v22_dsp_followup', 'compact_aw_v22', verify.DSP_PROFILE))
        self.assertEqual(export.functional_metadata('v22_dsp_p3', thin), export.HERE / 'compact_aw_v22')
        self.assertEqual((result['validation']['kept'], result['validation']['DSP'], result['validation']['BSRAM']), (33, 31, 2))
        self.assertEqual(len(result['validation']['dropped_rows']), 19)
        self.assertEqual(len(result['combined']), 4915)
        self.assertEqual(hashlib.sha256(result['combined']).hexdigest(), '38df04847e0f5d6b36b60f28a60bff4e0a601c7395c33e2bf1a17d64eba7d4e0')
        # Preparation evidence stays immutable even if the main launches PNR later.
        for path in thin.iterdir():
            if path.is_file() and path.suffix.lower() in {'.py', '.json', '.cst', '.md', '.diff', '.log'}:collector.blob(path)
        collector.tree(thin / 'prepared_revisions');collector.close_dependencies()
        package = Path(tempfile.mkdtemp(prefix='v22_dsp_preparation_archive_', dir=SCRATCH))
        for name in qualification['source_sha256']:
            destination = package / 'source' / name;destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(collector.origins['source']) / name, destination)
        index = json.loads(collector.finish(package).read_text());archive = verify.ArchivedEvidence(package, index)
        verify.validate_portable_preparation(archive, qualification)
        verify.validate_functional(archive, qualification);verify.validate_synthesis(archive, qualification)
        self.assertFalse((package / 'qualification.json').exists())
        bad = dict(qualification, netlist_sha256=verify.DSP20_VG_SHA)
        with self.assertRaises(SystemExit):verify.validate_portable_preparation(archive, bad)
        archive.origins['metadata'] = verify.evidence_key(thin)
        with self.assertRaises(SystemExit):verify.validate_portable_preparation(archive, qualification)

    def test_real_failed_DSP22_vendor1_root1_remains_rejected(self):
        collector, qualification = live('v22');with_synthesis(collector, qualification)
        thin = export.HERE / 'compact_aw_v22_dsp_followup';profile = verify.DSP_PROFILE
        attempt = REPO / 'out/z_aw_fix_20261026/compact_aw_v22' / profile
        collector.origins.update(physical_metadata=verify.evidence_key(thin), report=verify.evidence_key(thin / profile),
                                 attempt=verify.evidence_key(attempt), source=verify.evidence_key(attempt / 'source'))
        qualification.update(variant='v22_dsp_p3', profile=profile)
        terminal = collector.read(thin / profile / 'TERMINAL_MANIFEST.json')
        self.assertFalse(terminal['passed']);self.assertEqual(terminal['classification'], 'route_failure')
        self.assertEqual(terminal['vendor_actual_p_wait'], 1);self.assertEqual(terminal['runner_actual_p_wait'], 1)
        with self.assertRaisesRegex(SystemExit, 'Selected terminal qualification failed'):
            verify.validate_standard_evidence(collector, qualification)

    def test_original_helper_unchanged_and_v18_profiles(self):
        self.assertEqual(self.helper_before, verify.HELPER_SHA)
        self.assertEqual(export.sha(REPO / 'firmware/B0B4/build_candidate.py'), self.helper_before)
        self.assertIn('v18_p3', export.profiles)
        self.assertIn('v18_p2', export.profiles)


if __name__ == '__main__':
    unittest.main(verbosity=2)
