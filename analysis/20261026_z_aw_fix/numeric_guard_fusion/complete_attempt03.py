"""Reuse genuine PRE0 wait0, run PRE1 unchanged, accept standard Icarus finish trailer."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

BASE = Path(__file__).resolve().parent
R = BASE.parents[2]
OLD = R / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
NEW = R / 'out/z_aw_fix_20261026/compact_aw_v6/canonical/source'
PREVIOUS = BASE / 'attempt02'
O = BASE / 'completion03'
O.mkdir(exist_ok=False)
IV = Path(r'C:\Users\ScherrerL\Desktop\apple\.tools\iverilog\app\bin\iverilog.exe')
VVP = IV.with_name('vvp.exe')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def hashes(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def ref(p):
    return {'path': p.relative_to(BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}

def parse_log(p):
    lines = p.read_text().splitlines()
    assert len(lines) == 2, lines
    match = re.fullmatch(r'PASS ((?:\w+=\d+ ?)+)', lines[0])
    assert match, lines
    assert re.fullmatch(r'.+:\d+: \$finish called at \d+ \(1ps\)', lines[1]), lines
    counts = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', match[1])}
    assert counts['public_bits'] == 152 and counts['request_bits'] == 228 and counts['service_bits'] == 135
    return counts

original_input = json.loads((PREVIOUS / 'inputs.json').read_text())
before = {'v5': hashes(OLD), 'v6': hashes(NEW)}
assert before == original_input['source55_before']
assert len(before['v5']) == len(before['v6']) == 55
stages0 = [json.loads((PREVIOUS / ('pre0_' + s + '_exit.json')).read_text()) for s in ['compile', 'simulation']]
for s in stages0:
    assert s['actual_returncode'] == 0 and not s['timed_out']
    assert sha(PREVIOUS / s['log']) == s['log_sha256']
count0 = parse_log(PREVIOUS / 'pre0_simulation.log')
assert count0['PRE'] == 0 and count0['cycles'] == 1686784
for n in ['tb.v', 'v5_height.v', 'v6_height.v']:
    shutil.copyfile(PREVIOUS / n, O / n)
    assert sha(PREVIOUS / n) == sha(O / n)
assert not re.search(r'\bforce\s+\w', (O / 'tb.v').read_text())
inp = {
    'scope': 'Authoritative completion. PRE0 genuine compile/simulation wait0 reused unchanged; only PRE1 newly executed. No RTL source/fixture assertion change.',
    'source55_before': before, 'entry_sha256': sha(Path(__file__)),
    'first_environment_failure': ref(BASE / 'pre0_compile_exit.json'),
    'previous_inputs': ref(PREVIOUS / 'inputs.json'),
    'previous_entry': ref(BASE / 'verify_fusion_attempt02.py'),
    'previous_postprocessing_error': ref(BASE / 'attempt02.stderr.log'),
    'previous_rtl_stages': [ref(PREVIOUS / ('pre0_' + s + '_exit.json')) for s in ['compile', 'simulation']],
    'previous_compile_and_simulation_logs': [ref(PREVIOUS / ('pre0_' + s + '.log')) for s in ['compile', 'simulation']],
    'tb_sha256': sha(O / 'tb.v'),
    'renamed_real_sources': {n: sha(O / n) for n in ['v5_height.v', 'v6_height.v']},
    'real_math_sources': {n: sha(OLD / n) for n in ['nav_math_service.v', 'position/position_math.v']},
    'CLOCK': '20ns sim clock; CLK_HZ=5,000,000 accelerates 11ms timer10x to55,000 clocks. acc_dt_us11000 and AGE_LIMIT5,000,000 retain original arithmetic/age thresholds.',
    'iverilog_sha256': sha(IV), 'vvp_sha256': sha(VVP),
}
(O / 'inputs.json').write_text(json.dumps(inp, indent=2) + '\n')
temp = O / 'tmp'
temp.mkdir()
env = dict(os.environ, TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
exe = O / 'pre1.vvp'
commands = [
    [str(IV), '-g2012', '-s', 'tb', '-Ptb.PRE=1', '-o', str(exe),
     str(O / 'tb.v'), str(O / 'v5_height.v'), str(O / 'v6_height.v'),
     str(OLD / 'nav_math_service.v'), str(OLD / 'position/position_math.v')],
    [str(VVP), str(exe)],
]
stages1 = []
for stage, command in zip(['compile', 'simulation'], commands):
    start = time.time()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = O / ('pre1_' + stage + '.log')
    with log.open('wb') as f:
        try:
            proc = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
                env=env, timeout=240)
            code, timed_out = proc.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    rec = {'stage': stage, 'command': command, 'actual_returncode': code,
           'normal_wait_return': not timed_out, 'timed_out': timed_out,
           'started_utc': utc, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'elapsed_seconds': round(time.time()-start, 3), 'log': log.name,
           'log_sha256': sha(log)}
    (O / ('pre1_' + stage + '_exit.json')).write_text(json.dumps(rec, indent=2) + '\n')
    stages1.append(rec)
    assert code == 0 and not timed_out, rec
count1 = parse_log(O / 'pre1_simulation.log')
assert count1['PRE'] == 1
assert count0['age_rejects'] == 3 and count0['age_bypasses'] == 0
assert count1['age_rejects'] == 0 and count1['age_bypasses'] == 4
for x in [count0, count1]:
    assert x['numeric_pulses'] == x['commit_vetoes'] == 4
    assert x['epoch_pulses'] == 5 and x['publications'] >= 20
    assert x['mul_consumed'] >= 200 and x['div_consumed'] >= 200 and x['acc_div_consumed'] >= 100
after = {'v5': hashes(OLD), 'v6': hashes(NEW)}
assert before == after
result = {
    'passed': True, 'source55_before_after_identical': True,
    'source55_after': after, 'inputs_sha256': sha(O / 'inputs.json'),
    'runs': [{'PRE': 0, 'reused_actual_run': True, 'coverage': count0,
              'stages': stages0, 'local_vvp_omitted': ref(PREVIOUS / 'pre0.vvp')},
             {'PRE': 1, 'reused_actual_run': False, 'coverage': count1,
              'stages': stages1, 'local_vvp_omitted': ref(exe)}],
    'comparison': 'Every rising edge after NBA:152 public bits+228 request/cancel/operand bits+135 real service bits, including multiply/divide accepted results. Same-cycle invalid numeric sources_ok/tail and state84 veto also asserted.',
    'scope_limit': 'Finite two-state traces, not exhaustive/formal. No wrapper simulation, flight/plant, hardware, contention, or natural5,000,000-clock publication-age expiry claim. Age tests change external range_age_ticks around its exact threshold. PRE1 bypass intentional at AGE_LIMIT5,000,000.',
    'history': 'First compiler failed before RTL due TMP environment. Second attempt PRE0 realwait0 passed all RTL assertions; Python fullmatch then rejected standard Icarus finish trailer. Historical files unchanged; completion parser accepts exactly PASS plus standard finish trailer. No passed trace was rerun.',
}
(O / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'passed': True, 'results_sha256': sha(O / 'results.json'), 'coverage': [count0, count1]}, indent=2))
