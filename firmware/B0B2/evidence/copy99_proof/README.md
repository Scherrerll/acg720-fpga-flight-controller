# SiK A585 five-field copy removal: frozen out-only prototype

This is an isolated review artifact. The frozen B0B2 `source/`, `tools/` and `tests/` were not changed. No programmer, serial port or hardware API was used. The only Gowin commands for this prototype were two **single-module `run syn`** runs. No PNR was started for this prototype, and this directory is not a programmable acceptance/release.

## Exact candidate and scope

Candidate: `sik_copy99.v`, SHA256 `6ae4b1dfd0aaf2e918b3524b5c953e68de607746c62edd705ecbd5c6d870002b`.
Frozen source `firmware/B0B2/source/sik_imu_diagnostic.v`: SHA256 `8bff3d129b80875c4bced236238952ccdee43f8107947ff13489d2c52945dfcc`.
`copy99.diff` is the complete minimal diff. The module rename exists only to instantiate baseline and candidate side by side.

The candidate replaces five local history registers with wires to the corresponding fields already held by the actual upstream tap. It removes only their reset/update assignments. It retains the full field widths; it does not truncate or remove any A585 field.

| Local cached field | Held upstream slice | Retained FF in actual frozen VG |
|---|---|---:|
| accepted_count | raw_body[79:48] | 32 |
| consumed_id | pose_body[223:192] | 32 |
| held_dt | pose_body[191:160] | 22 |
| pose_flags | pose_body[15:8] | 5 |
| pose_fault | pose_body[7:0] | 8 |
| Total | | 99 |

The declared widths total112 bits;13 were already constants/aliases in the real VG. The prototype still exposes all112 declared field bits.

`summary_body` and `summary_tick` retain exactly the same reset, `!snapshot_hold` enable and publication edge. Last rejected metadata, first diagnostic/protection event lifetime, event-window handling and max-pose-gap state are unchanged. The serializer and CRC implementation were not edited. In particular the separate32-bit `last_pose_tick` optimization hypothesis was **not** applied.

## Required held-body contract and actual binding

This optimization is valid when the raw/pose payloads are held by the producer between their valid pulses, and producer and summary share the same clock/reset. It is not an arbitrary-invalid-input-data equivalence claim.

The current top directly connects `imu_diagnostic_tap` raw/pose outputs to `sik_imu_diagnostic` (source/acg720_ano_port.v:297). In the actual tap, raw_body changes only in reset or `if(decision_pending)` alongside raw_valid; pose_body changes only in reset or `if(attitude_update)` alongside pose_valid (source/core/imu_diagnostic_tap.v:82,91). The NBA timing is preserved: on an emitting edge both summaries read the prior source tuple; on the following edge both use the newly held tuple. The five downstream history copies therefore add no distinct history under this contract.

`copy_miter_tb.v` directly instantiates the real frozen tap, not a payload stub, and asserts on every observed edge that a body cannot change while its valid is low. Both summary implementations receive the same tap outputs, clock/reset, hold and events. It compares the full512-bit summary and32-bit tick after NBA on every clock.

## Simulation evidence

`summary_tb.v` retains the existing summary unit assertions with the candidate module name. It passes same-cycle input updates, frozen-output hold, ongoing gaps, first diagnostic/protection events, new-window suppression, event-sequence wrap and reset.

The120000-cycle actual-tap miter passed with no body/tick mismatch:

| Coverage | Count |
|---|---:|
| raw and pose valid together | 14358 |
| rejected raw publications | 29979 |
| input updates while snapshot held | 38664 |
| hold rising / falling | 28697 / 28696 |
| longest pose-publication pause | 7001 clocks |
| reset clocks | 11 |

The clock half-period is10ns (50MHz); this test covers2.4ms. Its tap diagnostic trigger parameter is1000 clocks to exercise diagnostic event handling promptly. It does not replace the separate production-policy20/30/60ms source-timeout tests.

The first miter run reached a coverage failure, not an output mismatch. Its accepted stimulus used a correlated LFSR tap; the revised TB uses independent bit18 so rejection coverage is exercised. `copy_miter_tb_initial_coverage.v` and `sik_copy_miter_initial_coverage.log` preserve the initial FAIL. The candidate RTL was unchanged between those runs.

`miter_result.json` binds the frozen producer/summary/serializer sources, candidate, TB files and final outputs. The side-by-side baseline is `sik_original.v`; the candidate is `sik_copy99.v`. Their actual invocations used Icarus `-g2012 -s sik_copy_miter` with the real `source/core/imu_diagnostic_tap.v`, then VVP `-i -n`.

## Single-module synthesis evidence and limits

Both `synth_baseline/` and `synth_copy99/` contain the complete GPRJ, Tcl, exact module source, identical context wrapper, console log and synthesis outputs. Both returned0 and report `GowinSynthesis finish`; neither has an impl/pnr directory. The Tcl ends in `run syn`, never `run pnr`.

| Same wrapper / same Gowin options | Baseline | Copy99 | Reduction |
|---|---:|---:|---:|
| FF | 833 | 734 | **99** |
| LUT | 386 | 287 | **99** |
| ALU | 79 | 79 | 0 |

The wrapper applies only contextual facts already present in the frozen whole-design VG: build ID B0B2, published held_dt high10 bits zero, pose_flags high2 bits zero and initialized bit equal to ready bit. All other inputs remain unconstrained. These constraints estimate the actual retained sizes; they are not field or protocol changes to the candidate.

The absolute baseline833 differs from the real integrated summary803 because the wrapper leaves other upstream correlations/constants unconstrained. The measured **difference99** is the single-module evidence. It does not establish a new integrated FF count, CLS packing, routing success, timing, or a flight qualification.

## Resource-review findings and decision boundary

The frozen integrated summary has803 FF:448 retained payload snapshot bits +32 tick bits +323 persistent history bits. All803 use boot reset n13_16. `telemetry_tx` has a wire `diagnostic_packet`, not another512-bit payload snapshot. Its local FF count is176¡ú177 (+1), while weighted local LUT increases2651¡ú3075 (+424). The shared CRC register and UART were not duplicated.

The existing staged_telemetry.core_q_453_16 global hold and the summary480 FF snapshot bank remain required and untouched here. Removing these would change the common snapshot contract. This candidate removes99 local capture/mux/reset loads, not the unique output snapshot.

The earlier +1129 whole-design FF comparison mixed phases/settings: synthesis27363¡ú27816 (+453), then the current replicate=1 PNR report28492 added676 FF. The old successful physical run used replicate=0. A fair physical comparison must use the pendingreplicate=0 result; the prototype does not justify more blind PNR parameter sweeps.

Before any adoption, root will archive the prior module, integrate a separately reviewed candidate, rerun complete source/byte/CRC checks, then independently synthesize/route and accept the new artifact. No such integration or PNR was performed here.

## Integrity and replay

`index.json` lists SHA256 and sizes for every preserved artifact, including wrappers, baseline/candidate, both TB revisions, logs, all synthesis reports/netlists and result JSONs. It also binds all53 unchanged frozen source inputs. Preserve this directory as-is. Replays should copy the listed source/project/Tcl inputs into a new output directory, so the archived failed and successful evidence is not overwritten.
