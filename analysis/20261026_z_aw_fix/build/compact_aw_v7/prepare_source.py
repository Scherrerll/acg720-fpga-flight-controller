"""Create one isolated v7 from frozen v5; never alter prior candidates."""
from pathlib import Path
import difflib, hashlib, json, shutil

O = Path(__file__).resolve().parent
R = O.parents[3]
PRIOR = R / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
CANON = R / 'out/z_aw_fix_20261026/compact_aw_v7/canonical/source'
HOLD = 'position/mtf_xyz_hold_control.v'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = json.loads((O.parent / 'compact_aw_v5/source_freeze.json').read_text())['source55']
assert len(expected) == 55
assert expected[HOLD] == '04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
assert {p: sha(PRIOR/p) for p in expected} == expected
assert not CANON.exists() and not (O/'source_freeze.json').exists()
shutil.copytree(PRIOR, CANON)
assert len([p for p in CANON.rglob('*') if p.is_file()]) == 55
raw = (CANON/HOLD).read_bytes()
replacements = [
 ('reg signed [33-1:0] iz_store=0;', 'reg signed [27-1:0] iz_store=0;'),
 ('wire signed [32:0] candidate_iz_store=iz_lower_q[32:0];', 'wire signed [26:0] candidate_iz_store=iz_lower_q[26:0];'),
 ('wire signed [32:0] p_bias_store={{2{exz_store[30]}},exz_store};', 'wire signed [28:0] p_bias_store=exz_store[28:0];'),
 ('wire signed [32:0] candidate_collective_store=inner_alt_speed[32:0];', 'wire signed [29:0] candidate_collective_store=inner_alt_speed[29:0];'),
 ('wire signed [32:0] current_collective_store={{2{sample_vx_store[30]}},sample_vx_store};', 'wire signed [29:0] current_collective_store=sample_vx_store[29:0];'),
 ('wire signed [63:0] candidate_iz={{31{candidate_iz_store[32]}},candidate_iz_store};', 'wire signed [63:0] candidate_iz={{37{candidate_iz_store[26]}},candidate_iz_store};'),
 ('wire signed [63:0] p_bias={{31{p_bias_store[32]}},p_bias_store};', 'wire signed [63:0] p_bias={{35{p_bias_store[28]}},p_bias_store};'),
 ('wire signed [63:0] candidate_collective={{31{candidate_collective_store[32]}},candidate_collective_store};', 'wire signed [63:0] candidate_collective={{34{candidate_collective_store[29]}},candidate_collective_store};'),
 ('wire signed [63:0] current_collective={{31{current_collective_store[32]}},current_collective_store};', 'wire signed [63:0] current_collective={{34{current_collective_store[29]}},current_collective_store};'),
 ('// Both sums fit signed31 Q16 by the source-level bound; keep the 64-bit', '// Both sums fit signed30 Q16 by the source-level bound; keep the 64-bit'),
 ('wire signed [30:0] compact_candidate_sum31=compact_candidate_sum[30:0];', 'wire signed [29:0] compact_candidate_sum30=compact_candidate_sum[29:0];'),
 ('reg signed [33-1:0] bias_store=0;', 'reg signed [26-1:0] bias_store=0;'),
 ('wire signed [63:0] iz={{31{iz_store[32]}},iz_store};', 'wire signed [63:0] iz={{37{iz_store[26]}},iz_store};'),
 ('wire signed [63:0] bias={{31{bias_store[32]}},bias_store};', 'wire signed [63:0] bias={{38{bias_store[25]}},bias_store};'),
 ('inner_alt_speed<={{33{compact_candidate_sum31[30]}},compact_candidate_sum31};', 'inner_alt_speed<={{34{compact_candidate_sum30[29]}},compact_candidate_sum30};'),
]
new = raw
for old, replacement in replacements:
    assert new.count(old.encode()) == 1, old
    new = new.replace(old.encode(), replacement.encode())
(CANON/HOLD).write_bytes(new)
actual = {p: sha(CANON/p) for p in expected}
assert [p for p in expected if actual[p] != expected[p]] == [HOLD]
assert {p: sha(PRIOR/p) for p in expected} == expected
(O/'source_changes.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True), new.decode().splitlines(True), fromfile='v5/'+HOLD, tofile='v7/'+HOLD)), encoding='utf8', newline='')
freeze = dict(scope='v5 fork: bounded Z I/bias storage and qualified lifetime aliases only; signed64 arithmetic/interfaces/state schedule unchanged', source_root=str(CANON), baseline_source55=expected, source55=actual, changed_files=[HOLD], exact_raw_replacements=len(replacements), source_review_sha256=sha(O/'source_review.md'), proof_sha256=sha(O.parent/'sign_step_bound.md'), physical_started=False)
(O/'source_freeze.json').write_text(json.dumps(freeze, indent=2)+'\n', encoding='utf8')
print(json.dumps({'source_root':str(CANON), 'hold_sha256':actual[HOLD], 'changed_files':[HOLD], 'unchanged_files':54, 'source_freeze_sha256':sha(O/'source_freeze.json')}, indent=2))
