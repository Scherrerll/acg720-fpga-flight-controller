# Height fusion numeric guard: v5/v6 finite RTL comparison

**PASS, no two-state counterexample in these traces.** The actual v5 and v6 `mtf_shared_height_fusion` modules ran side by side, each with its own real `nav_math_service` multiply/divide engines and `position_math`. No private state was forced. The test compares all152 public output bits, all228 request/cancel/operand output bits, and all135 service response/result/grant bits on every rising edge after NBA updates. It also checks immediate combinational source/tail revocation before the injected bad-value edge.

| RANGE_AGE_PRECHECKED | Cycles | Height publications | Seed completions | Mul/div consumed, each | Acceleration-filter divide consumption |
|---|---:|---:|---:|---:|---:|
| 0 | 1,686,784 | 26 | 14 | 2,208 | 1,980 |
| 1 | 1,508,078 | 23 | 11 | 1,980 | 1,776 |

Both configurations compiled and simulated with actual return code0. Normal traces include range300/500/490mm and acceleration0/+30000/−30000mm/s². Four separate one-clock pulses of +30001, −30001, INT32_MAX, and INT32_MIN occur at an actually reached live state84 publication boundary: both modules immediately drop `sources_ok`, estimate readiness and numeric tail, suppress that publication, assert cleanup cancellation, then naturally reseed and publish after legal input returns. Each configuration also checks origin reset, range/acc validity, height−1/5001 rejection, legal height0/5000 qualification, and reset during actual arithmetic. External age4999999/5000000/5000001/UINT32_MAX exercises exact threshold rejection in PRE0 and the documented age bypass in PRE1.

The simulation clock remains50MHz. Parameter `CLK_HZ=5000000` shortens the height timer from550000 to55000 clocks (10× accelerated callback cadence). The integration dt remains11000µs; acceleration admission is every10000 clocks. `AGE_LIMIT` remains5000000, preserving the special prechecked-age contract. These are finite module-level traces, not flight/plant replay, exhaustive/formal equivalence, contention testing, wrapper testing, or a natural5000000-clock publication-age expiry test. The wrapper is handled separately by the parent task.

The authoritative result is `completion03/results.json`, SHA256 `eb0295ca89af3ac66db0a65d923d30097c1c9bdd6c8fd99a1b9954f48b825e39`. It binds all55 v5 and v6 input hashes before/after, which remained identical. Only the two expected v6 files differ from v5; the hold controller is unchanged at `04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873`. Generated height references change only the module name plus text newline normalization. Real math reference bytes are preserved under `references/` and are bound to the input hashes.

Historical failures are retained: the first compiler returned1 before RTL because its configured temporary path could not be opened. Attempt02 fixed only the child TMP/TEMP/TMPDIR environment; PRE0 then passed actual compile/vvp0, but the Python postprocessor rejected Icarus's standard `$finish` trailer after the PASS line. Completion03 accepts exactly that PASS line and standard finish trailer, reuses the unchanged genuine PRE0 receipts, and newly runs only PRE1. No RTL assertions were weakened and no passed trace was rerun.

For a fresh replay, compile `completion03/tb.v`, `completion03/v5_height.v`, `completion03/v6_height.v`, `references/nav_math_service.v`, and `references/position_math.v` with Icarus `-g2012 -s tb -Ptb.PRE=0`, then repeat with PRE1. Choose a new writable TMP/TEMP/TMPDIR and new output path. Historical runners deliberately refuse to overwrite their existing evidence directories.

`MANIFEST.json` includes the retained scripts, source references, receipts, logs and report. It explicitly excludes local compiled `.vvp`, temporary files and caches; omitted compiled hashes are recorded separately for provenance and are not required to verify the retained files. No source, synthesis/physical output, hardware, HTTP, serial or Git action was performed.
