# Idle gain snapshot enable candidate

Status: all source/cycle/numerical/safety/contention proofs PASS; exactly one synthesis completed with actual p.wait()=0; mapped purpose realized. Driver discrepancy remains for root review: this run retained explicit Tcl exit instead of the requested strict EOF driver. Isolated and not selected. No PNR, programming, promotion, packed CLS, routing improvement or timing-closure claim.

The immutable baseline is `../response_compact/source` (map2 configuration retained). The only source edit is `position/mtf_xyz_hold_control.v`: both existing16-bit P/I snapshot assignments now execute in an independent `always @(posedge clk) if(state==0)` block. Their declaration INIT500/0, all arithmetic reads, signed casts, FSM states, reset branches and callback/publication timing are unchanged.55 tracked source files are frozen;54 are byte-identical. `candidate.diff`, `change.json` and the reversible raw-byte preparation assertion show the exact edit. Canonical was not used as a baseline or modified.

On each XY admission edge pre-state is0, so the same full16-bit pair is captured at the same edge. Every active state is nonzero and freezes the pair. The source-level induction in `SOURCE_PROOF.md` covers arbitrary16-bit gain inputs, even values above production-bank range and changes during work. Private idle/reset/Z snapshot waveforms intentionally differ: the new snapshots track inputs while idle. No declared output or current telemetry/debug output exposes these private idle values. No all-cycle private-register equivalence is claimed. The reset assignments and initialized declarations are unchanged.

## Actual RTL proof

`verify_cycle_pair.py` instantiates the actual frozen old controller (only module name changed), actual candidate and separate real multiply/divide services. It compares all450 declared output bits every cycle, including math start/cancel/operands and parameter_boundary, without forcing private state or requiring idle snapshot equality.

The final run compared956,519 clocks with79XY and79Z publications,87same-edge captures,528,118nonidle freeze checks and79joint-ready Z-priority checks. It exercised full16-bit corner/high-bit values,77distinct captured P and76I values, random gain changes each work/idle clock, XY rollback, busy multiply/divide cancellation and drain, RC/sensor/origin/stop/age revocation,2busy resets, taking-off changes and an error injected on the public divider-error input with real service done. Private idle pairs differed320,942cycles with zero public mismatches. Simulation supplements the source proof; it is not exhaustive enumeration or a formal solver proof.

The first proof attempt reached the same79XY/79Z publications without mismatch but failed a coverage threshold because only11callbacks had joint-ready stick snapshots. The legal stimulus was strengthened to wait for both stick helpers and pause sample strobes around admission. The60case threshold and active-work assertions were retained; the final run reaches79. No RTL changed after preparation. The attempt is disclosed in `verification/cycle_pair/attempt1_coverage_note.json`.

Existing suites were reused with path-only adaptations, preserving their TB, assertions and stimulus. Numerical tests passed defaultP005/I0 versus frozen reference, V15P015/I010, nondefault P, both I rails, zero-error retention, modes, cancellations, coherent pair changes and maximum legal P clipping; maximum isolated XY callback5082clocks=101.64us. All13top safety cases passed, including real bank/controller boundary and simultaneous arm/commit rejection. Four-client contention passed12XY/20Z callbacks: maximum XY request-to-publication17792clocks=355.84us, active work13737clocks=274.74us, Z12554clocks=251.08us. Existing top-level simulation forces are preserved only in that unchanged suite; the new cycle proof uses none. All three child process exits were0. Fixed test baselines and all55candidate input hashes were rechecked. Machine proof records are `verification/cycle_pair/results.json` and `verification/regressions/results.json`.

## Measured synthesis

`run_synthesis.py` requires both proof result gates, derives Tcl from the unchanged build file by replacing only `run all` with `run syn`, uses stdinDEVNULL and CREATE_NO_WINDOW, and records actual child p.wait()=0. It incorrectly retained the baseline's trailing explicit `exit` while its initial mode label called the driver EOF. This is not the requested strict EOF driver and is not relabeled as satisfying it. `verification/synthesis_driver_discrepancy.json` and the immutable executed-helper copy preserve the actual launch facts. Root was notified before completion. Exactly one synthesis invocation was made, with no intervention or automatic rerun. Configuration remains map2/place2/route0/replicate0; no PNR was started.

| XML top resource | Frozen response | Idle gain CE | Delta |
|---|---:|---:|---:|
| Registers | 27764 | 27764 | +0 |
| LUT | 35999 | 36020 | +21 |
| ALU | 9565 | 9564 | -1 |
| MULTALU27X18 | 30 | 30 | +0 |
| MULT12X12 | 7 | 7 | +0 |
| MULT27X36 | 13 | 13 | +0 |
| BSRAM | 2 | 2 | +0 |

The actual mapped controller snapshot enable changes from215CE FF pins on `n55704_3` to183on `n55194_3`. The32work coefficient FF pins use separate `n16252_13`. This idle-decode net has92total direct loads:32CE pins plus60existing LUT inputs. It is not a32total-fanout net. The full actual groups, drivers and all direct input loads (including non-CE loads) are recorded in `verification/synthesis_comparison.json`; no fanout result is inferred from RTL alone. The remaining snapshot group contains saved IX/IY54, saved AFX/AFY66, sample VY31 and world AX/AY32. Both gain pairs retain all16bits; live and saved integrals retain27bits. Controller direct mapped FF count is2314¡ú2314.

`audit_idle_decode.py` checks the actual mapped work-enable cone: LUT4 INIT0001 on state0..3, then LUT4 INIT0002 with state4..6. All128mapped state-bit combinations are evaluated; CE asserts only for state0. The cone leaves are solely the seven state FF bits; source state7 is optimized away in the unchanged0..101reachable state graph. This verifies the mapped idle qualification as well as the measured fanout split, without claiming full sequential netlist equivalence.

Mapped audit passed every27866clock pin (clk50 or ground only), unchanged physical top ports, all32bank-to-work bit connections, and the raw radio pad's sole loads at the first synchronizer D pins. Meta-Q drives only the second-stage synchronizer D pins. The unchanged sole radio_rx false path therefore ends at the first-stage D pins; downstream synchronizer and logic paths remain timed. These are synthesis structural checks, not STA closure.

Controller SHA256: `9bb8eae57f9491d8e187ac4d5e5868666714920cb91f17e6423daae95618bad9`. Netlist/resource/proof/log/script SHA256 values and both55file source manifests are frozen in `freeze_manifest.json`. Selection and any PNR require the root task's next instruction.
