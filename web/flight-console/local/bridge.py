"""HTTP-only sidecar: observe an existing receiver; never open a serial device."""
from __future__ import annotations

import argparse
import copy
import csv
import gzip
import datetime as dt
import io
import json
import math
import mimetypes
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_RESPONSE = 20 * 1024 * 1024
MAX_SAMPLES = 20000
SESSION = re.compile(r"\d{8}T\d{6}Z_[0-9a-f]{8}\Z")
COLUMNS = ["t_s", "roll_deg", "pitch_deg", "yaw_deg", "height_m", "vx_mps", "vy_mps", "vz_mps",
           "m1_us", "m2_us", "m3_us", "m4_us", "throttle_us", "armed",
           "roll_sp_deg", "pitch_sp_deg", "yaw_rate_dps", "yaw_rate_sp_dps"]
TRACKING = ("roll_sp_deg", "pitch_sp_deg", "yaw_rate_dps", "yaw_rate_sp_dps")
HERE = Path(__file__).resolve().parent


class BridgeError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) and abs(result) <= 1e15 else None


def boolean(value):
    return value if isinstance(value, bool) else None


def first_number(*values):
    return next((n for n in (number(v) for v in values) if n is not None), None)


def scaled(value, divisor):
    n = number(value)
    return None if n is None else n / divisor


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def dictionary(value):
    return value if isinstance(value, dict) else {}


def mode_value(value):
    if isinstance(value, str):
        return value if value in {"ATT_STAB", "LOC_HOLD", "MANUAL", "XYZ", "ALT_HOLD", "STABILIZE", "DISARMED",
            "自稳", "定高", "定点", "未上报"} else None
    return number(value)


def sanitize_live(state):
    """Build a new object; never copy arbitrary metadata, source text or raw packets."""
    state = dictionary(state)
    data = dictionary(state.get("data"))
    nav = dictionary(state.get("navigation"))
    nv = dictionary(state.get("navigation_values"))
    mtf = dictionary(state.get("mtf_sensor"))
    info = dictionary(state.get("flight_info"))
    stats = dictionary(state.get("stats"))
    rec = dictionary(state.get("recording"))
    build = number(info.get("build_id"))
    build = int(build) if build is not None and build == int(build) and 0 <= build <= 0xffffffff else None
    connected = state.get("connected") is True
    primary_sequence, info_sequence = number(state.get("sequence")), number(info.get("sequence"))
    legal_sequences = all(v is not None and v == int(v) and 0 <= v <= 65535
        for v in (primary_sequence, info_sequence))
    identity_matches = legal_sequences and ((int(primary_sequence) - int(info_sequence)) & 65535) in (0, 1)
    fresh = bool(connected and state.get("fresh") is True and state.get("flight_info_fresh") is True
        and build is not None and identity_matches)
    nf = state.get("navigation_fresh") is True
    mf = state.get("mtf_fresh") is True
    vx = scaled(nv.get("nav_fused_vx_mm_s"), 1000) if nf else number(data.get("velocity_x_m_s"))
    vy = scaled(nv.get("nav_fused_vy_mm_s"), 1000) if nf else number(data.get("velocity_y_m_s"))
    height = scaled(nv.get("nav_fused_height_mm"), 1000) if nf else first_number(
        scaled(data.get("height_estimate_cm"), 100), scaled(data.get("height_cm"), 100))
    channels = data.get("rc_us")
    channels = [number(v) for v in channels[:16]] if isinstance(channels, list) else []
    motors = data.get("pwm_us")
    motors = [number(v) for v in motors[:4]] if isinstance(motors, list) else []
    motors += [None] * (4 - len(motors))
    reason = first_number(nav.get("reason"), data.get("mode_inhibit_reason"), data.get("inhibit_reason"))
    health = {"imu": boolean(data.get("sensor_ok")), "flow": boolean(data.get("flow_valid")),
        "range": boolean(data.get("range_valid")), "nav": boolean(state.get("navigation_fresh")),
        "rc": boolean(data.get("rc_valid"))}
    if mf:
        health["flow"] = boolean(mtf.get("flow_provisionally_valid"))
        health["range"] = boolean(mtf.get("range_provisionally_valid"))
    age = number(state.get("frame_age_ms"))
    ttl = number(state.get("fresh_timeout_ms"))
    ttl = min(ttl, 1000) if ttl is not None and ttl > 0 else 1000
    # History's source t is seconds since receiver start, not Unix time. Anchor its
    # last sample to source frame age, preserving differences and gaps in between.
    history = []
    raw_history = state.get("history")
    raw_history = [dictionary(v) for v in raw_history[-600:]] if isinstance(raw_history, list) else []
    times = [number(v.get("t")) for v in raw_history]
    valid_times = [v for v in times if v is not None]
    if valid_times and age is not None and age >= 0:
        latest = valid_times[-1]
        anchor = time.time() * 1000 - age
        for row, t in zip(raw_history, times):
            if t is None or t > latest:
                continue
            x, y = number(row.get("velocity_x_m_s")), number(row.get("velocity_y_m_s"))
            history.append({"t": round(anchor - (latest - t) * 1000), "roll_deg": number(row.get("roll_deg")),
                "pitch_deg": number(row.get("pitch_deg")), "yaw_deg": number(row.get("yaw_relative_deg")),
                "height_m": scaled(row.get("height_cm"), 100),
                "speed_mps": math.hypot(x, y) if x is not None and y is not None else None})
    if len(history) > 120:
        history = [history[round(i * (len(history) - 1) / 119)] for i in range(120)]
    stamp = utc_now()
    return {"schema": 1, "mode": "local", "connected": connected, "fresh": fresh,
        "age_ms": age, "received_at": stamp, "source_publish_at": stamp,
        "source_valid": fresh, "source_ttl_ms": ttl,
        "firmware": f"{build:04X}" if build is not None else None,
        "sequence": number(state.get("sequence")), "armed": boolean(data.get("armed")),
        "control_mode": mode_value(data.get("mode_active")),
        "attitude": {"roll_deg": number(data.get("roll_deg")), "pitch_deg": number(data.get("pitch_deg")), "yaw_deg": number(data.get("yaw_relative_deg"))},
        "tracking": {k: number(dictionary(state.get("tracking")).get(k)) if fresh else None for k in TRACKING},
        "motion": {"height_m": height, "vx_mps": vx, "vy_mps": vy,
            "speed_mps": math.hypot(vx, vy) if vx is not None and vy is not None else None,
            "x_m": scaled(nv.get("nav_position_x_mm"), 1000) if nf else number(data.get("position_x_m")),
            "y_m": scaled(nv.get("nav_position_y_mm"), 1000) if nf else number(data.get("position_y_m")),
            "vz_mps": scaled(nv.get("nav_fused_vz_mm_s"), 1000) if nf else None},
        "rc": {"valid": boolean(data.get("rc_valid")), "throttle_us": channels[2] if len(channels) > 2 else None, "channels": channels},
        "motors_us": motors, "health": health,
        "flags": {"requested": mode_value(data.get("mode_requested")), "xy_active": boolean(nav.get("xy_shadow_active")),
            "z_active": boolean(nav.get("xyz_active")), "reason_text": "状态码 " + str(int(reason)) if reason is not None else None},
        "recording": {"frames": number(rec.get("frames")),
            "missing_frames": first_number(rec.get("missing_primary_frames"), stats.get("missing_frames")),
            "decode_errors": first_number(rec.get("receiver_checksum_errors"), stats.get("checksum_errors")),
            "sequence_resets": number(stats.get("sequence_resets")), "bytes": number(rec.get("bytes")),
            "active": not rec["closed"] if isinstance(rec.get("closed"), bool) else None},
        "history": history, "_source_ttl_ms": ttl}


def age_live(result, elapsed, upstream_ok):
    ttl = result.pop("_source_ttl_ms", 1000)
    result["source_publish_at"] = utc_now()
    result["server_response_time_ms"] = time.time() * 1000
    if result["age_ms"] is not None and elapsed is not None:
        result["age_ms"] = max(0, result["age_ms"] + max(0, elapsed) * 1000)
    result["connected"] = bool(result["connected"] and upstream_ok and elapsed is not None and elapsed <= 2)
    result["source_valid"] = bool(result.get("source_valid") and upstream_ok
        and elapsed is not None and 0 <= elapsed <= 1)
    result["fresh"] = bool(result["fresh"] and result["connected"] and result["age_ms"] is not None
        and result["age_ms"] <= ttl and elapsed is not None and elapsed <= 1)
    return result


def origin(value, local=False):
    try:
        u = urllib.parse.urlsplit(value)
        port = u.port
    except (TypeError, ValueError):
        raise BridgeError(400, "Invalid endpoint configuration") from None
    if (u.scheme not in ("http", "https") or not u.hostname or u.username or u.password
            or u.path not in ("", "/") or u.query or u.fragment):
        raise BridgeError(400, "Endpoint must be an origin")
    if local and (u.scheme != "http" or u.hostname not in ("127.0.0.1", "localhost")):
        raise BridgeError(400, "Upstream must use loopback HTTP")
    if not local and u.scheme != "https" and u.hostname not in ("127.0.0.1", "localhost"):
        raise BridgeError(400, "Sharing requires HTTPS")
    if port is not None and not 1 <= port <= 65535:
        raise BridgeError(400, "Invalid endpoint port")
    return value.rstrip("/")


@dataclass(repr=False)
class Config:
    upstream: str = "http://127.0.0.1:8765"
    listen_port: int = 8766
    site_url: str = ""
    publish_token: str = field(default="", repr=False)

    def __post_init__(self):
        self.upstream = origin(self.upstream, local=True)
        if isinstance(self.listen_port, bool) or not isinstance(self.listen_port, int) or not 0 <= self.listen_port <= 65535:
            raise BridgeError(400, "Invalid listen port")
        if self.site_url:
            self.site_url = origin(self.site_url)
        if not isinstance(self.publish_token, str) or len(self.publish_token) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in self.publish_token):
            raise BridgeError(400, "Invalid publication configuration")
        if self.publish_token and not self.site_url:
            raise BridgeError(400, "Publication endpoint is required")
        a = urllib.parse.urlsplit(self.upstream)
        if self.listen_port and (a.port or 80) == self.listen_port:
            raise BridgeError(400, "Upstream and bridge ports must differ")

    @property
    def sharing(self):
        return bool(self.site_url and self.publish_token)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HTTPClient:
    def __init__(self, config):
        self.config = config
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        # The local receiver never leaves loopback. Outbound HTTPS follows the
        # user's existing system proxy, which may be needed on this network.
        self.publish_opener = urllib.request.build_opener(urllib.request.ProxyHandler(), NoRedirect())

    def _read(self, request, limit=MAX_RESPONSE, timeout=8, opener=None):
        try:
            with (opener or self.opener).open(request, timeout=timeout) as response:
                if response.status != 200 and not 200 <= response.status < 300:
                    raise BridgeError(502, "Remote service unavailable")
                length = response.headers.get("Content-Length")
                if length and int(length) > limit:
                    raise BridgeError(413, "Response exceeds limit; no complete log was loaded")
                value = response.read(limit + 1)
                if len(value) > limit:
                    raise BridgeError(413, "Response exceeds limit; no complete log was loaded")
                return value
        except BridgeError:
            raise
        except (OSError, ValueError, urllib.error.URLError):
            # Never return exception strings: URLs, paths, source identity or credentials may occur there.
            raise BridgeError(502, "Remote service unavailable") from None

    def get(self, path):
        if path not in ("/api/state", "/api/logs") and not re.fullmatch(r"/api/logs/\d{8}T\d{6}Z_[0-9a-f]{8}/download\?format=csv", path):
            raise BridgeError(400, "Unsupported upstream resource")
        return self._read(urllib.request.Request(self.config.upstream + path, method="GET"))

    def get_json(self, path):
        try:
            value = json.loads(self.get(path))
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except (ValueError, UnicodeError):
            raise BridgeError(502, "Invalid upstream response") from None

    def server_clock(self):
        if not self.config.site_url:
            raise BridgeError(409, "Sharing is not configured")
        request = urllib.request.Request(self.config.site_url + "/api/health", method="GET",
            headers={"User-Agent": "ACG720-GroundStation/1.0", "Cache-Control": "no-cache"})
        remote = urllib.parse.urlsplit(self.config.site_url).hostname not in ("127.0.0.1", "localhost")
        raw = self._read(request, limit=16384, opener=self.publish_opener if remote else self.opener)
        try:
            value = json.loads(raw)
            stamp = number(value.get("server_time_ms")) if isinstance(value, dict) else None
            if stamp is None or not 0 < stamp <= 253402300799000:
                raise ValueError()
            return stamp
        except (ValueError, UnicodeError):
            raise BridgeError(502, "Invalid server clock response") from None

    def publish(self, kind, payload):
        if not self.config.sharing:
            raise BridgeError(409, "Sharing is not configured")
        if kind not in ("live", "log"):
            raise BridgeError(400, "Unsupported publication")
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
        if len(body) > 8 * 1024 * 1024:
            raise BridgeError(413, "Publication exceeds 8 MiB; nothing was uploaded")
        encoding = {}
        if kind == "log":
            body = gzip.compress(body, mtime=0)
            if len(body) > 5 * 1024 * 1024:
                raise BridgeError(413, "Compressed publication exceeds 5 MiB; nothing was uploaded")
            encoding = {"Content-Encoding": "gzip"}
        request = urllib.request.Request(self.config.site_url + "/api/publish/" + kind, data=body, method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "ACG720-GroundStation/1.0", "X-Flight-Publish-Token": self.config.publish_token, **encoding})
        remote = urllib.parse.urlsplit(self.config.site_url).hostname not in ("127.0.0.1", "localhost")
        raw = self._read(request, limit=65536, opener=self.publish_opener if remote else self.opener)
        try:
            result = json.loads(raw) if raw else {}
        except ValueError:
            result = {}
        return result if isinstance(result, dict) else {}


def validate_id(identifier):
    if not isinstance(identifier, str) or not SESSION.fullmatch(identifier):
        raise BridgeError(400, "Invalid session ID")
    return identifier


def csv_samples(raw, identifier):
    """Convert the existing analysis.export_csv contract, without reading local files."""
    if len(raw) > MAX_RESPONSE:
        raise BridgeError(413, "Response exceeds limit; no complete log was loaded")
    try:
        text = raw.decode("utf-8-sig")
        stream = io.StringIO(text, newline="")
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "elapsed_s" not in reader.fieldnames:
            raise BridgeError(502, "Unsupported upstream CSV columns")
        rows, input_rows, invalid_time_rows = [], 0, 0
        for row in reader:
            input_rows += 1
            t = number(row.get("elapsed_s"))
            if t is None or t < 0:
                invalid_time_rows += 1
                continue
            protocol = str(row.get("protocol") or "").lower()
            if protocol not in ("a579", "a581", "a582"):
                continue
            sample = dict.fromkeys(COLUMNS)
            sample["t_s"] = t
            if protocol == "a579":
                for k in ("roll_deg", "pitch_deg", "yaw_deg", "throttle_us", "m1_us", "m2_us", "m3_us", "m4_us"):
                    sample[k] = number(row.get(k))
                for k in TRACKING:
                    sample[k] = number(row.get(k))
                sample["height_m"] = scaled(row.get("selected_height_cm"), 100)
                # Never reinterpret diagnostic/nav placeholder armed=False as a real motor state.
                sample["armed"] = {"true": True, "false": False, "1": True, "0": False}.get(str(row.get("armed", "")).lower())
            elif protocol == "a582":
                sample["height_m"] = scaled(row.get("nav_fused_height_mm"), 1000)
                for axis in "xyz":
                    sample[f"v{axis}_mps"] = scaled(row.get(f"nav_fused_v{axis}_mm_s"), 1000)
            else:
                # MTF slant range and module-frame velocities are NOT vertical height / fused local velocity.
                # They cannot fill the unified height_m/vx_mps fields without inventing a frame conversion.
                continue
            if any(v is not None for k, v in sample.items() if k != "t_s"):
                rows.append(sample)
    except (UnicodeError, csv.Error):
        raise BridgeError(502, "Invalid upstream CSV") from None
    original_samples = len(rows)
    if len(rows) > MAX_SAMPLES:
        last = len(rows) - 1
        rows = [rows[round(i * last / (MAX_SAMPLES - 1))] for i in range(MAX_SAMPLES)]
    duration = max((r["t_s"] for r in rows), default=0) - min((r["t_s"] for r in rows), default=0) if rows else None
    summary = {"duration_s": duration, "frames": original_samples, "missing_frames": None, "sequence_resets": None,
        "source_rows": input_rows, "eligible_samples": original_samples, "exported_samples": len(rows),
        "downsampled": original_samples > MAX_SAMPLES, "source_complete": True,
        "complete": invalid_time_rows == 0 and original_samples <= MAX_SAMPLES,
        "invalid_time_rows": invalid_time_rows, "source_format": "existing_receiver_csv",
        "time_basis": "receiver elapsed_s: seconds relative to the recording session, not UTC or sequence",
        "units": "angles deg; selected/fused height m; fused local velocity m/s; PWM command us",
        "scope": "Numeric allowlist only; sparse protocol rows remain sparse. MTF slant range/module-frame velocity and diagnostics are excluded. PWM is command telemetry, not measured RPM."}
    return {"log": {"id": validate_id(identifier), "title": "遥测记录 " + identifier,
        "columns": COLUMNS, "samples": rows, "summary": summary}}


def export_csv(log):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in log["log"]["samples"]:
        writer.writerow({k: (int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in COLUMNS})
    return stream.getvalue().encode("utf-8-sig")


class Bridge:
    def __init__(self, config, client=None, clock=time.monotonic, wall_clock=time.time):
        self.config, self.client, self.clock = config, client or HTTPClient(config), clock
        self.wall_clock = wall_clock
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.publish_lock = threading.RLock()
        self.sharing_enabled = False
        self.snapshot = None
        self.fetched_at = None
        self.upstream_ok = False
        self.log_cache = {}
        self.log_lock = threading.Lock()
        self.history = deque(maxlen=120)
        self.last_history_time = None
        self.last_history_identity = None
        self.last_clock_attempt = None
        self.server_clock_base = None
        self.server_clock_monotonic = None
        self.clock_uncertainty_ms = None

    def poll_once(self):
        try:
            state = self.client.get_json("/api/state")
            value = sanitize_live(state)
            with self.lock:
                now = self.clock()
                oldest = self.wall_clock() * 1000 - 60000
                while self.history and self.history[0]["t"] < oldest:
                    self.history.popleft()
                identity = (value["firmware"], value["sequence"])
                source_age = value["age_ms"]
                current = bool(value["fresh"] and source_age is not None and 0 <= source_age <= value["_source_ttl_ms"])
                if (current and identity != self.last_history_identity
                        and (self.last_history_time is None or now - self.last_history_time >= .5)):
                    source_time = self.wall_clock() * 1000 - source_age
                    # Build only from this successful poll's live fields, never
                    # backfill old source history or reset the source frame age.
                    if not self.history or source_time > self.history[-1]["t"]:
                        self.history.append({"t": round(source_time), **value["attitude"], **value["tracking"],
                            "height_m": value["motion"]["height_m"], "speed_mps": value["motion"]["speed_mps"]})
                        self.last_history_time, self.last_history_identity = now, identity
                value["history"] = list(self.history)
                if not value["fresh"] and self.snapshot:
                    # The receiver intentionally clears its data once stale. Retain
                    # only our already sanitized last-known values, visibly stale.
                    for key in ("firmware", "sequence", "armed", "control_mode"):
                        if value[key] is None:
                            value[key] = self.snapshot[key]
                    for key in ("attitude", "motion", "rc", "flags"):
                        for name, v in value[key].items():
                            if v is None or v == []:
                                value[key][name] = copy.deepcopy(self.snapshot[key][name])
                    if all(v is None for v in value["motors_us"]):
                        value["motors_us"] = copy.deepcopy(self.snapshot["motors_us"])
                    if value["age_ms"] is None and self.snapshot["age_ms"] is not None and self.fetched_at is not None:
                        value["age_ms"] = self.snapshot["age_ms"] + max(0, self.clock() - self.fetched_at) * 1000
                self.snapshot, self.fetched_at, self.upstream_ok = value, self.clock(), True
        except (BridgeError, ValueError, TypeError, KeyError):
            with self.lock:
                self.upstream_ok = False
    def set_sharing(self, enabled):
        if not isinstance(enabled, bool):
            raise BridgeError(400, "enabled must be boolean")
        if enabled and not self.config.sharing:
            raise BridgeError(409, "Sharing is not configured")
        # Stop waits for a current request; no further clock/publish request starts
        # after the endpoint confirms disabled. Local recording remains separate.
        with self.publish_lock:
            self.sharing_enabled = enabled
            if enabled:
                self.last_clock_attempt = None
            return {"sharing_enabled": self.sharing_enabled}

    def publish_once(self):
        with self.publish_lock:
            if self.sharing_enabled:
                self._publish_once()

    def _publish_once(self):
        if self.config.sharing:
            try:
                now = self.clock()
                if self.last_clock_attempt is None or now - self.last_clock_attempt >= 60:
                    self.last_clock_attempt = now
                    try:
                        t0 = self.clock()
                        server_time = number(self.client.server_clock())
                        t1 = self.clock()
                        rtt_ms = (t1 - t0) * 1000
                        if (server_time is not None and 0 < server_time <= 253402300799000
                                and 0 <= rtt_ms <= 4000):
                            self.server_clock_base = server_time + rtt_ms / 2
                            self.server_clock_monotonic = t1
                            self.clock_uncertainty_ms = rtt_ms / 2
                    except BridgeError:
                        pass  # A previous synchronization may remain valid up to 120 seconds.
                # live() takes a short snapshot lock; no lock is held during HTTP.
                # Configuration and its bearer are read-only after initialization.
                value = self.live()
                elapsed = self.clock() - self.server_clock_monotonic if self.server_clock_monotonic is not None else None
                timing_valid = bool(self.server_clock_base is not None and elapsed is not None and 0 <= elapsed <= 120)
                value.update(timing_version=2, timing_valid=timing_valid,
                    clock_uncertainty_ms=self.clock_uncertainty_ms if timing_valid else None)
                # Reference for translating locally timestamped history into the
                # projected server timebase; it is not a cloud sample timestamp.
                value["history_reference_time_ms"] = self.wall_clock() * 1000
                value["source_publish_at"] = (dt.datetime.fromtimestamp(
                    (self.server_clock_base + elapsed * 1000) / 1000, dt.timezone.utc)
                    .isoformat(timespec="milliseconds").replace("+00:00", "Z")) if timing_valid else None
                value["fresh"] = bool(timing_valid and value["source_valid"] and value["connected"]
                    and value["age_ms"] is not None and value["age_ms"] <= 5000)
                self.client.publish("live", value)
            except BridgeError:
                pass  # Do not log publication URLs, response bodies or the in-memory bearer.

    def run(self):
        while not self.stop.is_set():
            started = self.clock()
            self.poll_once()
            self.stop.wait(max(0, .25 - (self.clock() - started)))

    def run_publisher(self):
        while not self.stop.is_set():
            started = self.clock()
            self.publish_once()
            self.stop.wait(max(0, 1.0 - (self.clock() - started)))

    def live(self):
        with self.lock:
            result = copy.deepcopy(self.snapshot or sanitize_live({}))
            oldest = self.wall_clock() * 1000 - 60000
            while self.history and self.history[0]["t"] < oldest:
                self.history.popleft()
            result["history"] = list(self.history)
            elapsed = (self.clock() - self.fetched_at) if self.fetched_at is not None else None
            okay = self.upstream_ok
        return age_live(result, elapsed, okay)

    def logs(self):
        value = self.client.get_json("/api/logs")
        result = []
        for item in value.get("sessions", [])[:200]:
            if not isinstance(item, dict) or not SESSION.fullmatch(str(item.get("id", ""))):
                continue
            ident = item["id"]
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            # Only strict UTC date syntax, never arbitrary original-machine strings.
            created = meta.get("started_utc")
            if not isinstance(created, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT[0-9:.]+(?:Z|\+00:00)", created):
                created = None
            result.append({"id": ident, "title": "遥测记录 " + ident, "created_at": created,
                "frames": None, "duration_s": None, "missing_frames": None, "shared": False,
                "active": item.get("active") is True, "bytes": number(item.get("bytes"))})
        return {"logs": result, "local_controls": True}

    def log(self, identifier):
        validate_id(identifier)
        with self.log_lock:
            cached = self.log_cache.get(identifier)
            if cached and self.clock() - cached[0] < 10:
                return copy.deepcopy(cached[1])
            value = csv_samples(self.client.get("/api/logs/" + identifier + "/download?format=csv"), identifier)
            self.log_cache = {identifier: (self.clock(), value)}
            return copy.deepcopy(value)

    def share_log(self, identifier):
        if not self.config.sharing:
            raise BridgeError(409, "Sharing is not configured")
        value = self.log(identifier)
        self.client.publish("log", value["log"])
        # Never trust/return arbitrary response text or URLs from a remote service.
        return {"ok": True, "share_url": self.config.site_url + "/?log=" + urllib.parse.quote(identifier), "id": identifier}


def make_server(bridge, frontend=None):
    frontend = Path(frontend or HERE.parent / "frontend").resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def allowed(self, post=False):
            port = self.server.server_port
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            if self.headers.get("Host") not in hosts:
                raise BridgeError(403, "Local requests only")
            request_origin = self.headers.get("Origin")
            if (post and not request_origin) or (request_origin and request_origin not in {"http://" + h for h in hosts}):
                raise BridgeError(403, "Same-origin requests only")
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                raise BridgeError(403, "Same-origin requests only")

        def send(self, code, body, content_type="application/json; charset=utf-8", filename=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if filename:
                self.send_header("Content-Disposition", 'attachment; filename="' + filename + '"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            try:
                self.allowed()
                u = urllib.parse.urlsplit(self.path)
                path = u.path
                if path.startswith("/api/") and u.query:
                    raise BridgeError(400, "Unsupported API query")
                if path == "/api/live":
                    return self.send(200, bridge.live())
                if path == "/api/capabilities":
                    return self.send(200, {"mode": "local", "share_url": bridge.config.site_url or None,
                        "can_share_logs": bridge.config.sharing, "sharing_enabled": bridge.sharing_enabled})
                if path == "/api/logs":
                    return self.send(200, bridge.logs())
                match = re.fullmatch(r"/api/logs/(\d{8}T\d{6}Z_[0-9a-f]{8})(/download\.csv)?", path)
                if match:
                    value = bridge.log(match[1])
                    if match[2]:
                        return self.send(200, export_csv(value), "text/csv; charset=utf-8", match[1] + ".csv")
                    return self.send(200, value)
                if path.startswith("/api"):
                    raise BridgeError(404, "Unknown API")
                decoded = urllib.parse.unquote(path)
                relative = "index.html" if decoded == "/" else decoded.lstrip("/")
                file = (frontend / relative).resolve()
                if not file.is_relative_to(frontend) or not file.is_file():
                    raise BridgeError(404, "Not found")
                mime = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
                return self.send(200, file.read_bytes(), mime)
            except BridgeError as exc:
                self.send(exc.code, {"error": exc.message})
            except (OSError, ValueError, TypeError):
                self.send(502, {"error": "Request unavailable"})

        def do_POST(self):
            try:
                self.allowed(post=True)
                if self.path not in ("/api/share/log", "/api/sharing"):
                    raise BridgeError(403, "Read-only bridge")
                if self.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json":
                    raise BridgeError(415, "JSON required")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 512 or self.headers.get("Transfer-Encoding"):
                    raise BridgeError(400, "Invalid body")
                body = json.loads(self.rfile.read(length))
                if self.path == "/api/sharing":
                    if not isinstance(body, dict) or set(body) != {"enabled"}:
                        raise BridgeError(400, "Only enabled is accepted")
                    return self.send(200, bridge.set_sharing(body["enabled"]))
                if not isinstance(body, dict) or set(body) != {"id"}:
                    raise BridgeError(400, "Only a session ID is accepted")
                return self.send(200, bridge.share_log(validate_id(body["id"])))
            except BridgeError as exc:
                self.send(exc.code, {"error": exc.message})
            except (OSError, ValueError, TypeError):
                self.send(400, {"error": "Invalid request"})

        def do_OPTIONS(self):
            self.send(405, {"error": "Cross-origin API access is disabled"})

    return ThreadingHTTPServer(("127.0.0.1", bridge.config.listen_port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description="HTTP-only receiver sidecar; no hardware access")
    parser.add_argument("--stdin-config", action="store_true", help="Read one JSON line from stdin; publication secret stays in memory")
    parser.add_argument("--port", type=int, default=None, help="Loopback listener port (default 8766)")
    args = parser.parse_args(argv)
    try:
        settings = {}
        if args.stdin_config:
            line = sys.stdin.readline(16385)
            if len(line) > 16384:
                raise BridgeError(400, "Configuration too large")
            settings = json.loads(line)
            if not isinstance(settings, dict) or set(settings) - {"site_url", "publish_token", "upstream", "listen_port"}:
                raise BridgeError(400, "Unsupported configuration")
        if args.port is not None:
            settings["listen_port"] = args.port
        config = Config(**settings)
        bridge = Bridge(config)
        server = make_server(bridge)
    except (BridgeError, ValueError, TypeError, OSError):
        print("Bridge configuration or listener unavailable", file=sys.stderr)
        return 2
    thread = threading.Thread(target=bridge.run, name="http-observer", daemon=True)
    thread.start()
    publisher = None
    if config.sharing:
        publisher = threading.Thread(target=bridge.run_publisher, name="summary-publisher", daemon=True)
        publisher.start()
    print("Read-only preview: http://127.0.0.1:" + str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop.set()
        server.server_close()
        thread.join(timeout=10)
        if publisher:
            publisher.join(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
