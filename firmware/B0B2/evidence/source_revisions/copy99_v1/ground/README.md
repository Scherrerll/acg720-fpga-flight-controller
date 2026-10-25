# B0B2 SiK diagnostic receiver

B0B2 transmits passive telemetry at 115200 baud on SiK; USB mirrors exactly the same stream. There is no B0B2 921600-baud/A584 mode. The original A579–A583 frames retain their layouts. The additional A585 v1/type1 frame carries 64 bytes of diagnostic payload in a 76-byte CRC frame at 5 Hz. The complete group is 644 bytes.

The strict decoder is [protocol.py](protocol.py); the exact field table, timing, publication-gap meaning and distinction between first diagnostic anomaly and first actual protection are in [SIK_DIAGNOSTIC_PROTOCOL.md](../SIK_DIAGNOSTIC_PROTOCOL.md).

Prepare a separate receiver without touching the frozen ground/B0B0 tree:

```powershell
python -B firmware/B0B2/tools/prepare_sik_receiver.py --output out/B0B2/sik_receiver
```

This preparation never opens a serial port and refuses to overwrite an existing receiver directory. Its `B0B2_PREPARATION_RECEIPT.json` records source/output file hashes, generator hash and the complete patch. The generated directory contains the existing read-only ground_server.py, recorder, old decoders and tests, plus a copy of the A585 decoder. The server defaults to SiK/115200 and its inherited configurable COM port; select the actual telemetry port when a separate hardware session is authorized. Do not use the programmer interface as a telemetry port.

Decoded A585 rows appear as `_protocol: "a585"` in telemetry.jsonl, with the original receive timestamp, stream order and epoch. Raw serial bytes still go to raw.bin. The dashboard snapshot adds `imu_diagnostic` and `imu_diagnostic_fresh`; these do not replace primary data, accepted counts or controller readiness. Freshness requires a current connected A585 report, fresh compatible A580 identity and matching uptime context. Disconnect, source switch and firmware uptime rollback invalidate freshness.

Run all offline communication proofs:

```powershell
python -B firmware/B0B2/tests/run_sik_tests.py
```

The suite uses FPGA simulation and mock byte input only, samples the actual 115200 UART wire, compares all legacy bytes to the frozen sender, verifies CRC and parser resynchronization, and verifies both raw and decoded disk recording. It does not access a serial port, programmer, motors or an FPGA. No hardware actions have been taken by preparing these files.
