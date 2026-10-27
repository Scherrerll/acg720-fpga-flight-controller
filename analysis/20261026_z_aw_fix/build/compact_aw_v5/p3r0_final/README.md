# v5 normal P3R0 final status

The exact v5 netlist `2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9` completed its actual vendor process with `p.wait()=1` at 2026-10-26 07:22:59 UTC. Gowin reported `DesRoute failed` and **648 unrouted nets**. No TR, FS, or PR was generated. This is a routing failure with no STA result, and is not a delivery/download candidate.

The profile used place3/route0/map2/replicate0/timing-driven1 and the unchanged 20 ns SDC. Canonical v5, synthesis snapshot, and physical snapshot all55 source hashes were rechecked, as were the unchanged original B4 and v4 reference snapshots. The donor synthesis had a genuine normal wait0 and the exact mapped/gain/clock receipts are bound by hash. No new synthesis, source edits, hardware action, or cancellation occurred during sealing.

The first launcher rejected an incorrect donor-options dictionary before opening a vendor profile. Its original script and failure receipts remain unchanged. The separate launch02 corrected only that dictionary shape; timing-driven1 remained explicit in the actual physical options and Tcl. The raw failed run and historical launcher evidence are hash-bound by `FINAL_STATUS.json`.

`MANIFEST.json` seals only the three listed files in this terminal evidence directory. External raw artifacts are referenced by repository-relative path, bytes, and SHA256 in `FINAL_STATUS.json`. It excludes compiled VVP/cache and does not freeze or modify the sibling P2 build.
