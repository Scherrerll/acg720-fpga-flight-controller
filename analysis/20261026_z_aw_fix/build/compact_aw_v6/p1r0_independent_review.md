# v6 P1R0 independent raw review — FAIL

This exact attempt completed routing and bitstream generation, and its real vendor wait returned 0 at **2026-10-26 08:20:06.877617 UTC**. The log contains the physical EOF marker and matches the actual exit receipt hash. It fails the unchanged 20.000 ns / 50 MHz physical timing gate and is **not deliverable or qualified**. The producer wrote physical_audit.json and build_failure.json; no build_result.json exists.

Values below were parsed directly from the original TR tables before comparison with the producer audit:

| Check | Worst slack (ns) | Raw table rows |
|---|---:|---:|
| Setup | -2.580 | 25 |
| Hold | +0.138 | 25 |
| Recovery | +12.305 | 25 |
| Removal | +2.469 | 25 |
| Minimum pulse width | +7.387 | 10 |

Actual Fmax is **44.286 MHz**, versus 50.000 MHz required. There are **862 setup** and **0 hold** violated endpoints. Worst setup path: `acc_time/output_az_20_s0/Q` → `core/manual_angles/pending_np_0_s0/CE`, relation 20.000 ns, clock skew +0.437 ns, data delay 21.863 ns. Full raw rows and their section hashes are in the JSON.

All 18 raw RPT I/O locations and directions match CST, including radio_rx B16 input and radio_tx B15 output. The 17,456,635-byte FS is stable and nonempty, with complete header UserCode 0x0000b0b4, binary-only payload and footer; CFG also contains 0x0000B0B4. FS SHA256: `f2d66602e8b93a0320a0323f1c28c7bf420e9a0a01d7ed156b2c59737b1d5b6f`. Bitstream existence and syntax do not cure the timing failure.

The attempt, canonical v6, and donor source55 maps match before/after. Wrapper f826345e…, shared height fusion 69b386c2…, hold 04e75ada… and exact VG `6b169818d5029c45e0a778d74d8d3e90e129caa430e93eb3778661f18fa7cb99` are verified. All 11 donor binding SHA/byte pairs and all summary audit hashes match original files. SYN actual wait=0; gain audit has 16 P/I FF each with INIT P=1000 and I=350; strict-clock audit has 27,725 FF, all CLK50, bad=[]. Fixed original SDC and its existing radio_rx pad exception are unchanged.

Scope is independent read-only physical-artifact review of this attempt. The JSON includes raw file SHA256, byte sizes, timestamps, actual values and pre/post stability. No new build, process control, source edit, Git, serial, programming, hardware or flight action occurred. Prior software evidence was not rerun. Preserve this as **fullroute_timingfail**; do not select its FS for delivery.
