"""Create one isolated source-only v6 from frozen v5; never build or route."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

O = Path(__file__).resolve().parent
R = O.parents[2]
OLD = R / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
NEW = R / 'out/z_aw_fix_20261026/compact_aw_v6/canonical/source'
REPORT = O / 'compact_aw_v6'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

assert not NEW.exists() and not REPORT.exists(), 'Never overwrite candidate or evidence'
freeze = json.loads((O / 'compact_aw_v5/source_freeze.json').read_text())
baseline = freeze['source55']
assert len(baseline) == 55
assert {p.relative_to(OLD).as_posix(): sha(p) for p in OLD.rglob('*') if p.is_file()} == baseline
assert baseline['position/mtf_xyz_hold_control.v'] == '04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
shutil.copytree(OLD, NEW)
REPORT.mkdir()
changed = ['mtf_xyz_navigation_control.v', 'position/mtf_shared_height_fusion.v']
for name in changed:
    target = NEW / name
    original = target.read_bytes()
    eol = b'\r\n' if b'\r\n' in original else b'\n'
    helper = eol.join([
        b' // Exact signed32 +/-30000 predicate for two-state inputs.',
        b' // Keep the upper-word check: truncation alone accepts invalid values.',
        b' function accel_in_range;',
        b'  input signed [31:0] x;',
        b'  begin',
        b"   accel_in_range=(x[31:16]=={16{x[15]}}) &&",
        b"    $signed(x[15:0])>=-16'sd30000 && $signed(x[15:0])<=16'sd30000;",
        b'  end',
        b' endfunction',
        b'',
    ])
    assert b'function accel_in_range' not in original
    if name.startswith('position/'):
        anchor = b' wire sources_ok='
        assert original.count(anchor) == 1
        content = original.replace(anchor, helper + anchor)
        pair = b'az_up_mmps2>=-30000 && az_up_mmps2<=30000'
        assert content.count(pair) == 2
        content = content.replace(pair, b'accel_in_range(az_up_mmps2)')
        pair = b'held_rawaz< -30000 || held_rawaz>30000'
        assert content.count(pair) == 1
        content = content.replace(pair, b'!accel_in_range(held_rawaz)')
    else:
        anchor = b' wire raw_numeric_ok='
        assert original.count(anchor) == 1
        content = original.replace(anchor, helper + anchor)
        for signal in [b'height_sample_az', b'ax_mmps2', b'ay_mmps2', b'az_up_mmps2']:
            pair = signal + b'>=-30000 && ' + signal + b'<=30000'
            assert content.count(pair) == 1
            content = content.replace(pair, b'accel_in_range(' + signal + b')')
    target.write_bytes(content)
expected = {p: sha(NEW / p) for p in baseline}
assert sorted(p for p in expected if expected[p] != baseline[p]) == changed
assert {p.relative_to(NEW).as_posix(): sha(p) for p in NEW.rglob('*') if p.is_file()} == expected
assert {p: sha(OLD / p) for p in baseline} == baseline
result = dict(scope='Only seven +/-30000 Boolean guards in two modules; explicit upper sign-extension and signed16 comparison; no state/math/interface/cycle change. Two-state equivalence only; four-state X propagation can differ.',
    source_root=str(NEW), baseline_v5_source_root=str(OLD), baseline_source55=baseline, source55=expected,
    changed_files=changed, exact_raw_replacements=7, unchanged_from_v5_count=53,
    design_sha256=sha(O / 'numeric_guard_design.md'), preparation_sha256=sha(Path(__file__)), physical_started=False)
(REPORT / 'source_freeze.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
diff = ''.join(''.join(difflib.unified_diff((OLD / p).read_text().splitlines(True), (NEW / p).read_text().splitlines(True), fromfile='v5/' + p, tofile='v6/' + p)) for p in changed)
(REPORT / 'source_changes.diff').write_text(diff, encoding='utf8')
print(json.dumps(dict(source_root=str(NEW), changed={p: expected[p] for p in changed}, unchanged_from_v5_count=53), indent=2))
