# v7 AW storage-width independent review

Reviewed 2026-10-26T08:29:18.730743+00:00. **No mathematical or lifetime counterexample found in the proposed width changes under the reset-reachable scope below.** This is a source-level feasibility review against exact v5 hold SHA256 `04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873` and `sign_step_bound.md` SHA256 `cf2a9de051973862c68cd2d462678cf6436756c3a65cc4ef2c4f16f933de9c0d`. Candidate v7 source is not yet bound by this document: no candidate hash, simulation pass, synthesis result, timing result, or delivery qualification is claimed. A separate addendum must bind and inspect the actual candidate diff.

## Exact integer bounds

Q=65536. Division is nearest, ties away from zero, matching the real position_divide service. Initial/reset/global-cancel I and bias are zero. The existing sign-step lemma gives committed I in [-350Q,850Q], bias in [0,350Q], and absolute integral step at most 72090 Q16 integers. Its strict bounds are used, not decimal 1.1 approximations.

| Quantity | Conservative exact interval | Proposed signed width | Representable interval |
|---|---:|---:|---:|
| Committed IZ | [-22937600,55705600] | 27 | [-67108864,67108863] |
| Candidate IZ | [-23009690,55777690] | 27 | [-67108864,67108863] |
| Bias | [0,22937600] | 26 | [-33554432,33554431] |
| RN(exz_store/5) | [-214748365,214748365] | unchanged math | derived from signed31 exz |
| P + bias | [-214748365,237685965] | 29 | [-268435456,268435455] |
| P + bias + candidate I | [-237758055,293463655] | 30 | [-536870912,536870911] |
| P + bias + old I | [-237685965,293391565] | 30 | [-536870912,536870911] |

For the P bound the full type range of exz_store is used: [-1073741824,1073741823], so RN division by five has absolute value at most 214748365, independent of the tighter normal sensor range. Both source arithmetic operands must remain signed64 aliases; the proposal retains a 64-bit sum before explicitly retaining and sign-extending the proven low bits.

The original rails are captured at state53 as ±(131072000-biasOld). Their smallest absolute magnitude is 108134400. Candidate [-23009690,55777690] is strictly inside both rails, so the old clip cannot change the candidate or its direction. Rails must stay signed64.

## Write/read lifetimes checked in exact v5

| Representation | Definition/writes | Qualified consumers | Required preservation |
|---|---|---|---|
| iz_store / signed64 iz | initial0; reset/cancel0; state67 selected I or0 | state22 z_shared_sum and taking_off=false flags; state66 current sum; state67 reject fallback; z_add_rhs at22 | Change storage to27 and sign-extend bit26 to64; all committed values fit. No other I writer exists. |
| bias_store / signed64 bias | initial0; reset/cancel0; tracking entry0; state23 relaxation or0 | state53 original rails; state22 bias-relaxation calc; state23 shared sum; state24 P+bias | Change storage to26 and sign-extend bit25 to64; RN relaxation cannot overshoot [0,350Q], even if taking_off changes. |
| candidate_iz from iz_lower_q | state53 holds original lower rail; state22 replaces it with full64 candidate | state66 candidate sum; state67 candidate/reject selection | Lower27 alias is allowed to differ before the state22 nonblocking write. iz_lower_q itself stays64 so state22 still sees the old complete rail. |
| p_bias from exz_store | state21/state53 hold error; state24 replaces it with P+bias | state66 candidate/current sums | Low29 alias may differ while exz still holds error. The original exz_store31 and signed64 exz alias must stay for state53 and state23 calc(exz,1,5,24). After24 the P+bias interval fits29. |
| candidate_collective from inner_alt_speed | state0 captures alt_speed, consumed by state21 calc; state66 writes candidate total | state67 rejection and selected collective | inner_alt_speed itself stays64. Low30 alias may differ before66; state21 still uses full64 speed. The writer must sign-extend compact_sum30 bit29 to64. |
| current_collective from sample_vx_store | state0 captures Z velocity or XY velocity; state66 writes P+bias+oldI | state67 selected fallback collective | sample_vx_store itself stays31 and its original signed64 sample_vx stays for Z21 and XY30/34–38. Only the private current alias becomes low30. |
| compact candidate sum | Continuous signed64 p_bias+candidate_iz | state66 writes reused inner_alt_speed | Retain full64 expression then take low30 and sign-extend; do not change shared math, rails, or earlier lifetimes. |

Source search found no public consumer of the four private candidate/current aliases before their write-qualified uses. Their continuous reject/selected wires can differ outside that lifetime, but public outputs and math request operands must not: selected values are sampled only at67, after22/24/66 have completed. state66 reads old candidate/P and writes both totals; state67 reads the resulting nonblocking updates.

## Taking-off transitions and cancellation

The proof does not assume taking_off is constant within a callback. At22 true proposes I+d and captures value>0/<0; false proposes0 and captures oldI<0/>0. Bias23 independently relaxes or clears, always remaining bounded. The candidate sign flags and I are unchanged from22 to67 unless reset/cancel/origin/blocked aborts the entire operation. A false67 forces I and collective0; a true67 selects candidate or old I, both bounded. Flips at22/23/66/67 therefore do not break the width bounds.

Reset/cancel/origin/blocked branches precede the state case, clear I/bias/rails/flags, and return state0. A Z transaction sets work_xy0, so the XY partial-callback rollback path cannot interleave an I update between22 and67. Math error marks blocked and exits; the next cancellation clears state rather than committing a stale candidate. Pending input updates queue or block; they do not write these reused storage locations mid-transaction.

## Scope and candidate requirements

This covers initial/reset-reachable exact-v5 behavior, both supported velocity formats, accepted legal interfaces and the real correct math service. It does not cover force of private registers outside reachable bounds or fabricated asynchronous math results. No v6 guard, timing exception, arithmetic sequencing change, clock reduction, gain-bank change, or other54-file change is part of this proposal.

Actual v7 must retain rails64, exz_store31, sample_vx_store31, inner_alt_speed64; preserve all signed64 arithmetic aliases and original assignment ordering; change only the hold file relative to frozen v5; and show public equivalence even where pre-qualified private aliases differ. This document performed no build, test rerun, source mutation, process control, PNR access, Git, serial, hardware programming, or flight action. The P1 independent review and existing archives were not edited.
