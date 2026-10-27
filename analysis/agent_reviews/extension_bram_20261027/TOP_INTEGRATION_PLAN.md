# Proposed next proof, not an implemented candidate

The WIDTH888 standalone test passed against the original complete GW5A vendor
model. This establishes the storage primitive contract, not top integration,
mapped resources, routed timing, hardware startup or flight behavior.

1. Freeze and rehash the current v18 canonical source55. Work only on explicit
   old/new fixture copies in a new proof directory. Rename the two top module
   types. In the new copy, change only the extension snapshot declaration and
   its enabled assignment into a WIDTH888 `gw5_snapshot_bram` instance with
   `.enable(!telemetry_snapshot_hold)`. Keep the other snapshot assignments on
   their original edge. Preserve the original extension producer, all masks,
   startup/reset decisions, clocks, serializer and every default parameter.
   Verify an exact reversible text diff before compiling.

2. Compile both actual top copies and their exact source dependencies with
   `-DGW5_USE_VENDOR_BRAM` and the same unmodified, hash-bound GW5A prim_sim.v.
   Provide one top-level `GSR GSR(.GSRI(1'b1))`. Assert and inspect elaboration
   for exactly28 added SP instances and no portable_simulation branch. The
   existing source55 wrapper must remain unchanged.

3. Start with natural initialization and common external pin inputs, without
   forcing or preloading boot, reset, snapshot, serializer, memory or control
   state. Compare all public top outputs, extension snapshots, other snapshots
   and serializer start/data/hold on every sampled edge, including before the
   first edge. Exercise repeated reset/stop input conditions while snapshot
   hold is high and low: the extension storage itself has no new reset term.
   Use actual UART frame input where feasible, including malformed/duplicate
   MTF frames and stale intervals. This is a natural-input top smoke/integration
   proof; do not claim it spans arbitrary extension payloads.

4. Separately stress arbitrary extension payloads through the actual
   `telemetry_tx` RTL and the exact old/new snapshot block, with identical
   explicit fixture inputs for the other frame bodies. Use natural serializer
   scheduling and a documented byte-level transport acknowledgment fixture;
   do not force its state/index/cache/hold. Cover both short legal scheduling
   periods and the production period, variable stalls, all extension bits,
   invalid/status masks, sequence wrap, complete frame lengths and independent
   XOR/CRC checks. Compare start/data/hold cycle-for-cycle. This additional
   component integration proof is not a physical UART waveform or whole-flight
   proof and must not be mislabeled as the natural-input whole-top test.

5. Bind actual compile/vvp/root returns, original source55, isolated exact diff,
   both fixtures, source dependencies, tools and vendor model. Preserve any
   failed attempts separately. A new source candidate is justified only after
   these checks and review. Any later synthesis/PNR must separately demonstrate
   actual28 SP mapping and unchanged controls, then pass true20ns/50MHz full
   setup/hold/recovery/removal/pulse, zero violated endpoints and original pins.

Historical SP candidates replaced core/info/rotation snapshots, not extension,
and failed routing. Their functional pass does not predict physical improvement
for this proposed28-SP extension-only experiment.
