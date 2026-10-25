# B0B2 A585 v2 projected regression proof

This archive preserves small, portable v2 projection/wire proof artifacts; no VG/VVP/DB or hardware acceptance is included. Current source was compiled directly by the formal runners. The exact archived copy99/v1 reference SHA is7783baba34cc7cdc014d17f38e9e0d5f52210e1d8b02bde49a5f308d8ee3160e. Its only replay transformation is the reference module name (reference_renamed.v).

The current v2 summary intentionally loses latest_rejected_source_id (bits319:288) and first_protection_time_ms_low32 (95:64), fixed0/unavailable. It is not full protocol/diagnostic equivalence. All448 retained summary bits and32-bit tick are compared every clock after NBA, both excluded slots asserted0 every clock. The actual tap's held-body prerequisite is asserted; reset, same-cycle raw/pose, rejection, hold, new-window and same-edge event coverage thresholds remain.

Actual formal run:120000-cycle PASS; raw_pose_same14358, rejects29979, held_updates38664, hold rise/fall28697/28696, max no-pose7001, reset clocks11. Window rises121, held-window62, qualifying event+new-window same-edge11. projection_result.json binds current53 source hashes, old/tap/candidate/TB/runner/tools/logs. Its absolute output/tool paths are original provenance, not requirements for replay.

Portable projection replay from this directory, using your Icarus paths, writes only to a NEW scratch output:

    iverilog -g2012 -s sik_copy_contract_tb -o <scratch>/projection.vvp reference_renamed.v candidate_v2.v actual_tap.v sik_copy_contract_tb.v
    vvp <scratch>/projection.vvp

Repository replay (both runners reject existing output directories):

    python -B firmware/B0B2/tests/run_sik_copy_tests.py --output out/B0B2/NEW_PROJECTION
    python -B firmware/B0B2/tests/run_sik_tests.py --output out/B0B2/NEW_SIK

The archived runner copies are provenance; repository invocation uses their normal firmware/tests location. Set IVERILOG/VVP if needed on another system.

Actual SiK run: summary/window/hold assertions PASS;434-clock real UART sampling,644 bytes, header version2/type1, both unavailable slots0, all CRC/XOR valid and original568 bytes equal manifest-verified frozen B0B0 golden.18 decoder/receiver/recorder tests and full-top elaboration PASS. SIK_WIRE_FIXTURE explicitly selected this NEW run's v2 wire fixture, not old v1 output. sik_step logs, result and both wire hex files are preserved. This is not a physical timing/flight proof.

Formal synthesis is separately identified: VG7e0a3dcea65355fcd4233edebf9ac3f37727a0647df3366dea6054b57710cd74 differs from the shadow VGe1984437f3b6cbf28a092dd5b59ee594fe20b19b6f14e27439284268df34415a. Both resource XML totals match27460FF/35735LUT/9237ALU, DSP30/7/13 andBSRAM2. formal_shadow_binding.json confirms exact53 source hashes and preserves distinct VG identity; it does not claim whole-netlist equivalence or physical acceptance. Official PNR/STA remains a separate root-owned operation.

No hardware, serial port, programmer, state API, SRAM or Flash access was performed by these tests or this archive step.
