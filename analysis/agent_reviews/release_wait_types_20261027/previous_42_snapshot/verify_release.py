"""Verify saved B0B4 release bytes and qualification; never program a device."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse
import binascii
import gzip
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
HELPER_SHA = 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
TIMING_TYPES = {'setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width'}
DSP_VARIANT = 'v18_dsp_p3'
DSP_PROFILE = 'physical_p3r0_dsploc_01'
DSP_VG_SHA = '64e76270fe35298e698bfe5b14b9d9e267469f746d3c2382a8a15284c5942d4f'
DSP20_VARIANT = 'v20_dsp_p3'
DSP20_VG_SHA = 'bb2d4a6d20184a0c38739b550d2fc04adf9fe9ce219106064a2051edbc26274f'
DSP22_VARIANT = 'v22_dsp_p3'
DSP22_VG_SHA = 'e84a81f4a5abb4c15c9e599cc4c2d2e77397a328c9372d0a94c8949fbbf7f4f8'
DSP_VARIANTS = {DSP_VARIANT, DSP20_VARIANT, DSP22_VARIANT}


def evidence_key(value):
    """Normalize an original path without accessing the original filesystem."""
    text = str(value).replace('\\', '/')
    pure = PureWindowsPath(text) if re.match(r'^[A-Za-z]:/', text) else PurePosixPath(text)
    require('..' not in pure.parts, 'Parent traversal in evidence path')
    for part in pure.parts:
        name = part.lower().rstrip(' .')
        require(':' not in part or part == pure.anchor, 'Alternate data streams are excluded from evidence')
        require(not name.startswith('.env') and not name.endswith('.env')
                and '.env' not in [s.lower() for s in PurePosixPath(name).suffixes],
                'Environment files are excluded from evidence')
    normalized = pure.as_posix()
    return normalized[0].lower() + normalized[1:] if re.match(r'^[A-Za-z]:/', normalized) else normalized


def original_join(base, *parts):
    value = evidence_key(base)
    for part in parts:
        relative = evidence_key(part)
        require(not PureWindowsPath(relative).is_absolute() and not PurePosixPath(relative).is_absolute(),
                'Expected a relative evidence inventory path')
        value = value.rstrip('/') + '/' + relative
    return evidence_key(value)


def original_identity(value):
    key = evidence_key(value)
    return key.casefold() if PureWindowsPath(key).is_absolute() else key


def original_contains(path, root):
    path, root = evidence_key(path), evidence_key(root)
    if PureWindowsPath(root).is_absolute():
        return PureWindowsPath(path).is_relative_to(PureWindowsPath(root))
    return PurePosixPath(path).is_relative_to(PurePosixPath(root))


def known_toolchain(repo):
    """Only these recorded external toolchain inputs may remain prerequisites."""
    repo = evidence_key(repo)
    pure = PureWindowsPath(repo) if PureWindowsPath(repo).is_absolute() else PurePosixPath(repo)
    apple = evidence_key(pure.parent.parent)
    gowin = 'c:/Gowin/Gowin_V1.9.12.04_x64/IDE'
    paths = [
        original_join(gowin, 'bin/gw_sh.exe'), original_join(gowin, 'simlib/gw5a/prim_sim.v'),
        original_join(apple, '.tools/iverilog/app/bin/iverilog.exe'),
        original_join(apple, '.tools/iverilog/app/bin/vvp.exe'),
        original_join(apple, 'runtime_xy_pi_20261026/tools/read_cones.py')]
    profile = re.match(r'(?i)^([a-z]:/Users/[^/]+)(?:/|$)', repo)
    if profile:
        paths.append(original_join(profile[1], 'AppData/Local/Programs/Python/Python313/python.exe'))
    return {original_identity(p) for p in paths}


def known_external_data(repo):
    pure = PureWindowsPath(evidence_key(repo))
    return {original_identity(original_join(pure.parent.parent, name)) for name in [
            'runtime_xy_pi_20261026/candidates/idle_gain_integral_ce/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml',
            'routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG550-2.4E_GowinSynthesis User Guide.txt']}


def safe_local(path, root):
    """Reject secrets, links and escapes before opening or hashing anything."""
    evidence_key(path)
    path, root = Path(path), Path(root)
    require(path.resolve().is_relative_to(root.resolve()), 'Evidence path escapes its allowed root')
    for part in [path, *path.parents]:
        require(not part.is_symlink() and not (hasattr(part, 'is_junction') and part.is_junction()),
                'Links are excluded from evidence')
        if part == root:
            break
    return path


class ArchivedEvidence:
    """Resolve frozen original names through the portable archive index only."""
    def __init__(self, root, index):
        self.root, self.index = Path(root), index
        require(index['version'] == 1, 'Unsupported evidence index')
        self.files = index['files']
        self.tools = index['toolchain_prerequisites']
        self.origins = index['origins']
        self.versions = index.get('historical_versions', {})
        self.invalid_failed_inputs = index.get('invalid_failed_input_references', {})
        self.cache = {}
        require(not {original_identity(p) for p in self.files}.intersection(original_identity(p) for p in self.tools),
                'Bundled evidence conflicts with toolchain prerequisite')
        for key in [*self.files, *self.tools, *self.origins.values()]:
            require(evidence_key(key) == key, 'Noncanonical original evidence path')
        for key, item in self.files.items():
            require(PurePosixPath(key).suffix.lower() not in {'.exe', '.dll'}, 'Tool binaries must not be bundled')
            require(isinstance(item['bytes'], int) and item['bytes'] >= 0
                    and re.fullmatch(r'[0-9a-f]{64}', item['sha256'])
                    and re.fullmatch(r'[0-9a-f]{64}', item['archive_sha256']), 'Malformed indexed evidence identity')
        for key, item in self.tools.items():
            require(not original_contains(key, self.origins['repo']) and original_identity(key) in known_toolchain(self.origins['repo']),
                    'Unrecognized or repository-local toolchain prerequisite')
            require(re.fullmatch(r'[0-9a-f]{64}', item['sha256']) and isinstance(item['bytes'], int) and item['bytes'] >= 0,
                    'Toolchain prerequisite hash/byte count missing')
        for original, versions in self.versions.items():
            require(original_contains(original, self.origins['repo']), 'Historical version is outside repository')
            for digest, saved in versions.items():
                require(saved in self.files and self.files[saved]['sha256'] == digest,
                        'Historical version does not bind its immutable saved copy')

    def blob(self, original, expected=None):
        key = evidence_key(original)
        if expected is not None:
            key = self.versions.get(key, {}).get(expected, key)
        require(key in self.files, 'Missing archived dependency: ' + key)
        item = self.files[key]
        if key not in self.cache:
            path = safe_file(self.root, item['archive_path'])
            require(item['compression'] in {'none', 'gzip'}, 'Unknown evidence compression')
            require(sha(path) == item['archive_sha256'], 'Archived evidence bytes differ: ' + key)
            opener = gzip.open if item['compression'] == 'gzip' else open
            with opener(path, 'rb') as stream:
                data = stream.read()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                    'Archived evidence content differs: ' + key)
            self.cache[key] = data
        data = self.cache[key]
        if expected is not None:
            require(hashlib.sha256(data).hexdigest() == expected, 'Declared evidence hash differs: ' + key)
        return data

    def check(self, original, digest):
        key = evidence_key(original)
        if key in self.tools:
            require(self.tools[key]['sha256'] == digest, 'Toolchain prerequisite hash differs')
        else:
            self.blob(key, digest)

    def read(self, original, expected=None):
        return json.loads(self.blob(original, expected).decode('utf8'))

    def size(self, original, expected=None):
        key = evidence_key(original)
        if expected is not None:key = self.versions.get(key, {}).get(expected, key)
        return self.tools[key]['bytes'] if key in self.tools else len(self.blob(key))


def check_inventory(evidence, base, items):
    for name, item in items.items():
        if PureWindowsPath(str(name)).is_absolute() and '/proofs_attempt01/../proofs_alias_retry02/' in str(name).replace('\\', '/').casefold():
            meta = evidence.origins['metadata']
            require(PurePosixPath(meta).name == 'compact_aw_v22', 'Sibling proof path appears outside the v22 family')
            name = v22_reference(meta, original_join(meta, 'proofs_attempt01'), name)
        # The original contention runner writes results in its child directory.
        inventory_base = base.rsplit('/', 1)[0] if str(name) == 'run.py' and str(base).endswith('/contention/contention') else base
        path = evidence_key(name) if PureWindowsPath(str(name)).is_absolute() or str(name).startswith('/') else original_join(inventory_base, name)
        digest = item['sha256'] if isinstance(item, dict) else item
        evidence.check(path, digest)
        if isinstance(item, dict) and 'bytes' in item:
            require(evidence.size(path, digest) == item['bytes'], 'Declared evidence byte count differs')


def check_receipt(evidence, path, digest=None):
    receipt = evidence.read(path, digest)
    if 'actual_p_wait' in receipt:
        require(receipt.get('normal_wait_return') is True and receipt['actual_p_wait'] == 0
                and not receipt.get('terminated_after_timeout'), 'Actual process wait failed: ' + str(path))
    else:
        require(receipt.get('normal_return') is True and receipt.get('actual_completedprocess_returncode') == 0,
                'Actual subprocess result failed: ' + str(path))
    folder = evidence_key(path).rsplit('/', 1)[0]
    stem = PurePosixPath(evidence_key(path)).name.removesuffix('_exit.json')
    for channel in ['stdout', 'stderr']:
        if channel + '_sha256' in receipt:
            evidence.check(original_join(folder, stem + '.' + channel + '.log'), receipt[channel + '_sha256'])
    if 'log_sha256' in receipt:
        evidence.check(receipt['log'], receipt['log_sha256'])
    for arg in receipt.get('command', []):
        if isinstance(arg, str) and arg.lower().endswith(('.py', '.tcl')) and (PureWindowsPath(arg).is_absolute() or arg.startswith('/')):
            evidence.blob(arg)
    if 'runner_sha256' in receipt:
        if receipt['runner_sha256'] == HELPER_SHA:
            evidence.check(original_join(evidence.origins['repo'], 'firmware/B0B4/build_candidate.py'), HELPER_SHA)
        else:
            scripts = [arg for arg in receipt.get('command', []) if str(arg).lower().endswith('.py')]
            require(len(scripts) == 1, 'Executed runner script identity missing')
            evidence.check(scripts[0], receipt['runner_sha256'])
    if 'supervisor_sha256' in receipt:
        if folder == original_join(evidence.origins['metadata'], 'proofs_alias_retry02'):
            supervisor = original_join(evidence.origins['metadata'], 'launch_alias_compile_retry02.py')
        elif folder == original_join(evidence.origins['metadata'], 'audit_retry02'):
            supervisor = original_join(folder, 'launch_audit_retry02_hidden.py')
        elif folder == evidence.origins.get('proofs') and PurePosixPath(evidence_key(path)).name == 'functional_runner_exit.json':
            supervisor = original_join(evidence.origins['metadata'], 'launch_completion02.py' if folder.endswith('/proofs_completion02') else 'launch_functional_retry02_hidden.py')
        elif folder == evidence.origins.get('metadata'):
            supervisor = original_join(folder, 'launch_synthesis_hidden.py')
        elif folder == evidence.origins.get('report'):
            supervisor = original_join(evidence.origins.get('physical_metadata', evidence.origins['metadata']), 'launch_physical_hidden.py')
        elif folder.endswith('/proofs_retry02'):
            supervisor = original_join(folder.rsplit('/', 1)[0], 'launch_retry02_hidden.py')
        else:
            raise SystemExit('Unresolved executed supervisor script: ' + str(path))
        evidence.check(supervisor, receipt['supervisor_sha256'])
    return receipt


def check_timing(physical):
    require(physical['passed'] is True and all(physical['criteria'].values()), 'Physical acceptance gate failed')
    require(physical['period_ns'] == 20 and math.isfinite(physical['fmax_mhz']) and physical['fmax_mhz'] >= 50,
            '50MHz acceptance failed')
    require(physical['setup_violated_endpoints'] == physical['hold_violated_endpoints'] == 0,
            'Setup or hold endpoints remain violated')
    require(set(physical['checks']) == TIMING_TYPES and all(math.isfinite(x['worst_slack_ns']) and x['worst_slack_ns'] >= 0
            for x in physical['checks'].values()), 'Incomplete or negative timing acceptance')


def validate_functional(e, qualification):
    """Check current top/FSM receipts and exact reused controller/ground chains."""
    family = qualification['variant'].split('_')[0]
    if family == 'v22':
        validate_v22(e, qualification)
        return
    if family == 'v20':
        validate_v20(e, qualification)
        return
    if family == 'v21':
        validate_v21(e, qualification)
        return
    o = e.origins
    expected = qualification['source_sha256']
    meta, proofs = o['metadata'], o['proofs']
    proof = e.read(original_join(meta, 'PROOF_BINDING.json'), qualification['functional_binding_sha256'])
    require(proof['passed'] is True and proof['source55'] == expected and proof['actual_proof_runner_wait'] == 0,
            'Functional qualification differs from selected source55')
    inputs = e.read(original_join(proofs, 'inputs.json'), proof['inputs_sha256'])
    require(inputs['source55'] == expected, 'Functional inputs source55 differs')
    check_inventory(e, o['repo'], inputs['bound_files'])
    top = e.read(original_join(proofs, 'top_safety_results.json'), proof['top13_result_sha256'])
    require(top['passed'] is True and top['cases'] == 13, 'Current top13 did not pass')
    require(proof['top13']['passed'] is True and proof['top13']['cases'] == 13
            and proof['top13']['actual_root_wait'] == 0 and proof['top13']['compile_and_vvp_actual_waits'] == [0, 0],
            'Current top13 binding omits successful actual waits')
    check_receipt(e, original_join(proofs, 'runner_exit.json'), proof['actual_top13_runner_exit_sha256'])
    for name in ['compile_exit.json', 'vvp_exit.json']:
        check_receipt(e, original_join(proofs, name))
    for name in ['top_safety_tb.v', 'top_safety.compile.log', 'top_safety.log', 'run_top13.py']:
        e.blob(original_join(proofs, name))
    miter = proof['flight_state_miter']
    require(miter['passed'] is True and miter['all_internal_and_public_state_bits'] is True
            and miter['threshold_vectors'] == 2097152 and miter['no_DUT_force_or_preload'] is True,
            'Landing/FSM proof is incomplete')
    for phase in ['fsm_compile', 'fsm_vvp']:
        check_receipt(e, original_join(proofs, phase + '_exit.json'))
    require(b'completeFSM' in e.blob(original_join(proofs, 'fsm_vvp.stdout.log')), 'FSM pass witness missing')
    freeze = e.read(original_join(meta, 'source_freeze.json'))
    require(freeze['source55'] == expected, 'Source freeze differs')
    e.check(original_join(meta, 'source_review.md'), freeze['source_review_sha256'])
    e.check(original_join(meta, 'SOURCE_EQUIVALENCE_BASIS.json'), freeze['source_equivalence_basis_sha256'])
    family = qualification['variant'].split('_')[0]
    reused = e.read(original_join(meta, 'REUSED_BINDINGS_RECHECK.json'))
    require(reused['passed'] is True and reused['source55'] == expected
            and reused['new_' + family + '_proof_binding_sha256'] == qualification['functional_binding_sha256']
            and reused['reused_controller_actual_root_wait'] == 0 and reused['ground_current_inputs_rehashed'] == 43,
            'Reused proof binding differs')
    parent = e.read(original_join(o['parent_proofs'], 'RESULT.json'), proof['parent_proof_sha256'])
    require(parent['passed'] is True and reused['parent_binding_sha256'] == proof['parent_proof_sha256'],
            'Parent functional qualification differs')
    parent_inputs = e.read(original_join(o['parent_proofs'], 'inputs.json'), parent['inputs_sha256'])
    check_receipt(e, original_join(o['parent_proofs'], 'runner_exit.json'), parent['runner_exit_sha256'])
    controller = evidence_key(parent_inputs['reused_controller_proofs'])
    result = e.read(original_join(controller, 'results.json'), parent_inputs['reused_results_sha256'])
    require(result['passed'] is True and reused['parent_controller_results_sha256'] == parent_inputs['reused_results_sha256'],
            'Reused controller result differs')
    check_receipt(e, original_join(controller, 'runner_exit.json'), reused['parent_controller_runner_exit_sha256'])
    dependencies = parent_inputs['exact_dependencies']
    require(len(dependencies) == 6 and reused['six_exact_controller_dependencies'] == dependencies,
            'Expected six exact controller dependencies')
    for name, digest in dependencies.items():
        require(expected[name] == parent['source55'][name] == result['source55'][name] == digest,
                'Reused controller dependency changed: ' + name)
        e.check(original_join(o['source'], name), digest)
    require(result['five']['passed'] and result['five']['completed'] == 5
            and result['boundary']['passed'] and result['boundary']['completed'] == 2
            and result['contention']['passed'], 'Controller five/boundary/contention proof failed')
    for case in result['five']['results']:
        require(case['exit_code'] == 0, 'Controller case failed')
        base = original_join(controller, 'five', case['name'])
        e.check(original_join(base, 'simulation.log'), case['log_sha256'])
        e.check(original_join(base, 'trace.csv'), case['trace_sha256'])
    for case in result['boundary']['results']:
        require(case['exit_code'] == 0, 'Controller fraction boundary failed')
        e.check(original_join(controller, 'boundary', 'fraction_' + str(case['fraction']), 'simulation.log'), case['log_sha256'])
    check_inventory(e, original_join(controller, 'contention', 'contention'), result['contention']['evidence_sha256'])
    require(len(result['stages']) == 4, 'Controller stage receipts missing')
    for name, stage in zip(['five', 'boundary', 'top', 'contention'], result['stages']):
        require(stage['normal_wait_return'] is True and stage['actual_p_wait'] == 0, 'Controller stage wait failed')
        receipt = check_receipt(e, original_join(controller, name + '_exit.json'))
        require(all(receipt.get(key) == value for key, value in stage.items()), 'Controller stage result/receipt differs')
    ground_path = original_join(o['repo'], 'ground/B0B4/test_results/verification.json')
    ground = e.read(ground_path, parent_inputs['ground_verification_sha256'])
    require(ground['result'] == 'PASS' and len(ground['input_sha256']) == 43
            and reused['ground_verification_sha256'] == parent_inputs['ground_verification_sha256'],
            'Ground proof binding differs')
    check_inventory(e, o['repo'], ground['input_sha256'])
    for name in ['python', 'node']:
        require(ground[name]['actual_exit_code'] == 0, 'Ground subprocess failed')
        e.check(original_join(o['repo'], 'ground/B0B4/test_results/' + name + '.log'), ground[name]['log_sha256'])
    if family == 'v18':
        e.check(original_join(meta, 'VY_BINDING.json'), proof['vy_binding_sha256'])
        validate_vy(e, meta, expected)


class EvidenceView:
    """Read an explicitly identified parent chain without relabeling its source55."""
    def __init__(self, evidence, **origins):
        self.base = evidence
        self.origins = dict(evidence.origins, **origins)
    def __getattr__(self, name):return getattr(self.base, name)


def proof_directory(meta, value):
    directory = evidence_key(value) if PureWindowsPath(str(value)).is_absolute() or str(value).startswith('/') else original_join(meta, value)
    require(original_contains(directory, meta), 'Proof directory escapes metadata family')
    return directory


def raw_success_receipt(e, path, digest, field='actual_p_wait'):
    receipt = e.read(path, digest)
    require(field in {'actual_p_wait', 'actual_child_p_wait', 'actual_completedprocess_returncode'}
            and receipt.get(field) == 0 and receipt.get('normal_return' if field == 'actual_completedprocess_returncode' else 'normal_wait_return') is True
            and not receipt.get('terminated_after_timeout'), 'Actual successful proof receipt failed')
    folder = evidence_key(path).rsplit('/', 1)[0]
    stem = PurePosixPath(evidence_key(path)).name.removesuffix('_exit.json')
    for channel in ['stdout', 'stderr']:
        if channel + '_sha256' in receipt:
            e.check(original_join(folder, stem + '.' + channel + '.log'), receipt[channel + '_sha256'])
    return receipt


def check_compile_simulation(e, compile_receipt, simulation_receipt, output=None, top=None, source=None, expected=None, simulation_extra=None):
    command, simulation = compile_receipt['command'], simulation_receipt['command']
    require(PureWindowsPath(command[0]).name.lower() in {'iverilog', 'iverilog.exe'}
            and command.count('-s') == command.count('-o') == 1
            and PureWindowsPath(simulation[0]).name.lower() in {'vvp', 'vvp.exe'} and len(simulation) >= 2
            and simulation[2:] == (simulation_extra or []),
            'Compile/simulation command roles differ')
    executable = command[command.index('-o') + 1]
    require(original_identity(executable) == original_identity(simulation[1])
            and (output is None or original_identity(executable) == original_identity(output))
            and (top is None or command[command.index('-s') + 1] == top), 'Compile/simulation executable or top differs')
    e.blob(executable)
    if source is not None:
        project = ET.fromstring(e.blob(original_join(source, 'acg720_ano_port.gprj'), expected['acg720_ano_port.gprj']))
        files = [item.attrib['path'].replace('\\', '/') for item in project.findall('.//File')
                 if item.attrib.get('type') == 'file.verilog' and item.attrib.get('enable') == '1']
        require(files and len(set(files)) == len(files), 'Compiled project source inventory is empty or duplicated')
        arguments = {original_identity(arg) for arg in command if isinstance(arg, str) and (PureWindowsPath(arg).is_absolute() or arg.startswith('/'))}
        for name in files:
            require(name in expected and original_identity(original_join(source, name)) in arguments,
                    'Compile command omits selected project source: ' + name)
            e.check(original_join(source, name), expected[name])


def check_failed_receipt(e, path, digest):
    receipt = e.read(path, digest)
    require(receipt.get('normal_wait_return') is True and receipt.get('actual_p_wait') == 1,
            'Original failed receipt was not preserved')
    folder = evidence_key(path).rsplit('/', 1)[0]
    stem = PurePosixPath(evidence_key(path)).name.removesuffix('_exit.json')
    for channel in ['stdout', 'stderr']:
        require(channel + '_sha256' in receipt, 'Original failure log hash missing')
        e.check(original_join(folder, stem + '.' + channel + '.log'), receipt[channel + '_sha256'])
    return receipt


def validate_parent18_components(e, selected, digest, dependencies):
    parent_meta = original_join(e.origins['repo'], 'analysis/20261026_z_aw_fix/build/compact_aw_v18')
    parent = e.read(original_join(parent_meta, 'PROOF_BINDING.json'), digest)
    require(parent['source55'] != selected, 'Parent full source55 must retain its distinct identity')
    for name, expected in dependencies.items():
        require(selected[name] == parent['source55'][name] == expected, 'Named parent component dependency changed: ' + name)
    parent_source = original_join(e.origins['repo'], 'out/z_aw_fix_20261026/compact_aw_v18/canonical/source')
    view = EvidenceView(e, metadata=parent_meta, proofs=original_join(parent_meta, 'proofs'), source=parent_source)
    validate_functional(view, {'variant': 'v18_p3', 'source_sha256': parent['source55'], 'functional_binding_sha256': digest})
    return parent


def validate_new_source_count(e, expected, count):
    baseline = e.read(original_join(e.origins['repo'], 'firmware/B0B3/qualification.json'))['source_sha256']
    require(len(expected) == 55 and set(expected) == set(baseline)
            and len([name for name in expected if expected[name] != baseline[name]]) == count,
            'B3-relative source change count differs')


def compiled_source_root(e):
    family = PurePosixPath(e.origins['metadata']).name
    require(family in {'compact_aw_v20', 'compact_aw_v21', 'compact_aw_v22'}, 'Compiled proof source family differs')
    return original_join(e.origins['repo'], 'out/z_aw_fix_20261026', family, 'canonical/source')


def v22_reference(meta, base, name):
    """Only the declared sibling alias retry may use the preserved ../ spelling."""
    name = str(name).replace('\\', '/')
    prefix = '../proofs_alias_retry02/'
    absolute_prefix = evidence_key(base).rstrip('/') + '/' + prefix
    if name.casefold().startswith(absolute_prefix.casefold()):
        require(original_identity(base) == original_identity(original_join(meta, 'proofs_attempt01')), 'v22 absolute sibling inventory base differs')
        return original_join(meta, 'proofs_alias_retry02', name[len(absolute_prefix):])
    if name.startswith(prefix):
        require(original_identity(base) == original_identity(original_join(meta, 'proofs_attempt01')), 'v22 sibling inventory base differs')
        return original_join(meta, 'proofs_alias_retry02', name[len(prefix):])
    return evidence_key(name) if PureWindowsPath(name).is_absolute() else original_join(base, name)


def check_v22_inventory(e, meta, base, items):
    for name, item in items.items():
        check_inventory(e, e.origins['repo'], {v22_reference(meta, base, name): item})


def validate_v22_failed_inputs(e):
    """Preserve two invalid self-output declarations in the failed attempt only.

    The original JSON and actual terminal logs remain archived unchanged. This
    returns the real immutable inventory; no general hash check is relaxed.
    """
    meta = e.origins['metadata'];a = original_join(meta, 'proofs_attempt01');d = original_join(meta, 'proofs_completion02')
    p = e.read(original_join(meta, 'PROOF_BINDING.json'))
    require(p['passed'] is True and p['original_attempt_root_actual_wait'] == p['original_failed_alias_compile_wait'] == 1
            and p['actual_completion_runner_wait'] == p['actual_alias_retry_root_wait'] == 0, 'v22 original/retry proof wait scope differs')
    current = e.read(original_join(d, 'inputs.json'), p['inputs_sha256'])
    old_path = original_join(a, 'inputs.json')
    terminal_inputs = {v22_reference(meta, a, name): digest for name, digest in current['bound_inputs'].items()}
    require(len(terminal_inputs) == len(current['bound_inputs']), 'v22 completion input path aliases collide')
    require(old_path in terminal_inputs, 'v22 completion must bind the exact original input JSON')
    old_bytes = e.blob(old_path, terminal_inputs[old_path]);old = json.loads(old_bytes)
    require(old['source55'] == current['source55'] == p['source55'], 'v22 failed/current input source differs')
    failed_root = check_failed_receipt(e, original_join(a, 'functional_runner_exit.json'), p['original_functional_root_exit_sha256'])
    failed_compile = check_failed_receipt(e, original_join(a, 'alias_compile_exit.json'), terminal_inputs[original_join(a, 'alias_compile_exit.json')])
    error = e.blob(original_join(a, 'functional_runner.stderr.log')).decode('utf8')
    compile_error = e.blob(original_join(a, 'alias_compile.stderr.log')).decode('utf8')
    require(error.rstrip().endswith("AssertionError: ('alias_compile', 1)") and 'Error opening temporary file' in compile_error
            and 'Please check TMP or TMPDIR' in compile_error
            and PureWindowsPath(failed_compile['command'][0]).name.lower() in {'iverilog', 'iverilog.exe'},
            'v22 original failure must be the actual TEMP compile failure, not a waived assertion')
    invalid = {original_join(a, 'functional_runner.' + channel + '.log') for channel in ['stdout', 'stderr']}
    excluded = {evidence_key(path) for path in current['excluded_original_misclassified_outputs']}
    require(excluded == invalid | {original_join(a, 'functional_runner_process.json')}, 'v22 invalid self-output declarations differ')
    declared = {evidence_key(path): digest for path, digest in old['bound_inputs'].items()}
    require(len(declared) == len(old['bound_inputs']), 'v22 original input path aliases collide')
    require(invalid <= set(declared), 'v22 original self-output declarations missing')
    empty_sha = hashlib.sha256(b'').hexdigest();references = {}
    for path in sorted(invalid):
        channel = 'stdout' if path.endswith('.stdout.log') else 'stderr';actual = failed_root[channel + '_sha256']
        require(declared[path] == empty_sha and actual != empty_sha and terminal_inputs[path] == actual,
                'v22 invalid self-output declaration/real terminal log binding differs')
        e.check(path, actual)
        references[path] = dict(inventory=old_path, inventory_sha256=hashlib.sha256(old_bytes).hexdigest(), declared_sha256=empty_sha,
                                terminal_sha256=actual, terminal_receipt=original_join(a, 'functional_runner_exit.json'),
                                terminal_receipt_sha256=p['original_functional_root_exit_sha256'],
                                reason='Invalid mutable self-output reference in preserved TEMP-failed attempt; never an immutable proof input or actual original failure cause.')
    if isinstance(e, ArchivedEvidence):
        require(e.invalid_failed_inputs == references, 'v22 indexed invalid failed-input reference inventory differs')
    else:
        e.invalid_failed_inputs = references
    immutable = {path: digest for path, digest in declared.items() if path not in invalid}
    check_inventory(e, e.origins['repo'], immutable)
    return immutable


def validate_v22(e, qualification):
    o, expected, meta = e.origins, qualification['source_sha256'], e.origins['metadata']
    compiled = compiled_source_root(e)
    p = e.read(original_join(meta, 'PROOF_BINDING.json'), qualification['functional_binding_sha256'])
    require(p['passed'] is True and p['source55'] == expected and p['actual_proof_runner_wait'] == p['actual_completion_runner_wait'] == 0
            and p['new_state_bits'] == p['legacy_public_output_cycle_change'] == 0
            and p['old_six_controller_byte_identity_reuse_claimed'] is False, 'v22 current proof source/scope/waits differ')
    validate_new_source_count(e, expected, 12)
    directory = proof_directory(meta, p['proof_directory']);a = original_join(meta, 'proofs_attempt01');b = original_join(meta, 'proofs_alias_retry02')
    require(directory == o['proofs'] == original_join(meta, 'proofs_completion02')
            and original_identity(p['fresh_proof_directory']) == original_identity(a)
            and original_identity(p['alias_retry_directory']) == original_identity(b), 'v22 proof/retry directories differ')
    source = e.read(original_join(meta, 'SOURCE_CHANGES.json'))
    require(source['passed'] is True and source['source55'] == expected and source['changed_files'] == ['position/mtf_xyz_hold_control.v']
            and source['new_state_bits'] == source['new_clock_edges'] == source['legacy_public_output_cycle_change'] == 0
            and source['function_unchanged'] is True and source['other54_byte_exact'] is True, 'v22 reversible local-only source scope differs')
    parent_meta = original_join(o['repo'], 'analysis/20261026_z_aw_fix/build/compact_aw_v20')
    parent_source = original_join(o['repo'], 'out/z_aw_fix_20261026/compact_aw_v20/canonical/source')
    parent55 = e.read(original_join(parent_meta, 'PROOF_BINDING.json'))['source55']
    require(source['parent_source55'] == parent55 and [name for name in expected if expected[name] != parent55[name]] == source['changed_files'],
            'v22 must retain a distinct exact parent source boundary')
    data = e.blob(original_join(compiled, source['changed_files'][0]), expected[source['changed_files'][0]])
    for item in reversed(source['exact_reversible_edits']):
        old, new = bytes.fromhex(item['old_hex']), bytes.fromhex(item['new_hex'])
        require(data.count(new) == 1, 'v22 exact reversible edit marker differs');data = data.replace(new, old, 1)
    require(data == e.blob(original_join(parent_source, source['changed_files'][0]), parent55[source['changed_files'][0]]), 'v22 local edit does not reverse exactly')
    e.check(source['official_document'], source['official_document_sha256'])
    inputs = e.read(original_join(directory, 'inputs.json'), p['inputs_sha256'])
    require(inputs['source55'] == expected, 'v22 completion inputs source differs');check_v22_inventory(e, meta, a, inputs['bound_inputs'])
    validate_v22_failed_inputs(e)
    result = e.read(original_join(directory, 'RESULT.json'), p['result_sha256'])
    require(result['passed'] is True and result['source55'] == expected and result['inputs_sha256'] == p['inputs_sha256']
            and result['original_attempt_root_actual_wait'] == result['original_failed_alias_compile_wait'] == 1
            and result['actual_alias_retry_root_wait'] == 0 and result['new_controller_not_claimed_byte_identical_to_parent'] is True,
            'v22 completion result/actual waits differ')
    require(original_identity(result['artifact_base']) == original_identity(a) and original_identity(result['exit_receipts_base']) == original_identity(a),
            'v22 result inventory base differs')
    check_v22_inventory(e, meta, a, result['artifacts'])
    check_inventory(e, o['repo'], p['additional_bound_inputs'])
    check_receipt(e, original_join(directory, 'functional_runner_exit.json'), p['functional_root_exit_sha256'])
    roles = {stage + '_exit.json' for stage in ['five', 'boundary', 'contention', 'top13']}
    roles |= {stage + '/actual_child_receipts/' + str(i).zfill(2) + '_exit.json'
              for stage, count in [('five', 6), ('boundary', 4), ('contention', 2), ('top13', 2)] for i in range(1, count + 1)}
    roles |= {'../proofs_alias_retry02/' + name + '_exit.json' for name in ['compile', 'vvp', 'runner']}
    require(set(result['exit_receipts']) == roles and len(p['fresh_actual_exit_receipts']) == 22, 'v22 actual successful phase inventory incomplete')
    declared = {v22_reference(meta, a, item['path']): item for item in p['fresh_actual_exit_receipts']}
    actual = {}
    for name, digest in result['exit_receipts'].items():
        path = v22_reference(meta, a, name)
        require(path in declared and declared[path]['sha256'] == digest, 'v22 successful phase binding differs')
        actual[name] = check_receipt(e, path, digest)
    require(set(declared) == {v22_reference(meta, a, name) for name in roles} | {original_join(directory, 'functional_runner_exit.json')},
            'v22 successful phase roles contain missing or extra receipts')
    for stage, count in [('five', 6), ('boundary', 4), ('contention', 2), ('top13', 2)]:
        index = e.read(original_join(a, stage, 'actual_child_receipts/INDEX.json'))
        require(index['passed'] is True and len(index['receipts']) == count, 'v22 child receipt inventory differs: ' + stage)
        for item in index['receipts']:e.check(item['path'], item['sha256'])
        e.check(original_join(meta, 'record_stage.py'), index['recorder_sha256'])
        children = [actual[stage + '/actual_child_receipts/' + str(i).zfill(2) + '_exit.json'] for i in range(1, count + 1)]
        pairs = [(children[0], item) for item in children[1:]] if stage == 'five' else list(zip(children[::2], children[1::2]))
        for pair_index, (compile_receipt, simulation) in enumerate(pairs):
            check_compile_simulation(e, compile_receipt, simulation, simulation_extra=['+CASE=' + str(pair_index + 1)] if stage == 'five' else None)
            if stage == 'boundary':
                require('-Ptb.F=' + str([0, 16][pair_index]) in compile_receipt['command'], 'v22 actual FRAC compile parameter differs')
            arguments = {original_identity(arg) for arg in compile_receipt['command'] if isinstance(arg, str) and PureWindowsPath(arg).is_absolute()}
            dependencies = p['fresh_controller_six_dependencies']
            for name, digest in dependencies.items():
                require(expected[name] == digest and original_identity(original_join(compiled, name)) in arguments,
                        'v22 fresh controller compile dependencies differ')
                e.check(original_join(compiled, name), digest)
    five = e.read(original_join(a, 'five/results.json'))
    require(five['passed'] is True and five['completed'] == p['fresh_five_cases'] == 5 and len(five['results']) == 5, 'v22 fresh five-case results incomplete')
    for item in five['results']:
        require(item['exit_code'] == 0 and len(item['checks']) >= 2, 'v22 five-case assertion failed')
        for name, key in [('simulation.log', 'log_sha256'), ('trace.csv', 'trace_sha256')]:e.check(original_join(a, 'five', item['name'], name), item[key])
    boundary = e.read(original_join(a, 'boundary/results.json'))
    require(boundary['passed'] is True and boundary['completed'] == 2 and p['fresh_fraction_cases'] == [0, 16]
            and [item['fraction'] for item in boundary['results']] == [0, 16], 'v22 FRAC boundaries incomplete')
    for item in boundary['results']:
        require(item['exit_code'] == 0 and item['pass_lines'], 'v22 FRAC assertion failed')
        e.check(original_join(a, 'boundary/fraction_' + str(item['fraction']) + '/simulation.log'), item['log_sha256'])
    contention = e.read(original_join(a, 'contention/contention/results.json'))
    require(contention['passed'] is True and result['four_client'] == contention and p['fresh_four_client'] is True, 'v22 fresh four-client results differ')
    check_inventory(e, original_join(a, 'contention/contention'), contention['evidence_sha256'])
    original_tb = original_join(o['repo'], 'analysis/20261026_z_aw_fix/build/v4_release_proofs/top_safety_tb.v')
    require(e.blob(original_join(a, 'top13/top_safety_tb.v')) == e.blob(original_tb)
            and e.read(original_join(a, 'top13/top_safety_results.json'))['cases'] == p['fresh_top13']['cases'] == 13
            and e.read(original_join(a, 'top13/top_safety_results.json'))['passed'] is True, 'v22 original top13 fixture/results differ')
    for name in ['five/aw_tb.v', 'boundary/boundary_tb.v', 'contention/contention/contention_tb.v']:
        require(e.blob(original_join(a, name)) == e.blob(original_join(o['repo'], 'analysis/20261026_z_aw_fix/build/compact_aw_v9/proofs_retry02', name)),
                'v22 fresh proof changed the original substantive stimulus: ' + name)
    alias = e.read(original_join(b, 'RESULT.json'));alias_inputs = e.read(original_join(b, 'inputs.json'), alias['inputs_sha256'])
    require(alias['passed'] is True and alias['source55'] == alias_inputs['source55'] == expected
            and alias['source_function_and_fixture_byte_exact_to_failed_compile'] is True and p['actual_function_alias_miter'] is True,
            'v22 same-byte function alias proof failed')
    check_inventory(e, o['repo'], alias_inputs['bound_inputs']);check_inventory(e, b, alias['artifacts'])
    check_compile_simulation(e, actual['../proofs_alias_retry02/compile_exit.json'], actual['../proofs_alias_retry02/vvp_exit.json'])
    pass_line = 'PASS actual_alias vectors=53116 signed64=42768 fourstate=10348 all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1'
    require(alias['pass_line'] == pass_line and pass_line in e.blob(original_join(b, 'vvp.stdout.log')).decode('utf8'), 'v22 actual 53116-vector/four-state witness missing')
    for name in ['actual_functions.v', 'alias_tb.v', 'STRUCTURAL_IDENTITY.json']:
        require(e.blob(original_join(b, name)) == e.blob(original_join(a, 'alias', name)), 'v22 alias fixture changed during environment retry')
    identity = e.read(original_join(a, 'alias/STRUCTURAL_IDENTITY.json'), result['alias_identity_sha256'])
    require(identity['passed'] is True and identity['actual_function_byte_identical'] is True
            and identity['source_controller_sha256'] == {'v20': parent55['position/mtf_xyz_hold_control.v'], 'v22': expected['position/mtf_xyz_hold_control.v']},
            'v22 alias function/source binding differs')
    function_pattern = r' function signed \[31:0\] quantized_climb_q16;.*? end endfunction'
    # The executed fixture extractor used Path.read_text universal newlines.
    # Raw whole-source identity/reversal remains checked above without rewriting.
    current_text = e.blob(original_join(compiled, 'position/mtf_xyz_hold_control.v')).decode('utf8').replace('\r\n', '\n')
    parent_text = e.blob(original_join(parent_source, 'position/mtf_xyz_hold_control.v')).decode('utf8').replace('\r\n', '\n')
    functions = re.findall(function_pattern, current_text, re.S);fixture_text = e.blob(original_join(b, 'actual_functions.v')).decode('utf8').replace('\r\n', '\n')
    require(len(functions) == 1 and functions == re.findall(function_pattern, parent_text, re.S)
            and re.findall(function_pattern, fixture_text, re.S) == functions * 2
            and hashlib.sha256(functions[0].encode()).hexdigest() == identity['function_sha256']
            and identity['actual_wire_declaration_and_assignment'] in current_text and identity['actual_wire_declaration_and_assignment'] in fixture_text
            and identity['actual_old_alt_rhs'] in parent_text and identity['actual_new_alt_rhs'] in current_text,
            'v22 alias fixture does not contain the exact actual functions and sampled expression')
    component = e.read(original_join(meta, 'COMPONENT_REUSE_BINDING.json'), p['guard_binding_sha256'])
    require(component['passed'] is True and component['source55'] == expected and component['new_controller_requires_fresh_proof'] is True
            and component['old_six_controller_hashes_claimed_current'] is False and len(component['bound_inputs']) == 568
            and component['ground_current_inputs_rehashed'] == 43, 'v22 named inherited component scope differs')
    check_inventory(e, o['repo'], component['bound_inputs'])
    for dependencies in component['unchanged_dependency_sets'].values():
        require(all(expected[name] == parent55[name] == digest for name, digest in dependencies.items()), 'v22 inherited compiled dependency differs')
    parent = e.read(component['parent_binding_path'], component['parent_binding_sha256'])
    require(parent['source55'] == parent55 and parent55 != expected, 'v22 historical parent context must remain distinct')
    view = EvidenceView(e, metadata=parent_meta, source=parent_source, proofs=original_join(parent_meta, 'proofs_retry02'))
    validate_functional(view, dict(variant='v20_p3', source_sha256=parent55,
                        functional_binding_sha256=hashlib.sha256(e.blob(original_join(parent_meta, 'PROOF_BINDING.json'))).hexdigest()))
    reused = e.read(original_join(meta, 'REUSED_BINDINGS_RECHECK.json'))
    require(reused['passed'] is True and reused['source55'] == expected and reused['new_v22_proof_binding_sha256'] == qualification['functional_binding_sha256']
            and reused['old_six_controller_byte_identity_reuse_claimed'] is False and reused['ground_current_inputs_rehashed'] == 43,
            'v22 fresh/inherited proof recheck differs')


def validate_v20(e, qualification):
    o, expected, meta = e.origins, qualification['source_sha256'], e.origins['metadata']
    p = e.read(original_join(meta, 'PROOF_BINDING.json'), qualification['functional_binding_sha256'])
    require(p['passed'] is True and p['source55'] == expected and p['actual_proof_runner_wait'] == p['actual_top13_runner_wait'] == 0
            and p['new_private_same_publication_predicate_bits'] == 2 and p['legacy_public_output_cycle_change'] == 0
            and p['core_FSM_rerun'] is False, 'v20 current proof source/scope/waits differ')
    validate_new_source_count(e, expected, 12)
    directory = proof_directory(meta, p['proof_directory'])
    require(directory == o['proofs'], 'v20 selected proof directory differs')
    inputs = e.read(original_join(directory, 'inputs.json'), p['inputs_sha256'])
    require(inputs['source55'] == expected, 'v20 proof inputs source55 differs')
    check_inventory(e, o['repo'], inputs['bound_inputs'])
    result = e.read(original_join(directory, 'RESULT.json'))
    require(all(p.get(key) == value for key, value in result.items()), 'v20 result/binding differs')
    check_receipt(e, original_join(directory, 'functional_runner_exit.json'), p['functional_root_exit_sha256'])
    top = p['fresh_top13'];topdir = proof_directory(meta, top['directory'])
    top_root = original_join(meta, 'proofs/top13_runner_exit.json')
    require(top['passed'] is True and top['cases'] == 13 and top['actual_root_wait'] == 0
            and top['candidate_top13_total_actual_runs'] == 1 and top['reused_in_retry_after_exact_hash_check'] is True
            and top['original_v4_TB_byte_exact'] is True and original_identity(top['root_exit_path']) == original_identity(top_root),
            'v20 requires its single fresh successful top13 run')
    roles = {top_root: 'actual_p_wait', original_join(topdir, 'compile_exit.json'): 'actual_completedprocess_returncode',
             original_join(topdir, 'vvp_exit.json'): 'actual_completedprocess_returncode',
             original_join(directory, 'integration_compile_exit.json'): 'actual_p_wait', original_join(directory, 'integration_vvp_exit.json'): 'actual_p_wait'}
    records = {evidence_key(item['path']): item for item in p['fresh_actual_exit_receipts']}
    require(set(records) == set(roles), 'v20 fresh actual receipt roles incomplete')
    actual = {}
    for path, field in roles.items():
        require(records[path]['actual_wait_field'] == field, 'v20 receipt wait role differs')
        actual[path] = raw_success_receipt(e, path, records[path]['sha256'], field)
    check_compile_simulation(e, actual[original_join(topdir, 'compile_exit.json')], actual[original_join(topdir, 'vvp_exit.json')],
                             original_join(topdir, 'top_safety.vvp'), 'tb', compiled_source_root(e), expected)
    check_compile_simulation(e, actual[original_join(directory, 'integration_compile_exit.json')], actual[original_join(directory, 'integration_vvp_exit.json')],
                             original_join(directory, 'integration.vvp'), 'guard_integration_tb', compiled_source_root(e), expected)
    require(original_identity(actual[top_root]['command'][-1]) == original_identity(original_join(topdir, 'run_top13.py')),
            'v20 fresh top13 root command differs')
    original_tb = original_join(o['repo'], 'analysis/20261026_z_aw_fix/build/v4_release_proofs/top_safety_tb.v')
    require(e.blob(original_join(topdir, 'top_safety_tb.v'), top['top_TB_sha256']) == e.blob(original_tb), 'v20 top13 original stimulus differs')
    top_result = e.read(original_join(topdir, 'top_safety_results.json'), top['result_sha256'])
    require(top_result['passed'] is True and top_result['cases'] == 13, 'v20 top13 result failed')
    require(b'PASS actual top/core stopped-width arm/controller/fresh/takeoff gates' in e.blob(original_join(topdir, 'top_safety.log')),
            'v20 original top13 pass log missing')
    integration = p['fresh_integration']
    require(integration['passed'] is True and integration['no_DUT_force_or_preload'] is True
            and integration['pass_line'] in e.blob(original_join(directory, 'integration_vvp.stdout.log')).decode('utf8')
            and 'combinations=1111' in integration['pass_line'] and 'default_wrong_flags_ignored=1' in integration['pass_line'],
            'v20 combined/default-caller integration evidence incomplete')
    failure = p['historical_failed_functional_root']
    failed = check_failed_receipt(e, failure['path'], failure['sha256'])
    require(failed['actual_p_wait'] == failure['actual_p_wait'] == 1 and failed['normal_wait_return'] is True, 'v20 original failed root was not preserved')
    correction = e.read(original_join(meta, 'FUNCTIONAL_CORRECTION_02.json'))
    require(correction['candidate_source55_unchanged'] == expected, 'v20 fixture retry changed source55')
    for original, snapshot in correction['changed_original_input_snapshots'].items():
        require(e.blob(original, snapshot['sha256']) == e.blob(snapshot['preserved_path'], snapshot['sha256']), 'v20 historical fixture bytes differ')
    component = e.read(original_join(meta, 'COMPONENT_REUSE_BINDING.json'), p['guard_binding_sha256'])
    require(component['passed'] is True and component['source55'] == expected and p['component_binding_sha256'] == p['guard_binding_sha256']
            and len(component['bound_inputs']) == 563 and component['limitations']['no_full_source_parent_identity_claim'] is True, 'v20 component reuse scope differs')
    check_inventory(e, o['repo'], component['bound_inputs'])
    for group, receipt_key, count, field in [('AZ', 'actual_compile_sim_receipts', 6, 'actual_p_wait'),
                                           ('VY', 'actual_compile_sim_receipts', 8, 'actual_child_p_wait'),
                                           ('reused_core_FSM', 'actual_compile_vvp_receipts', 2, 'actual_p_wait')]:
        item = component[group]
        deps = item['exact_compiled_source_dependencies'] if group != 'reused_core_FSM' else item['exact_core_dependencies']
        require(all(expected[name] == digest for name, digest in deps.items()) and len(item[receipt_key]) == count,
                'v20 named component/receipt count differs: ' + group)
        actual = []
        for receipt in item[receipt_key]:
            require(receipt['actual_wait_field'] == field and receipt['actual_wait'] == 0 and receipt['normal_wait_return'] is True, 'v20 inherited wait differs')
            actual.append(raw_success_receipt(e, receipt['path'], receipt['sha256'], field))
        for compile_receipt, simulation_receipt in zip(actual[::2], actual[1::2]):
            check_compile_simulation(e, compile_receipt, simulation_receipt)
    dependencies = dict(component['six_controller_dependencies'], **component['reused_core_FSM']['exact_core_dependencies'],
                        **component['VY']['exact_compiled_source_dependencies'])
    validate_parent18_components(e, expected, component['reused_core_FSM']['parent_proof_sha256'], dependencies)
    reused = e.read(original_join(meta, 'REUSED_BINDINGS_RECHECK.json'))
    require(reused['passed'] is True and reused['source55'] == expected and reused['new_v20_proof_binding_sha256'] == qualification['functional_binding_sha256']
            and reused['component_reuse_binding_sha256'] == p['guard_binding_sha256'] and reused['ground_current_inputs_rehashed'] == 43,
            'v20 final reused binding differs')


def validate_v21(e, qualification):
    o, expected, meta = e.origins, qualification['source_sha256'], e.origins['metadata']
    p = e.read(original_join(meta, 'PROOF_BINDING.json'), qualification['functional_binding_sha256'])
    require(p['passed'] is True and p['source55'] == expected and p['actual_proof_runner_wait'] == 0, 'v21 proof source/root differs')
    validate_new_source_count(e, expected, 10)
    require(p['baseline_source55'] != expected and [name for name in expected if expected[name] != p['baseline_source55'][name]] == ['acg720_ano_port.v'],
            'v21 must change only top relative to its distinct v18 baseline')
    directory = proof_directory(meta, p['proof_directory'])
    require(directory == o['proofs'] and PurePosixPath(directory).name == 'proofs_retry02', 'v21 selected retry proof directory differs')
    inputs = e.read(original_join(directory, 'inputs.json'), p['inputs_sha256'])
    result = e.read(original_join(directory, 'RESULT.json'), p['new_proof_results_sha256'])
    require(result['passed'] is True and result['source55'] == inputs['source55'] == expected
            and result['baseline_source55'] == inputs['baseline_source55'] == p['baseline_source55']
            and result['inputs_sha256'] == p['inputs_sha256'], 'v21 result/input source binding differs')
    check_inventory(e, o['repo'], inputs['bound_files'])
    require(inputs['model_sha256'] == '7109c2568188627465d218bc099cf72f12e90807c21d4d862d2335b499043544', 'v21 must use the complete official primitive model')
    e.check(inputs['model'], inputs['model_sha256'])
    roles = ['integration8_compile', 'integration8_vvp', 'integration12000_compile', 'integration12000_vvp',
             'top13_default_compile', 'top13_default_vvp', 'top13_vendor_compile', 'top13_vendor_vvp']
    root_name = 'proof_retry02_runner_exit.json'
    require(set(p['exit_receipts']) == {'proofs_retry02/' + role + '_exit.json' for role in roles} | {root_name}
            and set(result['exit_receipts']) == {role + '_exit.json' for role in roles} and len(result['stages']) == 8,
            'v21 requires eight compile/simulation roles and its actual root')
    root = check_receipt(e, original_join(meta, root_name), p['exit_receipts'][root_name])
    require(result['actual_proof_retry02_runner_wait'] == 0 and result['root_exit_sha256'] == p['exit_receipts'][root_name], 'v21 root binding differs')
    e.check(original_join(meta, 'supervise_proofs_retry02.py'), root['supervisor_script_sha256'])
    for index, role in enumerate(roles):
        digest = result['exit_receipts'][role + '_exit.json']
        require(p['exit_receipts']['proofs_retry02/' + role + '_exit.json'] == digest, 'v21 per-role receipt digest differs')
        receipt = check_receipt(e, original_join(directory, role + '_exit.json'), digest)
        require(receipt == result['stages'][index], 'v21 stage/result receipt differs')
        command = receipt['command'];exe = PureWindowsPath(command[0]).name.lower()
        if role.endswith('_compile'):
            require(exe in {'iverilog', 'iverilog.exe'} and command.count('-s') == command.count('-o') == 1,
                    'v21 compile role command differs')
            vendor = role != 'top13_default_compile'
            require(('-DGW5_USE_VENDOR_BRAM' in command) == vendor and inputs['model'] in command, 'v21 vendor/default compile branch differs')
        else:
            require(exe in {'vvp', 'vvp.exe'} and len(command) == 2, 'v21 simulation role command differs')
            check_compile_simulation(e, result['stages'][index - 1], receipt, source=compiled_source_root(e), expected=expected)
    integration = p['new_vendor_SP_integration']
    require(integration['passed'] is True and integration['periods'] == [8, 12000]
            and integration['actual_SP_instances'] == 28 and integration['actual_GSR_instances'] == 1 and integration['extension_bits'] == 888
            and integration['all_public_top_outputs_compared'] == 13 and integration['complete_protocol_groups'] == 6
            and integration['frames'] == 42 and integration['bytes'] == 3864 and integration['independent_sequence_XOR_CRC'] is True
            and integration['hold_and_serializer_scheduling_natural'] is True and integration['no_internal_state_force_or_preload'] is True,
            'v21 vendor-SP integration coverage differs')
    require(len(result['integration']) == 2 and len(result['framing']) == 6, 'v21 integration/framing cases missing')
    layout = [(0xa586, 224, False), (0xa587, 32, False), (0xa588, 40, True), (0xa581, 128, True),
              (0xa582, 96, True), (0xa589, 48, True), (0xa585, 76, True)]
    for period, item in zip([8, 12000], result['integration']):
        require(item['period'] == period, 'v21 natural serializer period differs')
        base = original_join(directory, 'period' + str(period))
        executable = e.blob(original_join(base, 'top.vvp'), item['elaboration']['vvp_sha256']).decode('utf8')
        require(len(re.findall(r'\.scope module,\s*"memory"\s*"SP"', executable)) == 28
                and len(re.findall(r'\.scope module,\s*"GSR"\s*"GSR"', executable)) == 1 and 'portable_simulation' not in executable,
                'v21 integration did not elaborate actual28 SP and outer GSR')
        wire = e.blob(original_join(base, 'wire.hex'), item['wire_sha256'])
        raw = bytes.fromhex(wire.decode('ascii'));require(len(raw) == 1932, 'v21 wire group byte count differs')
        sequence = int.from_bytes(raw[2:4], 'big')
        for group in range(3):
            offset = group * 644
            for header, length, crc in layout:
                frame = raw[offset:offset + length]
                require(int.from_bytes(frame[:2], 'big') == header
                        and int.from_bytes(frame[4:6] if header == 0xa585 else frame[2:4], 'big') == (sequence + group) & 65535,
                        'v21 protocol header/sequence differs')
                if crc:
                    require(binascii.crc_hqx(frame[2:-2], 65535) == int.from_bytes(frame[-2:], 'big'), 'v21 protocol CRC differs')
                else:
                    checksum = 0
                    for byte in frame[2:-1]:checksum ^= byte
                    require(checksum == frame[-1], 'v21 protocol XOR differs')
                offset += length
        log = e.blob(original_join(directory, 'integration' + str(period) + '_vvp.stdout.log')).decode('utf8')
        require('PASS actual_v18_FF_vs_v21_vendor_SP extension888=1 SP=28' in log and 'no_internal_state_force_or_preload=1' in log,
                'v21 same-edge/hold public-output pass witness missing')
    original_tb = e.blob(original_join(o['repo'], 'analysis/20261026_z_aw_fix/build/v4_release_proofs/top_safety_tb.v'))
    require(e.blob(original_join(directory, 'top_safety_tb.v')) == original_tb and b'GSR GSR' in e.blob(original_join(directory, 'top13_root.v')),
            'v21 original top13 bytes or outer GSR fixture differs')
    for name, vendor, count in [('top13_default', False, 0), ('top13_vendor', True, 28)]:
        item = p[name]
        require(item['passed'] is True and item['cases'] == 13 and item['vendor_branch'] is vendor and item['original_stimulus_byte_identical'] is True,
                'v21 top13 mode/result failed')
        executable = e.blob(original_join(directory, name, 'top.vvp'), item['elaboration']['vvp_sha256']).decode('utf8')
        require(len(re.findall(r'\.scope module,\s*"memory"\s*"SP"', executable)) == count
                and len(re.findall(r'\.scope module,\s*"GSR"\s*"GSR"', executable)) == 1, 'v21 top13 actual primitive count differs')
    reused = e.read(original_join(meta, 'REUSED_BINDINGS_RECHECK.json'))
    require(reused['passed'] is True and reused['source55'] == expected and reused['parent_v18_source55'] == p['baseline_source55']
            and reused['full_source55_differs'] is True and reused['exact_changed_files'] == ['acg720_ano_port.v']
            and reused['new_v21_proof_binding_sha256'] == qualification['functional_binding_sha256'] and len(reused['bound_files']) == 178,
            'v21 inherited source/proof boundaries differ')
    check_inventory(e, o['repo'], reused['bound_files'])
    deps = dict(reused['six_exact_controller_dependencies'], **reused['reused_core_FSM_dependencies'], **reused['reused_VY_component_dependencies'])
    validate_parent18_components(e, expected, p['parent_v18_proof_binding_sha256'], deps)
    standalone = [path for path, digest in reused['bound_files'].items() if digest == reused['reused_standalone_vendor_SP_result_sha256']]
    require(len(standalone) == 1, 'v21 standalone WIDTH888 vendor-model proof missing')
    standalone_result = e.read(standalone[0], reused['reused_standalone_vendor_SP_result_sha256'])
    require(standalone_result['passed'] is True and standalone_result['actual_root_wait'] == 0
            and standalone_result['elaboration']['actual_SP_instances'] == 28 and standalone_result['elaboration']['portable_FF_branch_absent'] is True
            and any('initial_before_first_clock=0' in line and 'same_edge_capture=1' in line and 'unknown_enable_holds=' in line
                    for line in standalone_result['pass_lines']), 'v21 standalone initial-zero/same-edge/enable-hold proof failed')
    standalone_dir = evidence_key(standalone[0]).rsplit('/', 1)[0]
    standalone_inputs = e.read(original_join(standalone_dir, standalone_result['inputs_file']), standalone_result['inputs_sha256'])
    require(standalone_inputs['source55'] == p['baseline_source55'] == standalone_result['source55']
            and standalone_inputs['wrapper_sha256'] == expected['gw5_snapshot_bram.v'] and standalone_inputs['clock_hz'] == 50000000
            and standalone_inputs['width'] == 888 and standalone_inputs['model_sha256'] == inputs['model_sha256'],
            'v21 standalone source/model/clock binding differs')
    check_inventory(e, o['repo'], standalone_inputs['bound_files'])
    require(set(standalone_result['exit_receipts']) == {'attempt01/compile_exit.json', 'attempt01/vvp_exit.json', 'root_exit.json'}
            and len(standalone_result['stages']) == 2, 'v21 standalone actual receipt roles incomplete')
    standalone_receipts = {name: check_receipt(e, original_join(standalone_dir, name), digest)
                           for name, digest in standalone_result['exit_receipts'].items()}
    require(standalone_receipts['attempt01/compile_exit.json'] == standalone_result['stages'][0]
            and standalone_receipts['attempt01/vvp_exit.json'] == standalone_result['stages'][1], 'v21 standalone stage receipts differ')
    e.check(original_join(standalone_dir, 'supervise_proof.py'), standalone_receipts['root_exit.json']['supervisor_script_sha256'])
    check_compile_simulation(e, standalone_result['stages'][0], standalone_result['stages'][1],
                             original_join(standalone_dir, 'attempt01/extension_bram.vvp'), 'extension_bram_tb')
    require('-DGW5_USE_VENDOR_BRAM' in standalone_result['stages'][0]['command']
            and standalone_inputs['model'] in standalone_result['stages'][0]['command'], 'v21 standalone vendor compile command differs')
    executable = e.blob(original_join(standalone_dir, 'attempt01/extension_bram.vvp'), standalone_result['elaboration']['vvp_sha256']).decode('utf8')
    require(len(re.findall(r'\.scope module,\s*"memory"\s*"SP"', executable)) == 28
            and len(re.findall(r'\.scope module,\s*"GSR"\s*"GSR"', executable)) == 1 and 'portable_simulation' not in executable,
            'v21 standalone actual primitive elaboration differs')
    log = e.blob(original_join(standalone_dir, 'attempt01/vvp.stdout.log')).decode('utf8')
    require(all(line in log for line in standalone_result['pass_lines']), 'v21 standalone actual simulation log differs')
    failure = p['preserved_failed_attempt'];failed_path = original_join(meta, 'proof_runner_exit.json')
    failed = check_failed_receipt(e, failed_path, failure['root_exit_sha256'])
    require(failed['normal_wait_return'] is True and failed['actual_p_wait'] == failure['actual_root_wait'] == 1,
            'v21 original failed proof root was not preserved')


def validate_vy(e, meta, expected):
    binding = e.read(original_join(meta, 'VY_BINDING.json'))
    vyroot = original_join(meta, 'vy_proofs')
    vy = e.read(original_join(vyroot, 'RESULT.json'), binding['result_sha256'])
    require(binding['passed'] is True and binding['source55'] == expected
            and vy['passed'] is True and vy['source55'] == expected, 'VY source/result binding failed')
    roles = ['root', 'metric_compile', 'metric_vvp', 'uart_mode0_compile', 'uart_mode0_vvp',
             'uart_mode1_compile', 'uart_mode1_vvp', 'geometry_compile', 'geometry_vvp']
    declared = {'successful_wait_receipts/' + role + '_exit.json': role for role in roles}
    require(isinstance(vy.get('exit_receipts'), dict) and set(vy['exit_receipts']) == set(declared),
            'VY requires root and all eight compile/simulation receipt roles')
    require(len(vy.get('stages', [])) == 8 and vy['actual_successful_root_wait'] == 0
            and vy['actual_proof_supervisor_child_wait'] == 0 and vy['successful_compile_and_vvp_waits'] == [0] * 8,
            'VY result does not bind all successful actual waits')
    attempt = evidence_key(vy['attempt_directory'])
    require(original_contains(attempt, vyroot) and evidence_key(PurePosixPath(attempt).parent) == vyroot,
            'VY successful attempt escapes its proof directory')
    originals = vy.get('original_actual_wait_receipts', {})
    require(isinstance(originals, dict) and len(originals) == 9, 'VY original actual receipt inventory incomplete')
    seen_originals = set()
    for name, digest in vy['exit_receipts'].items():
        role = declared[name]
        receipt = check_receipt(e, original_join(vyroot, name), digest)
        require(receipt.get('schema_adapter_only') is True and receipt.get('actual_p_wait') == 0,
                'VY successful adapter is not an actual zero-wait binding')
        require(receipt['original_receipt'] in originals
                and originals[receipt['original_receipt']] == receipt['original_receipt_sha256'], 'VY original receipt inventory differs')
        original_path = original_join(vyroot, receipt['original_receipt'])
        expected_path = evidence_key(vy['supervisor_exit_receipt']) if role == 'root' else original_join(attempt, role + '_exit.json')
        require(original_identity(original_path) == original_identity(expected_path)
                and original_identity(original_path) not in seen_originals, 'VY receipt does not match its unique role')
        seen_originals.add(original_identity(original_path))
        actual = e.read(original_path, receipt['original_receipt_sha256'])
        field = 'actual_proof_supervisor_child_wait' if role == 'root' else 'actual_child_p_wait'
        require(receipt['original_actual_wait_field'] == field and actual.get('normal_wait_return') is True
                and actual[field] == 0 and not actual.get('terminated_after_timeout'), 'Original VY actual Popen wait did not pass')
        command = actual['command']
        require(isinstance(command, list) and command, 'VY original command missing')
        executable = PureWindowsPath(command[0]).name.lower()
        if role == 'root':
            require(executable in {'python', 'python.exe', 'python3'} and command[-1] == PurePosixPath(attempt).name
                    and [original_identity(arg) for arg in command if str(arg).lower().endswith('.py')] ==
                    [original_identity(original_join(meta, 'run_vy_proofs.py'))]
                    and vy['supervisor_exit_receipt_sha256'] == receipt['original_receipt_sha256'], 'VY supervisor role/command differs')
            e.check(original_join(meta, 'supervise_vy_proofs.py'), actual['supervisor_script_sha256'])
            e.check(original_join(meta, 'run_vy_proofs.py'), actual['runner_sha256'])
        else:
            pair = role.removesuffix('_compile').removesuffix('_vvp')
            output = original_join(attempt, pair + '.vvp' if pair != 'metric' else 'metric.vvp')
            if role.endswith('_compile'):
                top = 'metric_tb' if pair == 'metric' else 'geometry_tb' if pair == 'geometry' else 'uart_reader_tb'
                require(executable in {'iverilog', 'iverilog.exe'} and command.count('-s') == command.count('-o') == 1
                        and command[command.index('-s') + 1] == top
                        and original_identity(command[command.index('-o') + 1]) == original_identity(output)
                        and original_identity(original_join(attempt, top + '.v')) in [original_identity(arg) for arg in command],
                        'VY compile role/target/output differs')
                parameters = [command[i + 1] for i, arg in enumerate(command[:-1]) if arg == '-P']
                require(parameters == (['uart_reader_tb.MODE=' + pair[-1]] if pair.startswith('uart_mode') else []),
                        'VY UART mode/compile parameters differ')
            else:
                require(executable in {'vvp', 'vvp.exe'} and len(command) == 2
                        and original_identity(command[1]) == original_identity(output), 'VY simulation role/command differs')
            require(actual == vy['stages'][roles[1:].index(role)], 'VY stage result/original receipt differs')
            require(original_identity(actual['cwd']) == original_identity(attempt), 'VY phase working directory differs')
        folder = original_path.rsplit('/', 1)[0]
        stem = PurePosixPath(original_path).name.removesuffix('_exit.json').removesuffix('.exit.json')
        for channel in ['stdout', 'stderr']:
            e.check(original_join(folder, stem + '.' + channel + '.log'), actual[channel + '_sha256'])
    require(seen_originals == {original_identity(original_join(vyroot, name)) for name in originals},
            'VY declared original receipt roles differ')
    inputs = e.read(original_join(vyroot, vy['inputs_file']), vy['inputs_sha256'])
    require(inputs['source55'] == expected, 'VY inputs source55 differs')
    check_inventory(e, vyroot, inputs.get('bound_files', {}))


def parse_resource_cst(data):
    rows, seen = [], set()
    pattern = r'INS_LOC "([^"\r\n]+)" ((?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?(?:,(?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?)*);'
    for line in data.decode('utf8').splitlines():
        text = line.strip()
        if not text or text.startswith('//'):
            continue
        match = re.fullmatch(pattern, text)
        require(match is not None, 'Portable CST contains a non-resource directive or invalid row')
        name, locations = match.groups()
        require(name not in seen and all(not part.startswith('\\') for part in name.split('/')), 'Duplicate or nonsemantic resource row')
        seen.add(name)
        kinds = {location.split('_R')[0] for location in locations.split(',')}
        require(len(kinds) == 1 and len(locations.split(',')) == len(set(locations.split(','))), 'Mixed/duplicate resource locations')
        rows.append({'instance': name, 'line': text, 'resource_kind': next(iter(kinds))})
    return rows


def validate_v20_portable_preparation(e, qualification):
    o, expected = e.origins, qualification['source_sha256']
    family = 'v22' if qualification['variant'] == DSP22_VARIANT else 'v20'
    vg_sha = DSP22_VG_SHA if family == 'v22' else DSP20_VG_SHA
    kept_count, dsp_count, excluded_count = (33, 31, 19) if family == 'v22' else (41, 39, 11)
    base = original_join(o['repo'], 'analysis/20261026_z_aw_fix/build')
    standard, thin = original_join(base, 'compact_aw_' + family), original_join(base, 'compact_aw_' + family + '_dsp_followup')
    runtime = original_join(o['repo'], 'out/z_aw_fix_20261026/compact_aw_' + family)
    require(qualification['variant'] in {DSP20_VARIANT, DSP22_VARIANT} and qualification['profile'] == DSP_PROFILE and qualification['netlist_sha256'] == vg_sha
            and original_identity(o['metadata']) == original_identity(standard)
            and original_identity(o.get('physical_metadata', standard)) == original_identity(thin)
            and original_identity(o['donor']) == original_identity(original_join(runtime, 'build_attempt_01')),
            'Portable DSP profile must use standard v20 source/proof/SYN and runtime')
    binding_data = e.blob(original_join(thin, 'PORTABLE_CONSTRAINT_BINDING.json'))
    binding = json.loads(binding_data);binding_sha = hashlib.sha256(binding_data).hexdigest()
    counts = {'official_export_rows': 52, 'kept': kept_count, 'excluded': excluded_count, 'DSP': dsp_count, 'BSRAM': 2}
    require(binding['source55'] == expected and binding['VG_sha256'] == vg_sha and binding['measured_counts'] == counts
            and original_identity(binding['standard_source_proof_origin']) == original_identity(standard), 'Portable portable binding identity/counts differ')
    check_inventory(e, o['repo'], binding['bound_inputs'])
    e.check(original_join(thin, 'portable_constraints.py'), binding['checker_sha256'])
    e.check(original_join(standard, 'PROOF_BINDING.json'), binding['standard_proof_binding_sha256'])
    e.check(original_join(standard, 'COMPONENT_REUSE_BINDING.json'), binding['standard_guard_binding_sha256'])
    e.check(original_join(standard, 'physical_input_contract.py'), binding['standard_physical_contract_sha256'])
    require(binding['standard_proof_binding_sha256'] == qualification['functional_binding_sha256'], 'Portable portable standard functional binding differs')
    filtered = e.read(original_join(thin, 'PORTABLE_FILTER_VALIDATION.json'), binding['filter_validation_sha256'])['report']
    require(filtered['passed'] is True and all(filtered[key] == value for key, value in counts.items())
            and filtered['VG_sha256'] == vg_sha and len(filtered['kept_rows']) == kept_count and len(filtered['dropped_rows']) == excluded_count,
            'Portable official portable filter result differs')
    export_root = original_join(base, 'native_v4_DSP_export')
    official = e.blob(original_join(export_root, 'vendor_dsp_bsram.cst'), filtered['official_export_sha256'])
    exported = e.read(original_join(export_root, 'EXPORT_VALIDATION.json'), filtered['original_validation_sha256'])
    require(exported['exported_rows'] == 52 and exported['export_sha256'] == filtered['official_export_sha256'], 'Portable official export provenance differs')
    official_rows = parse_resource_cst(official)
    portable = e.blob(original_join(thin, 'portable_' + family + '_dsp_bsram.cst'), binding['portable_CST_sha256'])
    portable_rows = parse_resource_cst(portable)
    kept = [row['original_line'] for row in filtered['kept_rows']]
    require(len(official_rows) == 52 and len(portable_rows) == kept_count and [row['line'] for row in portable_rows] == kept
            and [row['line'] for row in official_rows] == [row['line'] for row in exported['rows']]
            and set(kept).isdisjoint(row['original_line'] for row in filtered['dropped_rows'])
            and set(kept) | {row['original_line'] for row in filtered['dropped_rows']} == {row['line'] for row in official_rows}
            and sum(row['resource_kind'] == 'DSP' for row in portable_rows) == dsp_count
            and sum(row['resource_kind'] == 'BSRAM' for row in portable_rows) == 2, 'Portable portable CST is not exact official41 subset')
    for row in filtered['kept_rows']:
        require(row['original_line_sha256'] == hashlib.sha256(row['original_line'].encode('utf8')).hexdigest()
                and row['primitive'] in ({'pROM', 'SP', 'DP', 'SDP', 'ROM'} if row['resource_kind'] == 'BSRAM' else {'MULT12X12', 'MULT27X36', 'MULTALU27X18'}),
                'Portable kept manufacturer line/type binding differs')
    prefix = e.blob(original_join(runtime, 'canonical/source/acg720_ano_port.cst'), expected['acg720_ano_port.cst'])
    combined = prefix + portable
    require(prefix.endswith(b'\n') and filtered['original_baseline_CST_sha256'] == binding['original_baseline_CST_sha256'] == expected['acg720_ano_port.cst']
            and filtered['original_baseline_prefix_bytes'] == len(prefix)
            and filtered['original_CLOCK_LOC_preserved'] == ['CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;']
            and [line.strip() for line in prefix.decode('utf8').splitlines() if line.strip().startswith('CLOCK_LOC')] == filtered['original_CLOCK_LOC_preserved']
            and filtered['portable_CST_sha256'] == binding['portable_CST_sha256']
            and hashlib.sha256(combined).hexdigest() == filtered['combined_CST_sha256'] == binding['combined_CST_sha256']
            and len(combined) == filtered['combined_CST_bytes'], 'Portable original complete CST prefix/portable suffix differs')
    require(e.blob(original_join(thin, 'source_freeze.json')) == e.blob(original_join(standard, 'source_freeze.json')), 'Portable thin source freeze differs')
    prep_data = e.blob(original_join(thin, 'PHYSICAL_PREPARATION.json'));prep = json.loads(prep_data)
    require(prep['profile'] == DSP_PROFILE and prep['source55'] == expected and prep['VG_sha256'] == vg_sha
            and prep['portable_constraint_binding_sha256'] == binding_sha and prep['measured_counts'] == counts
            and prep['effective_option_delta'] == {'cst_warn_to_error': 1} and prep['B3_relative_change_count'] == 12
            and prep['preflight_actual_returncode'] == 0 and prep['source_freeze_byte_exact_standard'] is True,
            'Portable portable physical preparation differs')
    for field, path in [('ROOT', runtime), ('CANON', original_join(runtime, 'canonical/source')), ('DONOR', original_join(runtime, 'build_attempt_01')),
                        ('standard_source_proof_origin', standard)]:
        require(original_identity(prep[field]) == original_identity(path), 'Portable portable preparation origin differs: ' + field)
    check_inventory(e, thin, prep['new_scripts_sha256']);check_inventory(e, standard, prep['parent_scripts_sha256'])
    preflight = e.read(original_join(thin, 'PHYSICAL_TCL_PREFLIGHT.json'), prep['physical_Tcl_preflight_sha256'])
    require(preflight['profile_label'] == DSP_PROFILE and preflight['combined_CST_sha256'] == binding['combined_CST_sha256']
            and (preflight['measured_kept_rows'], preflight['measured_DSP'], preflight['measured_BSRAM']) == (kept_count, dsp_count, 2)
            and all(item['Tcl_complete'] is item['options_verified'] is True for item in preflight['profiles'].values()), 'Portable portable Tcl preflight differs')
    preflight_exit = e.read(original_join(thin, 'PREFLIGHT_EXIT.json'))
    require((preflight_exit.get('normal_return') is True and preflight_exit.get('actual_completedprocess_returncode') == 0)
            or (preflight_exit.get('normal_wait_return') is True and type(preflight_exit.get('actual_p_wait')) is int and preflight_exit['actual_p_wait'] == 0),
            'Portable portable Tcl preflight did not exit successfully')
    require(original_identity(preflight_exit['command'][-1]) == original_identity(original_join(thin, 'preflight_physical_recipe.py')),
            'Portable portable Tcl preflight command differs')
    for channel in ['stdout', 'stderr']:e.check(original_join(thin, 'preflight.' + channel + '.log'), preflight_exit[channel + '_sha256'])
    review = e.read(original_join(thin, 'INDEPENDENT_PREPARATION_REVIEW.json'))
    require(review['passed'] is True and review['profile'] == DSP_PROFILE and review['measured_counts'] == counts
            and review['preparation_sha256'] == hashlib.sha256(prep_data).hexdigest() and review['constraint_binding_sha256'] == binding_sha
            and review['standard_physical_helper_calls_AST_identical'] is True
            and review['all_original_independent_raw_checks_AST_identical_after_provenance_alias'] is True,
            'Portable portable independent preparation review differs')
    if family == 'v22':
        require(prep['fresh_successful_proof_receipt_count'] == 22 and prep['original_TEMP_compile1_root1_preserved'] is True
                and prep['alias_retry0_completion0'] is True and prep['actual_DSP_delta_vs_v20'] == -1
                and prep['sealer_standard_SYN_provenance_corrected'] is True and prep['current_preparer_reexecuted'] is False
                and prep['current_preparer_AST_passed'] is True, 'v22 portable current proof/sealer provenance differs')
        e.check(original_join(o['donor'], 'verification/local_hint_effect_audit.json'), binding['local_hint_effect_audit_sha256'])
        source = e.read(original_join(standard, 'SOURCE_CHANGES.json'))
        protected = e.read(original_join(base, 'compact_aw_v4/source_freeze.json'))['source55']
        require(prep['baseline_source55'] == source['parent_source55'] and prep['protected_v4_source55'] == protected,
                'v22 portable parent-v20/protected-v4 source identities differ')
        truth = e.read(original_join(thin, 'DIAGNOSTIC_TRUTH_CHECKS.json'), prep['diagnostic_truth_checks_sha256'])
        receipt = e.read(original_join(thin, 'DIAGNOSTIC_TRUTH_EXIT.json'), prep['diagnostic_truth_exit_sha256'])
        require(truth['passed'] is True and receipt['normal_wait_return'] is True and receipt['actual_p_wait'] == 0
                and prep['diagnostic_truth_actual_wait'] == 0 and prep['distinct_truth_vectors'] == 1183 and prep['actual_script_expression_checks'] == 2366,
                'v22 portable actual status truth checks failed')
        check_inventory(e, thin, truth['scripts_sha256'])
        for channel in ['stdout', 'stderr']:e.check(original_join(thin, 'diagnostic_truth.' + channel + '.log'), receipt[channel + '_sha256'])
    validation = dict(filtered, original_IO_CST_sha256=expected['acg720_ano_port.cst'])
    return {'binding_sha256': binding_sha, 'validation': validation, 'combined': combined}


def validate_portable_preparation(e, qualification):
    if qualification['variant'] in {DSP20_VARIANT, DSP22_VARIANT}:return validate_v20_portable_preparation(e, qualification)
    """Validate the official46 input recipe without creating a physical attempt."""
    o, expected = e.origins, qualification['source_sha256']
    physical_meta = o.get('physical_metadata', o['metadata'])
    base = original_join(o['repo'], 'analysis/20261026_z_aw_fix/build')
    standard = original_join(base, 'compact_aw_v18')
    thin = original_join(base, 'compact_aw_v18_dsp_followup')
    runtime = original_join(o['repo'], 'out/z_aw_fix_20261026/compact_aw_v18')
    require(qualification['variant'] == DSP_VARIANT and qualification['profile'] == DSP_PROFILE
            and qualification['netlist_sha256'] == DSP_VG_SHA
            and original_identity(o['metadata']) == original_identity(standard)
            and original_identity(physical_meta) == original_identity(thin)
            and original_identity(o['donor']) == original_identity(original_join(runtime, 'build_attempt_01')),
            'DSP profile must use standard v18 functional/SYN evidence and runtime')
    binding_path = original_join(thin, 'PORTABLE_CONSTRAINT_BINDING.json')
    binding_bytes = e.blob(binding_path)
    binding = json.loads(binding_bytes.decode('utf8'))
    binding_sha = hashlib.sha256(binding_bytes).hexdigest()
    result = binding['validation']
    require(binding['profile'] == DSP_PROFILE and result['passed'] is True and result['source55'] == expected
            and binding['actual_SYN_VG_sha256'] == result['VG_sha256'] == DSP_VG_SHA
            and (result['official_rows'], result['kept'], result['DSP'], result['BSRAM']) == (52, 46, 44, 2)
            and len(result['dropped']) == 6 and binding['effective_option_delta'] == {'cst_warn_to_error': '1'},
            'Portable constraint binding source/VG/row counts differ')
    for field, path in [('runtime_ROOT', runtime), ('CANON', original_join(runtime, 'canonical/source')),
                        ('DONOR', original_join(runtime, 'build_attempt_01'))]:
        require(original_identity(binding[field]) == original_identity(path), 'Portable input origin differs: ' + field)
    check_inventory(e, o['repo'], binding['bound_inputs'])
    e.check(original_join(thin, 'portable_constraints.py'), binding['checker_sha256'])
    export_root = original_join(base, 'native_v4_DSP_export')
    for field, name in [('official_export_path', 'vendor_dsp_bsram.cst'), ('portable_constraint_path', 'portable_v18_dsp_bsram.cst'),
                        ('export_validation_path', 'EXPORT_VALIDATION.json')]:
        require(original_identity(binding[field]) == original_identity(original_join(export_root, name)), 'Official portable CST origin differs')
    exported = e.read(binding['export_validation_path'])
    official_data = e.blob(binding['official_export_path'], exported['export_sha256'])
    target = exported['portable']['v18']
    portable_data = e.blob(binding['portable_constraint_path'], target['constraint_sha256'])
    official, portable = parse_resource_cst(official_data), parse_resource_cst(portable_data)
    require(exported['exported_rows'] == len(official) == 52 and len(portable) == target['kept'] == 46
            and target['VG_sha256'] == DSP_VG_SHA and target['DSP'] == 44 and target['BSRAM'] == 2,
            'Official/portable constraint export differs')
    lines = [row['line'] for row in portable]
    require(lines == [row['line'] for row in target['kept_rows']] == [row['line'] for row in result['rows']]
            and [row['line'] for row in official] == [row['line'] for row in exported['rows']]
            and all(line in {row['line'] for row in official} for line in lines)
            and sum(row['resource_kind'] == 'DSP' for row in portable) == 44
            and sum(row['resource_kind'] == 'BSRAM' for row in portable) == 2,
            'Portable CST is not the exact official46 row subset')
    original = e.blob(original_join(binding['CANON'], 'acg720_ano_port.cst'), expected['acg720_ano_port.cst'])
    combined = original + portable_data
    require(original.endswith(b'\n') and result['original_IO_CST_sha256'] == expected['acg720_ano_port.cst']
            and result['portable_CST_sha256'] == target['constraint_sha256']
            and hashlib.sha256(combined).hexdigest() == result['combined_CST_sha256']
            and len(combined) == result['combined_CST_bytes'] and len(original) == result['original_IO_prefix_bytes'],
            'Original CST prefix/official suffix bytes differ')
    require(e.blob(original_join(thin, 'source_freeze.json')) == e.blob(original_join(standard, 'source_freeze.json')),
            'Thin physical family changed standard v18 source freeze')
    prep_bytes = e.blob(original_join(thin, 'PHYSICAL_PREPARATION.json'))
    prep = json.loads(prep_bytes.decode('utf8'))
    require(prep['profile'] == DSP_PROFILE and prep['source55'] == expected
            and prep['portable_constraint_binding_sha256'] == binding_sha and prep['actual_SYN_VG_sha256'] == DSP_VG_SHA
            and prep['preflight_actual_returncode'] == 0, 'Portable physical preparation differs')
    for name, digest in prep['new_scripts_sha256'].items():
        e.check(original_join(thin, name), digest)
    for name, digest in prep['parent_scripts_sha256'].items():
        e.check(original_join(standard, name), digest)
    for name, field in [('PROOF_BINDING.json', 'functional_binding_sha256'), ('VY_BINDING.json', 'VY_binding_sha256')]:
        e.check(original_join(standard, name), binding[field])
        require(prep[field] == binding[field], 'Portable preparation functional/VY origin differs')
    preflight = e.read(original_join(thin, 'PHYSICAL_TCL_PREFLIGHT.json'), prep['physical_Tcl_preflight_sha256'])
    require(preflight['combined_CST_sha256'] == result['combined_CST_sha256'] and preflight['portable_rows'] == 46
            and preflight['DSP'] == 44 and preflight['BSRAM'] == 2, 'Portable Tcl preflight differs')
    preflight_exit = e.read(original_join(thin, 'PREFLIGHT_EXIT.json'))
    require(preflight_exit['normal_return'] is True and preflight_exit['actual_completedprocess_returncode'] == 0,
            'Portable Tcl preflight did not exit successfully')
    for channel in ['stdout', 'stderr']:
        e.check(original_join(thin, 'preflight.' + channel + '.log'), preflight_exit[channel + '_sha256'])
    review = e.read(original_join(thin, 'INDEPENDENT_PREPARATION_REVIEW.json'))
    require(review['passed'] is True and review['profile'] == DSP_PROFILE
            and review['preparation_sha256'] == hashlib.sha256(prep_bytes).hexdigest()
            and review['constraint_binding_sha256'] == binding_sha
            and review['original_physical_gate_calls_AST_identical'] is True
            and review['original_independent_raw_checks_AST_identical'] is True, 'Portable independent preparation review differs')
    return {'binding_sha256': binding_sha, 'validation': result, 'combined': combined}


def validate_standard_evidence(e, qualification):
    o, expected = e.origins, qualification['source_sha256']
    physical_meta = o.get('physical_metadata', o['metadata'])
    require(len(expected) == 55, 'Expected exact source55')
    terminal = e.read(original_join(o['report'], 'TERMINAL_MANIFEST.json'))
    review = e.read(original_join(o['report'], 'INDEPENDENT_RAW_REVIEW.json'))
    require(terminal['passed'] is True and terminal['source55'] == expected
            and terminal['vg_sha256'] == qualification['netlist_sha256']
            and terminal['vendor_actual_p_wait'] == terminal['runner_actual_p_wait'] == 0,
            'Selected terminal qualification failed')
    require(review['passed'] is True and all(review['checks'].values()) and len(review['pins']) == 18,
            'Independent raw acceptance failed')
    e.check(original_join(physical_meta, 'independent_raw_review.py'), review['review_script_sha256'])
    require(review['period_ns'] == 20 and math.isfinite(review['fmax_mhz']) and review['fmax_mhz'] >= 50
            and review['violated_endpoints'] == {'setup': 0, 'hold': 0}
            and set(review['slacks_ns']) == TIMING_TYPES
            and all(math.isfinite(x) and x >= 0 for x in review['slacks_ns'].values()),
            'Independent raw timing acceptance differs')
    check_inventory(e, o['repo'], terminal['artifacts'])
    check_inventory(e, o['repo'], review['raw_sha256'])
    physical = e.read(original_join(o['attempt'], 'verification/physical_audit.json'))
    require(physical == qualification['physical'] and physical['source_sha256'] == expected,
            'Physical audit source/qualification differs')
    check_timing(physical)
    check_inventory(e, o['attempt'], physical['evidence_sha256'])
    for name, digest in expected.items():
        e.check(original_join(o['source'], name), digest)
    sdc = e.blob(original_join(o['source'], 'acg720_ano_port.sdc')).decode('utf8')
    require([x.strip() for x in sdc.splitlines() if x.strip() and not x.lstrip().startswith('#')] ==
            ['create_clock -name clk50 -period 20.000 [get_ports {clk50}]', 'set_false_path -from [get_ports {radio_rx}]'],
            'Original clock/false-path constraints differ')
    project = ET.fromstring(e.blob(original_join(o['source'], 'physical.gprj')))
    dsp = qualification['variant'] in DSP_VARIANTS
    constraint = 'physical_constraints.cst' if dsp else 'acg720_ano_port.cst'
    require([(f.attrib['path'], f.attrib['type']) for f in project.find('FileList')] ==
            [('impl/gwsynthesis/acg720_ano_port.vg', 'file.netlist'), (constraint, 'file.cst'), ('acg720_ano_port.sdc', 'file.sdc')],
            'Replay project is not the exact netlist/constraints project')
    if dsp:
        binding = validate_portable_preparation(e, qualification)
        require(e.blob(original_join(o['source'], 'physical_constraints.cst')) == binding['combined'],
                'Selected combined CST is not the byte-exact official46 suffix')
        applied = e.read(original_join(o['attempt'], 'verification/portable_constraint_binding.json'))
        require(applied['passed'] is True and applied['resource_rows'] == binding['validation']['kept'] and applied['DSP'] == binding['validation']['DSP'] and applied['BSRAM'] == 2
                and applied['source55_unchanged'] is True
                and applied['binding_sha256'] == binding['binding_sha256']
                and applied['combined_CST_sha256'] == binding['validation']['combined_CST_sha256']
                and applied['original_baseline_CST_sha256' if qualification['variant'] in {DSP20_VARIANT, DSP22_VARIANT} else 'original_IO_CST_sha256'] == expected['acg720_ano_port.cst'], 'Applied portable constraint receipt differs')
        if qualification['variant'] in {DSP20_VARIANT, DSP22_VARIANT}:
            require(original_identity(applied['standard_source_proof_origin']) == original_identity(o['metadata'])
                    and applied['standard_proof_binding_sha256'] == qualification['functional_binding_sha256'], 'Applied v20 portable standard proof origin differs')
        else:require(original_identity(applied['binding_path']) == original_identity(original_join(physical_meta, 'PORTABLE_CONSTRAINT_BINDING.json')), 'Applied v18 portable binding origin differs')
        tcl = e.blob(original_join(o['attempt'], 'physical.tcl')).decode('utf8')
        for option, value in [('place_option', '3'), ('route_option', '0'), ('map_option', '2'), ('replicate_resources', '0'),
                              ('route_maxfan', '23'), ('global_freq', '50'), ('timing_driven', '1'),
                              ('user_code', '0000B0B4'), ('cst_warn_to_error', '1')]:
            require(re.findall(r'^set_option -' + option + r'\s+(\S+)\s*$', tcl, re.M) == [value],
                    'Portable constraint physical option differs: ' + option)
    e.check(original_join(o['source'], 'impl/gwsynthesis/acg720_ano_port.vg'), qualification['netlist_sha256'])
    e.check(original_join(o['source'], 'impl/pnr/acg720_ano_port.fs'), qualification['bitstream_sha256'])
    e.blob(original_join(o['source'], 'impl/pnr/acg720_ano_port.pr'))
    check_receipt(e, original_join(o['attempt'], 'verification/physical_exit.json'))
    check_receipt(e, original_join(o['report'], 'runner_exit.json'))
    build_input = e.read(original_join(o['attempt'], 'verification/build_input.json'))
    require(build_input['source_sha256'] == expected and evidence_key(build_input['donor']) == o['donor'], 'Physical donor/source differs')
    physical_input = e.read(original_join(o['attempt'], 'verification/physical_input.json'))
    require(physical_input['source_sha256'] == expected and physical_input['donor_netlist_sha256'] == qualification['netlist_sha256'],
            'Physical execution source/VG differs')
    e.check(original_join(o['source'], 'physical.gprj'), physical_input['project_sha256'])
    e.check(original_join(o['attempt'], 'physical.tcl'), physical_input['tcl_sha256'])
    e.check(original_join(physical_meta, 'run_physical.py'), physical_input['runner_sha256'])
    if dsp:
        require(physical_input['portable_constraint_binding_sha256'] == binding['binding_sha256']
                and physical_input['combined_CST_sha256'] == binding['validation']['combined_CST_sha256']
                and physical_input['original_baseline_CST_sha256' if qualification['variant'] in {DSP20_VARIANT, DSP22_VARIANT} else 'original_IO_CST_sha256'] == expected['acg720_ano_port.cst'], 'Physical input portable binding differs')
    result = e.read(original_join(o['attempt'], 'verification/build_result.json'))
    require(result['passed'] is True and result['source_sha256'] == expected
            and result['netlist_sha256'] == qualification['netlist_sha256']
            and result['bitstream_sha256'] == qualification['bitstream_sha256'], 'Physical result binding differs')
    e.check(original_join(o['attempt'], 'verification/physical_audit.json'), result['physical_audit_sha256'])
    e.check(original_join(o['attempt'], 'verification/physical_exit.json'), result['physical_exit_sha256'])
    donor_binding = e.read(original_join(o['attempt'], 'verification/donor_evidence_binding.json'))
    require(donor_binding['passed'] is True and donor_binding['source55'] == expected
            and donor_binding['vg_sha256'] == qualification['netlist_sha256'], 'Donor binding differs')
    check_inventory(e, o['repo'], donor_binding['artifacts'])
    validate_synthesis(e, qualification)
    validate_functional(e, qualification)


def validate_v21_synthesis(e, qualification):
    o, expected, vg = e.origins, qualification['source_sha256'], qualification['netlist_sha256']
    meta = o['metadata'];syn = original_join(o['donor'], 'verification');directory = original_join(meta, 'audit_retry02')
    completion = e.read(original_join(directory, 'completion_result.json'), qualification['synthesis_completion_sha256'])
    manifest = e.read(original_join(directory, 'completion_manifest.json'), qualification['synthesis_completion_manifest_sha256'])
    require(completion['passed_audit_completion'] is True and completion['passed_SYN_only'] is True
            and completion['source55'] == manifest['source55'] == expected and completion['original_VG_sha256'] == manifest['original_VG_sha256'] == vg
            and original_identity(completion['completion_directory']) == original_identity(directory)
            and original_identity(manifest['completion_directory']) == original_identity(directory)
            and completion['SYN_rerun'] is manifest['SYN_rerun'] is False, 'v21 audit completion source/VG/scope differs')
    for key, value in [('original_vendor_actual_wait', 0), ('original_audit_actual_wait', 1), ('original_runner_actual_wait', 1),
                       ('successful_audit_wait', 0), ('actual_completion_root_wait', 0)]:
        require(completion[key] == manifest[key] == value, 'v21 original/retry actual waits differ: ' + key)
    require(completion['completion_runner_actual_wait'] == 0, 'v21 actual completion root wait failed')
    check_inventory(e, directory, manifest['artifacts'])
    preparation = e.read(original_join(directory, 'RETRY_PREPARATION.json'), completion['preparation_sha256'])
    approval = e.read(original_join(directory, 'REVIEW_APPROVAL.json'), completion['approval_sha256'])
    require(preparation['source55'] == approval['source55'] == expected and preparation['original_VG_sha256'] == approval['original_VG_sha256'] == vg
            and approval['approved'] is True and len(set(approval['reviewers'])) >= 2
            and approval['preparation_sha256'] == completion['preparation_sha256'], 'v21 retry review approval differs')
    require(set(preparation['retry_scripts_sha256']) == {'run_audit_retry02.py', 'complete_audit_retry02.py', 'launch_audit_retry02_hidden.py',
                                                       'escaped_port_adapter.py', 'ce_boolean.py'}
            and preparation['retry_scripts_sha256'] == approval['reviewed_scripts_sha256'], 'v21 reviewed retry script inventory differs')
    check_inventory(e, directory, preparation['retry_scripts_sha256'])
    check_inventory(e, o['repo'], approval['review_records'])
    validate_new_synthesis_review(e, qualification)
    for key, base in [('original_bound_files', o['repo']), ('original_attempt_artifacts', o['donor']), ('original_metadata_artifacts', meta)]:
        require(completion[key] == preparation[key], 'v21 original evidence preservation inventory differs: ' + key)
        check_inventory(e, base, completion[key])
    original_receipts = {original_join(syn, 'synthesis_exit.json'), original_join(syn, 'audit_exit.json'), original_join(meta, 'runner_exit.json')}
    declared = {evidence_key(name): digest for name, digest in completion['original_actual_exit_receipts'].items()}
    require(set(declared) == original_receipts and completion['original_actual_exit_receipts'] == manifest['original_actual_exit_receipts'],
            'v21 original actual receipt inventory differs')
    check_receipt(e, original_join(syn, 'synthesis_exit.json'), declared[original_join(syn, 'synthesis_exit.json')])
    # These are preserved failures; they must never be relabeled as successful waits.
    for name in [original_join(syn, 'audit_exit.json'), original_join(meta, 'runner_exit.json')]:
        failed = e.read(name, declared[name]);require(failed['normal_wait_return'] is True and failed['actual_p_wait'] == 1,
                                                   'v21 original audit/root failure was not preserved')
        if 'log_sha256' in failed:e.check(failed['log'], failed['log_sha256'])
        else:check_failed_receipt(e, name, declared[name])
    for key, name, runner in [('successful_audit_exit', 'successful_audit_exit.json', 'run_audit_retry02.py'),
                              ('completion_root_exit', 'completion_runner_exit.json', 'complete_audit_retry02.py')]:
        item = completion[key]
        require(item == manifest[key] and original_identity(item['path']) == original_identity(original_join(directory, name)),
                'v21 retry actual receipt path/hash differs')
        receipt = check_receipt(e, item['path'], item['sha256'])
        require(original_identity(receipt['command'][-1]) == original_identity(original_join(directory, runner))
                and receipt['preparation_sha256'] == completion['preparation_sha256'] and receipt['SYN_rerun'] is False,
                'v21 retry executed command/preparation differs')
        if key == 'successful_audit_exit':e.check(original_join(directory, 'complete_audit_retry02.py'), receipt['coordinator_sha256'])
    for key in ['successful_audit_logs', 'completion_root_logs']:
        for item in completion[key].values():e.check(item['path'], item['sha256'])
    item = completion['retry_audit_result'];native_dir = original_join(directory, 'results_01')
    require(original_identity(item['path']) == original_identity(original_join(native_dir, 'RESULT.json')), 'v21 retry native result path differs')
    native = e.read(item['path'], item['sha256'])
    require(native['passed_checks'] is True and native['source55'] == expected and native['original_VG_sha256'] == vg
            and native['original_actual_waits'] == {'vendor': 0, 'audit': 1, 'root': 1}
            and native['original_actual_exit_receipts'] == completion['original_actual_exit_receipts']
            and native['original_source_and_artifacts_unchanged'] is True and native['SYN_rerun'] is False
            and native['actual_SP_count'] == 28 and native['all_SP_CLK50'] is True and native['strict_same_net_CE_gate_retained'] is True
            and native['core_snapshot_FF_count'] == 627 and native['FF_leaf_roots'] == 39,
            'v21 successful native audit source/VG/strict SP gates differ')
    check_inventory(e, native_dir, native['artifacts'])
    sp = e.read(original_join(native_dir, 'strict_SP_clock_audit.json'))
    require(sp['passed'] is True and sp['source55'] == expected and sp['vg_sha256'] == vg and sp['actual_SP_count'] == 28
            and sp['bank_indices'] == list(range(28)) and len(sp['cells']) == 28 and sp['all_SP_CLK50'] is True
            and sp['common_CE_matches_remaining_core_snapshot'] is True and sp['READ_MODE'] == 0 and sp['WRITE_MODE'] == 1
            and sp['BIT_WIDTH'] == 32 and sp['byte_enable_address'] == '000f' and sp['reset_constant_zero'] is True
            and sp['all_declared_INIT_RAM_zero'] is True and sp['last_bank_padding_zero'] is True and sp['remaining_extension_FF'] == [],
            'v21 strict SP clock/mode/CE/address/reset/padding audit differs')
    e.check(original_join(meta, 'sp_clock_audit.py'), sp['protected_SP_auditor_sha256'])
    e.check(original_join(directory, 'escaped_port_adapter.py'), sp['adapter_sha256'])
    aliases = e.read(original_join(native_dir, 'escaped_port_aliases.json'), sp['explicit_alias_proof_sha256'])
    boolean = e.read(original_join(native_dir, 'CE_BOOLEAN_EQUIVALENCE.json'), sp['CE_boolean_proof_sha256'])
    require(aliases['passed'] is True and aliases['alias_bit_count'] == 889 and aliases['only_explicit_escaped_ports_completed'] is True
            and sorted((item['direction'], item['width']) for item in aliases['aliases']) == [('input', 1), ('output', 888)]
            and boolean['passed'] is True and boolean['strict_same_net_after_explicit_alias'] is True
            and boolean['actual_SP_count'] == 28 and boolean['remaining_core_snapshot_FF_count'] == 627
            and boolean['FF_root_count'] == 39 and boolean['symbolic_all_shared_FF_assignments'] is True,
            'v21 explicit port/CE Boolean proof differs')
    validate_native_synthesis_audits(e, qualification, native_dir)
    validate_synthesis_inputs(e, qualification, syn)
    e.check(original_join(o['donor'], 'source/impl/gwsynthesis/acg720_ano_port.vg'), vg)
    e.check(original_join(o['repo'], 'firmware/B0B4/build_candidate.py'), HELPER_SHA)


def validate_synthesis_inputs(e, qualification, syn):
    o, expected = e.origins, qualification['source_sha256']
    syn_input = e.read(original_join(syn, 'build_input.json'))
    require(syn_input['source_sha256'] == expected, 'SYN build inputs source55 differs')
    check_inventory(e, o['repo'], syn_input['bound_inputs'])
    check_inventory(e, o['repo'], syn_input['tools'])
    execution = e.read(original_join(syn, 'synthesis_input.json'))
    require(execution['source_sha256'] == expected, 'SYN execution source55 differs')
    e.check(original_join(o['donor'], 'synth_only.tcl'), execution['execution_tcl_sha256'])
    e.check(original_join(o['metadata'], 'run_synthesis.py'), execution['runner_sha256'])
    for name, digest in expected.items():e.check(original_join(o['donor'], 'source', name), digest)


def validate_new_synthesis_review(e, qualification):
    meta, family = e.origins['metadata'], qualification['variant'].split('_')[0]
    gate = e.read(original_join(meta, 'SYN_REVIEW_GATE.json' if family in {'v20', 'v22'} else 'SYNTHESIS_REVIEW_APPROVAL.json'))
    require(len(set(gate['reviewers'])) >= 2 and gate['proof_binding_sha256'] == qualification['functional_binding_sha256'],
            'Source-bound synthesis review/proof binding differs')
    freeze = e.read(original_join(meta, 'source_freeze.json'), gate['source_freeze_sha256'])
    require(freeze['source55'] == qualification['source_sha256'], 'Reviewed synthesis source freeze differs')
    check_inventory(e, e.origins['repo'], gate['review_records'])
    if family in {'v20', 'v22'}:
        require(gate['main_review_passed'] is True and gate['independent_agent_review_passed'] is True
                and set(gate['reviewed_scripts_sha256']) == {'run_synthesis.py', 'audit_synthesis_only.py', 'seal_synthesis.py',
                                                            'launch_synthesis_hidden.py', 'validation_contract.py'},
                'v20 synthesis reviewer/script inventory differs')
        check_inventory(e, meta, gate['reviewed_scripts_sha256'])
    else:
        require(gate['approved'] is True and gate['source55'] == qualification['source_sha256'], 'v21 original synthesis review approval differs')
        for name in ['run_synthesis', 'audit_synthesis_only', 'sp_clock_audit']:
            e.check(original_join(meta, name + '.py'), gate[name + '_sha256'])


def validate_native_synthesis_audits(e, qualification, syn):
    o, expected = e.origins, qualification['source_sha256']
    mapped = e.read(original_join(syn, 'mapped_audit.json'))
    gain = e.read(original_join(syn, 'gain_port_audit.json'))
    clock = e.read(original_join(syn, 'strict_ff_clock_audit.json'))
    require(mapped['passed'] is True and mapped['source_sha256'] == expected and mapped['netlist_sha256'] == qualification['netlist_sha256'], 'Mapped audit differs')
    require(gain['passed'] is True and gain['netlist_sha256'] == qualification['netlist_sha256'] and len(gain['top_ports']) == 18
            and gain['gains']['p']['init_wire'] == 1000 and gain['gains']['i']['init_wire'] == 350, 'Gain/18-port audit failed')
    require(clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad']
            and clock['vg_sha256'] == qualification['netlist_sha256'], 'Strict FF clock audit failed')
    e.check(original_join(o['donor'], 'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'), mapped['resource_xml_sha256'])
    reference = next(path for path in known_external_data(o['repo']) if path.endswith('_syn_rsc.xml'))
    e.check(reference, mapped['reference_resources_sha256'])
    comparison = e.read(original_join(syn, 'resource_comparison.json'))
    e.check(original_join(o['repo'], 'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'), comparison['parent_xml_sha256'])
    e.check(original_join(o['donor'], 'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'), comparison['native_xml_sha256'])


def validate_synthesis(e, qualification):
    if qualification.get('variant', '').split('_')[0] == 'v21':
        validate_v21_synthesis(e, qualification)
        return
    o, expected = e.origins, qualification['source_sha256']
    syn = original_join(o['donor'], 'verification')
    summary = e.read(original_join(syn, 'synthesis_summary.json'))
    require(summary['passed'] is True and summary['source_sha256'] == expected
            and summary['netlist_sha256'] == qualification['netlist_sha256']
            and summary['actual_p_wait'] == summary['audit_actual_p_wait'] == 0, 'Synthesis source/VG/exit binding differs')
    for name, key in [('synthesis_exit.json', 'synthesis_exit_sha256'), ('mapped_audit.json', 'mapped_audit_sha256'),
                      ('gain_port_audit.json', 'gain_port_audit_sha256'), ('strict_ff_clock_audit.json', 'strict_ff_clock_audit_sha256'),
                      ('resource_comparison.json', 'resource_comparison_sha256')]:
        e.check(original_join(syn, name), summary[key])
    check_receipt(e, original_join(syn, 'synthesis_exit.json'))
    check_receipt(e, original_join(syn, 'audit_exit.json'))
    check_receipt(e, original_join(o['metadata'], 'runner_exit.json'))
    syn_input = e.read(original_join(syn, 'build_input.json'))
    require(syn_input['source_sha256'] == expected, 'SYN build inputs source55 differs')
    check_inventory(e, o['repo'], syn_input['bound_inputs'])
    check_inventory(e, o['repo'], syn_input['tools'])
    execution = e.read(original_join(syn, 'synthesis_input.json'))
    require(execution['source_sha256'] == expected, 'SYN execution source55 differs')
    e.check(original_join(o['donor'], 'synth_only.tcl'), execution['execution_tcl_sha256'])
    e.check(original_join(o['metadata'], 'run_synthesis.py'), execution['runner_sha256'])
    mapped = e.read(original_join(syn, 'mapped_audit.json'))
    gain = e.read(original_join(syn, 'gain_port_audit.json'))
    clock = e.read(original_join(syn, 'strict_ff_clock_audit.json'))
    require(mapped['passed'] is True and mapped['source_sha256'] == expected and mapped['netlist_sha256'] == qualification['netlist_sha256'], 'Mapped audit differs')
    require(gain['passed'] is True and gain['netlist_sha256'] == qualification['netlist_sha256'] and len(gain['top_ports']) == 18
            and gain['gains']['p']['init_wire'] == 1000 and gain['gains']['i']['init_wire'] == 350, 'Gain/18-port audit failed')
    require(clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad']
            and clock['vg_sha256'] == qualification['netlist_sha256'], 'Strict FF clock audit failed')
    e.check(original_join(o['donor'], 'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'), mapped['resource_xml_sha256'])
    frozen = e.read(original_join(o['donor'], 'synthesis_freeze_manifest_final.json'))
    require(frozen['source_sha256'] == expected and frozen['runner_actual_wait'] == frozen['vendor_actual_wait'] == frozen['audit_actual_wait'] == 0,
            'Synthesis freeze qualification differs')
    e.check(original_join(o['metadata'], 'runner_exit.json'), frozen['root_exit_sha256'])
    check_inventory(e, o['donor'], frozen['artifacts'])
    e.check(original_join(o['repo'], 'firmware/B0B4/build_candidate.py'), HELPER_SHA)
    if qualification.get('variant', '').split('_')[0] in {'v20', 'v22'}:
        validate_new_synthesis_review(e, qualification)
        validate_synthesis_inputs(e, qualification, syn)
        validate_native_synthesis_audits(e, qualification, syn)
        result = e.read(original_join(o['metadata'], 'SYNTHESIS_RESULT.json'))
        require(result['passed_SYN_only'] is True and result['source55'] == expected and result['netlist_sha256'] == qualification['netlist_sha256']
                and result['vendor_actual_wait'] == result['runner_actual_wait'] == result['audit_actual_wait'] == 0,
                'v20 final synthesis binding differs')
        e.check(original_join(syn, 'synthesis_summary.json'), result['synthesis_summary_sha256'])
        e.check(original_join(o['donor'], 'synthesis_freeze_manifest_final.json'), result['synthesis_freeze_sha256'])
        if qualification['variant'].split('_')[0] == 'v22':
            native = e.read(original_join(syn, 'native_synthesis_audit.json'))
            require(native['passed'] is True and native['source55'] == expected and native['netlist_sha256'] == qualification['netlist_sha256']
                    and native['local_hint_effect_audit_sha256'] == result['local_hint_effect_audit_sha256'] == summary['local_hint_effect_audit_sha256'],
                    'v22 native/summary local hint measurement hash differs')
            e.check(original_join(o['metadata'], 'audit_synthesis_only.py'), native['hook_sha256'])
            hint = e.read(original_join(syn, 'local_hint_effect_audit.json'), summary['local_hint_effect_audit_sha256'])
            require(hint['passed_measurement'] is True and hint['source55'] == expected and hint['mathematics_changed'] is False
                    and hint['current_vg_sha256'] == qualification['netlist_sha256'], 'v22 local hint measurement source/VG differs')
            parent = original_join(o['repo'], 'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01/source/impl/gwsynthesis')
            current = original_join(o['donor'], 'source/impl/gwsynthesis')
            e.check(original_join(parent, 'acg720_ano_port.vg'), hint['parent_vg_sha256'])
            def resources(path, digest):
                out = {}
                def walk(node, prefix=''):
                    name = prefix + node.attrib['name']
                    out[name] = {key: int(re.match(r'\d+', value)[0]) for key, value in node.attrib.items() if key.startswith('T_')}
                    for child in node:walk(child, name + '/')
                walk(ET.fromstring(e.blob(path, digest)));return out
            before = resources(original_join(parent, 'acg720_ano_port_syn_rsc.xml'), hint['parent_xml_sha256'])
            after = resources(original_join(current, 'acg720_ano_port_syn_rsc.xml'), hint['current_xml_sha256'])
            require(set(hint['resources']) == {'acg720_ano_port', 'acg720_ano_port/native_navigation/controller_proof', 'acg720_ano_port/parameters'},
                    'v22 measured resource hierarchy differs')
            for name, item in hint['resources'].items():
                require(item['sealed_v20'] == before[name] and item['v22_local_function_result_hint'] == after[name]
                        and item['delta'] == {key: after[name].get(key, 0) - before[name].get(key, 0) for key in before[name].keys() | after[name].keys()},
                        'v22 actual XML local hint resource measurement differs')


def sha(path):
    path = Path(path)
    safe_local(path, Path(path.anchor) if path.is_absolute() else Path.cwd())
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def safe_file(root, relative):
    evidence_key(relative)
    require(not PureWindowsPath(str(relative)).is_absolute() and not PurePosixPath(str(relative)).is_absolute(),
            'Expected an archive-relative path')
    path = root / relative
    name = path.name.lower()
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            'Artifact path escapes its expected directory')
    require(not name.startswith('.env') and not name.endswith('.env')
            and '.env' not in [suffix.lower() for suffix in path.suffixes],
            'Environment files are excluded from release verification')
    return safe_local(path, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-build', action='store_true')
    args = parser.parse_args()
    manifest_path = ROOT / 'release_manifest.json'
    require(sha(manifest_path) == (ROOT / 'release_manifest.sha256').read_text().split()[0],
            'Release manifest checksum mismatch')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for item in manifest['files']:
        path = safe_file(REPO, item['path'])
        require(any(path.resolve().is_relative_to((REPO / prefix).resolve())
                    for prefix in ['firmware/B0B4', 'ground/B0B4']),
                'Manifest contains a file outside this release')
        require(path.is_file() and sha(path) == item['sha256'], f"Changed or missing: {item['path']}")
    qualification = json.loads((ROOT / 'qualification.json').read_text(encoding='utf-8'))
    require(qualification['passed'], 'Release not qualified')
    expected = qualification['source_sha256']
    names = {p.relative_to(ROOT / 'source').as_posix()
             for p in (ROOT / 'source').rglob('*') if p.is_file()}
    require(len(expected) == 55 and names == set(expected), 'Canonical source55 names differ')
    current = {name: sha(safe_file(ROOT / 'source', name)) for name in expected}
    require(current == expected, 'Canonical source55 differs')
    physical = qualification['physical']
    require(physical['passed'] and all(physical['criteria'].values()), 'Physical acceptance gate failed')
    require(physical['period_ns'] == 20 and physical['fmax_mhz'] >= 50, '50MHz acceptance failed')
    require(physical['setup_violated_endpoints'] == physical['hold_violated_endpoints'] == 0,
            'Setup or hold endpoints remain violated')
    require(set(physical['checks']) == {'setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width'},
            'Missing timing analysis type')
    require(all(item['worst_slack_ns'] >= 0 for item in physical['checks'].values()),
            'Negative timing slack')
    check_timing(physical)
    selected = ROOT / 'evidence/selected'
    terminal = json.loads((selected / 'TERMINAL_MANIFEST.json').read_text(encoding='utf8'))
    review = json.loads((selected / 'INDEPENDENT_RAW_REVIEW.json').read_text(encoding='utf8'))
    vendor = json.loads((selected / 'physical_exit.json').read_text(encoding='utf8'))
    runner = json.loads((selected / 'runner_exit.json').read_text(encoding='utf8'))
    require(terminal['passed'] and review['passed'] and all(review['checks'].values()),
            'Selected terminal or independent raw acceptance failed')
    require(terminal['source55'] == expected and terminal['vg_sha256'] == qualification['netlist_sha256'],
            'Selected evidence does not bind the released source and netlist')
    require(vendor['normal_wait_return'] and runner['normal_wait_return']
            and vendor['actual_p_wait'] == runner['actual_p_wait']
            == terminal['vendor_actual_p_wait'] == terminal['runner_actual_p_wait'] == 0,
            'Actual selected vendor/runner exit receipts are not both zero')
    require(review['period_ns'] == 20 and review['fmax_mhz'] >= 50
            and review['violated_endpoints'] == {'setup': 0, 'hold': 0}
            and set(review['slacks_ns']) == set(physical['checks'])
            and all(value >= 0 for value in review['slacks_ns'].values()),
            'Independent raw timing acceptance differs')
    fs = safe_file(ROOT / 'release', Path(qualification['release_bitstream']).relative_to('release'))
    require(sha(fs) == qualification['bitstream_sha256'], 'Bitstream mismatch')
    with fs.open('rb') as stream:
        require(re.search(rb'UserCode:\s*0x0000b0b4\b', stream.read(4096), re.I),
                'Bitstream UserCode differs')
    compressed = 0
    for item in qualification.get('compressed_artifacts', []):
        digest = hashlib.sha256()
        with gzip.open(safe_file(ROOT, item['path']), 'rb') as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        require(digest.hexdigest() == item['uncompressed_sha256'],
                f"Compressed artifact content differs: {item['path']}")
        compressed += 1
    if re.match(r'^v(?:1[5-8]|20|21|22)_', qualification.get('variant', '')):
        index_path = safe_file(ROOT, 'evidence/selected/EVIDENCE_INDEX.json')
        index_relative = index_path.relative_to(REPO).as_posix()
        require(any(item['path'] == index_relative and item['sha256'] == sha(index_path)
                    for item in manifest['files']), 'Portable evidence index is not bound by release manifest')
        require(sha(index_path) == qualification['evidence_index_sha256'], 'Evidence index qualification hash differs')
        archive = ArchivedEvidence(ROOT, json.loads(index_path.read_text(encoding='utf8')))
        for original in archive.files:
            item = archive.files[original]
            relative = (ROOT / item['archive_path']).relative_to(REPO).as_posix()
            require(any(entry['path'] == relative and entry['sha256'] == item['archive_sha256']
                        for entry in manifest['files']), 'Indexed evidence is not bound by release manifest')
            archive.blob(original)
        validate_standard_evidence(archive, qualification)
    baseline = json.loads((REPO / 'analysis/20261026_z_aw_fix/BASELINE.json').read_text())
    for relative, digest in baseline['B0B3_source55'].items():
        require(sha(REPO / 'firmware/B0B3/source' / relative) == digest, 'Frozen B3 changed')
    external = 0
    if args.external_build:
        for path, digest in qualification['external_build_inputs'].items():
            external_path = safe_file(REPO / 'out', Path(path).relative_to(REPO / 'out'))
            require(external_path.is_file() and sha(external_path) == digest, f'External build input changed: {path}')
            external += 1
    print(json.dumps({'passed': True, 'archived_files': len(manifest['files']),
                      'source_files': len(expected), 'frozen_B3_sources_unchanged': True,
                      'compressed_artifact_contents_checked': compressed,
                      'external_build_files_checked': external,
                      'programming_performed_by_verifier': False,
                      'scope': 'Saved artifact/identity acceptance only; no simulation rerun, programming or flight claim.'}))


if __name__ == '__main__':
    main()
