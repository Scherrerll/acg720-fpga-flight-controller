# B0B2 SiK diagnostic receiver

Active policy v3 uses A586/A587/A588-v5/A589-v2 aliases and A585-v3, with explicit unavailable pose-age fields. The group remains 644 bytes; no deleted age is interpreted as zero/fresh. A581-v3 separates the 1s online indicator from 200ms metric validity and 100ms control freshness. The receiver continues to decode historical formats. See [POLICY_V3.md](../POLICY_V3.md). The v1/v2 description below is historical.

B0B2 transmits passive telemetry at 115200 baud on SiK; USB mirrors exactly the same stream. There is no B0B2 921600-baud/A584 mode. The original A579–A583 frames retain their layouts. The additional A585 v2/type1 frame carries 64 bytes of diagnostic payload in a 76-byte CRC frame at 5 Hz. The complete group is 644 bytes. The decoder also strictly supports historical v1/type1; unknown versions/types are rejected.

The strict decoder is [protocol.py](protocol.py); the exact field table, timing, publication-gap meaning and distinction between first diagnostic anomaly and first actual protection are in [SIK_DIAGNOSTIC_PROTOCOL.md](../SIK_DIAGNOSTIC_PROTOCOL.md).

Prepare a separate receiver without touching the frozen ground/B0B0 tree:

```powershell
python -B firmware/B0B2/tools/prepare_sik_receiver.py --output out/B0B2/sik_receiver_v3
```

This preparation never opens a serial port and refuses to overwrite an existing receiver directory. Its `B0B2_PREPARATION_RECEIPT.json` records source/output file hashes, generator hash and the complete patch. The generated directory contains the existing read-only ground_server.py, recorder, old decoders and tests, plus a copy of the A585 decoder. The server defaults to SiK/115200 and its inherited configurable COM port; select the actual telemetry port when a separate hardware session is authorized. Do not use the programmer interface as a telemetry port.

Decoded A585 rows appear as `_protocol: "a585"` in telemetry.jsonl, with the original receive timestamp, stream order and epoch. Raw serial bytes still go to raw.bin. The dashboard snapshot adds `imu_diagnostic` and `imu_diagnostic_fresh`; these do not replace primary data, accepted counts or controller readiness. Freshness requires a current connected A585 report, fresh compatible A580 identity and matching uptime context. Disconnect, source switch and firmware uptime rollback invalidate freshness.

V2 preserves the wire length, CRC and remaining field meanings, but gives up the retained rejected source ID and exact first-protection time. Payload bytes 24..27 and 52..55 must be zero; valid frames decode `latest_rejected_source_id` and `first_protection_time_ms_low32` to `null`. Nonzero slots are rejected even with a valid CRC. Every decoded row provides per-payload-field `capabilities` plus `unavailable_fields`, so null is never interpreted as ID zero, time zero or no fault. Latest reader/detail/flags, consumed ID, held dt, global gap, first diagnostic and first protection reason/pose age remain available. A579 rejected-count increments still identify new rejects; they cannot identify individual rejected source IDs. Once A580's latest-event register is overwritten, v2 cannot reconstruct the earlier first protection's exact time from snapshot ticks.

Run all offline communication proofs:

```powershell
python -B firmware/B0B2/tests/run_sik_tests.py
```

The suite uses FPGA simulation and mock byte input only, samples the actual 115200 UART wire, compares all legacy bytes to the frozen sender, verifies CRC and parser resynchronization, and verifies both raw and decoded disk recording. It does not access a serial port, programmer, motors or an FPGA. No hardware actions have been taken by preparing these files.

Evaluate a deliberately selected recorded bench interval separately; replace the example paths and UTC window and choose a new output file:

```powershell
python -B firmware/B0B2/tools/analyze_bench.py --input C:/bench-capture/telemetry.jsonl --start-utc 2026-10-25T02:00:00Z --end-utc 2026-10-25T02:01:10Z --stable-after-s 5 --output C:/bench-capture/new-evaluation.json
```

This requires at least 60 seconds after the selected settling trim. It checks complete raw protocol groups, strict v1/v2 capabilities, counter progress, age/gap/dt, flags, newly observed faults versus retained first causes, and reported stopped RC/PWM state. Stable total pose/accepted increments must agree within 1% after a two-sample endpoint allowance; this is an offline screening threshold, not an assumed sample rate or changed hardware protection. CH3/CH5/CH7 must each be 800..1100 and all eight command/physical widths 1000 us. A580 event pose age is retained history; live ages come from A579/A57A. Incomplete evidence or an old excessive global maximum cannot produce an acceptable interval. The log and tool SHA256 are recorded; output files cannot be overwritten. Decoded JSONL cannot establish CRC/noise/drop counts, so those remain unknown. PWM values are reported schedules, not independent waveform measurements; `flight_ready` always remains false.
