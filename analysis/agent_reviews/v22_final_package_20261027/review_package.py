"""Read-only final package review; writes this review directory only."""
from pathlib import Path
import collections
import datetime
import hashlib
import importlib.util
import json
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
B4 = REPO / 'firmware/B0B4'
MANIFEST_SHA = 'c8e03412ff44cbe929f5d8ce6fed6eb3c61078a2028df466a340a61894893a2d'
FS_SHA = '199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610'
VERIFY_SHA = '0ba2c0cdca20b7bcf60b34c4d7f2c059762e7f1723f78fa977b0ad4884353cbf'
EXPORT_SHA = 'cab893924c892327dc4168254064dfade00c2a4db3c19908dd34c5f58f6552f1'


def safe_name(value):
    text = str(value).replace('\\', '/')
    assert '..' not in text.split('/'), ('unsafe path', text)
    for part in text.split('/'):
        name = part.lower().rstrip(' .')
        assert not (name.startswith('.env') or name.endswith('.env') or '.env' in Path(name).suffixes), ('environment excluded', text)
        assert name not in {'credentials', 'credentials.json', 'credentials.toml', '.npmrc', '.pypirc', 'id_rsa', 'id_ed25519'}, ('credential excluded', text)
        assert not name.endswith(('.pem', '.p12', '.pfx')), ('private key excluded', text)


def safe_path(path):
    path = Path(path)
    safe_name(path)
    assert path.resolve().is_relative_to(REPO)
    for part in [path, *path.parents]:
        assert not part.is_symlink() and not part.is_junction(), ('link excluded', str(part))
        if part == REPO:
            break
    return path


def sha(path):
    digest = hashlib.sha256()
    with safe_path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(safe_path(path).read_text(encoding='utf8'))


def file_map(root):
    result = {}
    for p in root.rglob('*'):
        safe_name(p)
        assert not p.is_symlink() and not p.is_junction()
        if p.is_file():
            result[p.relative_to(root).as_posix()] = sha(p)
    return result


assert sha(B4 / 'release_manifest.json') == MANIFEST_SHA
assert (B4 / 'release_manifest.sha256').read_text().split()[0] == MANIFEST_SHA
manifest = read(B4 / 'release_manifest.json')
assert len(manifest['files']) == 652
indexed = {}
for item in manifest['files']:
    path = safe_path(REPO / item['path'])
    assert any(path.is_relative_to(REPO / root) for root in ['firmware/B0B4', 'ground/B0B4'])
    assert item['path'] not in indexed
    assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes']
    indexed[item['path']] = item

# Independent coverage inventory, excluding only explicit non-package cache/runtime names and the manifest pair itself.
coverage = set()
excluded = []
for root in [B4, REPO / 'ground/B0B4']:
    for path in root.rglob('*'):
        safe_name(path)
        assert not path.is_symlink() and not path.is_junction()
        if not path.is_file():
            continue
        rel = path.relative_to(REPO).as_posix()
        parts = path.relative_to(root).parts
        if any(part in {'__pycache__', 'node_modules', 'runtime'} for part in parts) or path.suffix.lower() in {'.pyc', '.pyo'} or path in {B4 / 'release_manifest.json', B4 / 'release_manifest.sha256'}:
            excluded.append(rel)
            continue
        coverage.add(rel)
assert coverage == set(indexed), ('coverage difference', sorted(coverage - set(indexed)), sorted(set(indexed) - coverage))

q = read(B4 / 'qualification.json')
assert manifest['qualification_sha256'] == sha(B4 / 'qualification.json')
assert q['passed'] is True and q['installed_B0B4'] is False and q['true_cold_boot_verified'] is False
assert q['variant'] == 'v22_p3' and q['profile'] == 'physical_p3r0_01'
physical = q['physical']
assert physical['passed'] is True and all(value is True for value in physical['criteria'].values())
assert physical['period_ns'] == 20 and physical['fmax_mhz'] >= 50
assert physical['setup_violated_endpoints'] == physical['hold_violated_endpoints'] == 0
assert set(physical['checks']) == {'setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width'}
assert all(v['worst_slack_ns'] >= 0 for v in physical['checks'].values())
assert sha(B4 / q['release_bitstream']) == q['bitstream_sha256'] == FS_SHA
with safe_path(B4 / q['release_bitstream']).open('rb') as stream:
    assert re.search(rb'UserCode:\s*0x0000b0b4\b', stream.read(4096), re.I)

freeze_path = REPO / 'analysis/20261026_z_aw_fix/build/compact_aw_v22/source_freeze.json'
expected = read(freeze_path)['source55']
assert len(expected) == 55 and q['source_sha256'] == expected
assert file_map(B4 / 'source') == expected
assert file_map(REPO / 'out/z_aw_fix_20261026/compact_aw_v22/canonical/source') == expected
bindings_path = REPO / 'analysis/20261026_z_aw_fix/handoff_20261026/SOURCE_BINDINGS.json'
before = read(bindings_path)['source_sha256']['B0B4_unpromoted_prototype']
backup = REPO / 'analysis/20261026_z_aw_fix/implementation_history/B4_initial_prototype_full55'
assert len(before) == 55 and set(before) == set(expected) and file_map(backup) == before
baseline_path = REPO / 'analysis/20261026_z_aw_fix/BASELINE.json'
baseline = read(baseline_path)['B0B3_source55']
assert len(baseline) == 55 and file_map(REPO / 'firmware/B0B3/source') == baseline

assert sha(B4 / 'verify_release.py') == VERIFY_SHA
assert sha(REPO / 'analysis/20261026_z_aw_fix/build/export_qualified_v4.py') == EXPORT_SHA
spec = importlib.util.spec_from_file_location('readonly_final_v22_verifier', B4 / 'verify_release.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
index_path = B4 / 'evidence/selected/EVIDENCE_INDEX.json'
assert sha(index_path) == q['evidence_index_sha256']
index = read(index_path)
archive = verifier.ArchivedEvidence(B4, index)
assert Path(index['origins']['metadata']).name == 'compact_aw_v22'
assert index['origins']['physical_metadata'] == index['origins']['metadata']
assert Path(index['origins']['attempt']).name == 'physical_p3r0_01'
for original, item in archive.files.items():
    safe_name(original)
    safe_name(item['archive_path'])
    relative = (B4 / item['archive_path']).relative_to(REPO).as_posix()
    assert relative in indexed and indexed[relative]['sha256'] == item['archive_sha256']
    assert Path(original).suffix.lower() not in {'.exe', '.dll'}
for tool in archive.tools:
    safe_name(tool)

conflicts = {}
for name in expected:
    old_key = verifier.original_join(index['origins']['repo'], 'firmware/B0B4/source', name)
    new_key = verifier.original_join(index['origins']['source'], name)
    assert old_key != new_key and old_key in archive.files and new_key in archive.files
    old_bytes = archive.blob(old_key, before[name])
    new_bytes = archive.blob(new_key, expected[name])
    assert old_bytes == safe_path(backup / name).read_bytes()
    assert new_bytes == safe_path(B4 / 'source' / name).read_bytes()
    if before[name] != expected[name]:
        assert old_bytes != new_bytes
        assert archive.files[old_key]['archive_path'] != archive.files[new_key]['archive_path']
        assert not archive.files[old_key]['archive_path'].startswith('source/')
        conflicts[name] = {'prototype_sha256': before[name], 'selected_sha256': expected[name],
                           'old_archive_path': archive.files[old_key]['archive_path'],
                           'new_archive_path': archive.files[new_key]['archive_path']}
assert len(conflicts) == 10

receipts = {}
def receipt(folder, script, argument=None, exporter=False):
    process, result = read(folder / 'process.json'), read(folder / 'exit.json')
    assert result['normal_wait_return'] is True and type(result['actual_p_wait']) is int and result['actual_p_wait'] == 0
    for field in ['command', 'cwd', 'pid', 'started_utc']:
        assert result[field] == process[field]
    assert type(result['pid']) is int and result['pid'] > 0
    assert str(script) in result['command']
    if argument:
        assert argument in result['command']
    for channel in ['stdout', 'stderr']:
        assert sha(folder / (channel + '.log')) == result[channel + '_sha256']
    if exporter:
        assert result['exporter_sha256'] == sha(script) == EXPORT_SHA
        assert result['verifier_sha256'] == VERIFY_SHA
    else:
        assert result['executed_script_sha256'] == sha(script)
    rel = folder.relative_to(REPO).as_posix()
    receipts[rel] = {'actual_p_wait': result['actual_p_wait'], 'normal_wait_return': True,
                     'exit_sha256': sha(folder / 'exit.json'), 'process_sha256': sha(folder / 'process.json'),
                     'stdout_sha256': result['stdout_sha256'], 'stderr_sha256': result['stderr_sha256']}

receipt(B4 / 'evidence/export', REPO / 'analysis/20261026_z_aw_fix/build/export_qualified_v4.py', 'v22_p3', exporter=True)
verification = REPO / 'analysis/20261026_z_aw_fix/build/release_verify_v22_20261027_01'
receipt(verification / 'seal', REPO / 'analysis/20261026_z_aw_fix/build/seal_release_manifest.py', 'offline_v22_20261027')
receipt(verification / 'verify', B4 / 'verify_release.py', '--external-build')
receipt(verification / 'replay_verify_only', B4 / 'rebuild_selected.py', '--verify-only')
for name in ['physical_exit.json', 'runner_exit.json']:
    result = read(B4 / 'evidence/selected' / name)
    assert result['normal_wait_return'] is True and type(result['actual_p_wait']) is int and result['actual_p_wait'] == 0
seal_output = json.loads((verification / 'seal/stdout.log').read_text())
assert seal_output['manifest_sha256'] == MANIFEST_SHA and seal_output['files'] == 652
verify_output = json.loads((verification / 'verify/stdout.log').read_text())
assert verify_output['passed'] is True and verify_output['archived_files'] == 652 and verify_output['external_build_files_checked'] == 2
replay_lines = (verification / 'replay_verify_only/stdout.log').read_text().splitlines()
replay_output = json.loads(replay_lines[-1])
assert replay_output['verified'] is True and replay_output['output_created'] is False and replay_output['vendor_started'] is False and replay_output['hardware_operation'] is False

# Check the sealed package remained stable throughout this review.
assert sha(B4 / 'release_manifest.json') == MANIFEST_SHA
assert file_map(B4 / 'source') == expected and file_map(backup) == before
result = {
    'passed': True, 'approved_final_package': True,
    'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'manifest_sha256': MANIFEST_SHA, 'manifest_files': len(indexed),
    'manifest_complete_regular_package_coverage': True,
    'manifest_files_by_root': dict(collections.Counter('/'.join(p.split('/')[:2]) for p in indexed)),
    'excluded_only_manifest_pair_and_cache_runtime_paths': excluded,
    'qualification_sha256': sha(B4 / 'qualification.json'),
    'offline_passed': q['passed'], 'installed_B0B4': q['installed_B0B4'], 'true_cold_boot_verified': q['true_cold_boot_verified'],
    'bitstream_sha256': FS_SHA, 'bitstream_usercode': '0000B0B4',
    'source55_matches_STD22': True, 'source_freeze_sha256': sha(freeze_path),
    'prototype_backup55_matches_before': True, 'before_source_bindings_sha256': sha(bindings_path),
    'B3_source55_unchanged': True, 'B3_baseline_sha256': sha(baseline_path),
    'physical_criteria_all_true': True, 'period_ns': physical['period_ns'], 'fmax_mhz': physical['fmax_mhz'],
    'all_five_nonnegative': True, 'setup_hold_endpoints_zero': True,
    'archive_index_sha256': sha(index_path), 'archived_original_keys': len(archive.files),
    'all_indexed_objects_manifest_bound': True,
    'archived_old_source55_and_selected_source55_independently_retrieved': True,
    'actual_conflicting_files': conflicts,
    'environment_credential_paths_absent_from_manifest_index_and_tools': True,
    'no_link_paths': True, 'actual_child_receipts': receipts,
    'actual_physical_vendor_root_normal_exact_int0': True,
    'production_exporter_sha256': EXPORT_SHA, 'production_verifier_sha256': VERIFY_SHA,
    'review_script_sha256': sha(Path(__file__)),
    'findings': [],
    'scope': 'Independent read-only final package inventory, identities, old/new source archive separation and existing actual receipt review. No full48/RTL/vendor rerun, no package edits, programming or hardware operation.'
}
(HERE / 'REVIEW.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'passed': True, 'manifest_files': len(indexed), 'archived_keys': len(archive.files), 'conflicts': len(conflicts)}))
