# B0B0 additional control review

Status: two related fallback defects repaired in a separate candidate and independently reviewed. The same directed regression fails 10/13 checks on the preserved old RTL and passes 13/13 on the repair. Component coverage passes 42,042 curve points; full-core stop/PWM and healthy-path equivalence tests pass. Actual synthesis freshness and diagnostic INIT reviews pass. No hardware programming. Routing closure remains pending: repaired-anchor candidate failed with 530 unrouted nets; additional MTF diagnostic-reset candidate failed with 436. Neither generated a bitstream.

Reviewed candidate: `variants/diagnostic_reset_p2_r2_rep1` (preserved).
Repair candidate: `variants/published_anchor_p2_r2_rep1`.

## Findings

1. The height controller legally publishes 1000–1850 us. The fallback only remembered values at least 1200 us, so published 1400 → 1100 could retain a stale 1400 anchor. With zero attitude corrections, the mixer clamps 1100 to 1200 per motor; height loss could then command 1400 without the manual slew limit.
2. Fallback validity referred to a previous published rate result, while its value came from `pending_throttle`. That request changes before the next result is published. A request still in flight could therefore become the fallback anchor, or publish its automatic collective after fallback entry.

## Accepted narrow repair

- Record any legal automatic collective, including 1000–1199, only on the actual motor publication edge.
- Preserve that exact pre-mixer value at entry; this preserves each motor's clamp under unchanged attitude corrections.
- Select fallback collective at the mixer while fallback is active, excluding queued automatic throttle requests.
- For an entry anchor below 1200, use zero lower slope numerator, then the existing target clamp and 1 us/ms slew to approach the manual idle floor. Do not allow unsigned subtraction to underflow.
- Preserve normal automatic behavior, hard-stop masks, fallback latching and disarm/reset recovery semantics.

The `taking_off` state is a control state, not proof of physical liftoff. A valid low automatic publication can establish fallback eligibility in that state. Exact continuity applies to collective selection with unchanged corrections, not a promise that changing attitude corrections leave every motor constant.

## Required proof

- Demonstrate pre-fix failure, then pass published 1400 → 1100 → loss, nonzero correction/clamping, unpublished and in-flight requests, first-publication boundaries, sub-idle arithmetic and slew, live stop, and recovery latch.
- Re-run affected component/core/healthy-path equivalence/top/UART tests.
- Verify the new actual synthesis and mapped INIT/freshness paths. Preserve the original completed diagnostic dual-top proof as evidence for its original source, and explicitly justify its applicability through an unchanged-interface and diagnostic-bank substitution proof. A redundant current-core full-top rerun was cancelled before completion; its partial trace is archived and is not counted as a pass.
- Require complete routing and 50 MHz timing before any stopped SRAM validation.

Independent Sol review found no other actionable defect in the examined fallback arithmetic, RC/manual selection, mode gating or live-stop paths. This is scoped evidence, not proof that the whole flight controller is free of defects. The earlier loaded-power-loss event remains unresolved and is not explained by these findings.

## Independent completion checks

- A second read-only Sol review accepted the source-bound diagnostic-bank substitution argument. It explicitly does not claim that the cancelled current-context full-top simulation completed. This is an algebraic source argument with recorded tests, not whole-design formal or sequential mapped equivalence.
- A separate read-only Sol review checked the build gates: source/proof hashes, exact audited mapped-netlist identity, complete routing, actual clk50 Fmax and setup/hold, all 17 physical pins and B0B0 UserCode.
- The SDC declares only clk50 at 20.000 ns, with no false-path or multicycle exceptions. Timing acceptance covers the constrained internal clock paths; external input/output delays are not specified.
- Root launched the full SYN+PNR at 2026-10-23T11:19:45Z, owned process 31048, session 65809. Actual VG/log/cmd.do creation times were checked after this start; final reports and image still require the completion gates.
- Read-only telemetry during compilation reports B0AC, disarmed, four reported PWM values of 1000 us. The programmer currently enumerates as serial 6 / COM20, so the previous serial 5 binding must be re-identified before a later SRAM installation. No programming has occurred in this review.

## MTF diagnostic bank and actual full synthesis

`variants/mtf_diag_reset_p2_r2_rep1` preserves the repaired control RTL exactly. It adds a default-off startup-only reset option for the MTF 976-bit telemetry bank and opts in only the actual single-release boot caller. The original initializer, capture predicate, payload and generic repeated-reset behavior are preserved. An isolated 50,000-cycle test plus source-level induction and independent review passed.

Actual full SYN was separately audited: NAV720 exact BDD and vendor-primitive INIT/label simulation; MTF976 INIT, payload, CE, inactive reset ports and mapped boot transitions; freshness and all 34 PWM inputs/four physical outputs. All passed. MTF has 827 physical bank FFs; storage was retained. Its reset pins are inactive rather than connected to the global reset.

The preliminary and full SYN streams differed by internal identifiers, including user-module port names. Original preliminary evidence was archived before re-auditing the actual full stream. A separately reviewed structural comparison accounts for all 287 renamed declared identifiers with consistent caller/callee bijections; all 3,779,777 tokens otherwise match. Top pins, cell types, vendor pins, widths, constants, INITs and topology remain exact. This diagnostic does not replace actual-full mapped audits or relax the canonical release gate.

Full PNR still failed with 436 unrouted nets, CLS 26269/29952, registers 28466. No FS or timing qualification exists. The next experiments reuse that exact audited VG and change only physical routing configuration.

Further PID-divider reset removal was explicitly rejected: the two actual engines use dynamic enable/fault resets. Their 532 FFs include 340 nonconstant reset pins, and removing reset would break transaction cancellation on stop/fault. No such code change was made.

## Routing-only dependency correction

The two copied-RTL-project trials (`mtf_diag_reuse_p2_r2_rep0`, `mtf_diag_reuse_p3_r2_rep1`) aborted after Gowin implicitly started synthesis. No routing result or image exists; the audited VG remained unchanged. Metadata/log changes are preserved as rejected evidence. Official installed Tcl documentation supports an explicit netlist-only input. An isolated project-creation probe recognized exactly VG/CST/SDC, with no run command. New trials will use that flow and retain exact-netlist, no-synthesis, timing, device and pin gates.

## Additional inactive generic telemetry issue

The isolated INFO snapshot-equivalence matrix exposed a pre-existing optional serializer case: RANGE_DIAGNOSTICS=1 together with FLIGHT_INFO=1 and later MTF/NAV/rotation packets can retain sending_range and loop into INFO at index47. This is not introduced by the INFO proposal. The actual N top explicitly sets RANGE_DIAGNOSTICS(0), so this case is excluded from the current mapped circuit. It is recorded separately; no current candidate or active routing input was changed. Broad-case timeout evidence is not counted as a completed-frame PASS.

## INFO duplicate snapshot contingency

`variants/info_snapshot_p2_r2_rep1` is separately qualified for offline context only. The sole RTL change is a default-off appended INFO_CALLER_SNAPSHOT parameter plus opt-in at the existing held caller. The original caller register and hold/state/serializer/CRC logic remain. Current control sources are byte-identical to N. Three actual-top frames with the unchanged real UART passed cycle/byte/sequence/CRC comparisons; finite test scope separates 12 completing configurations from 11 prefix-only configurations with pre-existing generic serializer limitations. No new full-top dynamic simulation is claimed.

Actual synthesis removed 225 duplicate FFs (27829 to27604) with 3 extra LUTs, unchanged ALU/BSRAM counts. The219 own caller FFs and6 shared core FFs remain. Independent mapped audit covers272 INFO bits, INIT/pin cones and payload substitution during the legal held serialization window. Current NAV720/MTF976/freshness audits and vendor NAV primitive probe pass on the same aa2de0222dc404ae2326da2d068fc079833296dece1b726f1af0b10f5bb9f941 VG. Aggregate1968 and qualification32 evidence files explicitly retain original N34/C128 proof scopes and current_full_top_simulation_passed=false.

Two N netlist-only fan23 trials failed: p2/r2/rep0 with221 unrouted nets, and p3/r2/rep1 with186. Neither produced FS or timing acceptance. Two Nfan32 trials and four INFO trials remain in progress. No accepted B0B0 bitstream, SRAM installation, receiver switch or Flash change has occurred in this phase.
