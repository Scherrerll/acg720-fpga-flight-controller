# Runtime coefficient and integral storage: read-only width review

No source, candidate, serial CRC STOP artifact, synthesis or PNR was changed. This review reads the frozen `candidates/response_compact` source/VG and the actual P005/I0 synthesis fixture from the handoff. Current canonical controller text matches that frozen runtime controller. The repeatable inventory is [audit_runtime_storage.py](audit_runtime_storage.py), with all input hashes, assignment/read line excerpts, mapped FF groups and direct pin counts in [runtime_storage_audit.json](runtime_storage_audit.json). It performs parsing and integer bounds only, not new RTL simulation or synthesis.

**Conclusion:** integral current/saved storage is already signed27, with no further sound reduction. Legal coefficients can use unsigned14 behind unchanged16-bit output aliases. The smallest sound product change would be bank-only internal coefficient storage: directly4 FF fewer, potentially up to8 total if existing16-bit controller snapshots' constant high bits are propagated away. Explicitly narrowing the controller snapshots would require the legal0..10000 input-domain precondition; it is not unconditional equivalence for arbitrary16-bit direct controller inputs. The current work-pair snapshots must stay. These savings do not establish a routing benefit.

## Frozen evidence identity

| Input | SHA256 |
|---|---|
| Handoff P005/I0 `v15_xy_p005_i0_syn/fixture/position/mtf_xyz_hold_control.v` | `78952264bf5a507f2f9e080e53fe0dd41b940cf13c699a134fb5aa12be539258` |
| `candidates/response_compact/source/position/mtf_xyz_hold_control.v` and current canonical controller | `d79d31b434045b2da0711dd54d801646959b4c17d51b1d3fa8cd10eb284f872e` |
| `candidates/response_compact/source/xy_pi_parameters.v` | `c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187` |
| Actual frozen P005/I0 mapped VG | `15d9f51da52cff0092dcbafd22918b4e97a5ea3e96c223e1a94315b48ceeea2b` |
| Actual response_compact mapped VG | `7d815709a3699e3805efadf4a287e388329d5a75ca2f63ef40ea05bbf349b3e9` |

Source line numbers below refer to those frozen files. [runtime_storage_controller.diff](runtime_storage_controller.diff) compares the actual old/new controller sources. Other physical candidates may have identical controller text but different global mapping and net names; this report's pin counts belong to the named VG hashes only.

## Every integral assignment and read

The two live registers are `reg signed [27-1:0] ix_store, iy_store` (runtime lines111–112); completed/rollback copies are `reg signed [26:0] saved_ix, saved_iy` (line113). These same27-bit declarations already appear in P005/I0 at lines109–111. `keep64` (lines43–44) is an identity function, not a64-bit register. `ix` and `iy` at lines163–164 are64-bit signed wires explicitly sign-extending bit26 by37 bits.

| Register | All assignments | All reads and meaning |
|---|---|---|
| `ix_store` | declaration INIT0; reset line280→0; broad cancel/origin/blocked line290→0; partial-callback rollback line325→`saved_ix`; state64 line353→`taking_off && work_i!=0 ? clip(ix+value,-65536000,65536000):0` | line163 sign-extension alias; line336 copies to `saved_ix`; `ix` is consumed by state64 addition/clamp and state8 P+I staging line356 |
| `iy_store` | declaration INIT0; reset line280→0; broad cancel/origin/blocked line290→0; rollback line325→`saved_iy`; state65 line355→same signed clamp/zero | line164 sign-extension alias; line336 copies to `saved_iy`; `iy` is consumed by state65 addition/clamp and state9 P+I staging line357 |
| `saved_ix`, `saved_iy` | declaration INIT0; simultaneous callback-start copy at line336 from the live27-bit registers; no separate reset/cancel assignment | only rollback line325, restoring the previous completed callback's live values |

This closes the invariant by induction: all four registers start in range; live writes are zero, an already-bounded saved value, or a clamped value; saved writes copy a bounded live value. No live or saved register ever temporarily holds `ix+value` before clipping. That addition is a64-bit expression through the signed aliases; do not narrow it, `value_store`, the shared multiply/divide operands or their result registers as part of this storage change.

The exact legal storage interval is [-65,536,000,+65,536,000] Q16 units, or ±1000 cdeg. Signed27 spans [-67,108,864,+67,108,863], equivalent to [-1024,+1023.9999847412] cdeg. Signed26 spans only [-33,554,432,+33,554,431], or approximately ±512 cdeg. Reducing to26 wraps the existing positive rail +65,536,000 to -1,572,864 (-24 cdeg); the negative rail becomes +24 cdeg. The existing actual controller proof explicitly reaches both ±65,536,000 rails (`verify_control.py`, rail and sign-reversal cases), so this is not a hypothetical unreachable magnitude. Changing fractional precision would also change defined arithmetic.

For valid callback dt1000..100000us, clamped error ±32,768,000 Q16 and I<=10000, the two existing truncating math stages yield |delta I|<=32,768,000 Q16 (500 cdeg). The pre-clip addition can reach ±98,304,000 Q16 (1500 cdeg); it requires at least28 signed bits and is currently evaluated in64. Therefore the fact that the stored result fits27 does not authorize narrowing its pre-clip arithmetic to27.

Reset and cancellation order matters: reset and broad cancel/origin/blocked zeroing take precedence over callback rollback. A normal ATT_STAB exit with `work_xy==0` retains the last completed I/filter state. An exit during a callback restores the saved pair before the state case runs. A successful state46 completes the callback and leaves both new clamped I values live. `taking_off==0` and I=0 clear I at their existing state64/state65 edges, not immediately on the input transition. No width proposal should add a new clear edge, omit a rollback copy or change this priority.

## Coefficient storage and exact scope

`xy_pi_parameters.v`: external active P/I are unsigned16-bit regs at line7, INIT500/0 at line12 and reset500/0 at line34. Their only other assignment is the atomic state2 pair commit at line83. The full16-bit proposed values at line27 are rejected when either exceeds10000 at line74; frame capture is disabled while validation/commit/response states run. Hence the commit consumes exactly the already-range-checked unchanged frame. CRC/format/opcode/replay/highwater/range and safety checks remain prerequisites. This proves active P/I stay0..10000 for every initialized protocol/reset trajectory, including arbitrary invalid16-bit packet fields.

Unsigned14 covers0..16383 and is sufficient; unsigned13 ends at8191 and rejects/truncates currently legal8192..10000. The suggested bank representation is14-bit `active_p_store`/`active_i_store`, with the same INIT/reset/commit edges and16-bit output wires `active_p={2'b0,active_p_store}`, `active_i={2'b0,active_i_store}`. Keep the output ports and response concatenation fields16 bits. Merely changing the widths in the existing concatenation would shrink/reposition packet fields. Keep the entire frame, proposed values and range comparators16 bits: truncating proposed P=0x4000 (16384) to14 before range validation turns a required RANGE rejection into a possible zero-gain write.

Controller `work_p/work_i` are unsigned16-bit INIT500/0 at line207. Their sole subsequent assignment is one simultaneous callback-start capture from the16-bit inputs at line333. They have no explicit reset/cancel assignment and remain stable for the whole callback. Reads are `$signed({1'b0,work_i})` at states6/7 (lines352/354), `work_i!=0` at lines353/355, and `$signed({1'b0,work_p})` at lines355/356. Each cast produces a positive signed17-bit value, then the signed64 task argument. Retaining16-bit aliases around any14-bit work store would preserve that exact cast sizing for legal values; replacing the snapshots with live inputs would violate the existing coherent-pair guarantee.

The minimal recommendation is **one bank file only**, leaving the controller ports, snapshot declarations, reads and capture edge literally unchanged. Explicit bank zero extension can allow an integrated synthesis to remove the four now-constant high work bits. Direct source storage savings are4 FF; the additional4 require mapped confirmation. A two-file explicit14-bit work-store change could guarantee the representation for legal protocol inputs but changes a standalone controller receiving e.g. P=16384 directly: current code snapshots16384, while14-bit truncation captures0. With100mm/s steady error, those can yield roughly1638 cdeg versus0 before other terms. That stimulus is rejected by the production bank, but prevents an unconditional all16-bit-input module-equivalence claim.

The existing `verify_control.py` mid-operation test changes legal inputs from1000/0 to2000/5000 during state6, requires the current callback's `work_p/work_i` to remain1000/0, then requires the next callback to capture2000/5000. Keep that proof and its16-bit test/telemetry interfaces intact. A future representation-only change needs same-cycle protocol and controller comparisons over legal endpoint/random gain pairs, invalid high-bit protocol rejections, the current pair-change scenario, both I rails, reset, cancellation and rollback. No such proposed change was implemented or newly simulated here.

## What the existing mapped registers and fanout actually add

The frozen P005/I0 source declares the same108 live/saved integral bits, but synthesis removes them because I is hard-zero. The runtime VG has all108 FF. Coefficient work snapshots add32 FF; their high14/15 FF physically exist. Bank output aliases are mapped as `parameter_response_111..96` for active P and `parameter_response_95..80` for active I, also all32 FF, including all four high bits. They were not automatically removed by the current range check.

| Controller mapped group | P005/I0 | Runtime | Delta |
|---|---:|---:|---:|
| `ix_store` + `iy_store` |0|54|+54|
| `saved_ix` + `saved_iy` |0|54|+54|
| `work_p` + `work_i` |0|32|+32|
| `ux_store` + `uy_store` |64|72|+8|
| `publish_roll` + `publish_pitch` |34|42|+8|
| `return_state` |6|7|+1|
| mapped `nav_xy_payload_roll_14` extra output register |0|1|+1|
| DFF primitives directly in controller module |2156|2314|+158|

The last total here is the parser's FF count directly inside the controller module; child primitive instances and mapped aliases are not a formal netlist equivalence proof. The group deltas sum exactly158. The36-bit P+I+FF staging is an existing reviewed overflow fix for legal maximum P; it is outside this integral/coefficient storage proposal and must not be collapsed to the old32-bit representation.

| Exact mapped load | Frozen P005/I0 VG | response_compact VG | Implication |
|---|---|---|---|
| Callback snapshot CE |`n54139_3`:129 direct pins|`n55704_3`:215 direct pins|+86 exactly equals54 new saved-I FF plus32 work-coefficient FF. Removing only high work bits would remove4 sinks before any remapping. |
| Controller broad cancel/reset qualifier |`n52323_6`:400 SR +3 logic =403 input pins|`n53888_6`:455 SR +3 logic =458 input pins|+55 SR;54 are new live-I FF, the remaining one is the mapped output-register change. Both drivers are LUT4 INIT FDFF with `rst_n_ff,blocked,cancel,controller_z_ready_6`. |
| New live `ix_store`/`iy_store` |not mapped|27+27 RESET pins on `n53888_6`; per-axis CE fanout27|Already-minimum27-bit I is responsible for54 new variable reset loads. Coefficient narrowing does not remove these. |
| New saved I/work snapshots |not mapped|54+32 FF; RESET/SET tied GND; common snapshot CE|They have INIT values and callback enables, but no variable reset-tree sinks. Counting them as86 new reset loads would be wrong. |
| Active bank P/I |bank absent|32 startup SR pins:26 RESET,6 SET; common commit CE `n2239_14` has63 total direct pins|Narrowing the four high zero bits removes4 RESET/CLK/CE sinks, with expected pre-remap CE63→59. Bank total is290 SR pins; coefficient narrowing is a small part of that tree. |

The callback CE129→215 comparison is particularly direct: the old saved acceleration/filter snapshots remain, and the additional54+32 captured bits use that same decoded callback-start enable. Work P high bits have one internal controller input load each; work I bits have two (gain operand plus nonzero checking). I sign bit26 has24 direct input loads per axis versus2 for other live I bits; that sign extension cannot be removed without changing the value representation. Counts are logical mapped input-pin fanout, not physical routes, placement congestion, unrouted identities or a timing diagnosis.

The older release_width36 diagnostic reported a different qualifier fanout (465). It belongs to a different complete synthesis VG even though the controller source matches. This review deliberately recomputes403→458 from the frozen P005/I0 and selected response_compact VGs rather than importing that older number.

## Bounded recommendation

Do not implement an integral width change: expected saving0 FF, and26 bits has an existing-rail counterexample. If a further bounded experiment is justified, bank-only14-bit stores behind exact16-bit aliases are the smallest coherent scope: no state/latency change at source level, no protocol range/CRC/field/telemetry change, controller work-pair snapshots untouched, direct4 FF reduction and possible additional4 work FF after constant propagation. Actual global FF/LUT totals, timing and routing benefit require later authorized synthesis and PNR; the serial CRC experiment already demonstrated that a local resource saving does not guarantee a full-top LUT reduction. No physical success is inferred here.
