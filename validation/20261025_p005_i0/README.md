# Historical installed P005/I0 evidence, 2026-10-25

This is a bounded, byte-preserving export from `handoff_xy_pi_runtime_20261026`. It records the P0.05 / I0 image installed on October 25. It does not install firmware, inspect the aircraft now, or grant permission for any future hardware operation. Approval and operator-confirmation strings inside the copied receipts are dated historical evidence only. The newer B0B3 release has not been installed or written to Flash.

The installed image retained user code B0B2. That code alone does not distinguish this P005/I0 image from the earlier original V15 B0B2 (P0.15 / I0.10). The P005/I0 image SHA256 is `a876c8ed073588e17b6289f8aac7573334a5d5e9c992d394d0d14f61ed17db7c`; the original V15 rollback image SHA256 is `3b9920acc1abecf6e0ef50465f5bc408d9b74af2ac6d046cb151137a375b4306`. Neither image is included here.

Timing must be read with its original scope:

- P005/I0: fully routed, Fmax 50.59MHz, original vendor constraint 19.5ns; setup **FAIL**, WNS **-0.267ns**, **51 violated endpoints**. The original full timing audit did not pass.
- Its historical 20ns / 50MHz acceptance was an **analytical review of the unchanged routed report and mapped clock proof**, with derived setup slack +0.233ns. It was **not a vendor STA rerun at 20ns**. `qualification.json` saying `passed: true` has that analytical scope.
- The earlier original V15 B0B2 had its own 51.400MHz / original 19.5ns full STA PASS. Those are different image/results; see the existing [original V15 record](../../firmware/B0B2/verified_timing_20261025/README.md).

Read [baseline.json](baseline.json), [timing review](timing/timing_50mhz_review.json), [original physical/STA summary](timing/complete_audit.json), and [historical qualification](timing/qualification.json) together.

All times below are Asia/Shanghai, UTC+08:00:

| Original event | Local timestamp |
| --- | --- |
| Preparation plan, before approval (`flash_approval_received: false` at that stage) | 2026-10-25 23:53:30 |
| Install directory / operation start | 2026-10-25 23:55:14 |
| Installation receipt completion | 2026-10-25 23:57:23 |
| Cold-boot observation directory start | 2026-10-25 23:57:51 |
| Operator battery-only cold-boot confirmation | 2026-10-25 23:59:02 |
| Retrospective handoff baseline creation | 2026-10-26 00:20:05 |

[flash_install.json](flash_install.json) records successful programming and independent Flash verification under the old approval. Its cold-boot field was still false at that stage. The later [cold-boot summary](cold_boot/summary.json) records a verified battery-only boot, reset boot counters, and 50 distinct stopped frames over 11.25 seconds. The cold-boot observer itself performed no Flash writes; that observation-stage field does not negate the earlier installation. Both stages retain `flight_ready: false`. Stopped boot verification does not establish hover, braking, loaded-flight, optical-flow accuracy, or dynamic acceptance.

[export_manifest.json](export_manifest.json) maps all 14 copied originals to handoff-relative paths, byte counts and SHA256 values. Copies preserve original bytes, paths and historical wording inside each document. Direct hash links between the install, plan, qualification, timing, installer-test and cold-boot summaries were checked. The 54-source hash maps in baseline and qualification match. This export does not contain those source files.

This is a summary export, not the complete original evidence closure. Firmware `.fs` files, mapped device code/netlists, executable scripts/binaries, large programmer logs, videos/photos, and raw JSONL are excluded. The original receipts retain pointers/hashes to those omitted leaves; they must not be interpreted as files supplied by this directory. The manifest records the excluded current/rollback image and cold-boot JSONL hashes checked against the handoff originals. No live hardware or Git operation was performed to make this export.
