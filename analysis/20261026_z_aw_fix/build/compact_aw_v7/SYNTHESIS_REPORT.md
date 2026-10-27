# compact_aw_v7 existing SYN_ONLY result

The one fresh v7 full-top map2/replicate0 SYN_ONLY completed normally. Elaboration, vendor synthesis and the supervised runner each returned actual `p.wait()=0`. The vendor finished at 2026-10-26 08:36:16 UTC and the runner at 08:36:21 UTC. Original mapped clock/radio, strict every-FF clk50, live 16-bit P/I with INIT 1000/350, and 18 scalar top-port audits all passed. Original B4 source55, v5 canonical source55 and v7 canonical source55 were checked unchanged by the runner. No PNR was launched; this result provides no route/Fmax/50MHz qualification.

The source is `out/z_aw_fix_20261026/compact_aw_v7/canonical/source`, forked directly from v5. Only `position/mtf_xyz_hold_control.v` differs, SHA256 `2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad`; the other 54 inputs match v5. The independent source/math review found no blocking counterexample. Fresh actual RTL qualification remains in the root-owned v7 regression records.

| Actual map2 resources | v5 baseline | v7 | Delta |
|---|---:|---:|---:|
| Top registers | 27725 | 27704 | -21 |
| Top ALU | 9461 | 9458 | -3 |
| Top LUT | 36150 | 36079 | -71 |
| Controller registers | 3241 | 3220 | -21 |
| Controller ALU | 1478 | 1475 | -3 |
| Controller LUT | 4910 | 4852 | -58 |
| Parameters registers | 290 | 290 | 0 |
| Parameters ALU | 79 | 79 | 0 |
| Parameters LUT | 433 | 438 | +5 |

DSP categories and BRAM are unchanged. These are actual synthesis resources against v5; no physical savings or timing improvement is inferred.

Netlist SHA256: `dc20d15cec4471df8679960fb05660349caaa19dfaee40604b419ca6450cf0e0`. Candidate resource XML SHA256: `22fa45e791e3811375667456c14ea90eb378208532bc420a31914ff611644aac`. Source freeze SHA256: `bf2f7d0765d53f06207a786afaee99cc3cdf673e1d05f38bd51fa11d9e9a1113`. Executed runner SHA256: `f56dc7a472e16a3f8fbf9b34772653a4a06b5f26e37b207b3ebe284fc7da899a`; original helper remains `abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84`.

Raw source/input/vendor logs, actual wait receipts, original audits, resource comparison and final artifact manifest are under `out/z_aw_fix_20261026/compact_aw_v7/build_attempt_01/`. The final manifest SHA256 is `023f956a9a7d1e5d5c70230c108476fd99faf52e4a742db868d488b7cf5e8d51`. Hidden supervisor/runner logs and runner actual wait receipt are alongside this report. The previously observed process chain was supervisor31448 -> runner5888 -> vendor64404; its normal completion is established by both exit receipts, not process disappearance. Latest user direction is to archive and plan before confirmation; no new implementation, test, PNR or chat is started after that direction.
