"""Seal finite fusion regression evidence, retaining failures and excluding compiled/cache files."""
from pathlib import Path
import hashlib
import json
import shutil

O = Path(__file__).resolve().parent
R = O.parents[2]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):
    return {'bytes': p.stat().st_size, 'sha256': sha(p)}

result = json.loads((O / 'completion03/results.json').read_text())
assert result['passed'] and result['source55_before_after_identical']
assert sha(O / 'completion03/results.json') == 'eb0295ca89af3ac66db0a65d923d30097c1c9bdd6c8fd99a1b9954f48b825e39'
inp = json.loads((O / 'completion03/inputs.json').read_text())
assert sha(O / 'completion03/inputs.json') == result['inputs_sha256']
for tag in ['v5', 'v6']:
    root = R / ('out/z_aw_fix_20261026/compact_aw_' + tag + '/canonical/source')
    expect = result['source55_after'][tag]
    assert len(expect) == 55
    assert all(sha(root / p) == h for p, h in expect.items())
refs = O / 'references'
refs.mkdir(exist_ok=False)
for p in ['nav_math_service.v', 'position/position_math.v']:
    src = R / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source' / p
    dst = refs / Path(p).name
    shutil.copyfile(src, dst)
    assert sha(dst) == inp['real_math_sources'][p] == sha(src)
for run in result['runs']:
    for s in run['stages']:
        assert s['actual_returncode'] == 0 and not s['timed_out']
    for key in ['numeric_pulses', 'commit_vetoes']:
        assert run['coverage'][key] == 4
    assert run['coverage']['epoch_pulses'] == 5
for n in ['tb.v', 'v5_height.v', 'v6_height.v']:
    assert sha(O / 'attempt02' / n) == sha(O / 'completion03' / n)
files = {}
omitted = {}
for p in sorted(O.rglob('*')):
    if not p.is_file() or p == O / 'MANIFEST.json':
        continue
    rel = p.relative_to(O).as_posix()
    if p.suffix in ['.vvp', '.pyc'] or 'tmp' in p.relative_to(O).parts or '__pycache__' in p.relative_to(O).parts:
        omitted[rel] = rec(p)
    else:
        files[rel] = rec(p)
manifest = {'scope': 'Retained finite actual-RTL fusion differential evidence only; no delivery/physical/hardware qualification.',
            'authoritative_result': 'completion03/results.json',
            'retained_file_count': len(files), 'retained_bytes': sum(x['bytes'] for x in files.values()),
            'files': files,
            'explicit_exclusions': ['*.vvp', '*.pyc', '**/tmp/**', '**/__pycache__/**', 'MANIFEST.json itself'],
            'omitted_local_compiled_or_temp_hashes_not_required_for_retained_verification': omitted}
(O / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
assert all(sha(O / p) == m['sha256'] and (O / p).stat().st_size == m['bytes'] for p, m in files.items())
print(json.dumps({'passed': True, 'retained_file_count': len(files),
                  'retained_bytes': manifest['retained_bytes'],
                  'manifest_sha256': sha(O / 'MANIFEST.json'),
                  'readme_sha256': sha(O / 'README.md')}, indent=2))
