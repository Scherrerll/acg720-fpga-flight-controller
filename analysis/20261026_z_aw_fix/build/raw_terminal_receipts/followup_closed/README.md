# Follow-up closed evidence receipts

This new archive leaves the original frozen eleven-attempt archive and ATTEMPTS indices unchanged. It adds two already-closed route failures: v4 P4R0 ended 2026-10-26 07:19:50 UTC with actual p.wait=1 and 7,273 unrouted nets; v5 P3R0 ended 07:22:59 UTC with actual p.wait=1 and 648 unrouted nets. Both have no TR/FS and remain unqualified. The v5 owner-sealed status and seal manifest are copied verbatim.

Two separate non-normal records are preserved: v5 incremental B3 PA2136 matching 2.81 < 80 caused automatic default-flow fallback, then root cancelled the verified duplicate. Its actual p.wait=4294967295 and inherited normal_wait_return=true mean the wait returned, not normal completion or route failure. The v5 P2R0 observation says both PIDs 45484/64524 were absent and no exit receipt existed; actual p.wait and end time remain null. It is an orchestration interruption of unknown cause, not a vendor route or STA failure. The existing cancellation report is copied as raw bytes, including its existing encoding.

RPT text is losslessly gzipped with an empty filename and mtime=0. Every copied receipt has original/archive/raw SHA256 in MANIFEST.json. Full55 source maps, exact input receipt bindings, log hashes from actual exits, VG hashes without VG copies, and pre/post stability are recorded. The owner manifests remain external scope references: their generated artifacts are not copied here.

No build/process/hardware/serial/Git action or source edit was performed. No active v5 repl1 or v6 physical logs were opened. No FS, VG, PR, build database or compiled binary is included. No candidate is qualified or selected by this archive.
