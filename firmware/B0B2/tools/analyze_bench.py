"""Evaluate an explicitly selected, recorded B0B2 props-off interval offline.

Example (UTC bounds and the settling interval are deliberate operator choices):
  python -B firmware/B0B2/tools/analyze_bench.py --input PATH/telemetry.jsonl \
    --start-utc 2026-10-25T02:00:00Z --end-utc 2026-10-25T02:01:10Z \
    --stable-after-s 5 --output NEW_REPORT.json

Exit codes: 0 acceptable recorded bench observations, 1 observed anomaly,
3 inconclusive, 2 invalid invocation. None authorizes installation or flight.
Only the explicitly selected log is analyzed, read-only; the report is created
exclusively and the tool hashes its own source. No receiver, serial, network,
programmer or live API import.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path

PROTOCOLS = ("a579", "a57a", "a580", "a585")
BUILD = 0xB0B2
TICKS_PER_MS = 50000
MIN_STABLE_SECONDS = 60
POSE_GAP_LIMIT = 20 * TICKS_PER_MS
AGE_LIMIT = 20 * TICKS_PER_MS
PROTECTION_AGE_LIMIT = 60 * TICKS_PER_MS
MAX_GROUP_SPAN_NS = 500_000_000
EDGE_TOLERANCE_S = 0.6
RELATIVE_COUNT_TOLERANCE = 0.01
COUNT_ENDPOINT_ALLOWANCE = 2
FIELDS = {
    "a579": "flags imu_reason attitude_fault accepted_count rejected_count command_count "
            "controller_fault_count last_controller_fault pose_age_ticks physical_flags ch3 ch5 ch7 "
            "m1_us m2_us m3_us m4_us physical_m1_us physical_m2_us physical_m3_us physical_m4_us",
    "a57a": "accel_flags pose_age_ticks raw_age_ticks",
    "a580": "version build_id uptime_ms controller_fault sticky_yaw_fault event_sequence "
            "event_code event_sensor_mask event_imu_reason event_attitude_fault event_pose_age_ticks",
    "a585": "version type build_id uptime_ms capture_tick raw_count accepted_count pose_count "
            "latest_rejected_source_id max_pose_gap_ticks consumed_accepted_id held_dt_ticks "
            "latest_reader_fault latest_temporal_detail latest_rejected_raw_flags latest_pose_flags "
            "latest_pose_attitude_fault first_diagnostic_tick first_diagnostic_trigger "
            "first_diagnostic_cause first_diagnostic_attitude_fault first_protection_time_ms_low32 "
            "first_protection_code first_protection_sensor_mask first_protection_imu_reason "
            "first_protection_attitude_fault first_protection_pose_age_ticks",
}
UNAVAILABLE_V2 = ("latest_rejected_source_id", "first_protection_time_ms_low32")
UNAVAILABLE_V3 = ('first_protection_pose_age_ticks',)
REMOVED_BY_PROTOCOL = {'a579':('pose_age_ticks','gate_last_interruption_pose_age_ticks','gate_last_revoke_pose_age_ticks'),
                       'a57a':('pose_age_ticks',),'a580':('event_pose_age_ticks',),'a585':UNAVAILABLE_V3}
A585_PAYLOAD_FIELDS = tuple(k for k in FIELDS["a585"].split() if k not in ("version", "type", "capture_tick"))
COUNTERS = {
    "a579": ("accepted_count", "rejected_count", "command_count", "controller_fault_count"),
    "a585": ("raw_count", "accepted_count", "pose_count", "consumed_accepted_id"),
}
SATURATING = {"a579.accepted_count", "a579.rejected_count", "a585.raw_count",
              "a585.accepted_count", "a585.pose_count", "a585.consumed_accepted_id"}
DIAGNOSTIC = tuple("first_diagnostic_tick first_diagnostic_trigger first_diagnostic_cause "
                   "first_diagnostic_attitude_fault".split())
PROTECTION = tuple("first_protection_time_ms_low32 first_protection_code "
                   "first_protection_sensor_mask first_protection_imu_reason "
                   "first_protection_attitude_fault first_protection_pose_age_ticks".split())


def utc(value):
    if not isinstance(value, str):
        raise ValueError("Timestamps must be ISO strings")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must include an explicit UTC offset")
    return result.astimezone(timezone.utc)


def integer(value):
    return type(value) is int and value >= 0


def tuple_fields(row, names):
    return tuple(row[k] for k in names)


def diagnostic_capabilities(row):
    """Validate decoded version-specific availability; never replace null by zero."""
    version = row.get("version")
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError("Unknown A585 version")
    unavailable = UNAVAILABLE_V2 if version == 2 else UNAVAILABLE_V3 if version==3 else ()
    if any(name not in row or row[name] is not None for name in unavailable):
        raise ValueError("unavailable fields must be explicitly null, never a number")
    expected = {name: name not in unavailable for name in A585_PAYLOAD_FIELDS}
    provided = "capabilities" in row or "unavailable_fields" in row
    if version in (2,3) or provided:
        capabilities = row.get("capabilities")
        if (not isinstance(capabilities, dict) or capabilities != expected or
                any(type(value) is not bool for value in capabilities.values()) or
                row.get("unavailable_fields") != list(unavailable)):
            raise ValueError("Missing or inconsistent diagnostic capabilities")
    # Old original v1 receiver records predate metadata but all v1 fields exist.
    return unavailable, provided


class Evaluation:
    def __init__(self, start, end):
        self.start, self.end = start, end
        self.issues = {"fail": Counter(), "inconclusive": Counter()}
        self.examples = []
        self.received = Counter()
        self.missing_protocols = Counter()
        self.duplicate_protocols = Counter()
        self.primary_previous = None
        self.primary_missing = self.primary_duplicates = 0
        self.groups = self.complete = self.duplicates = self.missing = self.wraps = 0
        self.seen = set()
        self.previous = None
        self.boots = {}
        self.flags = {k: Counter() for k in ("primary", "acceleration", "pose", "retained_rejected_raw")}
        self.ages = {k: 0 for k in ("primary_pose", "acceleration_pose", "accepted_raw")}
        self.age_valid_counts = Counter()
        self.age_unavailable_counts = Counter()
        self.sticky = []
        self.new_events = []
        self.first_time = self.last_time = None
        self.max_report_interval_ms = 0
        self.max_held_dt_ticks = 0
        self.idle_observations = dict(checked_snapshots=0, rc_channels={}, scheduled_pwm_us={})
        self.diagnostic_versions = Counter()
        self.inferred_v1_capabilities = 0

    def issue(self, severity, reason, detail=None):
        self.issues[severity][reason] += 1
        if len(self.examples) < 40:
            self.examples.append(dict(severity=severity, reason=reason, detail=detail))

    def in_window(self, time):
        return self.start <= time <= self.end

    def finish(self, group):
        if not group:
            return
        anchor = group["rows"].get("a580", group["first"])
        if not self.in_window(anchor["time"]):
            return
        self.groups += 1
        self.received.update(group["counts"])
        self.missing_protocols.update(set(PROTOCOLS) - set(group["rows"]))
        self.duplicate_protocols.update({p: n - 1 for p, n in group["counts"].items() if n > 1})
        primary_key = (group["first"]["epoch"], group["generation"])
        if integer(group["seq"]) and group["seq"] < 65536:
            if self.primary_previous and self.primary_previous[0] == primary_key:
                primary_step = (group["seq"] - self.primary_previous[1]) & 0xFFFF
                if not primary_step:
                    self.primary_duplicates += 1
                elif 1 < primary_step < 0x8000:
                    self.primary_missing += primary_step - 1
            self.primary_previous = primary_key, group["seq"]
        if group["bad"] or set(group["rows"]) != set(PROTOCOLS):
            self.issue("inconclusive", "incomplete_or_ambiguous_snapshot", dict(
                sequence=group["seq"], present=list(group["rows"]), problems=group["bad"]))
            return
        entries = group["rows"]
        rows = {p: entries[p]["row"] for p in PROTOCOLS}
        try:
            unavailable, capability_metadata = diagnostic_capabilities(rows["a585"])
        except ValueError as exc:
            self.issue("inconclusive", "invalid_diagnostic_capabilities", str(exc))
            return
        age_free=rows['a585']['version']==3
        if age_free and any(row.get('_age_policy')!='no_pose_age_v3' or
             row.get('unavailable_fields')!=list(REMOVED_BY_PROTOCOL[proto]) or
             any(name not in row or row[name]is not None for name in REMOVED_BY_PROTOCOL[proto])
             for proto,row in rows.items()):
            self.issue('inconclusive','mixed_or_invalid_age_free_schema',group['seq']);return
        for proto, row in rows.items():
            names = ("sequence " + FIELDS[proto]).split()
            if age_free:names=[k for k in names if k not in REMOVED_BY_PROTOCOL[proto]]
            if proto == "a585":
                names = [k for k in names if k not in unavailable]
            if any(not integer(row.get(k)) for k in names) or row["sequence"] >= 65536:
                self.issue("inconclusive", "missing_or_invalid_protocol_fields", proto)
                return
        info, diag = rows["a580"], rows["a585"]
        if (info["version"] != (5 if age_free else 4) or diag["type"] != 1 or
                info["build_id"] != BUILD or diag["build_id"] != BUILD or
                info["uptime_ms"] != diag["uptime_ms"]):
            self.issue("inconclusive", "snapshot_uptime_or_identity_mismatch", group["seq"])
            return
        if len({e["epoch"] for e in entries.values()}) != 1:
            self.issue("inconclusive", "receiver_epoch_changed_inside_snapshot", group["seq"])
            return
        ns = [e["host_ns"] for e in entries.values()]
        times = [e["time"] for e in entries.values()]
        if max(ns) - min(ns) > MAX_GROUP_SPAN_NS or (max(times) - min(times)).total_seconds() > .5:
            self.issue("inconclusive", "stale_protocol_join", group["seq"])
            return
        if diag["latest_pose_flags"] & 0xC0 or rows["a57a"]["accel_flags"] & ~3:
            self.issue("inconclusive", "unknown_reserved_flags", group["seq"])
            return
        boot = (anchor["epoch"], group["generation"], info["build_id"])
        identity = (boot, group["seq"], info["uptime_ms"])
        if identity in self.seen:
            self.duplicates += 1
            self.issue("inconclusive", "duplicate_snapshot", group["seq"])
            return
        self.seen.add(identity)
        self.complete += 1
        self.diagnostic_versions[str(diag["version"])] += 1
        if diag["version"] == 1 and not capability_metadata:
            self.inferred_v1_capabilities += 1
        time = anchor["time"]
        self.first_time = self.first_time or time
        self.last_time = time
        key = f"receiver:{boot[0]}/source:{boot[1]}/build:{boot[2]:04x}"
        lag = diag["accepted_count"] - diag["consumed_accepted_id"]
        accepted_lag = rows["a579"]["accepted_count"] - diag["accepted_count"]
        segment = self.boots.setdefault(key, dict(samples=0, first_uptime_ms=info["uptime_ms"],
            last_uptime_ms=info["uptime_ms"], counters={}, first_max_pose_gap_ticks=diag["max_pose_gap_ticks"],
            maximum_pose_gap_ticks=diag["max_pose_gap_ticks"], accepted_minus_consumed_id=dict(min=lag, max=lag),
            primary_minus_diagnostic_accepted=dict(min=accepted_lag, max=accepted_lag)))
        segment["samples"] += 1
        segment["last_uptime_ms"] = info["uptime_ms"]
        segment["accepted_minus_consumed_id"]["min"] = min(segment["accepted_minus_consumed_id"]["min"], lag)
        segment["accepted_minus_consumed_id"]["max"] = max(segment["accepted_minus_consumed_id"]["max"], lag)
        segment["primary_minus_diagnostic_accepted"]["min"] = min(segment["primary_minus_diagnostic_accepted"]["min"], accepted_lag)
        segment["primary_minus_diagnostic_accepted"]["max"] = max(segment["primary_minus_diagnostic_accepted"]["max"], accepted_lag)
        segment["maximum_pose_gap_ticks"] = max(segment["maximum_pose_gap_ticks"], diag["max_pose_gap_ticks"])
        self.max_held_dt_ticks = max(self.max_held_dt_ticks, diag["held_dt_ticks"])
        for proto, names in COUNTERS.items():
            for name in names:
                full = proto + "." + name
                segment["counters"].setdefault(full, dict(first=rows[proto][name], last=rows[proto][name],
                                                         known_delta=0, wraps=0, unknown_intervals=0))
                segment["counters"][full]["last"] = rows[proto][name]
        self.observe_live(rows)
        previous = self.previous
        if previous is None or previous["boot"] != boot:
            if previous is not None:
                self.issue("inconclusive", "boot_or_receiver_epoch_boundary_in_window", key)
            self.observe_entry(rows, key)
        else:
            self.observe_interval(previous, rows, segment, time)
        self.previous = dict(boot=boot, rows=rows, time=time, host_ns=anchor["host_ns"])

    def observe_live(self, rows):
        age_free=rows['a585']['version']==3
        primary, accel, info, diag = (rows[p] for p in PROTOCOLS)
        self.flags["primary"][str(primary["flags"])] += 1
        self.flags["acceleration"][str(accel["accel_flags"])] += 1
        self.flags["pose"][str(diag["latest_pose_flags"])] += 1
        # This byte belongs to the LAST REJECT, never the current accepted raw.
        self.flags["retained_rejected_raw"][str(diag["latest_rejected_raw_flags"])] += 1
        for label, age, valid in (("primary_pose", primary["pose_age_ticks"], bool(primary["flags"] & 4)),
                                  ("acceleration_pose", accel["pose_age_ticks"], bool(accel["accel_flags"] & 1)),
                                  ("accepted_raw", accel["raw_age_ticks"], bool(accel["accel_flags"] & 2))):
            if age is None and age_free and label!='accepted_raw':
                self.age_unavailable_counts[label]+=1
                continue
            self.ages[label] = max(self.ages[label], age)
            if valid:
                self.age_valid_counts[label] += 1
            if age >= AGE_LIMIT:
                self.issue("fail", label + "_stale", age)
        if primary["flags"] & 0x0E != 0x0E or accel["accel_flags"] != 3 or diag["latest_pose_flags"] & 0x1F != 0x1F:
            self.issue("fail", "invalid_stable_pose_or_acceleration_flags", primary["sequence"])
        if diag["latest_pose_flags"] & 0x20:
            self.issue("fail", "pose_reseed_observed", primary["sequence"])
        if any((primary["attitude_fault"], info["controller_fault"], diag["latest_pose_attitude_fault"])):
            self.issue("fail", "live_or_published_fault", primary["sequence"])
        if primary["imu_reason"]:
            self.issue("fail", "imu_reason_observed", primary["imu_reason"])
        if not 0 < diag["held_dt_ticks"] < AGE_LIMIT:
            self.issue("fail", "held_dt_outside_bench_interval", diag["held_dt_ticks"])
        self.idle_observations["checked_snapshots"] += 1
        if primary["flags"] & 0x70 or primary["physical_flags"] & 3:
            self.issue("fail", "idle_control_or_physical_frame_active", primary["sequence"])
        if not primary["flags"] & 1:
            self.issue("fail", "idle_rc_not_valid", primary["sequence"])
        for name, upper in (("ch3", 1100), ("ch5", 1100), ("ch7", 1100)):
            value = primary[name]
            observed = self.idle_observations["rc_channels"].setdefault(name, dict(min=value, max=value))
            observed["min"], observed["max"] = min(observed["min"], value), max(observed["max"], value)
            if not 800 <= value <= upper:
                self.issue("fail", "idle_rc_channel_not_low", dict(channel=name, value=value))
        for prefix in ("m", "physical_m"):
            for motor in range(1, 5):
                name = f"{prefix}{motor}_us"
                value = primary[name]
                observed = self.idle_observations["scheduled_pwm_us"].setdefault(name, dict(min=value, max=value))
                observed["min"], observed["max"] = min(observed["min"], value), max(observed["max"], value)
                if value != 1000:
                    self.issue("fail", "idle_reported_motor_width_not_1000", dict(field=name, value=value))

    def observe_entry(self, rows, key):
        primary, info, diag = rows["a579"], rows["a580"], rows["a585"]
        retained = dict(boot=key, first_diagnostic=dict(zip(DIAGNOSTIC, tuple_fields(diag, DIAGNOSTIC))),
            first_protection=dict(zip(PROTECTION, tuple_fields(diag, PROTECTION))),
            diagnostic_version=diag["version"],
            unavailable_fields=list(UNAVAILABLE_V2) if diag["version"] == 2 else list(UNAVAILABLE_V3) if diag['version']==3 else [],
            capabilities_source="decoded metadata" if "capabilities" in diag else "strict original v1 fields",
            last_controller_fault=primary["last_controller_fault"], controller_fault_count=primary["controller_fault_count"],
            last_rejected_tuple={k: diag[k] for k in ("latest_rejected_source_id", "latest_reader_fault",
                                  "latest_temporal_detail", "latest_rejected_raw_flags")},
            sticky_yaw_fault=info["sticky_yaw_fault"], event_sequence=info["event_sequence"],
            event_code=info["event_code"], event_pose_age_ticks=info["event_pose_age_ticks"],
            event_age_scope="retained gate event, NEVER live pose age")
        if len(self.sticky) < 20:
            self.sticky.append(retained)
        if diag["max_pose_gap_ticks"] >= POSE_GAP_LIMIT:
            self.issue("inconclusive", "old_global_max_pose_gap_masks_interval", diag["max_pose_gap_ticks"])
        if (diag["first_diagnostic_trigger"] or diag["first_protection_code"] or info["sticky_yaw_fault"]):
            self.issue("inconclusive", "retained_first_cause_at_interval_entry", key)

    def observe_interval(self, previous, rows, segment, time):
        old = previous["rows"]
        if old["a585"]["version"] != rows["a585"]["version"]:
            self.issue("inconclusive", "diagnostic_version_changed_inside_epoch")
        uptime_step = rows["a580"]["uptime_ms"] - old["a580"]["uptime_ms"]
        host_step = (time - previous["time"]).total_seconds()
        self.max_report_interval_ms = max(self.max_report_interval_ms, uptime_step)
        step = (rows["a579"]["sequence"] - old["a579"]["sequence"]) & 0xFFFF
        if not 0 < step < 0x8000 or uptime_step <= 0 or host_step < 0:
            self.issue("inconclusive", "nonprogressing_or_out_of_order_snapshot", step)
        elif step > 1:
            self.missing += step - 1
            self.issue("inconclusive", "missing_snapshot_sequences", step - 1)
        if 0 < step < 0x8000 and rows["a579"]["sequence"] < old["a579"]["sequence"]:
            self.wraps += 1
        if uptime_step > 0 and abs(uptime_step - step * 200) > 2:
            self.issue("inconclusive", "sequence_vs_onboard_period_mismatch", dict(step=step, uptime_ms=uptime_step))
        if host_step > .6:
            self.issue("inconclusive", "host_receive_gap", host_step)
        delta = {}
        for proto, names in COUNTERS.items():
            for name in names:
                full = proto + "." + name
                before, after = old[proto][name], rows[proto][name]
                counter = segment["counters"][full]
                value = after - before
                if full in SATURATING and after == before == 0xFFFFFFFF:
                    value = None
                elif value < 0:
                    if before >= 0xF0000000 and after < 0x10000000 and full not in SATURATING:
                        value &= 0xFFFFFFFF
                        counter["wraps"] += 1
                    else:
                        value = None
                delta[full] = value
                if value is None:
                    counter["unknown_intervals"] += 1
                    self.issue("inconclusive", "counter_reset_or_saturation", full)
                else:
                    counter["known_delta"] += value
        # Independent publication and consumed-source progress are mandatory.
        # No interpolation or assumption that accepted_count == pose_count.
        if uptime_step > 0 and (delta["a585.pose_count"] == 0 or delta["a585.consumed_accepted_id"] == 0):
            self.issue("fail", "pose_publication_or_consumed_source_stalled", dict(
                accepted_delta=delta["a585.accepted_count"], pose_delta=delta["a585.pose_count"],
                consumed_delta=delta["a585.consumed_accepted_id"]))
        publications = delta["a585.pose_count"]
        if (uptime_step > 0 and publications is not None and publications > 0 and
                (publications + 1) * POSE_GAP_LIMIT < uptime_step * TICKS_PER_MS):
            # A count/time lower bound on a publication gap, not fabricated samples.
            self.issue("fail", "pose_count_cannot_support_gap_limit", dict(
                publications=publications, interval_ms=uptime_step))
        if uptime_step > 0 and (delta["a585.raw_count"] == 0 or delta["a585.accepted_count"] == 0):
            self.issue("fail", "raw_or_accepted_stream_stalled", rows["a579"]["sequence"])
        for name in ("a579.controller_fault_count", "a579.rejected_count"):
            if delta[name] and delta[name] > 0:
                self.issue("fail", "new_" + name, delta[name])
        if delta["a579.command_count"] is not None and delta["a579.command_count"] > 0:
            self.issue("inconclusive", "new_control_transactions_while_reported_stopped",
                       dict(sequence=rows["a579"]["sequence"], command_delta=delta["a579.command_count"]))
        before, after = old["a585"], rows["a585"]
        if after["max_pose_gap_ticks"] < before["max_pose_gap_ticks"]:
            self.issue("inconclusive", "global_pose_gap_decreased_without_known_boot", after["max_pose_gap_ticks"])
        elif after["max_pose_gap_ticks"] > before["max_pose_gap_ticks"] and after["max_pose_gap_ticks"] >= POSE_GAP_LIMIT:
            self.issue("fail", "new_global_pose_gap_threshold_crossing", after["max_pose_gap_ticks"])
        for names, label in ((DIAGNOSTIC, "diagnostic"), (PROTECTION, "protection")):
            present = after["first_diagnostic_trigger"] if label == "diagnostic" else after["first_protection_code"]
            if tuple_fields(before, names) != tuple_fields(after, names) and present:
                event = dict(kind=label, observed_snapshot_uptime_ms=rows["a580"]["uptime_ms"],
                    observation_interval_uptime_ms=[old["a580"]["uptime_ms"], rows["a580"]["uptime_ms"]],
                    fields={k: after[k] for k in names})
                if label == "protection":
                    event["source_event_time_low32_available"] = after["version"] == 1
                if len(self.new_events) < 40:
                    self.new_events.append(event)
                if label == "diagnostic" and (after["first_diagnostic_trigger"] & 3 or
                        after["first_diagnostic_cause"] or after["first_diagnostic_attitude_fault"]):
                    self.issue("fail", "new_diagnostic_anomaly", event)
                else:
                    # Gate events can include an intentional landing lock;
                    # mask==0 must not be invented into a live hardware fault.
                    self.issue("inconclusive", "new_gate_or_protection_event_requires_context", event)
        if rows["a580"]["sticky_yaw_fault"] and rows["a580"]["sticky_yaw_fault"] != old["a580"]["sticky_yaw_fault"]:
            self.issue("fail", "new_sticky_yaw_fault", rows["a580"]["sticky_yaw_fault"])
        info = rows["a580"]
        if info["event_sequence"] != old["a580"]["event_sequence"]:
            event = dict(kind="retained_source_gate_event_changed", observed_snapshot_uptime_ms=info["uptime_ms"],
                observation_interval_uptime_ms=[old["a580"]["uptime_ms"], info["uptime_ms"]],
                fields={k: info[k] for k in ("event_sequence", "event_code", "event_sensor_mask",
                        "event_imu_reason", "event_attitude_fault", "event_pose_age_ticks")},
                age_scope="age at the recorded gate event, never live pose age")
            if len(self.new_events) < 40:
                self.new_events.append(event)
            health = (info["event_code"] >> 4 & 3) == 3 and info["event_code"] & 3
            severity = "fail" if health and any(info[k] for k in (
                "event_sensor_mask", "event_imu_reason", "event_attitude_fault")) else "inconclusive"
            self.issue(severity, "new_source_gate_event_requires_context", event)
        if (before["version"] == after["version"] == 1 and
                after["latest_rejected_source_id"] != before["latest_rejected_source_id"]):
            self.issue("fail", "new_rejected_source_tuple", {
                k: after[k] for k in ("latest_rejected_source_id", "latest_reader_fault",
                                     "latest_temporal_detail", "latest_rejected_raw_flags")})

    def report(self):
        if self.complete < 2:
            self.issue("inconclusive", "insufficient_complete_snapshots")
        if len(self.boots) != 1:
            self.issue("inconclusive", "not_one_continuous_source_epoch", len(self.boots))
        observed_s = (self.last_time - self.first_time).total_seconds() if self.first_time else 0
        board_spans = [(b["last_uptime_ms"] - b["first_uptime_ms"]) / 1000 for b in self.boots.values()]
        if observed_s < MIN_STABLE_SECONDS or not board_spans or min(board_spans) < MIN_STABLE_SECONDS:
            self.issue("inconclusive", "less_than_60s_stable_observed_coverage", dict(host_s=observed_s, onboard_s=board_spans))
        if self.first_time and ((self.first_time - self.start).total_seconds() > EDGE_TOLERANCE_S or
                                (self.end - self.last_time).total_seconds() > EDGE_TOLERANCE_S):
            self.issue("inconclusive", "selected_window_edges_not_covered")
        for segment in self.boots.values():
            counters = segment["counters"]
            accepted, pose = counters["a585.accepted_count"], counters["a585.pose_count"]
            segment["pose_to_accepted_known_delta_ratio"] = (
                pose["known_delta"] / accepted["known_delta"]
                if accepted["known_delta"] and not accepted["unknown_intervals"] and not pose["unknown_intervals"] else None)
            balance = dict(accepted_delta=accepted["known_delta"], pose_delta=pose["known_delta"],
                endpoint_sample_allowance=COUNT_ENDPOINT_ALLOWANCE, relative_limit=RELATIVE_COUNT_TOLERANCE,
                absolute_difference=None, relative_difference_after_allowance=None, assessed=False)
            if segment["pose_to_accepted_known_delta_ratio"] is not None:
                difference = abs(pose["known_delta"] - accepted["known_delta"])
                relative = max(0, difference - COUNT_ENDPOINT_ALLOWANCE) / accepted["known_delta"]
                balance.update(absolute_difference=difference, relative_difference_after_allowance=relative)
                if (segment["last_uptime_ms"] - segment["first_uptime_ms"]) >= MIN_STABLE_SECONDS * 1000:
                    balance["assessed"] = True
                    if relative > RELATIVE_COUNT_TOLERANCE:
                        self.issue("inconclusive", "publication_acceptance_total_mismatch", balance.copy())
            segment["publication_acceptance_balance"] = balance
            raw, rejected = counters["a585.raw_count"], counters["a579.rejected_count"]
            decisions = dict(raw_delta=raw["known_delta"], accepted_delta=accepted["known_delta"],
                rejected_delta=rejected["known_delta"], endpoint_sample_allowance=COUNT_ENDPOINT_ALLOWANCE,
                raw_minus_decisions=None, accepted_excess_over_raw_after_allowance=None,
                unaccounted_raw_after_allowance=None, assessed=False)
            if not any(c["unknown_intervals"] for c in (raw, accepted, rejected)):
                difference = raw["known_delta"] - accepted["known_delta"] - rejected["known_delta"]
                decisions.update(raw_minus_decisions=difference,
                    accepted_excess_over_raw_after_allowance=max(0, accepted["known_delta"] - raw["known_delta"] - COUNT_ENDPOINT_ALLOWANCE),
                    unaccounted_raw_after_allowance=max(0, difference - COUNT_ENDPOINT_ALLOWANCE))
                if (segment["last_uptime_ms"] - segment["first_uptime_ms"]) >= MIN_STABLE_SECONDS * 1000:
                    decisions["assessed"] = True
                    if abs(difference) > COUNT_ENDPOINT_ALLOWANCE:
                        self.issue("inconclusive", "raw_accept_reject_total_mismatch", decisions.copy())
            segment["raw_accept_reject_balance"] = decisions
        status = "fail" if self.issues["fail"] else "inconclusive" if self.issues["inconclusive"] else "acceptable"
        return dict(status=status, bench_data_acceptable=status == "acceptable", flight_ready=False,
            installation_authorized=False,
            scope="Screening of complete decoded B0B2 v1/v2/v3 snapshot groups only; no transport-integrity or flight acceptance",
            coverage=dict(candidate_snapshots=self.groups, complete_unique_snapshots=self.complete,
                diagnostic_version_counts=dict(self.diagnostic_versions),
                original_v1_snapshots_with_capabilities_inferred=self.inferred_v1_capabilities,
                protocol_counts=dict(self.received), duplicate_snapshots=self.duplicates,
                missing_protocol_records=dict(self.missing_protocols),
                duplicate_protocol_records=dict(self.duplicate_protocols),
                primary_sequence_gaps_lower_bound=self.primary_missing,
                duplicate_primary_sequences=self.primary_duplicates,
                missing_complete_snapshot_sequences_lower_bound=self.missing, sequence_wraps=self.wraps,
                observed_host_span_s=observed_s, onboard_spans_s=board_spans,
                maximum_onboard_report_interval_ms=self.max_report_interval_ms),
            source_epochs=self.boots, maximum_live_age_ticks={k:None if self.age_unavailable_counts[k] and not self.age_valid_counts[k] else v for k,v in self.ages.items()},
            maximum_live_age_ms={k:None if self.age_unavailable_counts[k] and not self.age_valid_counts[k] else v/TICKS_PER_MS for k,v in self.ages.items()},
            unavailable_age_sample_counts=dict(self.age_unavailable_counts),
            valid_age_sample_counts=dict(self.age_valid_counts), flags={k: dict(v) for k, v in self.flags.items()},
            maximum_held_dt_ticks=self.max_held_dt_ticks,
            reported_idle_state=self.idle_observations,
            retained_first_causes=self.sticky, newly_observed_first_cause_changes=self.new_events,
            issues={k: dict(v) for k, v in self.issues.items()}, examples=self.examples)


def analyze(path, start_utc, end_utc, stable_after_s):
    """Stream the original recorder JSONL; never join dashboard snapshots."""
    path = Path(path)
    start, end = utc(start_utc), utc(end_utc)
    if not math.isfinite(stable_after_s) or stable_after_s < 0 or start >= end:
        raise ValueError("Invalid time window or settling interval")
    stable = start + timedelta(seconds=stable_after_s)
    if stable >= end:
        raise ValueError("Settling interval consumes the selected window")
    evaluation = Evaluation(stable, end)
    digest = hashlib.sha256()
    before = path.stat()
    group = None
    last_info = None
    generation = 0
    previous_order = -1
    total = malformed = orphans = source_rollbacks = hashed_bytes = 0
    with path.open("rb") as stream:
        for line_no, line in enumerate(stream, 1):
            digest.update(line)
            hashed_bytes += len(line)
            total += 1
            try:
                outer = json.loads(line)
                row = outer["row"]
                time = utc(outer["utc"])
                if not isinstance(row, dict) or not all(integer(outer.get(k)) for k in ("epoch", "host_ns", "record_order")):
                    raise ValueError("Not a raw recorder protocol record")
            except (ValueError, TypeError, KeyError):
                malformed += 1
                evaluation.issue("inconclusive", "unplaceable_or_malformed_record", line_no)
                continue
            if outer["record_order"] <= previous_order:
                evaluation.issue("inconclusive", "nonmonotonic_record_order", line_no)
            previous_order = outer["record_order"]
            proto = row.get("_protocol")
            if proto not in PROTOCOLS:
                continue
            entry = dict(row=row, time=time, epoch=outer["epoch"], host_ns=outer["host_ns"])
            if proto == "a580" and integer(row.get("uptime_ms")) and integer(row.get("build_id")):
                if last_info and (row["build_id"] != last_info[0] or row["uptime_ms"] < last_info[1]):
                    generation += 1
                    source_rollbacks += 1
                last_info = row["build_id"], row["uptime_ms"]
            if proto == "a579":
                evaluation.finish(group)
                group = dict(seq=row.get("sequence"), first=entry, rows={proto: entry},
                             counts=Counter({proto: 1}), bad=[], generation=generation)
            elif group is None:
                if evaluation.in_window(time):
                    orphans += 1
                    evaluation.issue("inconclusive", "orphan_protocol_record", proto)
            else:
                group["counts"][proto] += 1
                if proto in group["rows"]:
                    group["bad"].append("duplicate " + proto)
                if PROTOCOLS.index(proto) != len(group["rows"]):
                    group["bad"].append("wire protocol order mismatch " + proto)
                if row.get("sequence") != group["seq"]:
                    group["bad"].append("sequence mismatch " + proto)
                group["rows"][proto] = entry
                if proto == "a580":
                    group["generation"] = generation
                if proto == "a585":
                    evaluation.finish(group)
                    group = None
    evaluation.finish(group)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        evaluation.issue("inconclusive", "input_changed_during_analysis")
    report = evaluation.report()
    report.update(schema="b0b2.offline-bench-data-evaluation.v1",
        input=dict(path=str(path.resolve()), sha256=digest.hexdigest(), bytes_hashed=hashed_bytes,
                   initial_stat_bytes=before.st_size, final_stat_bytes=after.st_size,
                   lines=total, malformed_records=malformed, orphan_protocol_records=orphans,
                   observed_A580_identity_or_uptime_rollbacks=source_rollbacks),
        tool=dict(path=str(Path(__file__).resolve()), sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
        selection=dict(start_utc=start.isoformat(), end_utc=end.isoformat(), stable_after_s=stable_after_s,
                       evaluation_start_utc=stable.isoformat()),
        policy=dict(required_protocols=list(PROTOCOLS), identity=BUILD, minimum_stable_seconds=60,
                    supported_diagnostic_versions=[1, 2, 3],
                    v3_unavailable_fields=list(UNAVAILABLE_V3),
                    v2_unavailable_fields=list(UNAVAILABLE_V2),
                    new_rejection_source="Primary rejected_count; v1/v3 additionally retain rejected source ID",
                    publication_acceptance_relative_tolerance=RELATIVE_COUNT_TOLERANCE,
                    publication_acceptance_endpoint_sample_allowance=COUNT_ENDPOINT_ALLOWANCE,
                    raw_accept_reject_endpoint_sample_allowance=COUNT_ENDPOINT_ALLOWANCE,
                    stopped_control_transaction_increment_limit=0,
                    expected_snapshot_period_ms=200, bench_live_age_limit_ms=20,
                    hardware_pose_age_protection_limit_ms=None if '3' in evaluation.diagnostic_versions else PROTECTION_AGE_LIMIT / TICKS_PER_MS,
                    independent_control_command_timeout_ms=60,
                    held_dt_exclusive_bounds_ms=[0, 20],
                    global_pose_gap_limit_ms=20,
                    maximum_protocol_group_span_ms=500, accepted_counter_alone_sufficient=False),
        transport_integrity=dict(crc_error_count=None, length_error_count=None,
            discarded_noise_bytes=None, recorder_dropped_chunks=None,
            scope="Unknown from decoded JSONL alone; bad/noise/nonrequired frames may produce no row"),
        limitations=["Decoded JSONL integrity is hash-bound; this tool does not revalidate raw.bin CRCs.",
            "Policy v3 explicitly removes pose age; null is unavailable, never zero/fresh. Independent command timeouts and numerical dt limits remain. Completed pose intervals do not advance during silence.",
            "A579/A57A carry no identity/uptime: only their contiguous same-sequence recorder group is joined to exact-matching A580/A585 uptime/build, within one receiver epoch.",
            "A580 event_pose_age_ticks and A585 first-protection age are retained event fields, never current pose age.",
            "A57A raw fields are latest accepted raw, not an independent native reader stream; A585 rejected-raw flags are retained rejection metadata.",
            "A585 v2 has no latest rejected source ID or first-protection exact source time. Its mandatory capability metadata marks both null, not zero; new rejects are detected from A579 rejected_count and a protection change is bracketed only by surrounding snapshots.",
            "The 5Hz snapshots do not reconstruct or interpolate 1kHz data. A585 maximum publication gap is global since boot and includes invalid publications.",
            "Missing decoded protocol coverage and sequence gaps do not identify RF loss versus CRC failure, source omission or host drop; raw/chunk/recorder diagnostics are not assessed here.",
            "The settling trim is explicitly selected by the operator; telemetry alone does not verify physical stillness or that propellers were removed.",
            "New controller transactions conflict with the selected stopped interval. Raw records must account for accepts plus rejects over the stable total, allowing two endpoint pipeline samples; these are consistency checks, not assumed sample rates.",
            "Idle command and physical/effective motor widths are reported schedules, not oscilloscope measurements or observed motor motion. CH3/CH5/CH7 are original A579 fields, including its extension.",
            "An already excessive sticky global maximum or retained first cause at entry cannot certify this later interval; the result stays inconclusive unless a direct new anomaly makes it fail.",
            "Bench observations do not prove vibration/load coverage, motor waveform, electrical health or flight readiness."],
        hardware_accessed=False)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True, help="Explicit recorder telemetry.jsonl file")
    parser.add_argument("--start-utc", required=True, help="Inclusive UTC/offset-aware capture-window start")
    parser.add_argument("--end-utc", required=True, help="Inclusive UTC/offset-aware capture-window end")
    parser.add_argument("--stable-after-s", type=float, required=True, help="Explicit settling trim from window start")
    parser.add_argument("--output", type=Path, required=True, help="New JSON report; never overwritten")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.resolve() == args.input.resolve():
        parser.error("Output must be a new file distinct from the input")
    try:
        report = analyze(args.input, args.start_utc, args.end_utc, args.stable_after_s)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(dict(status=report["status"], flight_ready=False, output=str(args.output)), ensure_ascii=False))
    return {"acceptable": 0, "fail": 1, "inconclusive": 3}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
