# B0B2 SiK IMU diagnostic protocol v2, with strict v1 decoding

B0B2 uses one passive 115200-baud, 8N1 telemetry stream. USB mirrors the identical SiK signal. There is no B0B2 high-rate USB sender, A584 queue, or selectable USB profile. The B0B1 high-rate project and its isolated FF experiment remain historical independent evidence.

A579 (224 bytes), A57A (32), A580 (40), A581 (128), A582 (96), and A583 (48) retain their existing layouts, checksums, units and order. A580 reports build `0x0000B0B2`. The B0B2 usercode is B0B2. One A585 frame is appended after A583 at each 5 Hz snapshot. The new frame adds 380 bytes/s, approximately 3.30% of a 115200 8N1 link. The complete 644-byte group uses 3220 bytes/s, approximately 27.95%; actual serialization takes approximately 55.9 ms. The original UART divides the 50 MHz clock by 434, giving approximately 115207.4 baud.

## Wire frame

All multibyte integers are unsigned, big endian. Frame length is exactly 76 bytes.

| Wire offset | Size | Field |
| --- | ---: | --- |
| 0 | 2 | Header `A5 85` |
| 2 | 1 | Version = 2 for the current lightweight candidate; historical version 1 remains separately decoded |
| 3 | 1 | Type = 1: SiK with USB 115200 mirror; all other values rejected |
| 4 | 2 | Snapshot sequence; same sequence as the preceding A579–A583 group, wraps at 65536 |
| 6 | 4 | Capture tick, low 32 bits of the 50 MHz diagnostic clock |
| 10 | 64 | Payload below |
| 74 | 2 | CRC16-CCITT-FALSE, polynomial 0x1021, initial 0xFFFF, no reflection/final XOR, over bytes 2 through 73 |

## Payload

The Python format is `>Q9I8BI4BI`, exactly 64 bytes. Offsets below are relative to payload byte 0.

| Offset | Size | Field | Meaning |
| --- | ---: | --- | --- |
| 0 | 8 | uptime_ms | FPGA uptime in ms |
| 8 | 4 | build_id | 0x0000B0B2 |
| 12 | 4 | raw_count | Tap raw-record count, saturates at 0xFFFFFFFF |
| 16 | 4 | accepted_count | Guard accepted count in the latest emitted raw decision tuple; saturates at 0xFFFFFFFF |
| 20 | 4 | pose_count | Tap publication count, saturates at 0xFFFFFFFF |
| 24 | 4 | v2: unavailable slot; v1: latest_rejected_source_id | v2 must transmit zero and decodes to null. v1 retains the latest raw decision ID with accepted flag clear, including reader-fault rejects |
| 28 | 4 | max_pose_gap_ticks | Maximum publication gap since boot, including the currently unfinished gap; starts after the first pose publication |
| 32 | 4 | consumed_accepted_id | Accepted-source identity consumed by the latest pose publication; the accepted identity saturates rather than wrapping |
| 36 | 4 | held_dt_ticks | Integration dt held for that same latest pose publication |
| 40 | 4 | first_diagnostic_tick | Capture tick of the tap's first diagnostic anomaly in its current taking_off window; zero if none |
| 44 | 1 | latest_reader_fault | Reader fault of latest rejected raw tuple |
| 45 | 1 | latest_temporal_detail | Temporal-check detail of that same rejected tuple |
| 46 | 1 | latest_rejected_raw_flags | Flags of that same rejected tuple |
| 47 | 1 | latest_pose_flags | Flags of the latest pose publication |
| 48 | 1 | latest_pose_attitude_fault | Attitude fault attached to that same pose publication, not the current live fault |
| 49 | 1 | first_diagnostic_trigger | Tap anomaly trigger bits; independent of protection event below |
| 50 | 1 | first_diagnostic_cause | Estimator diagnostic first-cause code; may be zero |
| 51 | 1 | first_diagnostic_attitude_fault | Attitude fault at that anomaly capture |
| 52 | 4 | v2: unavailable slot; v1: first_protection_time_ms_low32 | v2 must transmit zero and decodes to null. v1 retains low 32 bits of the first qualifying A580-source event's FPGA time |
| 56 | 1 | first_protection_code | The first qualifying recorded event's gate code; zero means none |
| 57 | 1 | first_protection_sensor_mask | Sensor mask captured with that event |
| 58 | 1 | first_protection_imu_reason | IMU reason captured with that event |
| 59 | 1 | first_protection_attitude_fault | Attitude fault captured with that event |
| 60 | 4 | first_protection_pose_age_ticks | Pose age captured with that event |

Version 2 retains the 64-byte payload, 76-byte frame, existing offsets, CRC, cadence and all other field meanings. Its two unavailable slots are payload bytes 24..27 and 52..55 (wire bytes 34..37 and 62..65). The decoder rejects nonzero bytes in either v2 slot even when the CRC is valid. It never exposes those zeros as a real source identity or event time. Unknown versions and types are rejected; version 1 preserves both original integer fields without relabeling them.

Every newly decoded row includes `capabilities`, a map from each payload field name to a Boolean availability value, and `unavailable_fields`. For v2 the latter is exactly `["latest_rejected_source_id", "first_protection_time_ms_low32"]`; those two values are `null`, their capabilities are false, and all other payload capabilities are true. For v1 all payload capabilities are true and the unavailable list is empty. Availability describes the wire schema, not live validity, freshness, or the existence of a recorded event.

The v2 cost is explicit: individual rejected raw source IDs cannot be joined to other evidence, and the retained first protection has no exact source event time. The latest A580 event still carries its own time, but after that source register is overwritten it cannot recover the earlier retained first-protection time. Capture tick and summary uptime date the snapshot observation, not that earlier event. New rejects remain observable through same-group A579 `rejected_count` increments; its accepted/rejected guard counters saturate at 0xFFFFFFFF, so a saturated counter cannot establish the absence of later increments. Latest reader fault/detail/rejected flags remain retained rejection metadata, not an independent live stream.

Raw flags: bit0 reader_valid, bit1 reader_config_ok, bit2 checked_base_ok, bit3 accepted, bit4 link_usable, bit5 guard_qualified, bit6 attitude_valid, bit7 temporal candidate pending. Pose flags: bit0 attitude_valid, bit1 linear_acceleration_valid, bit2 calibrated, bit3 initialized, bit4 ready, bit5 reseed; bits6–7 zero.

`first_diagnostic_trigger`: bit0 pose-publication gap reached 20 ms; bit1 attitude_valid fell; bit2 gate event. The tap may freeze at 20 ms with cause zero and therefore precede a later 60 ms control protection. It is evidence of the first diagnostic anomaly, not the first protection or physical root cause. This tuple remains whatever the tap froze until its next taking_off rising edge. The summary explicitly suppresses the prior frozen tuple on that same edge so it cannot leak into a new snapshot window.

The separate first-protection tuple observes the existing top-level A580 event registers and sequence. A new event qualifies only when its recorded stage bits `code[5:4]` equal 3 (armed stage) and its health reason bits `code[1:0]` are nonzero. It uses the recorded stage rather than current armed, which can already be false after revocation. Manual SWA event 0x34 does not qualify. The taking_off rising edge opens/clears this window; the first new qualifying event wins, including an event on that exact clearing edge. Once captured, later events cannot overwrite it until the next window. The window remains open after taking_off falls so the resulting revocation can be captured. No pre-window event or unchanged event-sequence value is reused. The tuple reports the source register's recorded event; it cannot recover events coalesced before those existing registers.

The maximum gap is a publication interval, including publications whose attitude_valid flag is zero. It is not continuous invalid-pose duration, exposure timing, or end-to-end telemetry latency. It resets only at FPGA reset, not each takeoff. One tick is 20 ns; divide by 50000 for ms. Tick values wrap every approximately 85.9 s. The stored maximum never decreases; an outage exceeding one wrap is represented only by a lower bound near the 32-bit limit. The separate first-protection pose age has the source's existing meaning.

Summary output and capture tick freeze under the same telemetry snapshot_hold as the legacy group. Tracking of raw/pose updates, outstanding gap and first protection continues during that hold. Same-cycle raw and pose tuples bypass the local previous values coherently. Counters describe their named source streams; accepted_count is the last emitted raw decision's count rather than a promise that every source counter is taken on the same internal processing edge.

This diagnostic path has no control outputs and does not feed control, sensor acceptance, actuation, timing thresholds or flow compensation.

## Offline proof

Run `python -B firmware/B0B2/tests/run_sik_tests.py`. It samples real UART bits at the existing 434-clock period, checks start/stop bits, CRCs, exact 644-byte group size and all original 568 bytes against the manifest-verified frozen B0B0 telemetry module. It also checks hold/window races, ongoing gap, first-event retention, sequence wrap, strict v1/v2 parser rejection/resynchronization, B0B2 identity, an isolated legacy receiver, raw/decoded disk logging and full top elaboration. Each run uses a fresh output directory below `out/B0B2`; historical v1 wire evidence is retained. `SIK_WIRE_FIXTURE` explicitly binds the protocol test to the new run's real UART fixture, and a missing explicitly selected fixture fails.

The receiver generator copies frozen ground/B0B0 into a new child of out/B0B2, adds B0B2 identity support and the A585 decoder, and records source/output file hashes plus patch evidence. It does not open serial ports. The recorder keeps the new decoded rows in telemetry.jsonl alongside unchanged legacy protocol rows. A585 data never replaces primary controller data or its freshness.

`tools/analyze_bench.py` is a separate offline screen of explicitly selected original recorder rows. It joins the contiguous same-sequence A579/A57A/A580/A585 group, exact A580/A585 build/uptime and one source/receiver epoch. A585 v2 requires exact capability metadata and null unavailable values; original v1 rows predating capability metadata remain usable only with their complete strict v1 fields. Missing/contradictory capabilities, missing required protocols, source transitions or an already excessive global publication-gap maximum leave the interval inconclusive. The evaluator does not substitute A580 retained event age for live A579/A57A pose age.

The operator selects a settling trim and at least 60 seconds of subsequent coverage. The screen requires live accepted-raw/pose ages below 20 ms, held dt strictly between 0 and 20 ms, independent raw/accepted/publication/consumed-ID progress, and no newly observed reject/fault. Over that stable interval, the absolute pose-versus-accepted total increment difference, after allowing two endpoint pipeline samples, must be at most 1% of the accepted increment; excess is inconclusive. This is a bench screening threshold for missing/duplicate publications, not a 1 kHz rate assumption or hardware protection. Same-snapshot accepted/consumed and A579/A585 accepted-count lags are reported without forcing exact internal-cycle equality. The 20 ms age screen is distinct from the unchanged 60 ms hardware protection. Reported idle state requires valid RC, CH3/CH5/CH7 each 800..1100, no armed/enabled/fresh-command or active physical-frame bits, and all four command plus four physical/effective PWM widths equal 1000 us. These are reported schedules, not measured waveforms or proof that props were removed.

Decoded JSONL alone cannot establish zero CRC/length errors, noise bytes or recorder drops; these are reported as unknown. An acceptable result applies only to the observed complete decoded groups. Every result keeps `flight_ready=false` and does not authorize installation or flight. No interpolation reconstructs unobserved high-rate data.
