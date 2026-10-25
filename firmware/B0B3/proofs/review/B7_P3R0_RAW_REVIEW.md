# Independent raw B7 P3R0 artifact review

PASS for the existing exact physical fixture `builds/idle_integral_p3r0`. This review did not read `inspect_timing` code or its JSON. It directly checked the final raw TR/RPT/log/SDC/CST/VG/FS/PR, actual process receipts and netlist-only physical project. No synthesis, PNR, source/constraint/build-output change, process operation or hardware access was performed.

The actual process started 2026-10-25T22:45:34.204754+00:00 and returned0 at 2026-10-25T23:07:52.628945+00:00. The log independently records skipped synthesis, placement/routing completion, bitstream completion and the EOF completion sentinel, without ERROR or an unrouted-net report. The physical project contains exactly one netlist plus CST/SDC, and the actual Tcl/options are place3/route0/map2/replicate0. Generic build-input started_utc is donor-inherited; output freshness was checked against the actual process start instead.

The build-input `tcl_sha256` is also donor-inherited: `395828b978a46bacbbb7eca0fcf6888de91898813fafc06065cac1986373a126` exactly matches the donor's `synth_only.tcl` and its original synthesis receipt. It is not a physical Tcl binding. The actual separate `physical.tcl` has SHA256 `8cb88e3b7042d5cd6862197e382847727e586a31dbea492ba5da7ecd7a186f41` and is independently read/hashed here; its generated project SHA256 `8f504062fd5ea71330a8514aaffad1e8a2ee53ed47100b6a3e5195673cddf081` exactly matches `physical_project_sha256`. No old receipt was rewritten. This explicit separation must be retained in execution/release provenance.

The raw TR and RPT name this fixture's exact VG/CST/SDC and GW5AT-LV60PG484AC1/I0, device versionB. Actual VG SHA256 is `4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb`. SDC has exactly clk50 period20.000ns and the existing radio_rx false path; no additional command or internal timing exception was introduced. TR clock summary has one base clk50, actual Fmax50.257MHz, setup and hold violated endpoints both0.

Every numeric row in the five raw summary tables was parsed independently and checked finite/nonnegative:

| Table | Reported rows checked | Minimum slack ns |
|---|---:|---:|
| setup | 25 | +0.102 |
| hold | 25 | +0.145 |
| recovery | 25 | +11.895 |
| removal | 25 | +3.312 |
| min_pulse | 10 | +7.387 |

FS, TR, RPT and PR are all nonempty and were created/last-written after the actual process start and before its exit. Embedded FS/RPT/TR created times are07:07:45/07:07:49/07:07:51 local, respectively. FS header identifies GW5AT-60B, the correct part/package, UserCode0x0000b0b3 and CRCCheckON. The FS is17456619bytes with SHA256 `a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd`; TR SHA256 `e155cdef595756f4b5033fe752cc230186cae259803e1ee2b3cb179abe570ea3`. All input/output evidence hashes matched before and after the review, so no mutable partial file was accepted.

All18 active raw physical-report pin rows exactly match the18 CST locations and18 raw VG top-level directions (13 outputs). All IO types, specified pull modes and output drive settings match. Radio RX isB16/input/PULL_MODE=UP; radio TX isB15/output. This establishes software artifact/pin identity, not current physical wiring.

Detailed rows, all18 pin assignments, timestamps, raw FS header and hashes for all15 evidence files are in [B7_P3R0_RAW_REVIEW.json](B7_P3R0_RAW_REVIEW.json). Script SHA256 `b337495e90ce14e43eb98f29d9c37d2e0122f8d32b9e187a9d1f4d7916092206`. Scope is the existing raw implementation/timing evidence only, not a new STA run, whole-netlist functional equivalence proof, hardware or flight acceptance.
