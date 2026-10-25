# Saved integral idle enable candidate

Status: source proof, actual-controller public-cycle proof, unchanged numerical/safety/contention suites and one real synthesis PASS. Measured CE redistribution is realized. Frozen backup candidate; not selected or promoted. No PNR, programming or hardware access. No packed-CLS, unrouted-count improvement or50MHz closure claim.

Only `position/mtf_xyz_hold_control.v` changes relative to immutable `../idle_gain_ce/source` (controller9bb8eae57f9491d8e187ac4d5e5868666714920cb91f17e6423daae95618bad9). Both `saved_ix<=ix_store;saved_iy<=iy_store;` assignments move from XY callback admission into the already accepted independent state0 sampler. Signed27-bit declarations/INIT0, savedAFX/AFY admission capture, all liveI/reset/cancel/rollback/math statements, every state and public interface remain unchanged. The other54of55source files are byte-identical. The exact edit and reversible raw-byte assertion are in `candidate.diff` and `prepare_candidate.py`. No changing canonical source was used as a baseline.

## Semantic boundary and proof

`SOURCE_PROOF.md` was written before editing. SavedI has one declaration/INIT, one paired capture and one paired read at XY rollback. Both designs capture the same liveI pair on the same admission edge; subsequent nonzero states freeze it until a possible rollback. Reset/global cancel/blocked have priority and never read savedI. On the divider-error state0/work_xy1 transient, old blocked1 selects the global clear before a saved read. Z never consumes savedI. The new private saved pair can change on idle/reset/Z admission edges, including sampling pre-clear liveI on an idle reset edge. It is intentionally excluded from idle private-register equivalence; every later real rollback has a fresh admission snapshot. No published output or current telemetry/debug port exposes idle savedI.

`verify_cycle_pair.py` compares all450public output bits, including math requests/cancels/operands and parameter_boundary, against BOTH actual immutable response_compact and immediate frozen idle_gain_ce controllers. Only comparator module names are changed; each controller uses actual shared multiply/divide services. There is no forced private state. Original956,519cycle directed/random stimulus and gain active-work assertions are retained, including arbitrary16-bit gain corners/high bits/mid-work changes, XY/Z priority, resets, cancellation/drain, public divider fault, age and mode changes. Additional checks assert savedI same-edge capture, active equality/freeze and exact same-edge restoration.

Final proof:1,002,843total clocks,92savedI admission captures,557,291nonidle savedI freeze checks,4actual savedI rollbacks including2changed/nonzero partialI rollbacks. The two added targeted cases trigger CH7 cancellation at state65 (X updated) and state17 (both axes updated before publication); the registered xy_cancel causes the actual restore edge later, checked directly by restore_edge. Private idle savedI differed416,516cycles without public mismatch. The first attempt passed the original956,519cycles against both references but its new partialI coverage count was0; the original assertions/stimulus were retained and the two cases were appended. The failed coverage receipt/log/harness are preserved. No RTL changed after preparation. Simulation complements the source induction; it is not exhaustive16-bit enumeration or a formal solver proof.

The original numerical suite was reused with path-only adaptation and passed all five groups: defaultP005/I0 reference, V15P015/I010, nondefault P, nonzero I/both rails, mode/reset/cancellation/coherent-pair behavior and maximum legal P clipping. Maximum isolated XY latency remains5082clocks=101.64us. Top safety passed all13cases. The existing top test's simulation forces are retained there; none occurs in the new controller-cycle proof. Four-client contention passed12XY/20Z callbacks with maximum XY request-to-publish17792clocks=355.84us, XY work13737clocks=274.74us and Z12554clocks=251.08us. All child p.wait receipts are0, original TB/assertion/function ASTs are unchanged and fixed baselines/source hashes were rechecked. Aggregate receipts and all stable evidence hashes are under `verification/regressions/`; the inherited regression scope label mentions idle_gain_ce, while the exact55source hash map and every actual source path bind this new candidate unambiguously.

## Actual mapped result

Exactly one `run syn` used an EOF Tcl with no explicit exit, stdinDEVNULL and CREATE_NO_WINDOW. `SYNTHESIS_COMMAND_RETURNED_EOF` was observed and actual p.wait() returned0. Both functional-proof gates passed before launch. The synthesis runner, tool, Tcl and proof-input hashes are bound in `verification/synthesis_input.json`; actual normal exit is in `verification/synthesis_exit.json`. No process intervention or automatic rerun occurred.

| XML top resource | Frozen gain CE | SavedI idle CE | Delta |
|---|---:|---:|---:|
| Registers | 27764 | 27765 | +1 |
| LUT | 36020 | 36040 | +20 |
| ALU | 9564 | 9564 | +0 |
| MULTALU27X18 | 30 | 30 | +0 |
| MULT12X12 | 7 | 7 | +0 |
| MULT27X36 | 13 | 13 | +0 |
| BSRAM | 2 | 2 | +0 |

The single extra mapped FF is identified exactly: `native_navigation/position` has408 to409direct FF. New `state_3_s1`, Q=`state_3_8`, duplicates existing `state_3_s0`, Q=`state[3]`; both have D=`n3456_35`, CLK=`clk50_d`, RESET=`n9819_5`, CE=`VCC` and the same default0 INIT. The position RTL file is byte-identical. `verification/register_delta_explanation.json` binds both actual rows/netlist hashes. This is a synthesis duplicate of an existing state bit; there is no added RTL state/register. Controller direct FF remains2314 and its XML total remains3280. Other hierarchy LUT mapping also changes, so controller LUT savings are not equated with a total-area saving.

The actual callback snapshot net `n55194_3` has183CE loads in the baseline; candidate `n54330_3` has129CE loads and129total direct input loads. SavedAFX/AFY remain on this net. Candidate idle net `n16252_13` has86CE loads (workP/I32 + savedIX/IY54), and146total loads including existing LUT inputs. Its actual LUT cone is evaluated over all128mapped state-bit combinations: CE iff state[6:0]==0. Both gain pairs remain16bits; live/savedI remain27bits. Controller direct mapped FF count:2314 to 2314.

The installed P005 VG has no live/savedI FF, a129load callback snapshot enable and403direct loads on the controller clear qualifier (394RESET+6SET+3LUT). Frozen gain CE has54liveI and54savedI FF and458clear loads (449RESET+6SET+3LUT); this refactor moves savedI CE only and does not remove liveI reset obligations. UG303-1.0E (printed26-27, PDF34-35) says the two FFs in a CLS require matching clock/CE/reset controls and permits compatible synchronous set/reset types; moving into the existing idle class is a credible control-distribution experiment. This does not identify failed physical routes or prove a packed-area saving.

Mapped audits passed all27867clock pins (clk50 or ground), identical physical top ports, all32bank-to-work gain connections, full stored widths, raw radio pad loads only at first-stage synchronizer D pins and metaQ loads only at the second stage. The unchanged sole radio_rx false path therefore retains its first-stage boundary. Downstream paths remain timed. These structural facts do not replace PNR/STA.

Controller SHA256:`b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6`. VG SHA256:`4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb`. `freeze_manifest.json` binds all source/proof/driver/netlist/resource/audit artifacts and the exact frozen donor manifest. Root must separately select any diagnostic physical evaluation.
