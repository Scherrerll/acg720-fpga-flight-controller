"""Independent A584/v1 decoder. No serial access and no control imports.

The wire contract is ../DIAGNOSTIC_PROTOCOL.md. Capture ticks and acceptance
IDs are evidence; host timestamps never establish sample identity.
"""
from __future__ import annotations

import binascii
import collections
import struct

MAGIC = b"\xa5\x84"
VERSION = 1
BUILD_ID = 0xB0B1
TICKS_PER_MS = 50_000
MOD32 = 1 << 32
PAYLOAD_LENGTHS = {1: 26, 2: 28, 3: 88, 4: 40}
TYPE_NAMES = {1: "raw", 2: "pose", 3: "fault", 4: "status"}
CAUSES = {
    0: "none_recorded", 1: "link_loss", 2: "recovery_reject_cancellation",
    3: "accepted_sample_busy_collision", 4: "raw_sentinel", 5: "dt_limit",
    6: "recovery_gravity_failure", 7: "zero_recovery_norm",
    8: "arithmetic_numeric_failure", 9: "calibration_failure",
}
DROP_FIELDS = ("dropped_raw", "dropped_pose", "dropped_fault", "dropped_status")


class ProtocolError(ValueError):
    pass


def decode_payload(version: int, frame_type: int, payload: bytes) -> dict:
    """Decode exactly one fixed payload; reject unsupported/short/long data."""
    if version != VERSION or frame_type not in PAYLOAD_LENGTHS:
        raise ProtocolError("unsupported version/type")
    if len(payload) != PAYLOAD_LENGTHS[frame_type]:
        raise ProtocolError("payload length does not match fixed wire contract")
    if frame_type == 1:
        keys = ("source_id", "ax", "ay", "az", "gx", "gy", "gz",
                "accepted_count", "temporal_detail", "reader_fault", "flags",
                "quiet_count", "recovery_count", "estimator_state")
        r = dict(zip(keys, struct.unpack(">I6hI6B", payload)))
        for bit, key in enumerate(("reader_valid", "config_ok", "checked_base_ok",
                                   "accepted", "link_usable", "guard_qualified",
                                   "attitude_valid", "candidate_pending")):
            r[key] = bool(r["flags"] & (1 << bit))
        r["physical_observation_valid"] = r["reader_valid"] and r["config_ok"]
        # Retain integer words even when invalid; never promote them to a sample.
        r["acceleration_g"] = [r[k] / 2048 for k in ("ax", "ay", "az")]
        r["gyro_deg_s"] = [r[k] / 16.4 for k in ("gx", "gy", "gz")]
    elif frame_type == 2:
        keys = ("consumed_accepted_id", "held_dt_ticks", "world_ax", "world_ay",
                "world_az", "sensor_roll_cdeg", "sensor_pitch_cdeg",
                "sensor_yaw_cdeg", "flags", "attitude_fault")
        r = dict(zip(keys, struct.unpack(">II3i3hBB", payload)))
        if r["flags"] & 0xC0:
            raise ProtocolError("reserved pose flag bits are set")
        for bit, key in enumerate(("attitude_valid", "linear_accel_valid",
                                   "calibrated", "initialized", "ready", "reseed")):
            r[key] = bool(r["flags"] & (1 << bit))
        r["coordinate_frame"] = "sensor_world_x_forward_y_left_z_up"
    elif frame_type == 3:
        keys = ("trigger_flags", "first_cause", "attitude_fault", "temporal_detail",
                "rejected_source_id", "accepted_count", "consumed_accepted_id",
                "pose_count", "last_accept_tick", "last_pose_tick",
                "max_accept_gap_ticks", "busy_age_ticks", "pose_age_ticks",
                "accepted_age_ticks", "estimator_state", "resume_state",
                "recovery_count", "reseed_count", "state_flags", "quiet_count",
                "reader_fault")
        words = struct.unpack(">4B10I4BH2B18h", payload)
        r = dict(zip(keys, words[:len(keys)]))
        for index, name in enumerate(("rejected_raw", "trusted", "candidate")):
            r[name] = dict(zip(("ax", "ay", "az", "gx", "gy", "gz"),
                               words[len(keys) + index * 6:len(keys) + (index + 1) * 6]))
        r["rejected_tuple_exists"] = r["rejected_source_id"] != 0
        r["first_cause_name"] = CAUSES.get(r["first_cause"], "unknown_cause")
        r["triggers"] = [name for bit, name in enumerate(
            ("pose_age_20ms", "attitude_valid_fall", "gate_event"))
            if r["trigger_flags"] & (1 << bit)]
    else:
        keys = ("uptime_ms", "build_id", *DROP_FIELDS,
                "max_accept_gap_ticks", "raw_count", "pose_count")
        r = dict(zip(keys, struct.unpack(">Q8I", payload)))
        if r["build_id"] != BUILD_ID:
            raise ProtocolError("status build_id is not B0B1")
        r["saturated_drop_counters"] = [k for k in DROP_FIELDS if r[k] == 0xFFFFFFFF]
    return r


class FrameParser:
    """Incremental fixed-length parser; bad/unknown headers resume byte scanning."""

    def __init__(self):
        self.buffer = bytearray()
        self.offset = 0
        self.eof_partial_candidates = 0
        self.stats = collections.Counter(bytes_received=0, valid_frames=0,
            crc_errors=0, unknown_versions=0, unknown_types=0, payload_errors=0,
            discarded_bytes=0, trailing_bytes=0, truncated_frames=0,
            eof_recovered_frames=0)

    def _discard(self, count, noise=False):
        del self.buffer[:count]
        self.offset += count
        if noise:
            self.stats["discarded_bytes"] += count

    def feed(self, data: bytes) -> list[dict]:
        self.stats["bytes_received"] += len(data)
        self.buffer.extend(data)
        result = []
        while True:
            at = self.buffer.find(MAGIC)
            if at < 0:
                keep = 1 if self.buffer.endswith(MAGIC[:1]) else 0
                self._discard(len(self.buffer) - keep, noise=True)
                break
            if at:
                self._discard(at, noise=True)
            if len(self.buffer) < 4:
                break
            version, typ = self.buffer[2:4]
            if version != VERSION:
                self.stats["unknown_versions"] += 1
                self._discard(1, noise=True)
                continue
            if typ not in PAYLOAD_LENGTHS:
                self.stats["unknown_types"] += 1
                self._discard(1, noise=True)
                continue
            size = 12 + PAYLOAD_LENGTHS[typ]
            if len(self.buffer) < size:
                break
            packet = bytes(self.buffer[:size])
            if binascii.crc_hqx(packet[2:-2], 0xFFFF) != int.from_bytes(packet[-2:], "big"):
                self.stats["crc_errors"] += 1
                self._discard(1, noise=True)
                continue
            _, _, seq, tick = struct.unpack(">BBHI", packet[2:10])
            try:
                payload = decode_payload(version, typ, packet[10:-2])
            except ProtocolError:
                self.stats["payload_errors"] += 1
            else:
                result.append(dict(kind="frame", version=version, type=TYPE_NAMES[typ],
                    type_code=typ, sequence=seq, capture_tick=tick,
                    byte_start=self.offset, byte_end=self.offset + size, payload=payload))
                self.stats["valid_frames"] += 1
            self._discard(size)
        return result

    def recover_eof(self) -> list[dict]:
        """At known EOF, skip incomplete outer candidates to salvage valid tails.

        During a live stream, a short candidate must wait for fragmentation.
        At EOF it cannot become complete, so later complete CRC-valid frames
        must not be hidden behind a corrupted long-type header.
        """
        recovered = []
        while True:
            recovered.extend(self.feed(b""))
            if not self.buffer.startswith(MAGIC):
                break
            self.eof_partial_candidates += 1
            self._discard(1, noise=True)
        self.stats["eof_recovered_frames"] += len(recovered)
        return recovered

    def finish(self) -> dict:
        self.stats["trailing_bytes"] = len(self.buffer)
        self.stats["truncated_frames"] = self.eof_partial_candidates + int(self.buffer.startswith(MAGIC))
        return dict(self.stats)


def _backwards_u32(before, after):
    return after < before and before - after < (1 << 31)


class StreamTracker:
    """Sequence/epoch/tick accounting and exact, bounded raw-to-pose joins.

    Status uptime is authoritative for reboot and long captures. A simultaneous
    raw source/acceptance counter reset can identify reboot before status. Other
    backward sequences are reported as ambiguous, never expanded to huge gaps.
    """

    def __init__(self, join_limit=8192):
        if join_limit < 1:
            raise ValueError("join_limit must be positive")
        self.join_limit = join_limit
        self.epoch = 0
        self.epochs = []
        self.stats = collections.Counter(sequence_missing=0, sequence_gap_events=0,
            duplicate_sequences=0, backward_sequences=0, joined_poses=0,
            evicted_raw_records=0, evicted_unmatched_poses=0, reboot_events=0)
        self._reset_epoch("capture_start")

    def _reset_epoch(self, reason):
        if hasattr(self, "pending"):
            self.current["unmatched_poses_at_epoch_end"] = sum(map(len, self.pending.values()))
        self.previous_sequence = None
        self.previous_capture_tick = None
        self.status = None
        self.anchor = None
        self.ticks = {}
        self.last_raw = None
        self.raw = collections.OrderedDict()
        self.pending = collections.OrderedDict()
        self.current = dict(epoch=self.epoch, start_reason=reason, frames=0,
            type_counts=collections.Counter(), first_fault=None, first_status=None,
            fault_captures=[], latest_status=None, joined_poses=0, counter_regressions=[])
        self.epochs.append(self.current)

    def _new_epoch(self, reason):
        self.epoch += 1
        self.stats["reboot_events"] += 1
        self._reset_epoch(reason)

    def _unwrap(self, typ, tick):
        if self.anchor is not None:
            anchor_tick, uptime = self.anchor
            ext = tick + ((anchor_tick - tick + (1 << 31)) // MOD32) * MOD32
            basis = "status_uptime_anchor"
        elif typ in self.ticks:
            prev_tick, prev_ext = self.ticks[typ]
            delta = ((tick - prev_tick + (1 << 31)) % MOD32) - (1 << 31)
            ext = prev_ext + delta
            basis = "per_type_modulo_unanchored"
        else:
            ext, basis = tick, "initial_tick_unanchored"
        self.ticks[typ] = (tick, ext)
        return ext, basis

    def _join(self, raw, pose):
        r, p = raw["payload"], pose["payload"]
        self.stats["joined_poses"] += 1
        self.current["joined_poses"] += 1
        return dict(kind="pose_raw_join", epoch=self.epoch,
            accepted_id=p["consumed_accepted_id"], raw_source_id=r["source_id"],
            raw_sequence=raw["sequence"], pose_sequence=pose["sequence"],
            raw_capture_tick=raw["capture_tick"], pose_capture_tick=pose["capture_tick"],
            held_dt_ticks=p["held_dt_ticks"],
            publication_gap_ticks_mod32=(pose["capture_tick"] - raw["capture_tick"]) % MOD32,
            identity_basis="same_epoch_exact_accepted_id", interpolation=False)

    def ingest(self, frame: dict) -> list[dict]:
        f = dict(frame)
        p, typ = f["payload"], f["type"]
        if typ == "status" and self.status and p["uptime_ms"] < self.status["uptime_ms"]:
            self._new_epoch("status_uptime_regression")
        elif (self.previous_sequence is not None and f["sequence"] < 16
                and (f["sequence"] - self.previous_sequence) % 65536 >= 32768
                and self.previous_capture_tick is not None
                and _backwards_u32(self.previous_capture_tick, f["capture_tick"])):
            self._new_epoch("transmit_sequence_and_capture_tick_restart")
        elif typ == "raw" and self.last_raw:
            old = self.last_raw
            if (_backwards_u32(old["source_id"], p["source_id"])
                    and _backwards_u32(old["accepted_count"], p["accepted_count"])):
                self._new_epoch("raw_source_and_acceptance_counter_reset")
        f["epoch"] = self.epoch
        if self.previous_sequence is not None:
            delta = (f["sequence"] - self.previous_sequence) % 65536
            if delta == 0:
                self.stats["duplicate_sequences"] += 1
                f["sequence_duplicate"] = True
                return [f]
            if delta >= 32768:
                self.stats["backward_sequences"] += 1
                f["sequence_order_ambiguous"] = True
            elif delta > 1:
                self.stats["sequence_missing"] += delta - 1
                self.stats["sequence_gap_events"] += 1
                f["missing_before"] = delta - 1
        self.previous_sequence = f["sequence"]
        # A frozen fault snapshot may be much older than its transmit order.
        if typ != "fault":
            self.previous_capture_tick = f["capture_tick"]
        if typ == "status":
            # Uptime anchors multiple tick wraps; difference within an ms is
            # expected because uptime is quantized. Never use host time here.
            tick = f["capture_tick"]
            extended = tick + ((p["uptime_ms"] * TICKS_PER_MS - tick + (1 << 31)) // MOD32) * MOD32
            self.anchor = (extended, p["uptime_ms"])
            if self.status:
                for key in DROP_FIELDS:
                    if p[key] < self.status[key]:
                        self.current["counter_regressions"].append(key)
            self.status = p
            if self.current["first_status"] is None:
                self.current["first_status"] = dict(p)
            self.current["latest_status"] = dict(p)
        tick64, basis = self._unwrap(typ, f["capture_tick"])
        f["capture_tick64"], f["tick_basis"] = tick64, basis
        if self.anchor:
            uptime_ticks = self.anchor[1] * TICKS_PER_MS + tick64 - self.anchor[0]
            f["onboard_uptime_ms_floor"] = uptime_ticks // TICKS_PER_MS
            f["onboard_sub_ms_ticks"] = uptime_ticks % TICKS_PER_MS
            f["onboard_uptime_ms_estimate"] = uptime_ticks / TICKS_PER_MS
            f["uptime_estimate_uncertainty_ms"] = 1
        self.current["frames"] += 1
        self.current["type_counts"][typ] += 1
        result = [f]
        if typ == "fault":
            fault = dict(sequence=f["sequence"],
                capture_tick=f["capture_tick"], first_cause=p["first_cause"],
                first_cause_name=p["first_cause_name"], triggers=p["triggers"],
                rejected_source_id=p["rejected_source_id"],
                pose_age_ticks=p["pose_age_ticks"], accepted_age_ticks=p["accepted_age_ticks"])
            self.current["fault_captures"].append(fault)
            if self.current["first_fault"] is None:
                self.current["first_fault"] = fault
        elif typ == "raw":
            self.last_raw = p
            if p["accepted"] and p["physical_observation_valid"]:
                key = p["accepted_count"]
                self.raw[key] = f
                for pose in self.pending.pop(key, []):
                    result.append(self._join(f, pose))
                while len(self.raw) > self.join_limit:
                    self.raw.popitem(last=False)
                    self.stats["evicted_raw_records"] += 1
        elif typ == "pose":
            key = p["consumed_accepted_id"]
            if key in self.raw:
                result.append(self._join(self.raw[key], f))
            else:
                self.pending.setdefault(key, []).append(f)
                while sum(map(len, self.pending.values())) > self.join_limit:
                    _, evicted = self.pending.popitem(last=False)
                    self.stats["evicted_unmatched_poses"] += len(evicted)
        return result

    def summary(self) -> dict:
        epochs = []
        for item in self.epochs:
            e = dict(item)
            e["type_counts"] = dict(item["type_counts"])
            if item is self.current:
                e["unmatched_poses_at_epoch_end"] = sum(map(len, self.pending.values()))
            first, last = item["first_status"], item["latest_status"]
            e["producer_drop_cumulative"] = {k: last[k] for k in DROP_FIELDS} if last else None
            e["producer_drop_observed_delta"] = ({k: last[k] - first[k] for k in DROP_FIELDS}
                if last and not item["counter_regressions"] else None)
            epochs.append(e)
        return dict(stats=dict(self.stats), epochs=epochs, join_limit=self.join_limit,
            limitations=[
                "Missing samples are never interpolated. An unmatched pose is not proof of no onboard publication.",
                "No raw/pose join crosses epochs or substitutes source_id for accepted_count.",
                "Before status, epoch and tick extension can be provisional; a reboot without counter-reset/status evidence is unresolvable.",
                "Nearest-anchor tick extension assumes less than half a tick wrap (42.95s) queue delay; original ticks are always retained.",
                "Sequence gaps measure transmitted frames absent here; status producer-drop counters measure a different loss boundary.",
                "First cause is the firmware diagnostic label, not an independently proven physical root cause."])
