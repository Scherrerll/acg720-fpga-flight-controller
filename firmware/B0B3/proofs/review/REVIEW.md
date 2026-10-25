# Runtime XY P/I focused review

Reviewed the current `source` tree after the signed36 Q16 `ux_store`/`uy_store` correction. No additional actionable defect was found in the reviewed parameter, arithmetic, and arbitration paths. This is a focused source review, not a hardware, timing, or flight acceptance.

The known signed32 P+I+FF overflow has been corrected by the parent. `position/mtf_xyz_hold_control.v:133–137,180–181` now retains signed36 Q16 values before the final angle clamp. No narrower intermediate was found that defeats this correction.

`bounds.json` records the reviewed source hashes and a read-only integer recurrence of `position_sincos` over all 36,001 legal cdeg yaw inputs. This is a source-equation enumeration, not an independent RTL simulation. The largest `|sin|+|cos|` is 92,692 Q16 (factor 1.41436767578125). Allowing each world velocity component ±10,000 mm/s, each acceleration component ±30,000 mm/s², and each stick speed ±1,500 mm/s gives these conservative layer bounds (apart from sub-LSB division truncation):

| Stored quantity | Bound | Representation capacity | Result |
|---|---:|---:|---|
| sampled velocity | ±10,000 mm/s | signed31 Q16: ±16,384 | Fits |
| rotated velocity error + stick (`fixx/fixy`) | ±15,643.68 mm/s | signed32 Q16: ±32,768 | Fits |
| rotated acceleration / LPF (`hx/hy`, `afx/afy`) | ±42,431.04 mm/s² | signed33 Q16: ±65,536 | Fits |
| P error after 0.03s acceleration lead (`ex/ey`) | ±16,916.61 mm/s | signed32 Q16: ±32,768 | Fits |
| integral after existing clamp | ±1,000 cdeg | signed27 Q16: ±1,024 | Fits |
| P+I+FF at public P=1 | ±170,466.08 cdeg | signed36 Q16: ±524,288 | Fits |

The acceleration LPF update uses a positive alpha below unity for eligible dt, so it does not expand its input/initial-state envelope. The I error is clipped before dt/gain scaling; eligible dt≤100ms and public I≤1 limit one update to ±500cdeg before the ±1000cdeg accumulator clamp. The signed50 multiply-A, signed34 multiply-B, signed48 quotient stores have ample room for these XY paths. Gain operands use `$signed({1'b0, work_*})`, so gains 0..10000 cannot become negative through sign interpretation.

`xy_pi_parameters.v:57–93` checks CRC/format/opcode/range, consumes fresh SET sequence numbers (including rejected fresh requests), and rejects equal/older SETs. Active P/I/generation change together only in state2, with a renewed write-safe check and controller boundary. The response snapshot is assembled in state3, after the committing edge; CRC completion precedes response_valid. Response backpressure prevents subsequent parsing from overwriting a pending response.

`core/flight_core.v:556–558` excludes valid CH5-high intent throughout the pre-arm confirmation interval as well as raw armed/controller/taking-off/fresh-command states and non-idle selected motor widths. This closes the synchronous old-armed-Q edge case. `mtf_xyz_hold_control.v:205–208,333` advertises only cancelled idle as a parameter boundary and captures a complete working pair at XY callback start. Ordinary ATT_STAB retention/partial-callback rollback remains separate from stopped parameter changes.

`telemetry_tx.v:17,194–207` captures a whole parameter response at idle and uses the existing single UART until all 24 bytes finish. Already-started telemetry groups cannot be interrupted. Due telemetry wins the idle arbitration; at the actual PERIOD=10,000,000 clocks (200ms), the telemetry group occupies about 56ms and leaves response service time. A future PERIOD shorter than a complete telemetry group could starve commands, but that unsupported configuration is not the current top-level design.

UART/header timeout reset, duplicate headers, fixed length bounds, CRC byte coverage, response field offsets, and response-ready handshake were inspected. No code path was found by which bad CRC, truncated requests, duplicate SETs, or a rejected commit changes the active gains. This review does not add authentication, characterize metastability MTBF, validate current physical wiring, or certify loop dynamics; those are outside the reviewed mechanism.
