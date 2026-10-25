"""Offline counterexamples for original recorder rows, never dashboard snapshots."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

FW = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("b0b2_analyze_bench", FW / "tools/analyze_bench.py")
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)
BASE = datetime(2026, 10, 25, tzinfo=timezone.utc)


def fixture(seconds=60, first_sequence=10, restart_at=None, version=1, capability_metadata=False):
    """Names/flags follow recorder.py, monitor_control.py and A585 v1 wire ABI.

    A580 intentionally carries an enormous RETAINED event pose age. It must
    never contaminate the independent fresh A579/A57A age measurements.
    """
    records = []
    for i in range(round(seconds * 5) + 1):
        ms = i * 200
        reboot = restart_at is not None and ms >= restart_at
        progress = ms - restart_at if reboot else ms
        uptime = 1000 + progress
        seq = (first_sequence + i) & 0xFFFF
        primary = dict(_protocol="a579", sequence=seq, flags=15, imu_reason=0,
            attitude_fault=0, accepted_count=1000 + progress, rejected_count=2,
            command_count=0, controller_fault_count=0, last_controller_fault=0,
            pose_age_ticks=5000, physical_flags=0, ch3=1000, ch5=1000, ch7=1000,
            m1_us=1000, m2_us=1000, m3_us=1000, m4_us=1000,
            physical_m1_us=1000, physical_m2_us=1000, physical_m3_us=1000, physical_m4_us=1000)
        accel = dict(_protocol="a57a", sequence=seq, accel_flags=3,
            pose_age_ticks=5000, raw_age_ticks=5000)
        info = dict(_protocol="a580", sequence=seq, version=4, build_id=0xB0B2,
            uptime_ms=uptime, controller_fault=0, sticky_yaw_fault=0,
            event_sequence=4, event_code=0x22, event_sensor_mask=0,
            event_imu_reason=0, event_attitude_fault=0, event_pose_age_ticks=0xFFFFFFFF)
        diag = dict(_protocol="a585", sequence=seq, version=version, type=1,
            build_id=0xB0B2, uptime_ms=uptime, capture_tick=(uptime * 50000) & 0xFFFFFFFF,
            raw_count=1100 + progress, accepted_count=1000 + progress,
            pose_count=950 + progress, consumed_accepted_id=999 + progress,
            max_pose_gap_ticks=50001, held_dt_ticks=50000,
            latest_rejected_source_id=9, latest_reader_fault=0x40,
            latest_temporal_detail=0, latest_rejected_raw_flags=0,
            latest_pose_flags=31, latest_pose_attitude_fault=0,
            first_diagnostic_tick=0, first_diagnostic_trigger=0,
            first_diagnostic_cause=0, first_diagnostic_attitude_fault=0,
            first_protection_time_ms_low32=0, first_protection_code=0,
            first_protection_sensor_mask=0, first_protection_imu_reason=0,
            first_protection_attitude_fault=0, first_protection_pose_age_ticks=0)
        unavailable = ["latest_rejected_source_id", "first_protection_time_ms_low32"] if version == 2 else ['first_protection_pose_age_ticks'] if version==3 else []
        if version in (2,3):
            for name in unavailable:diag[name] = None
        if version in (2,3) or capability_metadata:
            diag["capabilities"] = {name:name not in unavailable for name in diag
                if name not in ("_protocol", "sequence", "version", "type", "capture_tick")}
            diag["unavailable_fields"] = unavailable
        if version==3:
            info['version']=5
            for row in (primary,accel,info,diag):
                removed=BENCH.REMOVED_BY_PROTOCOL[row['_protocol']]
                row['_age_policy']='no_pose_age_v3';row['unavailable_fields']=list(removed)
                for name in removed:row[name]=None
        for row in (primary, accel, info, diag):
            records.append(dict(utc=(BASE + timedelta(milliseconds=ms)).isoformat(),
                host_ns=1_000_000_000 + ms * 1_000_000, elapsed_s=ms / 1000,
                epoch=int(reboot), record_order=len(records) + 1, row=row))
    return records


class BenchTests(unittest.TestCase):
    def evaluate(self, records, seconds=60, stable_after=0):
        with tempfile.TemporaryDirectory(prefix="b0b2_bench_offline_") as temp:
            path = Path(temp) / "telemetry.jsonl"
            for index, record in enumerate(records):
                record["record_order"] = index + 1
            path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
            report = BENCH.analyze(path, BASE.isoformat(),
                                   (BASE + timedelta(seconds=seconds)).isoformat(), stable_after)
            self.assertEqual(report["input"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(report["tool"]["sha256"], hashlib.sha256((FW / "tools/analyze_bench.py").read_bytes()).hexdigest())
            self.assertFalse(report["flight_ready"])
            self.assertFalse(report["installation_authorized"])
            self.assertFalse(report["hardware_accessed"])
            return report

    def test_normal_60s_and_retained_event_age_is_not_live(self):
        report = self.evaluate(fixture())
        self.assertEqual(report["status"], "acceptable")
        self.assertEqual(report["coverage"]["complete_unique_snapshots"], 301)
        self.assertEqual(report["maximum_live_age_ticks"]["primary_pose"], 5000)
        self.assertEqual(report["retained_first_causes"][0]["event_pose_age_ticks"], 0xFFFFFFFF)
        self.assertIsNone(report["transport_integrity"]["crc_error_count"])
        self.assertIsNone(report["transport_integrity"]["length_error_count"])
        segment = next(iter(report["source_epochs"].values()))
        self.assertEqual(segment["counters"]["a585.pose_count"]["known_delta"], 60000)

    def test_v2_normal_null_capabilities_and_v1_metadata_compatibility(self):
        report = self.evaluate(fixture(version=2))
        self.assertEqual(report["status"], "acceptable")
        self.assertEqual(report["coverage"]["diagnostic_version_counts"], {"2":301})
        retained = report["retained_first_causes"][0]
        self.assertIsNone(retained["first_protection"]["first_protection_time_ms_low32"])
        self.assertIsNone(retained["last_rejected_tuple"]["latest_rejected_source_id"])
        self.assertEqual(retained["unavailable_fields"], ["latest_rejected_source_id", "first_protection_time_ms_low32"])
        self.assertEqual(self.evaluate(fixture(capability_metadata=True))["status"], "acceptable")
    def test_v3_no_age_value_or_hardware_age_protection_is_inferred(self):
        report=self.evaluate(fixture(version=3))
        self.assertEqual(report['status'],'acceptable')
        self.assertIsNone(report['maximum_live_age_ticks']['primary_pose'])
        self.assertIsNone(report['maximum_live_age_ms']['acceleration_pose'])
        self.assertIsNone(report['policy']['hardware_pose_age_protection_limit_ms'])
        self.assertEqual(report['policy']['independent_control_command_timeout_ms'],60)
        self.assertEqual(report['unavailable_age_sample_counts']['primary_pose'],301)
    def test_v3_reserved_zero_cannot_masquerade_as_a_fresh_age(self):
        records=fixture(version=3);records[100]['row']['pose_age_ticks']=0
        report=self.evaluate(records)
        self.assertEqual(report['status'],'inconclusive')
        self.assertIn('mixed_or_invalid_age_free_schema',report['issues']['inconclusive'])
    def test_v3_mixed_legacy_or_missing_policy_metadata_cannot_pass(self):
        records=fixture(version=3);records[102]['row'].pop('_age_policy')
        self.assertEqual(self.evaluate(records)['status'],'inconclusive')

    def test_v2_new_rejection_uses_primary_saturating_count(self):
        records = fixture(version=2)
        for record in records[600:]:
            if record["row"]["_protocol"] == "a579":record["row"]["rejected_count"] = 3
        report = self.evaluate(records)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["issues"]["fail"]["new_a579.rejected_count"], 1)
        self.assertNotIn("new_rejected_source_tuple", report["issues"]["fail"])

    def test_v2_zero_missing_or_inconsistent_capabilities_cannot_pass(self):
        for field in ("latest_rejected_source_id", "first_protection_time_ms_low32",
                      "missing_capabilities", "wrong_capabilities", "wrong_unavailable", "version", "type"):
            with self.subTest(field=field):
                records = fixture(version=2)
                row = records[103]["row"]
                if field == "missing_capabilities":del row["capabilities"]
                elif field == "wrong_capabilities":row["capabilities"]["latest_rejected_source_id"] = True
                elif field == "wrong_unavailable":row["unavailable_fields"] = []
                else:row[field] = 3 if field == "version" else 2 if field == "type" else 0
                self.assertEqual(self.evaluate(records)["status"], "inconclusive")

    def test_v2_retained_or_new_protection_has_no_fabricated_time(self):
        records = fixture(version=2)
        for record in records[600:]:
            if record["row"]["_protocol"] == "a585":
                record["row"].update(first_protection_code=0x32, first_protection_sensor_mask=4,
                                      first_protection_pose_age_ticks=3_000_000)
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        event = report["newly_observed_first_cause_changes"][0]
        self.assertEqual(event["observed_snapshot_uptime_ms"],31000)
        self.assertEqual(event["observation_interval_uptime_ms"],[30800,31000])
        self.assertFalse(event["source_event_time_low32_available"])
        self.assertIsNone(event["fields"]["first_protection_time_ms_low32"])

    def test_accepted_grows_but_pose_and_consumed_source_stop(self):
        records = fixture()
        for record in records:
            if record["row"]["_protocol"] == "a585":
                record["row"].update(pose_count=950, consumed_accepted_id=999)
        report = self.evaluate(records)
        self.assertEqual(report["status"], "fail")
        self.assertIn("pose_publication_or_consumed_source_stalled", report["issues"]["fail"])
        segment = next(iter(report["source_epochs"].values()))
        self.assertGreater(segment["counters"]["a585.accepted_count"]["known_delta"], 0)

    def test_missing_protocol_is_inconclusive(self):
        records = fixture()
        del records[101]  # A57A only, not the whole snapshot.
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        self.assertIn("incomplete_or_ambiguous_snapshot", report["issues"]["inconclusive"])

    def test_stale_protocol_and_wrong_identity_cannot_join(self):
        for mutate in ("stale", "uptime", "build"):
            with self.subTest(mutate=mutate):
                records = fixture()
                record = records[103]
                if mutate == "stale":
                    record["host_ns"] += 1_000_000_000
                    record["utc"] = (BASE + timedelta(seconds=6)).isoformat()
                elif mutate == "uptime":
                    record["row"]["uptime_ms"] -= 200
                else:
                    record["row"]["build_id"] = 0xB0B0
                self.assertEqual(self.evaluate(records)["status"], "inconclusive")

    def test_restart_separates_counters_and_cannot_pass_aggregate_60s(self):
        report = self.evaluate(fixture(restart_at=30000))
        self.assertEqual(report["status"], "inconclusive")
        self.assertEqual(len(report["source_epochs"]), 2)
        self.assertEqual(report["input"]["observed_A580_identity_or_uptime_rollbacks"], 1)
        self.assertNotIn("counter_reset_or_saturation", report["issues"]["inconclusive"])

    def test_sequence_and_diagnostic_tick_wrap_are_not_reboots(self):
        records = fixture(first_sequence=65530)
        # Arbitrary clock phase makes a capture_tick wrap during the interval.
        for record in records:
            if record["row"]["_protocol"] == "a585":
                record["row"]["capture_tick"] = (0xFFFFFF00 + record["row"]["uptime_ms"] * 50000) & 0xFFFFFFFF
        report = self.evaluate(records)
        self.assertEqual(report["status"], "acceptable")
        self.assertEqual(report["coverage"]["sequence_wraps"], 1)
        self.assertEqual(len(report["source_epochs"]), 1)

    def test_old_sticky_max_gap_masks_later_healthy_interval(self):
        records = fixture()
        for record in records:
            if record["row"]["_protocol"] == "a585":
                record["row"]["max_pose_gap_ticks"] = 3_000_000
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        self.assertIn("old_global_max_pose_gap_masks_interval", report["issues"]["inconclusive"])
        self.assertFalse(report["issues"]["fail"])

    def test_new_max_gap_or_fault_is_an_observed_failure(self):
        for mutate in ("gap", "fault"):
            with self.subTest(mutate=mutate):
                records = fixture()
                for record in records[600:]:
                    row = record["row"]
                    if row["_protocol"] == "a585" and mutate == "gap":
                        row["max_pose_gap_ticks"] = 1_000_000
                    if row["_protocol"] == "a579" and mutate == "fault":
                        row["controller_fault_count"] = 1
                self.assertEqual(self.evaluate(records)["status"], "fail")

    def test_live_age_invalidity_and_no_interpolation(self):
        records = fixture()
        records[101]["row"].update(raw_age_ticks=3_000_000, accel_flags=1)
        report = self.evaluate(records)
        self.assertEqual(report["status"], "fail")
        self.assertIn("accepted_raw_stale", report["issues"]["fail"])
        report = self.evaluate(fixture(seconds=50), seconds=50)
        self.assertEqual(report["status"], "inconclusive")

    def test_bench_20ms_age_and_exclusive_held_dt_bounds(self):
        for field, value in (("raw_age_ticks", 1_000_000), ("pose_age_ticks", 1_000_000),
                             ("held_dt_ticks", 0), ("held_dt_ticks", 1_000_000)):
            with self.subTest(field=field, value=value):
                records = fixture()
                records[103 if field == "held_dt_ticks" else 101]["row"][field] = value
                self.assertEqual(self.evaluate(records)["status"], "fail")

    def test_idle_armed_pwm_rc_and_missing_ch7(self):
        for field, value in (("flags", 31), ("flags", 14), ("physical_flags", 1),
                             ("m2_us", 1200), ("physical_m4_us", 1200),
                             ("ch3", 1101), ("ch5", 1101), ("ch7", 1101)):
            with self.subTest(field=field, value=value):
                records = fixture()
                records[100]["row"][field] = value
                self.assertEqual(self.evaluate(records)["status"], "fail")
        records = fixture()
        del records[100]["row"]["ch7"]
        self.assertEqual(self.evaluate(records)["status"], "inconclusive")

    def test_saturating_counter_drop_is_not_wrap(self):
        for proto, field in (("a579", "accepted_count"), ("a579", "rejected_count"),
                             ("a585", "accepted_count"), ("a585", "consumed_accepted_id")):
            with self.subTest(proto=proto, field=field):
                records = fixture()
                for record in records:
                    if record["row"]["_protocol"] == proto and record["record_order"] < 5:
                        record["row"][field] = 0xFFFFFFF0
                report = self.evaluate(records)
                self.assertEqual(report["status"], "inconclusive")
                counter = next(iter(report["source_epochs"].values()))["counters"][proto + "." + field]
                self.assertEqual(counter["wraps"], 0)
                self.assertGreater(counter["unknown_intervals"], 0)

    def test_slow_pose_count_is_not_rescued_by_fresh_sampled_ages(self):
        records = fixture()
        for i, record in enumerate(records):
            if record["row"]["_protocol"] == "a585":
                record["row"]["pose_count"] = 950 + i // 4
        report = self.evaluate(records)
        self.assertEqual(report["status"], "fail")
        self.assertIn("pose_count_cannot_support_gap_limit", report["issues"]["fail"])

    def test_total_publications_cannot_silently_drop_or_duplicate_accepts(self):
        for numerator, denominator in ((1,10), (2,1)):
            with self.subTest(pose_ratio=(numerator,denominator)):
                records = fixture(version=2)
                for record in records:
                    row = record["row"]
                    if row["_protocol"] == "a585":
                        row["pose_count"] = 950 + (row["uptime_ms"] - 1000) * numerator // denominator
                report = self.evaluate(records)
                self.assertEqual(report["status"], "inconclusive")
                self.assertIn("publication_acceptance_total_mismatch", report["issues"]["inconclusive"])
                self.assertFalse(report["issues"]["fail"])
                segment = next(iter(report["source_epochs"].values()))
                self.assertEqual(segment["pose_to_accepted_known_delta_ratio"],numerator/denominator)
                self.assertEqual(segment["publication_acceptance_balance"]["endpoint_sample_allowance"],2)

    def test_controller_commands_advancing_while_stopped_cannot_pass(self):
        # Same counterexample as the independent review: idle flags/RC/PWM
        # stay valid, but one controller transaction appears in every group.
        records = fixture(version=2)
        for index, record in enumerate(records):
            if record["row"]["_protocol"] == "a579":record["row"]["command_count"] = index // 4
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        self.assertIn("new_control_transactions_while_reported_stopped", report["issues"]["inconclusive"])
        self.assertFalse(report["issues"]["fail"])

    def test_raw_accept_reject_totals_cannot_lose_or_invent_records(self):
        for case in ("accepted_200x_raw", "unaccounted_raw", "three_endpoint_samples"):
            with self.subTest(case=case):
                records = fixture(version=2)
                for record in records:
                    row = record["row"]
                    if row["_protocol"] != "a585":continue
                    elapsed_ms = row["uptime_ms"] - 1000
                    if case == "accepted_200x_raw":row["raw_count"] = 1100 + elapsed_ms // 200
                    elif case == "unaccounted_raw":row["raw_count"] = 1100 + 2 * elapsed_ms
                    elif elapsed_ms == 60000:row["raw_count"] += 3
                report = self.evaluate(records)
                self.assertEqual(report["status"], "inconclusive")
                self.assertIn("raw_accept_reject_total_mismatch", report["issues"]["inconclusive"])
                self.assertFalse(report["issues"]["fail"])
                balance = next(iter(report["source_epochs"].values()))["raw_accept_reject_balance"]
                self.assertTrue(balance["assessed"])
                self.assertGreater(abs(balance["raw_minus_decisions"]), 2)

    def test_raw_decision_two_endpoint_samples_are_allowed(self):
        for difference in (-2, 2):
            with self.subTest(difference=difference):
                records = fixture(version=2)
                records[-1]["row"]["raw_count"] += difference
                report = self.evaluate(records)
                self.assertEqual(report["status"], "acceptable")
                balance = next(iter(report["source_epochs"].values()))["raw_accept_reject_balance"]
                self.assertTrue(balance["assessed"])
                self.assertEqual(balance["raw_minus_decisions"], difference)
                self.assertEqual(balance["endpoint_sample_allowance"], 2)

    def test_retained_first_cause_is_not_a_live_fault(self):
        records = fixture()
        for record in records:
            if record["row"]["_protocol"] == "a585":
                record["row"].update(first_diagnostic_tick=10, first_diagnostic_trigger=1,
                                      first_diagnostic_cause=0)
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        self.assertFalse(report["issues"]["fail"])

    def test_duplicate_protocol_is_ambiguous_even_with_complete_fields(self):
        records = fixture()
        records.insert(102, json.loads(json.dumps(records[101])))
        report = self.evaluate(records)
        self.assertEqual(report["coverage"]["duplicate_protocol_records"], {"a57a": 1})
        self.assertEqual(report["status"], "inconclusive")

    def test_new_mask_zero_gate_event_needs_context_not_invented_imu_fault(self):
        records = fixture()
        for record in records[600:]:
            if record["row"]["_protocol"] == "a580":
                record["row"].update(event_sequence=5, event_code=0x32)
        report = self.evaluate(records)
        self.assertEqual(report["status"], "inconclusive")
        self.assertFalse(report["issues"]["fail"])

    def test_dashboard_or_missing_row_schema_cannot_pass(self):
        report = self.evaluate([dict(utc=BASE.isoformat(), epoch=0, host_ns=1,
                                    record_order=1, data={"accepted_count": 100000})])
        self.assertEqual(report["status"], "inconclusive")
        self.assertEqual(report["input"]["malformed_records"], 1)
        self.assertFalse(report["issues"]["fail"])

    def test_duplicates_and_intragroup_epoch_boundary(self):
        records = fixture()
        records[104:104] = [json.loads(json.dumps(r)) for r in records[100:104]]
        report = self.evaluate(records)
        self.assertEqual(report["coverage"]["duplicate_snapshots"], 1)
        self.assertEqual(report["status"], "inconclusive")
        records = fixture()
        records[102]["epoch"] = 1
        self.assertEqual(self.evaluate(records)["status"], "inconclusive")

    def test_cli_explicit_selection_settling_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="b0b2_bench_cli_") as temp:
            path, output = Path(temp) / "telemetry.jsonl", Path(temp) / "new_report.json"
            path.write_text("".join(json.dumps(r) + "\n" for r in fixture(seconds=70)), encoding="utf-8")
            args = ["--input", str(path), "--start-utc", BASE.isoformat(), "--end-utc",
                    (BASE + timedelta(seconds=70)).isoformat(), "--stable-after-s", "5", "--output", str(output)]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(BENCH.main(args), 0)
            before = output.read_bytes()
            with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                BENCH.main(args)
            self.assertEqual(before, output.read_bytes())
            self.assertFalse(json.loads(before)["flight_ready"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
