"""Negative parser check using untouched genuine 19.5ns vendor evidence."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
B=R.parent/'handoff_xy_pi_runtime_20261026/workspace_snapshot/timing_closure_20261025/v15_xy_p005_i0_p2r0/fixture/impl/pnr/acg720_ano_port.tr'
F=R/'verification/timing_parser_legacy19p5'
assert B.is_file() and not F.exists()
P=F/'source/impl/pnr';P.mkdir(parents=True);O=F/'verification';O.mkdir()
data=B.read_bytes();(P/B.name).write_bytes(data)
(O/'gowin.log').write_text('DIAGNOSTIC FIXTURE ONLY: no physical run. Only the genuine old19.5ns TR was copied unchanged; no PR/FS or success evidence.\n')
r=subprocess.run([sys.executable,'-B',str(R/'inspect_timing.py'),str(F)],cwd=R,capture_output=True,text=True)
(F/'parser.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
t=json.loads((O/'timing_review.json').read_text())
assert t['period_ns']==19.5 and t['timing_passed'] is False
assert set(t['checks'])=={'setup','hold','recovery','removal','minimum_pulse_width'}
assert hashlib.sha256(B.read_bytes()).digest()==hashlib.sha256(data).digest()
out=dict(passed=True,scope='negative acceptance-parser check only; no build/PNR/hardware; old report cannot qualify',
 actual_old_period_ns=t['period_ns'],observed_timing_passed=t['timing_passed'],old_fmax_mhz=t['fmax_mhz'],
 source_report=str(B),source_report_sha256=hashlib.sha256(data).hexdigest(),
 parser_sha256=hashlib.sha256((R/'inspect_timing.py').read_bytes()).hexdigest(),
 source_preserved=True,all_five_analysis_tables_parsed=True)
(R/'verification/legacy_timing_rejection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
