# v7 AW storage-width candidate binding addendum

Reviewed 2026-10-26T08:32:27.280813+00:00. This adds the actual candidate binding and read-only diff review to `aw_storage_width_independent_review.md`; that earlier proof document is unchanged (SHA256 `3bbdfc3c0430df0507a291d20f2d70870ec1450ad94afafd68c53d90da2ebbcd`). **No source-level counterexample or out-of-scope source edit found.** This is not a simulation, synthesis, PNR, hardware, flight, or delivery PASS.

Candidate: `out/z_aw_fix_20261026/compact_aw_v7/canonical/source/position/mtf_xyz_hold_control.v`

- v5 hold SHA256: `04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873`
- v7 hold SHA256: `2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad`
- v5 full55 map fingerprint: `f41a3926752b07df5fb1b363bf4c896f521f3110a34a9ac9f86f16559ac48813`
- v7 full55 map fingerprint: `ae751d0dc62bbe5071098a9f8b473492bbac29318a799ba5a2004ed575a9dbe0`
- Candidate source-freeze JSON SHA256: `bf2f7d0765d53f06207a786afaee99cc3cdf673e1d05f38bd51fa11d9e9a1113`

Independent enumeration found 55 files in each canonical tree, the same path set, exactly one changed path (the hold), and all other54 byte-identical to v5. In particular the navigation wrapper is still v5 `5b46a541df7a4e99a8de3745e0360b0ffa7a7e0b05834452a9406ef7c2b2d3db` and shared height-fusion is still v5 `1205c8f88198e527ac9f272f829e1e58d996b61db8e9a67d6af865e19e320cf7`; the v6 numeric guard is not adopted. Actual full55 maps match source_freeze.json and are unchanged after review.

The entire v7 hold was independently reconstructed from v5 using precisely 15 reviewed text substitutions and compared equal. They consist of IZ33→27, bias33→26, candidateI27/P+bias29/candidate-total30/current-total30 aliases with explicit correct 64-bit sign extension, compact-sum31→30 and its state66 sign-extended writer, plus the matching width comment. Every other character is unchanged.

The actual sign extension counts are 37+27=64 for IZ/candidateI, 38+26=64 for bias, 35+29=64 for P+bias, and 34+30=64 for each total and the reused writer. The adder `p_bias+candidate_iz` remains signed64 before retaining30 bits. Retaining low bits of already-proven fitting signed values preserves their exact value.

Both rails remain signed64; exz_store31, sample_vx_store31 and inner_alt_speed64 remain intact, including original 64-bit exz/sample_vx consumers in their early lifetimes. State53 still captures original full rails, state22 consumes them before candidate overwrite; state23 still uses complete exz to compute P; state24 writes the fitting P+bias; state66 writes fitting totals; state67 consumes them. The private low27 candidate alias can differ while iz_lower_q contains the earlier lower rail, and the other private aliases can differ before their write-qualified phases. No public output or math operand reads those aliases in such phases. All state transitions, assignments other than the explicit state66 representation writer, flags, taking_off tests, reset/cancel priority and publish timing are otherwise unchanged.

The reset-reachable intervals, arbitrary taking_off flips at22/23/66/67, old/new bounded bias distinction, rail noncontact, and cancellation arguments in the first document therefore apply to this exact candidate. Scope remains legal accepted interfaces with the real correct math service, not forced private out-of-range state. Root-owned actual-RTL equivalence/top/boundary/contention tests and any later physical gates remain separate required evidence; no area or timing gain is inferred from width counts.

Only this new addendum was written by this review. Original v5/v7 sources, source-freeze JSON, prior P1 independent reports and old evidence archives were read without modification. No builds, process control, PNR access, source edits, Git, hardware, serial or flight actions were performed.
