"""ACG720 telemetry viewer and guarded level-reference capture. No serial writes."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import secrets
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit
from readonly_calibration import CalibrationError, LevelCalibration

HERE = Path(__file__).resolve().parent
DEFAULT_DECODER = HERE / 'monitor_control.py'
OPTIONAL_DECODERS = []
CLK_HZ = 50_000_000
FRAME_FRESH_SECONDS = 0.5
POSE_FRESH_TICKS = 3_000_000
SERIAL_BAUD = 115200
RANGE_HEADER = b"\xa5\x7b"
RANGE_COUNTERS = ("framing","checksum","interbyte_timeout","distance","weak_signal")
ACCEL_HEADER = b"\xa5\x7a"
ACCEL_FIELDS = ("linear_accel_x_m_s2", "linear_accel_y_m_s2", "linear_accel_z_m_s2",
                "sensor_accel_x_m_s2", "sensor_accel_y_m_s2", "sensor_accel_z_m_s2")


def load_decoder(path: Path):
    """Reuse the FPGA project's authoritative packet size/checksum decoder."""
    spec = importlib.util.spec_from_file_location(f"telemetry_{path.stem}_{id(path)}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load decoder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module.HEADER, bytes) or len(module.HEADER) != 2:
        raise ValueError("Decoder HEADER must be two bytes")
    if not 4 <= module.SIZE <= 4096 or not callable(module.decode):
        raise ValueError("Decoder must provide SIZE and decode(packet)")
    return module


class PacketReceiver:
    """Resynchronize mixed registered protocols without trusting corrupt packets."""

    def __init__(self, decoders):
        expanded = []
        for decoder in decoders:
            expanded.append(decoder)
            for attribute in ("ACCEL_DECODER","RANGE_DECODER"):
                extra = getattr(decoder, attribute, None)
                if extra is not None:expanded.append(extra)
        self.protocols = {}
        for decoder in expanded:
            if not isinstance(decoder.HEADER, bytes) or len(decoder.HEADER) != 2 or not 4 <= decoder.SIZE <= 4096 or not callable(decoder.decode):
                raise ValueError("Decoder must provide two-byte HEADER, SIZE and decode(packet)")
            if decoder.HEADER == ACCEL_HEADER and decoder.SIZE != 32:
                raise ValueError("A57A acceleration metadata must be32bytes")
            if decoder.HEADER==RANGE_HEADER and decoder.SIZE!=48:raise ValueError("A57B range metadata must be48bytes")
            self.protocols[decoder.HEADER] = (decoder.SIZE, decoder.decode)
        if not self.protocols:
            raise ValueError("At least one decoder is required")
        self.buffer = bytearray()
        self.checksum_errors = 0
        self.discarded_bytes = 0
        self.acceleration_checksum_errors = 0
        self.acceleration_discarded_bytes = 0
        self.metadata_reject_remaining = 0
        self.metadata_reject_header=None
        self.range_diagnostic_checksum_errors=0
        self.range_diagnostic_discarded_bytes=0

    def discard_prefix(self, count):
        metadata_count = min(count, self.metadata_reject_remaining)
        if self.metadata_reject_header==RANGE_HEADER:self.range_diagnostic_discarded_bytes+=metadata_count
        else:self.acceleration_discarded_bytes+=metadata_count
        self.metadata_reject_remaining -= metadata_count
        self.discarded_bytes += count - metadata_count
        del self.buffer[:count]

    def feed(self, data: bytes):
        self.buffer.extend(data)
        rows = []
        while True:
            matches = [(self.buffer.find(h), h) for h in self.protocols]
            matches = [(i, h) for i, h in matches if i >= 0]
            if not matches:
                keep = int(any(self.buffer.endswith(h[:1]) for h in self.protocols))
                self.discard_prefix(len(self.buffer) - keep)
                break
            index, header = min(matches)
            self.discard_prefix(index)
            size, decode = self.protocols[header]
            if len(self.buffer) < size:
                break
            try:
                row = decode(bytes(self.buffer[:size]))
            except (ValueError, OverflowError):
                if header in (ACCEL_HEADER,RANGE_HEADER):
                    if header==ACCEL_HEADER:
                        self.acceleration_checksum_errors += 1
                        self.acceleration_discarded_bytes += 1
                    else:
                        self.range_diagnostic_checksum_errors+=1
                        self.range_diagnostic_discarded_bytes+=1
                    self.metadata_reject_header=header
                    self.metadata_reject_remaining = size - 1
                    # Retain rejection order within a mixed receive chunk. This
                    # invalidates display metadata, never publishes a main frame.
                    rows.append({"_protocol": header.hex(), "_acceleration_invalid" if header==ACCEL_HEADER else "_range_invalid": True})
                else:
                    self.checksum_errors += 1
                    self.metadata_reject_remaining = 0
                del self.buffer[0]
                continue
            rows.append({**row, "_protocol": header.hex()})
            del self.buffer[:size]
            self.metadata_reject_remaining = 0
        return rows


def first(row, *names, default=None):
    return next((row[name] for name in names if name in row), default)


def valid_flag(value):
    # Unknown strings/configuration never make an absent sensor or scale valid.
    return value is True or type(value) is int and value == 1


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def acceleration_fields(metadata=None, primary=None, frame_age_seconds=0.0):
    """Two distinct measured accelerations; absent or expired values stay null."""
    fields = dict.fromkeys(ACCEL_FIELDS)
    fields.update(linear_accel_valid=False, sensor_accel_valid=False,
                  acceleration_missing=metadata is None,
                  acceleration_reported=metadata is not None,
                  linear_accel_age_ms=None, sensor_accel_age_ms=None,
                  acceleration_frame_age_ms=None, acceleration_telemetry_hz=10,
                  acceleration_age_basis="FPGA snapshot source age",
                  linear_accel_frame="relative_world_initial_heading_x_forward_y_right_z_up",
                  linear_accel_gravity_removed=True,
                  sensor_accel_frame="sensor_x_forward_y_left_z_up",
                  sensor_accel_gravity_removed=False)
    if metadata is None or primary is None:
        return fields
    if not finite(frame_age_seconds) or not 0 <= frame_age_seconds < FRAME_FRESH_SECONDS:
        fields.update(acceleration_reported=False, acceleration_missing=True)
        return fields
    flags = metadata.get("accel_flags")
    pose_age = metadata.get("pose_age_ticks")
    raw_age = metadata.get("raw_age_ticks")
    if type(flags) is not int or not 0 <= flags <= 3:
        return fields
    def fresh_age(age):
        return type(age) is int and 0 <= age < POSE_FRESH_TICKS
    fields["linear_accel_age_ms"] = pose_age / CLK_HZ * 1000 if type(pose_age) is int and pose_age >= 0 else None
    fields["sensor_accel_age_ms"] = raw_age / CLK_HZ * 1000 if type(raw_age) is int and raw_age >= 0 else None
    fields["acceleration_frame_age_ms"] = frame_age_seconds * 1000
    linear = [metadata.get(name) for name in ("world_ax_mmps2", "world_ay_mmps2", "world_az_up_mmps2")]
    raw = [metadata.get(name) for name in ("raw_ax", "raw_ay", "raw_az")]
    # Both packets share one FPGA snapshot, including its pose-age value.
    coherent_pose = type(primary.get("pose_age_ticks")) is int and pose_age == primary["pose_age_ticks"]
    primary_flags = primary.get("flags", 0)
    linear_valid = (type(primary_flags) is int and primary_flags & 6 == 6 and flags & 1 and
                    coherent_pose and fresh_age(pose_age) and
                    all(type(value) is int and -(1 << 31) <= value < (1 << 31) for value in linear))
    sensor_valid = (flags & 2 and fresh_age(raw_age) and
                    all(type(value) is int and -32768 <= value <= 32767 for value in raw))
    fields["linear_accel_valid"] = bool(linear_valid)
    fields["sensor_accel_valid"] = bool(sensor_valid)
    if linear_valid:
        fields.update(zip(ACCEL_FIELDS[:3], (value / 1000 for value in linear)))
    if sensor_valid:
        fields.update(zip(ACCEL_FIELDS[3:], (value * 9.81 / 2048 for value in raw)))
    return fields


def age_ms(row, prefix):
    value = row.get(prefix + "_age_ms")
    if finite(value):
        return value
    ticks = row.get(prefix + "_age_ticks")
    return ticks / CLK_HZ * 1000 if finite(ticks) else None


def mode_name(value):
    if value is None:
        return "未上报"
    if value in ("自稳", "定点", "未上报"):
        return value
    if type(value) is int:
        return {0: "自稳", 1: "定点"}.get(value, f"未知模式 ({value})")
    return str(value)


def gate_reason(code):
    # A574 code retains the FSM branch (stage in bits 5:4, cause in bits 3:0).
    if code is None:
        return "未上报"
    if code == 0:
        return "无记录"
    causes = [(1, "遥控信号无效"), (2, "姿态条件不满足"),
              (4, "解锁开关回低"), (8, "准备时油门离开最低位")]
    stage = {1: "低档准备", 2: "高档准备", 3: "已解锁"}.get((code >> 4) & 3, "未知阶段")
    reason = "、".join(text for bit, text in causes if code & bit) or f"代码 {code}"
    return f"{stage}：{reason}"


def inhibit_text(code):
    if code is None:
        return "未上报"
    if code == 0:
        return "解锁条件满足"
    reasons = [(1, "遥控信号或通道不满足"), (2, "SWA 未在高档"),
               (4, "有效姿态条件不满足"), (8, "未解锁或正在等候确认")]
    return "；".join(text for bit, text in reasons if code & bit)


def range_diagnostic_fields(metadata=None,primary=None,baseline=None):
    result=dict(range_diagnostics_reported=False,range_error_counts=None,
                range_error_counts_since_connection=None,range_last_reject_code=None,
                range_last_reject_distance_cm=None,range_last_reject_strength=None,
                range_mm_configured=None,range_config_retries=None,range_unit=None)
    if metadata is None or primary is None:return result
    bounded={'sequence':65535,'range_diag_flags':1,'range_last_reject_code':5,
             'range_last_reject_distance_cm':65535,'range_last_reject_strength':65535,
             'range_error_total':0xffffffff,'range_good_total':0xffffffff,
             'range_source_age_ticks':0xffffffff,**{k:0xffffffff for k in RANGE_COUNTERS}}
    # New A57C primary uses mm. The decoder exposes decimal cm to the UI,
    # while validation still checks the original integer mm protocol word.
    distance_key='range_last_reject_distance_cm'
    if metadata.get('range_unit')=='mm':
        bounded.pop(distance_key)
        bounded['range_last_reject_distance_mm']=65535
        raw_mm=metadata.get('range_last_reject_distance_mm')
        if type(raw_mm) is not int or metadata.get(distance_key)!=raw_mm/10:return result
    if any(type(metadata.get(k)) is not int or not 0<=metadata[k]<=limit for k,limit in bounded.items()):return result
    if (metadata.get('sequence')!=primary.get('sequence') or
        metadata.get('range_error_total')!=primary.get('range_error') or
        metadata.get('range_good_total')!=primary.get('range_sample_count') or
        metadata.get('range_source_age_ticks')!=primary.get('range_age_ticks') or
        bool(metadata.get('range_diag_flags',0)&1)!=bool(primary.get('range_valid'))):return result
    counts={k:metadata.get(k) for k in RANGE_COUNTERS}
    if any(type(v) is not int or not 0<=v<=0xffffffff for v in counts.values()):return result
    total=metadata['range_error_total'];count_sum=sum(counts.values())
    if (total!=0xffffffff and count_sum!=total) or (total==0xffffffff and count_sum<total):return result
    result.update(range_diagnostics_reported=True,range_error_counts=counts,
                  range_last_reject_code=metadata['range_last_reject_code'])
    if metadata.get('range_unit')=='mm':
        result.update(range_mm_configured=metadata.get('range_mm_configured'),
                      range_config_retries=metadata.get('range_config_retries'),range_unit='mm')
    if baseline is not None:
        result['range_error_counts_since_connection']={k:counts[k]-baseline[k] for k in counts}
    if metadata['range_last_reject_code'] in (4,5):
        result.update(range_last_reject_distance_cm=metadata['range_last_reject_distance_cm'],
                      range_last_reject_strength=metadata['range_last_reject_strength'])
    return result

def normalize(row):
    """Map supported raw fields; never integrate flow counts into metric position."""
    flags = row.get("flags", 0)
    pose_age = row.get("pose_age_ticks")
    pose_valid = bool(flags & 4) and pose_age is not None and pose_age < POSE_FRESH_TICKS
    distance_valid = valid_flag(first(row, "range_valid", "range_fresh", default=False))
    flow_valid = valid_flag(first(row, "flow_valid", "flow_fresh", default=False))
    flow_calibrated = valid_flag(first(row, "flow_calibrated", "calibration_valid", default=False))
    position_valid = flow_valid and flow_calibrated and valid_flag(row.get("position_valid"))
    height_valid = distance_valid and valid_flag(row.get("height_valid"))
    roll = row.get("roll_cdeg")
    pitch = row.get("pitch_cdeg")
    yaw = first(row, "yaw_relative_deg")
    if yaw is None and "yaw_relative_cdeg" in row:
        yaw = row["yaw_relative_cdeg"] / 100
    # A575 adapters may provide already normalized degrees instead of centidegrees.
    requested = mode_name(first(row, "mode_requested"))
    active = mode_name(first(row, "mode_active"))
    mode_reason = first(row, "mode_inhibit_reason", "fallback_reason", default="未上报")
    if isinstance(mode_reason, int):
        mode_reason = "无" if mode_reason == 0 else f"原因代码 {mode_reason}"
    data = {
        "roll_deg": (roll / 100 if roll is not None else row.get("roll_deg")) if pose_valid else None,
        "pitch_deg": (pitch / 100 if pitch is not None else row.get("pitch_deg")) if pose_valid else None,
        "yaw_relative_deg": yaw if pose_valid else None,
        "distance_cm": row.get("distance_cm") if distance_valid else None,
        # Only an explicitly supplied and validated vertical height is displayed.
        "height_cm": row.get("height_cm") if height_valid else None,
        "height_estimate_cm": row.get("height_estimate_cm") if distance_valid and pose_valid else None,
        "flow_dx": row.get("flow_dx") if flow_valid else None,
        "flow_dy": row.get("flow_dy") if flow_valid else None,
        "flow_squal": first(row, "flow_squal", "squal") if flow_valid else None,
        "flow_id": row.get("flow_id"),
        "flow_total_x": row.get("flow_total_x") if flow_valid else None,
        "flow_total_y": row.get("flow_total_y") if flow_valid else None,
        "position_x_m": row.get("position_x_m") if position_valid else None,
        "position_y_m": row.get("position_y_m") if position_valid else None,
        "velocity_x_m_s": row.get("velocity_x_m_s") if position_valid else None,
        "velocity_y_m_s": row.get("velocity_y_m_s") if position_valid else None,
        "position_valid": position_valid,
        "flow_calibrated": flow_calibrated,
        "height_valid": height_valid,
        "mode_requested": requested,
        "mode_active": active,
        "mode_inhibit_reason": mode_reason,
        "inhibit_reason": row.get("inhibit_reason"),
        "inhibit_text": inhibit_text(row.get("inhibit_reason")),
        "ch7": row.get("ch7"),
        "rc_valid": bool(flags & 1),
        "calibrated": bool(flags & 2),
        "attitude_valid": pose_valid,
        "sensor_ok": bool(flags & 8),
        "armed": bool(flags & 16),
        "controller_enabled": bool(flags & 32),
        "command_fresh": bool(flags & 64),
        "pose_age_ms": pose_age / CLK_HZ * 1000 if pose_age is not None else None,
        "pwm_us": [row.get(f"physical_m{i}_us") for i in range(1, 5)],
        "command_us": [row.get(f"m{i}_us") for i in range(1, 5)],
        "rc_us": [row.get(f"ch{i}") for i in range(1, 9)],
        "range_valid": distance_valid,
        "flow_valid": flow_valid,
        "range_age_ms": age_ms(row, "range"),
        "flow_age_ms": age_ms(row, "flow"),
        "position_age_ms": age_ms(row, "position"),
        "range_error": first(row, "range_error", "range_fault"),
        "flow_error": first(row, "flow_error", "flow_fault"),
        "range_strength": first(row, "range_strength", "strength"),
        "stop_reason": first(row, "stop_reason", default="未上报"),
        "physical_output_active": bool(row.get("physical_flags", 0) & 2),
        "program_label": row.get("program_label", "限速台架程序 · 四路 1000–1150 μs"),
        "coordinate_frame": row.get("coordinate_frame", "机头向前、右侧向右、向下为正"),
    }
    data.update(acceleration_fields())
    data.update(range_diagnostic_fields())
    # Non-finite extensions are unknown data, never JSON NaN or a drawn instrument.
    for key, value in data.items():
        if isinstance(value, float) and not math.isfinite(value):
            data[key] = None
    diagnostics = {name: row.get(name) for name in [
        "accepted_count", "rejected_count", "command_count", "controller_fault_count",
        "imu_reason", "attitude_fault", "last_controller_fault", "who", "pwr", "cal_count",
        "gate_interruption_count", "gate_revoke_count", "gate_last_interruption_code",
        "gate_last_revoke_code", "gate_last_interruption_sensor_mask",
        "gate_last_interruption_pose_age_ticks", "gate_last_interruption_imu_reason",
        "gate_last_interruption_attitude_fault", "gate_last_revoke_sensor_mask",
        "gate_last_revoke_pose_age_ticks", "gate_last_revoke_imu_reason",
        "gate_last_revoke_attitude_fault",
        "range_checksum_errors", "range_frame_errors", "range_sample_count",
        "flow_sample_count", "flow_rejected_count", "position_fault",
    ]}
    diagnostics["last_interruption_text"] = gate_reason(diagnostics["gate_last_interruption_code"])
    diagnostics["last_revoke_text"] = gate_reason(diagnostics["gate_last_revoke_code"])
    accepted = diagnostics["accepted_count"]
    rejected = diagnostics["rejected_count"]
    total = (accepted or 0) + (rejected or 0)
    diagnostics["rejection_percent"] = round(rejected / total * 100, 3) if total and rejected is not None else None
    return data, diagnostics


class Dashboard:
    def __init__(self, port="offline", demo=False, no_serial=False, clock: Callable = time.monotonic,
                 calibration_store=None, apply_callback=None):
        self.lock = threading.Lock()
        self.clock = clock
        self.start = clock()
        self.port = port
        self.demo = demo
        self.no_serial = no_serial
        self.connected = False
        self.error = "串口读取已关闭" if no_serial else "等待串口连接"
        self.latest = None
        self.latest_time = None
        self.latest_primary_row = None
        self.acceleration_metadata = None
        self.acceleration_metadata_time = None
        self.acceleration_metadata_seen = False
        self.range_metadata=None;self.range_metadata_seen=False;self.range_baseline=None;self.range_previous_metadata=None
        self.range_diagnostic_checksum_errors=0;self.range_diagnostic_discarded_bytes=0
        self.history_primary_time = None
        self.history = deque(maxlen=600)
        self.frames = self.checksum_errors = self.discarded_bytes = 0
        self.acceleration_checksum_errors = self.acceleration_discarded_bytes = 0
        self.sequence_gap_events = self.missing_frames = self.sequence_resets = 0
        self.previous_sequence = None
        self.last_history_time = -1.0
        self.raw_history = deque(maxlen=20000)
        self.calibration_token = secrets.token_urlsafe(32)
        self.calibration = LevelCalibration(calibration_store or HERE / "level_calibration.json",
            clock=clock, demo=demo, apply_callback=apply_callback, get_recent_raw_rows=self.get_recent_raw_rows)

    def connection(self, connected, error=None):
        with self.lock:
            self.connected = connected
            self.error = error
            if not connected:
                self.previous_sequence = None
                self.range_metadata=None;self.range_metadata_seen=False;self.range_baseline=None;self.range_previous_metadata=None
                # Reconnecting does not rehabilitate a frame received before disconnection.
                self.latest_time = None
                self.acceleration_metadata = None
                self.acceleration_metadata_time = None
                self.acceleration_metadata_seen = False
                if self.latest:
                    self.latest["data"].update(acceleration_fields())
                    self.latest["data"].update(range_diagnostic_fields())
        self.calibration.connection(connected)

    def update_receiver(self, receiver):
        with self.lock:
            self.checksum_errors = receiver.checksum_errors
            self.discarded_bytes = receiver.discarded_bytes
            self.acceleration_checksum_errors = getattr(receiver, "acceleration_checksum_errors", 0)
            self.acceleration_discarded_bytes = getattr(receiver, "acceleration_discarded_bytes", 0)
            self.range_diagnostic_checksum_errors=getattr(receiver,'range_diagnostic_checksum_errors',0)
            self.range_diagnostic_discarded_bytes=getattr(receiver,'range_diagnostic_discarded_bytes',0)

    def ingest_range_diagnostics(self,row):
        with self.lock:
            now=self.clock()
            if row.get('_range_invalid'):
                self.range_metadata=None
                if self.latest:self.latest['data'].update(range_diagnostic_fields())
                return
            if (not self.connected or self.latest is None or self.latest_time is None or
                self.latest['protocol'] not in ('a579','a57c') or not 0<=now-self.latest_time<FRAME_FRESH_SECONDS or
                self.range_metadata_seen):return
            fields=range_diagnostic_fields(row,self.latest_primary_row)
            if not fields['range_diagnostics_reported']:return
            counts=fields['range_error_counts']
            previous=self.range_previous_metadata
            if self.range_baseline is None or (previous is not None and any(row[k]<previous[k] for k in (*RANGE_COUNTERS,'range_good_total','range_error_total'))):
                self.range_baseline=dict(counts)
            self.range_metadata=dict(row);self.range_previous_metadata=dict(row);self.range_metadata_seen=True
            self.latest['data'].update(range_diagnostic_fields(row,self.latest_primary_row,self.range_baseline))

    def ingest(self, row):
        if row.get('_protocol')==RANGE_HEADER.hex():
            self.ingest_range_diagnostics(row);return
        if row.get("_protocol") == ACCEL_HEADER.hex():
            self.ingest_acceleration(row)
            return
        now = self.clock()
        data, diagnostics = normalize(row)
        sequence = row.get("sequence")
        with self.lock:
            if self.previous_sequence is not None and sequence is not None:
                gap = (sequence - self.previous_sequence - 1) & 0xFFFF
                if gap:
                    if gap > 0x8000:
                        self.sequence_resets += 1
                        self.range_baseline=None;self.range_previous_metadata=None
                        self.history.clear()
                        self.last_history_time = -1
                    else:
                        self.sequence_gap_events += 1
                        self.missing_frames += gap
            self.previous_sequence = sequence
            self.frames += 1
            self.latest = {"data": data, "diagnostics": diagnostics,
                           "sequence": sequence, "protocol": row.get("_protocol")}
            self.latest_time = now
            self.latest_primary_row = dict(row)
            self.range_metadata=None;self.range_metadata_seen=False
            self.acceleration_metadata = None
            self.acceleration_metadata_time = None
            self.acceleration_metadata_seen = False
            self.raw_history.append({"received_monotonic": now, "row": dict(row)})
            while self.raw_history and self.raw_history[0]["received_monotonic"] < now - 120:
                self.raw_history.popleft()
            if now - self.last_history_time >= 0.095:
                self.history.append({"t": round(now - self.start, 3),
                                     "sequence": sequence, "protocol": row.get("_protocol"),
                                     **{k: data[k] for k in ["roll_deg", "pitch_deg", "yaw_relative_deg", "distance_cm", "height_cm", "flow_total_x", "flow_total_y", "position_x_m", "position_y_m", "velocity_x_m_s", "velocity_y_m_s", *ACCEL_FIELDS, "linear_accel_valid", "sensor_accel_valid", "acceleration_missing"]}})
                self.history_primary_time = now
                self.last_history_time = now
        self.calibration.observe(row, now)

    def ingest_acceleration(self, row):
        """Supplement this A579 epoch without advancing any primary telemetry."""
        now = self.clock()
        with self.lock:
            if row.get("_acceleration_invalid"):
                self.acceleration_metadata = None
                self.acceleration_metadata_time = None
                fields = acceleration_fields()
            else:
                if (not self.connected or self.latest is None or self.latest_time is None or
                        self.latest["protocol"] not in ("a579","a57c") or
                        type(row.get("sequence")) is not int or row["sequence"] != self.latest["sequence"] or
                        not 0 <= now - self.latest_time < FRAME_FRESH_SECONDS or
                        self.acceleration_metadata_seen):
                    return
                self.acceleration_metadata = dict(row)
                self.acceleration_metadata_time = now
                self.acceleration_metadata_seen = True
                fields = acceleration_fields(row, self.latest_primary_row, now - self.latest_time)
            if self.latest:
                self.latest["data"].update(fields)
            if self.history and self.history_primary_time == self.latest_time:
                point = self.history[-1]
                self.history[-1] = {**point, **{name: fields[name] for name in (*ACCEL_FIELDS, "linear_accel_valid", "sensor_accel_valid", "acceleration_missing")}}

    def get_recent_raw_rows(self, seconds=30, after_monotonic=None):
        """Trusted worker view of complete decoded rows; the serial reader keeps COM23."""
        if not finite(seconds) or not 0 < seconds <= 120:
            raise ValueError("raw window must be within0..120seconds")
        now = self.clock()
        cutoff = max(now - seconds, after_monotonic if after_monotonic is not None else now - seconds)
        with self.lock:
            return {"rows": [{"received_monotonic": item["received_monotonic"], "row": dict(item["row"])}
                             for item in self.raw_history if item["received_monotonic"] >= cutoff],
                    "stats": {"frames": self.frames, "checksum_errors": self.checksum_errors,
                              "discarded_bytes": self.discarded_bytes, "missing_frames": self.missing_frames,
                              "sequence_resets": self.sequence_resets},
                    "connected": self.connected, "now_monotonic": now}

    def snapshot(self):
        calibration_status = self.calibration.status()
        with self.lock:
            now = self.clock()
            age = now - self.latest_time if self.latest_time is not None else None
            fresh = self.connected and age is not None and age <= FRAME_FRESH_SECONDS
            status = "live" if fresh else ("waiting" if self.connected else "disconnected")
            if self.connected and age is not None and not fresh:
                status = "stale"
            data = dict(self.latest["data"]) if self.latest and fresh else None
            if data is not None:
                data.update(acceleration_fields(self.acceleration_metadata, self.latest_primary_row, now - self.latest_time))
                data.update(range_diagnostic_fields(self.range_metadata,self.latest_primary_row,self.range_baseline) if now-self.latest_time<FRAME_FRESH_SECONDS else range_diagnostic_fields())
            return {
                "status": status, "connected": self.connected, "fresh": fresh,
                "demo": self.demo, "port": self.port,
                "level_calibration": calibration_status,
                "frame_age_ms": round(age * 1000, 1) if age is not None else None,
                "fresh_timeout_ms": FRAME_FRESH_SECONDS * 1000,
                "error": self.error,
                "sequence": self.latest["sequence"] if self.latest and fresh else None,
                "protocol": self.latest["protocol"] if self.latest else None,
                "data": data,
                # These are labelled retained diagnostics, never presented as live angles.
                "last_valid_diagnostics": dict(self.latest["diagnostics"]) if self.latest else None,
                "stats": {"frames": self.frames, "checksum_errors": self.checksum_errors,
                          "discarded_bytes": self.discarded_bytes,
                          "acceleration_checksum_errors": self.acceleration_checksum_errors,
                          "acceleration_discarded_bytes": self.acceleration_discarded_bytes,
                          "range_diagnostic_checksum_errors":self.range_diagnostic_checksum_errors,
                          "range_diagnostic_discarded_bytes":self.range_diagnostic_discarded_bytes,
                          "sequence_gap_events": self.sequence_gap_events,
                          "missing_frames": self.missing_frames, "sequence_resets": self.sequence_resets},
                "history": list(self.history),
                "program_label": self.latest["data"]["program_label"] if self.latest else "等待程序信息 · 尚未完成飞行验证",
            }



def make_server(dashboard, port=8765):
    """Minimal local HTTP base; ground_server owns assets/logging routes."""
    class Handler(BaseHTTPRequestHandler):
        def local_host(self):
            return self.headers.get('Host','') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')
        def json_response(self,status,value):
            body=json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if not self.local_host():self.send_error(403);return
            route=urlsplit(self.path).path
            if route=='/api/health':self.json_response(200,dict(ok=True,read_only=True,serial_writes=False))
            elif route=='/api/calibration/status':self.json_response(200,dict(calibration=dashboard.calibration.status()))
            else:self.send_error(404)
        def do_POST(self):self.send_error(403)
        def log_message(self,*_):pass
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    return server
