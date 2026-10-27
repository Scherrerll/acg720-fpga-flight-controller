# compact_aw_v7 bounded Z storage review

This candidate forks the frozen v5 hold `04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873`; the other 54 build inputs stay byte-identical. It changes only Z I/bias storage and qualified lifetime aliases. It retains signed64 expressions, both original signed64 rails, `exz_store` signed31, `sample_vx_store` signed31, `inner_alt_speed` signed64, all states, the two AW clocks, gains, policy, public interfaces and cancellation ordering. No numeric-guard v6 source is used.

## Bounds checked before editing

The real `position_divide` rounds nearest, ties away from zero. With Q=65536, the previously reviewed reset-reachable invariant is I in [-350Q,850Q]=[-22937600,55705600], bias in [0,350Q]=[0,22937600], and |d|<=RN(1000Q*11/10000)=72090. The sign-step proof in `../sign_step_bound.md` uses the same error for P and d. Its legal-input error bound fits signed31, so state53's stored error and math argument agree without truncation. The actual divider's rounding preserves sign. No unresolved counterexample was found.

The invariant does not assume taking_off is constant during a callback. State22 selects I+d when taking_off, or zero otherwise, and captures that selection's direction. State23 independently relaxes bounded bias toward 350Q, or clears it. State67 either keeps old I or accepts the candidate, and independently forces zero when taking_off is false. If I+d exceeds 850Q, d and P are positive so total exceeds the upper output rail and the candidate is rejected; if I+d is below -350Q, d and P are negative and total is below zero so it is rejected. The old original candidate rail has magnitude at least 1650Q=108134400, greater than the entire raw candidate interval; it does not truncate valid candidate I. Reset/cancel/origin/blocked clear I/bias/candidate rails and return state to zero; !tracking clears bias. XY rollback only changes XY state. A height update queues or blocks; it does not change I before state67.

For narrowing, a deliberately broader bound than legal e is enough: any signed31 error has |RN(e/5)|<=214748365. Therefore:

| Qualified value | Inclusive Q16 interval | Storage |
|---|---:|---:|
| committed I | [-22937600,55705600] | signed27 |
| candidate I | [-23009690,55777690], or 0 | signed27 |
| bias | [0,22937600] | signed26 |
| P+bias | [-214748365,237685965] | signed29 |
| P+bias+candidate I | [-237758055,293463655] | signed30 |
| P+bias+old I | [-237685965,293391565] | signed30 |

Each interval fits the named signed width. The candidate total keeps the existing full signed64 addition, then retains 30 exact bits and explicitly sign-extends 34 bits into unchanged signed64 `inner_alt_speed`. This does not narrow the adder's RTL expression.

## All references and use lifetimes

Full-source reference review: `iz_store` is initialized/reset/cancelled to zero and otherwise written only at67; all `iz` reads occur through its signed64 alias. `bias_store` is initialized/reset/cancelled/!tracking-cleared and otherwise written only at23; all `bias` reads use its signed64 alias, including original rails at53 and relaxation at22. These two aliases remain equal every cycle for reset-reachable histories.

`candidate_iz` reads the reused lower rail: state53 writes the original signed64 rail, state22 consumes that original rail and overwrites it with candidate I. The narrowed candidate alias is used in the sum at66 and selection at67, after22. `p_bias` reads reused `exz_store`: states21/53 hold errors, state23 consumes error for P, state24 writes P+bias; the narrowed alias is used only at66 and indirectly at67 after24. `candidate_collective` reads reused `inner_alt_speed`: state0 captures alt_speed for state21's calculation, while66 overwrites it with candidate total. `current_collective` reads reused `sample_vx_store`: state0 records sensor velocity for Z/XY calculations, while66 overwrites it with current total. These narrowed collective aliases are consumed by rejection/selection at67 after66. Their combinational values outside qualified lifetimes may differ from v5, but cannot reach any public output or math request. Cancellation exits the old transaction before any stale lifetime is consumed.

`iz_lower_q`/`iz_upper_q` remain signed64 because they first hold the original rails. `exz_store` remains signed31 because it first holds signed31 error; `sample_vx_store` remains signed31 for Z/XY sensor use; `inner_alt_speed` remains signed64 for its earlier altitude-speed lifetime. No other source file changes. Root owns fresh actual-RTL AW/boundary/top/contention regressions; this note does not claim they have passed. One fresh full-top map2/replicate0 SYN_ONLY may follow source audit. Actual mapped resources must be compared with v5, without any timing, area-saving, PNR or 50MHz qualification promise.
