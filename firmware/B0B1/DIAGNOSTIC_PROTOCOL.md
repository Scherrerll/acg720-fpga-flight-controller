# B0B1 diagnostic interface v1

USB pin M15: 921600 baud nominal, 8N1 (50 MHz / 54 = 925925.93 baud,
+0.47%). SiK pin B15 retains the original 115200 A579..A583 stream.
All integers are big endian; signed values are two's complement.

Each frame: `A5 84`, version u8 (=1), type u8, transmit sequence u16,
capture tick u32, fixed type payload, CRC16-CCITT-FALSE u16 (init FFFF,
polynomial 1021, over version through end of payload). Sequence increments
for transmitted frames, wraps modulo 65536. Tick is a 50 MHz clock and wraps
modulo 2^32. Status uptime anchors long captures; a capture/reboot is a new epoch.
Unsupported versions/types and bad CRCs are rejected and scanning resumes.

| Type | Payload bytes | Fields in wire order |
|---|---:|---|
| 1 raw | 26 | source_id u32; normalized raw ax,ay,az,gx,gy,gz i16 each; accepted_count u32; temporal_detail u8; reader_fault u8; flags u8; quiet_count u8; recovery_count u8; estimator_state u8 |
| 2 pose | 28 | consumed_accepted_id u32; held_dt_ticks u32; world_ax,world_ay,world_az i32 each; sensor roll,pitch,yaw i16 each; flags u8; attitude_fault u8 |
| 3 fault | 88 | trigger_flags u8; first_cause u8; attitude_fault u8; temporal_detail u8; rejected_source_id u32; accepted_count u32; consumed_accepted_id u32; pose_count u32; last_accept_tick u32; last_pose_tick u32; max_accept_gap_ticks u32; busy_age_ticks u32; pose_age_ticks u32; accepted_age_ticks u32; estimator_state u8; resume_state u8; recovery_count u8; reseed_count u8; state_flags u16; quiet_count u8; reader_fault u8; rejected_raw,trusted,candidate (six i16 each) |
| 4 status | 40 | uptime_ms u64; build_id u32 (=0xB0B1); dropped_raw,dropped_pose,dropped_fault,dropped_status u32 each; max_accept_gap_ticks u32; raw_count u32; pose_count u32 |

Raw flags bit0 reader_valid, 1 config_ok, 2 checked_base_ok, 3 accepted,
4 link_usable, 5 guard_qualified, 6 attitude_valid, 7 candidate_pending.
Raw values on invalid reader records may be retained old words: never treat
them as a new physical observation unless reader_valid and config_ok are set.
Accepted IDs count guard acceptances, including acceptances during recovery;
only a pose with matching consumed_accepted_id proves a publication.
Normalized units: acceleration 2048 counts/g; gyro 16.4 counts/(degree/s).

Pose flags bit0 attitude_valid, 1 linear_accel_valid, 2 calibrated,
3 initialized, 4 ready, 5 reseed; bits6..7 reserved zero. Pose world axes are
the estimator's sensor-world X-forward/Y-left/Z-up, mm/s^2, gravity removed.
Pose angles are the estimator's sensor signs, centidegrees; do not relabel as
the mounted body axes. held_dt is captured with the exact consumed acceptance.

Fault trigger bits: 0 pose age >= 1,000,000 ticks (20 ms), 1 attitude-valid
fall, 2 gate event. Capture is enabled only after a valid pose has existed;
all simultaneous trigger bits are retained. First trigger freezes the packet.
Reset clears it; a rising taking_off starts a new capture window. Snapshot
triple is the coherent tuple of the most recent rejected temporal decision,
not a later accepted sample. rejected_source_id=0 means no such tuple exists.
State flags bit0 calibrated, 1 initialized, 2 ready, 3 reseed, 4 link_usable,
5 guard_qualified, 6 guard_stale, 7 candidate_pending, 8 attitude_valid,
9 estimator_busy. first_cause is the first diagnostic invalidation since the
last pose publication: 0 none, 1 link loss, 2 recovery reject cancellation,
3 accepted-sample busy collision, 4 raw sentinel, 5 dt limit,
6 recovery gravity failure, 7 zero recovery norm, 8 arithmetic/numeric failure,
9 calibration failure. Diagnostic causes do not change existing fault codes.

No diagnostic signal feeds control, source qualification or reset. Capture
must never backpressure IMU/pose producers. Queues retain capture timestamps;
overflow drops the new item and increments its saturating type counter.
Fault capture remains frozen within its window and is retried until enqueued.
Retry cycles do not count as drops. If a new capture window deasserts a fault
that has not yet been enqueued, dropped_fault increments once and saturates;
releasing an already enqueued fault and reset do not increment it. Status is offered
once per second. At 1000 raw + 1000 pose per second the data rate is 78 kB/s
(~84.3% UART utilization), plus 52 B/s status and a one-shot 100-byte fault.
Counters and host sequence/CRC checks distinguish producer overflow from
USB transport loss. No interpolation is used to invent missing samples.

RTL seam owned by the diagnostic tap: raw_valid/raw_body[207:0]/raw_tick;
pose_valid/pose_body[223:0]/pose_tick; fault_valid/fault_body[703:0]/fault_tick;
clock_ticks, max_accept_gap, raw_count, pose_count (all u32).
UART accepts these, uptime_ms u64, build_id u32 and reset, and emits tx.
