"""Freeze the measured isolated candidate after all proof and synthesis gates."""
from pathlib import Path
import datetime,hashlib,json
C=Path(__file__).resolve().parent;O=C/'verification';S=C/'source';record=json.loads((C/'change.json').read_text());B=Path(record['baseline'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pair=json.loads((O/'cycle_pair/results.json').read_text());reg=json.loads((O/'regressions/results.json').read_text());syn=json.loads((O/'synthesis_comparison.json').read_text());ex=json.loads((O/'synthesis_exit.json').read_text())
assert pair['passed'] and reg['passed'] and syn['passed'] and syn['purpose_realized'] and ex['actual_p_wait']==0
decode=json.loads((O/'idle_decode_audit.json').read_text());assert decode['passed'] and decode['netlist_sha256']==sha(S/'impl/gwsynthesis/acg720_ano_port.vg')
assert all(sha(B/p)==v for p,v in record['baseline_source_sha256'].items())
assert all(sha(S/p)==v for p,v in record['candidate_source_sha256'].items())
assert [p for p in record['candidate_source_sha256']if record['candidate_source_sha256'][p]!=record['baseline_source_sha256'][p]]==['position/mtf_xyz_hold_control.v']
before,after=syn['reference_resources']['top'],syn['candidate_resources']['top']
ce=syn['mapped_CE'];rows=[]
for key,label in [('T_Register','Registers'),('T_Lut','LUT'),('T_Alu','ALU'),('T_MULTALU27X18','MULTALU27X18'),('T_MULT12X12','MULT12X12'),('T_MULT27X36','MULT27X36'),('T_Bsram','BSRAM')]:rows.append(f'| {label} | {before.get(key,0)} | {after.get(key,0)} | {after.get(key,0)-before.get(key,0):+d} |')
report=f'''# Idle gain snapshot enable candidate

Status: all source/cycle/numerical/safety/contention proofs PASS; exactly one synthesis completed with actual p.wait()=0; mapped purpose realized. Driver discrepancy remains for root review: this run retained explicit Tcl exit instead of the requested strict EOF driver. Isolated and not selected. No PNR, programming, promotion, packed CLS, routing improvement or timing-closure claim.

The immutable baseline is `../response_compact/source` (map2 configuration retained). The only source edit is `position/mtf_xyz_hold_control.v`: both existing16-bit P/I snapshot assignments now execute in an independent `always @(posedge clk) if(state==0)` block. Their declaration INIT500/0, all arithmetic reads, signed casts, FSM states, reset branches and callback/publication timing are unchanged.55 tracked source files are frozen;54 are byte-identical. `candidate.diff`, `change.json` and the reversible raw-byte preparation assertion show the exact edit. Canonical was not used as a baseline or modified.

On each XY admission edge pre-state is0, so the same full16-bit pair is captured at the same edge. Every active state is nonzero and freezes the pair. The source-level induction in `SOURCE_PROOF.md` covers arbitrary16-bit gain inputs, even values above production-bank range and changes during work. Private idle/reset/Z snapshot waveforms intentionally differ: the new snapshots track inputs while idle. No declared output or current telemetry/debug output exposes these private idle values. No all-cycle private-register equivalence is claimed. The reset assignments and initialized declarations are unchanged.

## Actual RTL proof

`verify_cycle_pair.py` instantiates the actual frozen old controller (only module name changed), actual candidate and separate real multiply/divide services. It compares all{pair['public_output_bits']} declared output bits every cycle, including math start/cancel/operands and parameter_boundary, without forcing private state or requiring idle snapshot equality.

The final run compared956,519 clocks with79XY and79Z publications,87same-edge captures,528,118nonidle freeze checks and79joint-ready Z-priority checks. It exercised full16-bit corner/high-bit values,77distinct captured P and76I values, random gain changes each work/idle clock, XY rollback, busy multiply/divide cancellation and drain, RC/sensor/origin/stop/age revocation,2busy resets, taking-off changes and an error injected on the public divider-error input with real service done. Private idle pairs differed320,942cycles with zero public mismatches. Simulation supplements the source proof; it is not exhaustive enumeration or a formal solver proof.

The first proof attempt reached the same79XY/79Z publications without mismatch but failed a coverage threshold because only11callbacks had joint-ready stick snapshots. The legal stimulus was strengthened to wait for both stick helpers and pause sample strobes around admission. The60case threshold and active-work assertions were retained; the final run reaches79. No RTL changed after preparation. The attempt is disclosed in `verification/cycle_pair/attempt1_coverage_note.json`.

Existing suites were reused with path-only adaptations, preserving their TB, assertions and stimulus. Numerical tests passed defaultP005/I0 versus frozen reference, V15P015/I010, nondefault P, both I rails, zero-error retention, modes, cancellations, coherent pair changes and maximum legal P clipping; maximum isolated XY callback5082clocks=101.64us. All13top safety cases passed, including real bank/controller boundary and simultaneous arm/commit rejection. Four-client contention passed12XY/20Z callbacks: maximum XY request-to-publication17792clocks=355.84us, active work13737clocks=274.74us, Z12554clocks=251.08us. Existing top-level simulation forces are preserved only in that unchanged suite; the new cycle proof uses none. All three child process exits were0. Fixed test baselines and all55candidate input hashes were rechecked. Machine proof records are `verification/cycle_pair/results.json` and `verification/regressions/results.json`.

## Measured synthesis

`run_synthesis.py` requires both proof result gates, derives Tcl from the unchanged build file by replacing only `run all` with `run syn`, uses stdinDEVNULL and CREATE_NO_WINDOW, and records actual child p.wait()=0. It incorrectly retained the baseline's trailing explicit `exit` while its initial mode label called the driver EOF. This is not the requested strict EOF driver and is not relabeled as satisfying it. `verification/synthesis_driver_discrepancy.json` and the immutable executed-helper copy preserve the actual launch facts. Root was notified before completion. Exactly one synthesis invocation was made, with no intervention or automatic rerun. Configuration remains map2/place2/route0/replicate0; no PNR was started.

| XML top resource | Frozen response | Idle gain CE | Delta |
|---|---:|---:|---:|
{chr(10).join(rows)}

The actual mapped controller snapshot enable changes from215CE FF pins on `{ce['reference_snapshot']['net']}` to183on `{ce['candidate_snapshot']['net']}`. The32work coefficient FF pins use separate `{ce['candidate_work']['net']}`. This idle-decode net has92total direct loads:32CE pins plus60existing LUT inputs. It is not a32total-fanout net. The full actual groups, drivers and all direct input loads (including non-CE loads) are recorded in `verification/synthesis_comparison.json`; no fanout result is inferred from RTL alone. The remaining snapshot group contains saved IX/IY54, saved AFX/AFY66, sample VY31 and world AX/AY32. Both gain pairs retain all16bits; live and saved integrals retain27bits. Controller direct mapped FF count is{syn['controller_FF']['reference']}→{syn['controller_FF']['candidate']}.

`audit_idle_decode.py` checks the actual mapped work-enable cone: LUT4 INIT0001 on state0..3, then LUT4 INIT0002 with state4..6. All128mapped state-bit combinations are evaluated; CE asserts only for state0. The cone leaves are solely the seven state FF bits; source state7 is optimized away in the unchanged0..101reachable state graph. This verifies the mapped idle qualification as well as the measured fanout split, without claiming full sequential netlist equivalence.

Mapped audit passed every{syn['clock_audit']['all_clock_pin_count']}clock pin (clk50 or ground only), unchanged physical top ports, all32bank-to-work bit connections, and the raw radio pad's sole loads at the first synchronizer D pins. Meta-Q drives only the second-stage synchronizer D pins. The unchanged sole radio_rx false path therefore ends at the first-stage D pins; downstream synchronizer and logic paths remain timed. These are synthesis structural checks, not STA closure.

Controller SHA256: `{record['candidate_controller_sha256']}`. Netlist/resource/proof/log/script SHA256 values and both55file source manifests are frozen in `freeze_manifest.json`. Selection and any PNR require the root task's next instruction.
'''
(C/'CANDIDATE_REPORT.md').write_text(report)
files={}
for p in C.rglob('*'):
 if not p.is_file() or p.name=='freeze_manifest.json' or '__pycache__'in p.parts or p.suffix in ('.bak','.user'):continue
 if p.suffix=='.log' and p.name.startswith('orchestrator.'):continue
 files[p.relative_to(C).as_posix()]=sha(p)
manifest=dict(status='frozen_isolated_not_selected_driver_discrepancy',frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_source_sha256=record['baseline_source_sha256'],candidate_source_sha256=record['candidate_source_sha256'],byte_identical_source_files=54,changed_files=record['changed_files'],proofs_passed=True,purpose_realized=True,actual_synthesis_p_wait=0,synthesis_invocations=1,strict_EOF_driver=False,driver_discrepancy='retained explicit Tcl exit; root review required; actual launch and executed-helper hash preserved',PNR_started=False,promoted=False,canonical_used_as_baseline=False,private_idle_waveform_equivalence=False,artifacts_sha256=files)
(C/'freeze_manifest.json').write_text(json.dumps(manifest,indent=2))
assert all(sha(C/p)==digest for p,digest in files.items())
print(json.dumps(dict(status=manifest['status'],artifact_count=len(files),manifest_sha256=sha(C/'freeze_manifest.json'),controller_sha256=record['candidate_controller_sha256'],resources_delta=syn['delta']['top'],snapshot_CE=ce['candidate_snapshot']['CE_FF_pins'],work_CE=ce['candidate_work']['CE_FF_pins']),indent=2))
