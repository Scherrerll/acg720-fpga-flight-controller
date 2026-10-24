"""Offline unit and loopback mock HTTP contracts. Never contact the real receiver."""
import copy
import csv
import gzip
import io
import json
import tempfile
import threading
import time
import unittest
import contextlib
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import bridge

ID = "20261020T140334Z_ca766040"


def state():
    return {"connected": True, "fresh": True, "flight_info_fresh": True,
        "sequence": 12, "frame_age_ms": 25, "fresh_timeout_ms": 500,
        "flight_info": {"build_id": 0xb0ac, "sequence": 12, "uptime_ms": 5000},
        "navigation_fresh": True, "mtf_fresh": True,
        "data": {"roll_deg": 1, "pitch_deg": -2, "yaw_relative_deg": 3,
            "rc_us": [1500, 1501, 1100, 1502], "pwm_us": [1000, 1001, 1002, 1003],
            "rc_valid": True, "sensor_ok": True, "armed": False,
            "mode_active": 2, "mode_requested": 2, "height_cm": 90},
        "navigation": {"reason": 0, "xy_shadow_active": True, "xyz_active": True},
        "navigation_values": {"nav_fused_height_mm": 1500, "nav_fused_vx_mm_s": 3000,
            "nav_fused_vy_mm_s": 4000, "nav_fused_vz_mm_s": -200, "nav_position_x_mm": 250},
        "mtf_sensor": {"flow_provisionally_valid": True, "range_provisionally_valid": False,
            "module_raw_hex": "PRIVATE_RAW_SENTINEL", "device_id": "PRIVATE_DEVICE_SENTINEL"},
        "recording": {"frames": 100, "missing_primary_frames": 2, "receiver_checksum_errors": 1,
            "bytes": 3000, "closed": False, "source": {"usb_device": "PRIVATE_DEVICE_SENTINEL"}},
        "stats": {"sequence_resets": 1},
        "source": {"port": "PRIVATE_PORT_SENTINEL", "usb_device": "PRIVATE_DEVICE_SENTINEL"},
        "error": "PRIVATE_PATH_SENTINEL",
        "history": [{"t": i * .1, "roll_deg": i, "pitch_deg": 2, "yaw_relative_deg": 3,
            "height_cm": 150, "velocity_x_m_s": 3, "velocity_y_m_s": 4} for i in range(600)]}


def csv_data(count=1):
    out = io.StringIO()
    fields = ["elapsed_s", "protocol", "sequence", "epoch", "roll_deg", "pitch_deg", "yaw_deg",
        "selected_height_cm", "nav_fused_height_mm", "nav_fused_vx_mm_s", "nav_fused_vy_mm_s", "nav_fused_vz_mm_s",
        "m1_us", "throttle_us", "armed", "mtf_range_cm", "mtf_vx_mm_s", "utc", "program_label"]
    writer = csv.DictWriter(out, fields)
    writer.writeheader()
    for i in range(count):
        writer.writerow({"elapsed_s": i * .2, "protocol": "a579", "sequence": i % 65536, "epoch": 0,
            "roll_deg": 1, "pitch_deg": 2, "yaw_deg": 3, "selected_height_cm": 150, "m1_us": 1100,
            "throttle_us": 1200, "armed": "False", "utc": "PRIVATE_PATH_SENTINEL", "program_label": "PRIVATE_DEVICE_SENTINEL"})
    writer.writerow({"elapsed_s": count * .2, "protocol": "a582", "nav_fused_height_mm": 1800,
        "nav_fused_vx_mm_s": 1500, "nav_fused_vy_mm_s": -300, "nav_fused_vz_mm_s": 125, "armed": "False"})
    writer.writerow({"elapsed_s": count * .2 + .01, "protocol": "a581", "mtf_range_cm": 250, "mtf_vx_mm_s": 400, "armed": "False"})
    writer.writerow({"elapsed_s": count * .2 + .02, "protocol": "a583", "armed": "False"})
    return out.getvalue().encode("utf-8-sig")


class FakeClient:
    def __init__(self):
        self.value = state()
        self.fail = False
        self.gets = []
        self.posts = []

    def get_json(self, path):
        self.gets.append(path)
        if self.fail:
            raise bridge.BridgeError(502, "Unavailable")
        if path == "/api/state":
            return copy.deepcopy(self.value)
        if path == "/api/logs":
            return {"sessions": [{"id": ID, "meta": {"started_utc": "2026-10-20T14:03:34Z", "source": "PRIVATE_DEVICE_SENTINEL"},
                "bytes": 100, "active": True}, {"id": "../../private", "meta": {}}]}
        raise AssertionError(path)

    def get(self, path):
        self.gets.append(path)
        assert path == f"/api/logs/{ID}/download?format=csv"
        return csv_data()

    def publish(self, kind, payload):
        self.posts.append((kind, copy.deepcopy(payload)))
        return {"ok": True, "unsafe": "PRIVATE_PATH_SENTINEL"}

    def server_clock(self):
        return 1800000000000


class UnitTests(unittest.TestCase):
    def test_reported_tracking_flows_to_history_and_csv_without_rc_reconstruction(self):
        fake = FakeClient()
        fake.value['tracking'] = dict(roll_sp_deg=4.5, pitch_sp_deg=-2,
                                     yaw_rate_dps=1.25, yaw_rate_sp_dps=3, private='PRIVATE_SECRET')
        observer = bridge.Bridge(bridge.Config(), fake)
        observer.poll_once()
        value = observer.live()
        self.assertEqual(value['tracking']['roll_sp_deg'], 4.5)
        self.assertEqual(value['history'][-1]['yaw_rate_sp_dps'], 3)
        self.assertNotIn('PRIVATE_SECRET', json.dumps(value))
        fake.value['fresh'] = False
        self.assertTrue(all(v is None for v in bridge.sanitize_live(fake.value)['tracking'].values()))
        raw = b'elapsed_s,protocol,roll_deg,roll_sp_deg,pitch_sp_deg,yaw_rate_dps,yaw_rate_sp_dps\n0,a579,1,2,-3,4,5\n1,a582,,,,,\n'
        sample = bridge.csv_samples(raw, ID)['log']['samples'][0]
        self.assertEqual([sample[k] for k in bridge.TRACKING], [2, -3, 4, 5])
        old = bridge.csv_samples(csv_data(), ID)['log']['samples'][0]
        self.assertTrue(all(old[k] is None for k in bridge.TRACKING))

    def test_live_sharing_defaults_off_skips_cloud_clock_and_posts(self):
        fake = FakeClient()
        calls = []
        fake.server_clock = lambda: calls.append("clock") or 1800000000000
        observer = bridge.Bridge(bridge.Config(site_url="https://example.test", publish_token="FAKE_TEST_BEARER"), fake)
        observer.poll_once(); observer.publish_once()
        self.assertEqual(calls, []); self.assertEqual(fake.posts, [])
        self.assertTrue(observer.live()["source_valid"])
        observer.set_sharing(True); observer.publish_once()
        self.assertEqual(calls, ["clock"]); self.assertEqual(len(fake.posts), 1)
        observer.set_sharing(False); observer.publish_once()
        self.assertEqual(calls, ["clock"]); self.assertEqual(len(fake.posts), 1)
        with self.assertRaises(bridge.BridgeError): observer.set_sharing("true")
        with self.assertRaises(bridge.BridgeError): bridge.Bridge(bridge.Config(), fake).set_sharing(True)

    def test_publication_size_limits_never_send_partial_data(self):
        client = bridge.HTTPClient(bridge.Config(site_url="https://example.test", publish_token="FAKE_TEST_BEARER"))
        with patch.object(client, "_read") as send:
            with self.assertRaises(bridge.BridgeError) as exc:
                client.publish("log", {"data":"x" * (8 * 1024 * 1024)})
            self.assertEqual(exc.exception.code, 413)
            send.assert_not_called()
            with patch.object(bridge.gzip, "compress", return_value=b"x" * (5 * 1024 * 1024 + 1)):
                with self.assertRaises(bridge.BridgeError) as exc: client.publish("log", {"samples":[]})
                self.assertEqual(exc.exception.code, 413)
            send.assert_not_called()

    def test_projection_units_nulls_and_no_private_data(self):
        value = bridge.age_live(bridge.sanitize_live(state()), 0, True)
        self.assertEqual(value["firmware"], "B0AC")
        self.assertTrue(value["fresh"])
        self.assertEqual(value["motion"]["height_m"], 1.5)
        self.assertEqual(value["motion"]["speed_mps"], 5)
        self.assertEqual(value["motion"]["vz_mps"], -.2)
        self.assertEqual(value["rc"]["throttle_us"], 1100)
        self.assertEqual(len(value["history"]), 120)
        self.assertGreater(value["history"][0]["t"], 1e12)
        self.assertEqual(value["history"][-1]["t"] - value["history"][0]["t"], 59900)
        self.assertEqual(value["history"][-1]["height_m"], 1.5)
        self.assertNotIn("PRIVATE_", json.dumps(value))
        empty = bridge.sanitize_live({})
        self.assertIsNone(empty["health"]["imu"])
        self.assertIsNone(empty["attitude"]["roll_deg"])
        self.assertFalse(empty["fresh"])
        s = state(); s["data"]["mode_active"] = "自稳"; s["data"]["mode_requested"] = "定点"
        self.assertEqual(bridge.sanitize_live(s)["control_mode"], "自稳")
        self.assertEqual(bridge.sanitize_live(s)["flags"]["requested"], "定点")

    def test_identity_and_ttl(self):
        for key in ("fresh", "flight_info_fresh", "connected"):
            s = state(); s[key] = False
            self.assertFalse(bridge.sanitize_live(s)["fresh"])
        s = state(); s["flight_info"]["sequence"] = 11
        self.assertTrue(bridge.sanitize_live(s)["fresh"])
        self.assertTrue(bridge.sanitize_live(s)["source_valid"])
        self.assertEqual(bridge.sanitize_live(s)["source_ttl_ms"], 500)
        s["flight_info"]["sequence"] = 10
        self.assertFalse(bridge.sanitize_live(s)["fresh"])
        s["sequence"] = 0; s["flight_info"]["sequence"] = 65535
        self.assertTrue(bridge.sanitize_live(s)["fresh"])
        for invalid in (-1, 65536, 1.5):
            s["sequence"] = s["flight_info"]["sequence"] = invalid
            self.assertFalse(bridge.sanitize_live(s)["fresh"])
        value = bridge.age_live(bridge.sanitize_live(state()), .6, True)
        self.assertFalse(value["fresh"])
        self.assertTrue(value["source_valid"])
        self.assertEqual(value["attitude"]["roll_deg"], 1)
        self.assertEqual(value["age_ms"], 625)

    def test_clock_projection_and_publication_source_assertion(self):
        now = [0]
        fake = FakeClient()
        server_epoch = 1800000000000
        attempts = []
        def server_clock():
            attempts.append(now[0]); now[0] += .2
            return server_epoch
        fake.server_clock = server_clock
        config = bridge.Config(site_url="https://example.test", publish_token="FAKE_TEST_BEARER")
        observer = bridge.Bridge(config, fake, lambda: now[0], lambda: server_epoch / 1000 - 35 + now[0])
        observer.set_sharing(True); observer.poll_once(); observer.publish_once()
        self.assertEqual(len(attempts), 1)
        self.assertTrue(fake.posts[-1][1]["timing_valid"])
        self.assertEqual(fake.posts[-1][1]["timing_version"], 2)
        self.assertAlmostEqual(fake.posts[-1][1]["clock_uncertainty_ms"], 100)
        fake.value["frame_age_ms"] = 480
        observer.poll_once(); now[0] += .03
        local = observer.live()
        self.assertAlmostEqual(local["age_ms"], 510)
        self.assertFalse(local["fresh"])
        self.assertTrue(local["source_valid"])
        observer.publish_once()
        published = fake.posts[-1][1]
        self.assertTrue(published["fresh"])
        self.assertTrue(published["source_valid"])
        self.assertEqual(published["source_ttl_ms"], 500)
        projected = bridge.dt.datetime.fromisoformat(published["source_publish_at"].replace("Z", "+00:00")).timestamp() * 1000
        self.assertAlmostEqual(projected, server_epoch + 130, delta=1)
        self.assertAlmostEqual(published["history_reference_time_ms"], server_epoch - 35000 + now[0] * 1000, delta=1)
        self.assertGreater(projected - published["history_reference_time_ms"], 34000)
        self.assertEqual(len(attempts), 1)  # No clock request on every 1Hz publication.
        fake.fail = True; observer.poll_once(); observer.publish_once()
        self.assertFalse(fake.posts[-1][1]["source_valid"])
        self.assertFalse(fake.posts[-1][1]["fresh"])
        fake.fail = False
        def unavailable_clock():
            attempts.append(now[0]); raise bridge.BridgeError(502, "Unavailable")
        fake.server_clock = unavailable_clock
        now[0] = 61; fake.value["frame_age_ms"] = 25; observer.poll_once(); observer.publish_once()
        self.assertTrue(fake.posts[-1][1]["timing_valid"])  # Failed renewal, old base is still younger than 120s.
        now[0] = 122; observer.poll_once(); observer.publish_once()
        self.assertTrue(fake.posts[-1][1]["source_valid"])
        self.assertFalse(fake.posts[-1][1]["timing_valid"])
        self.assertFalse(fake.posts[-1][1]["fresh"])
        self.assertIsNone(fake.posts[-1][1]["source_publish_at"])
        self.assertIsNone(fake.posts[-1][1]["clock_uncertainty_ms"])
        self.assertAlmostEqual(fake.posts[-1][1]["history_reference_time_ms"], server_epoch - 35000 + now[0] * 1000, delta=1)
        new = bridge.Bridge(config, fake, lambda: now[0])
        new.set_sharing(True); new.poll_once(); new.publish_once()
        self.assertFalse(fake.posts[-1][1]["timing_valid"])  # No initial synchronization cannot masquerade as realtime.
        def slow_clock():
            now[0] += 4.01; return server_epoch
        fake.server_clock = slow_clock
        slow = bridge.Bridge(config, fake, lambda: now[0])
        slow.set_sharing(True); slow.poll_once(); slow.publish_once()
        self.assertIsNone(slow.server_clock_base)
        self.assertFalse(fake.posts[-1][1]["timing_valid"])

    def test_own_height_history_2hz_60s_no_backfill_or_duplicate_sequence(self):
        now = [0]
        fake = FakeClient()
        for item in fake.value["history"]:
            item["height_cm"] = None
        observer = bridge.Bridge(bridge.Config(), fake, lambda: now[0], lambda: 1800000000 + now[0])
        observer.poll_once()
        first = observer.live()
        self.assertEqual(len(first["history"]), 1)
        self.assertEqual(first["history"][0]["height_m"], 1.5)
        self.assertEqual(first["history"][0]["t"], 1800000000000 - 25)
        self.assertEqual(first["age_ms"], 25)
        now[0] = .5; observer.poll_once()
        self.assertEqual(len(observer.live()["history"]), 1)  # unchanged primary sequence
        for i in range(1, 245):
            now[0] = i * .25 + .5
            fake.value["sequence"] = fake.value["flight_info"]["sequence"] = 12 + i
            observer.poll_once()
        points = observer.live()["history"]
        self.assertLessEqual(len(points), 120)
        self.assertTrue(all(b["t"] - a["t"] >= 500 for a, b in zip(points, points[1:])))
        self.assertTrue(all(p["t"] >= (1800000000 + now[0]) * 1000 - 60000 for p in points))
        before = len(points)
        now[0] += .5; fake.value["fresh"] = False; observer.poll_once()
        self.assertLessEqual(len(observer.live()["history"]), before)
        self.assertFalse(observer.live()["fresh"])
        now[0] += 61
        self.assertEqual(observer.live()["history"], [])

    def test_http_failure_and_source_stale_retain_last_values(self):
        now = [0]
        client = FakeClient(); b = bridge.Bridge(bridge.Config(), client, lambda: now[0])
        b.poll_once(); now[0] = 3; client.fail = True; b.poll_once()
        value = b.live()
        self.assertFalse(value["fresh"])
        self.assertFalse(value["connected"])
        self.assertEqual(value["age_ms"], 3025)
        self.assertEqual(value["attitude"]["roll_deg"], 1)
        client.fail = False; client.value["fresh"] = False; client.value["data"] = None
        b.poll_once()
        self.assertEqual(b.live()["attitude"]["roll_deg"], 1)
        self.assertFalse(b.live()["fresh"])
        self.assertEqual(client.posts, [])

    def test_csv_units_sparse_protocols_and_numeric_export(self):
        value = bridge.csv_samples(csv_data(), ID)
        samples = value["log"]["samples"]
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["t_s"], 0)
        self.assertEqual(samples[0]["height_m"], 1.5)
        self.assertEqual(samples[1]["height_m"], 1.8)
        self.assertEqual(samples[1]["vx_mps"], 1.5)
        self.assertEqual(samples[1]["vz_mps"], .125)
        self.assertIsNone(samples[1]["armed"])
        self.assertIsNone(samples[0]["vx_mps"])
        self.assertEqual(value["log"]["summary"]["source_rows"], 4)
        self.assertNotIn("PRIVATE_", json.dumps(value))
        result = bridge.export_csv(value).decode("utf-8-sig")
        self.assertEqual(result.splitlines()[0], ",".join(bridge.COLUMNS))
        self.assertNotIn("PRIVATE_", result)

    def test_downsample_and_limit_are_not_claimed_complete(self):
        value = bridge.csv_samples(csv_data(20001), ID)["log"]
        self.assertEqual(len(value["samples"]), 20000)
        self.assertEqual(value["summary"]["eligible_samples"], 20002)
        self.assertTrue(value["summary"]["downsampled"])
        self.assertFalse(value["summary"]["complete"])
        with self.assertRaises(bridge.BridgeError) as exc:
            bridge.csv_samples(b"x" * (bridge.MAX_RESPONSE + 1), ID)
        self.assertEqual(exc.exception.code, 413)

    def test_fixed_endpoints_and_configuration_no_secret_representation(self):
        for url in ("http://example.com", "file:///private", "http://127.0.0.1:8765/api/state", "http://user:pass@localhost"):
            with self.assertRaises(bridge.BridgeError):
                bridge.Config(upstream=url)
        config = bridge.Config(site_url="https://example.test", publish_token="FAKE_TEST_BEARER")
        self.assertNotIn("FAKE_TEST_BEARER", repr(config))
        with self.assertRaises(bridge.BridgeError):
            bridge.HTTPClient(config).get("/api/service/stop")
        for ident in ("../secret", ID + "/../../secret", "http://example.test"):
            with self.assertRaises(bridge.BridgeError):
                bridge.validate_id(ident)

    def test_independent_source_4hz_and_publication_1hz_schedulers(self):
        now, starts = [0], []
        observer = bridge.Bridge(bridge.Config(), FakeClient(), lambda: now[0])

        class Stop:
            def is_set(self): return len(starts) >= 3
            def wait(self, duration): now[0] += duration

        def poll():
            starts.append(now[0]); now[0] += .1
        observer.stop = Stop(); observer.poll_once = poll; observer.run()
        self.assertEqual(starts, [0, .25, .5])
        now[0] = 0; starts.clear()
        observer.publish_once = poll; observer.run_publisher()
        self.assertEqual(starts, [0, 1, 2])

        # A blocked publication must never hold the snapshot lock or run inside
        # source polling. Only a mock publisher is used, with no real network.
        entered, release = threading.Event(), threading.Event()
        fake = FakeClient()
        def blocked_publish(kind, value):
            entered.set(); release.wait(2)
        fake.publish = blocked_publish
        other = bridge.Bridge(bridge.Config(site_url="https://example.test", publish_token="FAKE_TEST_BEARER"), fake)
        other.set_sharing(True)
        other.poll_once()
        thread = threading.Thread(target=other.publish_once, daemon=True); thread.start()
        try:
            self.assertTrue(entered.wait(1))
            fake.value["sequence"] = 13; fake.value["flight_info"]["sequence"] = 13
            other.poll_once()
            self.assertEqual(other.live()["sequence"], 13)
            self.assertTrue(thread.is_alive())
        finally:
            release.set(); thread.join(2)

    def test_bad_stdin_configuration_does_not_echo_credentials(self):
        stderr = io.StringIO()
        with patch("sys.stdin", io.StringIO('{"publish_token":"FAKE_TEST_BEARER"}\n')), contextlib.redirect_stderr(stderr):
            self.assertEqual(bridge.main(["--stdin-config"]), 2)
        self.assertNotIn("FAKE_TEST_BEARER", stderr.getvalue())


class HTTPContractTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.config = bridge.Config(listen_port=0, site_url="https://example.test", publish_token="FAKE_TEST_BEARER")
        self.bridge = bridge.Bridge(self.config, self.fake)
        self.tmp = tempfile.TemporaryDirectory()
        Path(self.tmp.name, "index.html").write_text("<h1>preview</h1>", encoding="utf-8")
        self.server = bridge.make_server(self.bridge, self.tmp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.tmp.cleanup()

    def request(self, path, body=None, headers=None, method=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as response:
            return response.code, response.read()

    def test_read_contracts_and_no_log_upload_until_explicit_post(self):
        self.bridge.poll_once()
        self.assertEqual(self.fake.posts, [])
        self.bridge.publish_once()
        self.assertEqual(self.fake.posts, [])
        self.bridge.set_sharing(True)
        self.bridge.publish_once()
        self.assertEqual([p[0] for p in self.fake.posts], ["live"])
        code, raw = self.request("/api/live")
        self.assertEqual(code, 200); self.assertEqual(json.loads(raw)["schema"], 1)
        self.assertNotIn(b"FAKE_TEST_BEARER", raw)
        code, raw = self.request("/api/capabilities")
        self.assertEqual(json.loads(raw), {"mode": "local", "share_url": "https://example.test", "can_share_logs": True, "sharing_enabled": True})
        code, raw = self.request("/api/logs")
        self.assertEqual(len(json.loads(raw)["logs"]), 1)
        self.assertNotIn("PRIVATE_", raw.decode())
        self.assertNotIn(f"/api/logs/{ID}/download?format=csv", self.fake.gets)
        code, raw = self.request(f"/api/logs/{ID}")
        self.assertEqual(code, 200); self.assertEqual(json.loads(raw)["log"]["id"], ID)
        self.assertEqual([p[0] for p in self.fake.posts], ["live"])
        code, raw = self.request("/api/share/log", {"id": ID}, {"Origin": self.base, "Content-Type": "application/json"})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(raw)["share_url"], "https://example.test/?log=" + ID)
        self.assertEqual(self.fake.posts[-1][0], "log")
        self.assertIn("samples", self.fake.posts[-1][1])
        self.assertNotIn("log", self.fake.posts[-1][1])

    def test_local_sharing_toggle_requires_same_origin_and_boolean(self):
        headers = {"Origin":self.base, "Content-Type":"application/json"}
        self.assertEqual(self.request("/api/sharing", {"enabled":True}, {"Content-Type":"application/json"})[0], 403)
        self.assertEqual(self.request("/api/sharing", {"enabled":True}, {**headers,"Origin":"https://evil.test"})[0], 403)
        self.assertEqual(self.request("/api/sharing", {"enabled":"true"}, headers)[0], 400)
        self.assertEqual(self.request("/api/sharing", {"enabled":True,"url":"https://evil.test"}, headers)[0], 400)
        self.assertEqual(json.loads(self.request("/api/capabilities")[1])["sharing_enabled"], False)
        self.assertEqual(self.request("/api/sharing", {"enabled":True}, headers)[0], 200)
        self.bridge.publish_once(); self.assertEqual(len(self.fake.posts), 1)
        self.assertEqual(self.request("/api/sharing", {"enabled":False}, headers)[0], 200)
        self.bridge.publish_once(); self.assertEqual(len(self.fake.posts), 1)

    def test_host_origin_methods_traversal_and_api_allowlist(self):
        cases = [("/api/state", None, {}, None, 404),
            ("/api/live", None, {"Host": "evil.test"}, None, 403),
            ("/api/live", None, {"Origin": "https://evil.test"}, None, 403),
            ("/api/connection", {}, {"Origin": self.base, "Content-Type": "application/json"}, None, 403),
            ("/api/service/stop", {}, {"Origin": self.base, "Content-Type": "application/json"}, None, 403),
            ("/api/share/log", {"id": ID}, {"Content-Type": "application/json"}, None, 403),
            ("/api/share/log", {"id": ID}, {"Origin": self.base, "Content-Type": "text/plain"}, None, 415),
            ("/api/share/log", {"id": "../../secret"}, {"Origin": self.base, "Content-Type": "application/json"}, None, 400),
            ("/api/logs/../../secret", None, {}, None, 404),
            ("/api/live?url=http://evil.test", None, {}, None, 400),
            ("/%2e%2e/secret.txt", None, {}, None, 404)]
        for path, body, headers, method, expected in cases:
            with self.subTest(path=path, headers=headers):
                code, raw = self.request(path, body, headers, method)
                self.assertEqual(code, expected)
                self.assertNotIn("PRIVATE_", raw.decode())
        self.assertEqual(self.fake.gets, [])
        self.assertEqual(self.fake.posts, [])


class RealMockTransportTests(unittest.TestCase):
    def test_http_only_transport_publish_header_and_redirect_refusal(self):
        calls = []
        scenario = {"redirect": False, "oversize": False}

        class Mock(BaseHTTPRequestHandler):
            def log_message(self, *args): pass

            def do_GET(self):
                calls.append(("GET", self.path, self.headers.get("X-Flight-Publish-Token"), None))
                assert self.headers.get("Authorization") is None
                if scenario["redirect"]:
                    self.send_response(302); self.send_header("Location", "/must-not-follow"); self.end_headers(); return
                if scenario["oversize"]:
                    self.send_response(200); self.send_header("Content-Length", str(bridge.MAX_RESPONSE + 1)); self.end_headers(); return
                if self.path == "/api/state":
                    body = json.dumps(state()).encode()
                elif self.path == "/api/health":
                    assert self.headers.get("User-Agent") == "ACG720-GroundStation/1.0"
                    body = json.dumps({"server_time_ms": 1800000000000}).encode()
                elif self.path == "/api/logs":
                    body = json.dumps({"sessions": []}).encode()
                elif self.path == f"/api/logs/{ID}/download?format=csv":
                    body = csv_data()
                else:
                    self.send_response(404); self.end_headers(); return
                self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

            def do_POST(self):
                raw = self.rfile.read(int(self.headers["Content-Length"]))
                if self.path.endswith("/log"):
                    assert self.headers.get("Content-Encoding") == "gzip"
                    raw = gzip.decompress(raw)
                else:
                    assert self.headers.get("Content-Encoding") is None
                payload = json.loads(raw)
                calls.append(("POST", self.path, self.headers.get("X-Flight-Publish-Token"), payload))
                assert self.headers.get("Authorization") is None
                assert self.headers.get("User-Agent") == "ACG720-GroundStation/1.0"
                self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')

        server = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        config = bridge.Config(upstream=url, site_url=url, publish_token="FAKE_TEST_BEARER", listen_port=0)
        observer = bridge.Bridge(config)
        try:
            observer.set_sharing(True); observer.poll_once(); observer.publish_once(); observer.logs(); observer.log(ID)
            self.assertEqual(len([c for c in calls if c[0] == "POST"]), 1)
            observer.share_log(ID)
            self.assertEqual([c[1] for c in calls if c[0] == "POST"], ["/api/publish/live", "/api/publish/log"])
            self.assertTrue(all(c[2] == "FAKE_TEST_BEARER" for c in calls if c[0] == "POST"))
            self.assertTrue(all("PRIVATE_" not in json.dumps(c[3]) for c in calls if c[0] == "POST"))
            self.assertTrue(all(c[0] == "GET" for c in calls if not c[1].startswith("/api/publish/")))
            self.assertTrue(all(c[2] is None for c in calls if c[0] == "GET"))
            self.assertIn("/api/health", [c[1] for c in calls])
            scenario["redirect"] = True
            with self.assertRaises(bridge.BridgeError):
                observer.client.get_json("/api/state")
            self.assertNotIn("/must-not-follow", [c[1] for c in calls])
            scenario["redirect"] = False; scenario["oversize"] = True
            with self.assertRaises(bridge.BridgeError) as exc:
                observer.client.get_json("/api/state")
            self.assertEqual(exc.exception.code, 413)
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    unittest.main()
