"""Offline protocol proof. No serial port or hardware is opened."""
import binascii
import importlib.util
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

BASE = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("b0b1_ground", BASE / "ground" / "__init__.py",
    submodule_search_locations=[str(BASE / "ground")])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
from b0b1_ground.protocol import (BUILD_ID, MOD32, FrameParser, ProtocolError,
    StreamTracker, decode_payload)
from b0b1_ground import capture


def raw(source=10, accepted=3, flags=0x7F):
    return struct.pack(">I6hI6B", source, -32768, 12, 2048, -164, 0, 32767,
                       accepted, 0x80, 0, flags, 16, 2, 7)


def pose(accepted=3, flags=31):
    return struct.pack(">II3i3hBB", accepted, 50001, -123456, 2, -3,
                       -1234, 2345, -3000, flags, 0)


def fault(cause=3):
    return struct.pack(">4B10I4BH2B18h", 7, cause, 4, 128,
                       *range(10, 0, -1), 20, 21, 2, 3, 0x3FF, 4, 5,
                       *range(-9, 9))


def status(uptime=1000, drops=(0, 0, 0, 0), build=BUILD_ID):
    return struct.pack(">Q8I", uptime, build, *drops, 123, 1000, 900)


PAYLOADS = {1: raw, 2: pose, 3: fault, 4: status}


def packet(typ=1, seq=0, tick=100000, payload=None, version=1):
    body = struct.pack(">BBHI", version, typ, seq, tick) + (PAYLOADS[typ]() if payload is None else payload)
    return b"\xA5\x84" + body + struct.pack(">H", binascii.crc_hqx(body, 0xFFFF))


def tracked(tracker, *packets):
    parser = FrameParser()
    return [record for data in packets for frame in parser.feed(data)
            for record in tracker.ingest(frame)]


class FixedPayloadTests(unittest.TestCase):
    def test_all_types_and_signed_units(self):
        rows = [decode_payload(1, typ, factory()) for typ, factory in PAYLOADS.items()]
        self.assertEqual(rows[0]["ax"], -32768)
        self.assertEqual(rows[0]["acceleration_g"][2], 1)
        self.assertAlmostEqual(rows[0]["gyro_deg_s"][0], -10)
        self.assertTrue(rows[0]["physical_observation_valid"])
        self.assertEqual(rows[1]["world_ax"], -123456)
        self.assertEqual(rows[1]["held_dt_ticks"], 50001)
        self.assertEqual(rows[1]["sensor_roll_cdeg"], -1234)
        self.assertEqual(rows[2]["first_cause_name"], "accepted_sample_busy_collision")
        self.assertEqual(rows[2]["triggers"], ["pose_age_20ms", "attitude_valid_fall", "gate_event"])
        self.assertEqual(rows[2]["rejected_raw"]["ax"], -9)
        self.assertEqual(rows[2]["candidate"]["gz"], 8)
        self.assertEqual(rows[3]["build_id"], 0xB0B1)

    def test_exact_lengths(self):
        for typ, factory in PAYLOADS.items():
            for data in (factory()[:-1], factory() + b"\0"):
                with self.subTest(typ=typ, length=len(data)), self.assertRaises(ProtocolError):
                    decode_payload(1, typ, data)

    def test_unknown_version_type_reserved_bits_build(self):
        for version, typ, data in [(2, 1, raw()), (1, 99, b""),
                                    (1, 2, pose(flags=0x80)), (1, 4, status(build=0))]:
            with self.subTest(version=version, typ=typ), self.assertRaises(ProtocolError):
                decode_payload(version, typ, data)

    def test_invalid_reader_words_are_retained_but_not_observations(self):
        r = decode_payload(1, 1, raw(flags=8))
        self.assertEqual(r["ax"], -32768)
        self.assertTrue(r["accepted"])
        self.assertFalse(r["physical_observation_valid"])


class FramingTests(unittest.TestCase):
    def test_fragmentation_at_every_boundary_for_every_type(self):
        for typ in PAYLOADS:
            data = packet(typ=typ, seq=4321, tick=0xFEDCBA98)
            for at in range(len(data) + 1):
                with self.subTest(typ=typ, boundary=at):
                    p = FrameParser()
                    frames = p.feed(data[:at]) + p.feed(data[at:])
                    self.assertEqual(len(frames), 1)
                    self.assertEqual(frames[0]["sequence"], 4321)
                    self.assertEqual(frames[0]["capture_tick"], 0xFEDCBA98)
                    self.assertEqual(frames[0]["byte_end"], len(data))
                    self.assertEqual(p.finish()["trailing_bytes"], 0)

    def test_single_byte_fragmentation_and_embedded_magic(self):
        data = packet(1, payload=raw(source=0xA5841234)) + packet(2, seq=1)
        p = FrameParser()
        frames = [r for b in data for r in p.feed(bytes([b]))]
        self.assertEqual([r["type"] for r in frames], ["raw", "pose"])

    def test_crc_error_noise_and_resync(self):
        bad = bytearray(packet(1))
        bad[12] ^= 1
        prefix = b"noise\xA5"
        p = FrameParser()
        frames = p.feed(prefix + bad + packet(2, seq=2))
        self.assertEqual([r["sequence"] for r in frames], [2])
        self.assertEqual(p.stats["crc_errors"], 1)
        self.assertEqual(frames[0]["byte_start"], len(prefix) + len(bad))

    def test_unknown_version_and_type_recover(self):
        p = FrameParser()
        frames = p.feed(b"\xA5\x84\x02\x01bad\xA5\x84\x01\x77bad" + packet(4))
        self.assertEqual(len(frames), 1)
        self.assertEqual(p.stats["unknown_versions"], 1)
        self.assertEqual(p.stats["unknown_types"], 1)

    def test_bad_payload_with_valid_crc_recovers(self):
        p = FrameParser()
        frames = p.feed(packet(2, payload=pose(flags=0xC0)) + packet(1, seq=1))
        self.assertEqual(len(frames), 1)
        self.assertEqual(p.stats["payload_errors"], 1)

    def test_truncated_final_frame_is_reported(self):
        p = FrameParser()
        self.assertFalse(p.feed(packet(3)[:-1]))
        self.assertEqual(p.finish()["truncated_frames"], 1)
        self.assertEqual(p.finish()["trailing_bytes"], 99)

    def test_corrupt_long_type_header_cannot_hide_valid_short_tail_at_eof(self):
        p = FrameParser()
        bad_long_header = b"\xa5\x84\x01\x03" + b"\0" * 10
        self.assertFalse(p.feed(bad_long_header + packet(1, seq=3)))
        recovered = p.recover_eof()
        self.assertEqual([r["sequence"] for r in recovered], [3])
        self.assertEqual(p.finish()["truncated_frames"], 1)
        self.assertEqual(p.finish()["eof_recovered_frames"], 1)
        self.assertEqual(recovered[0]["byte_start"], len(bad_long_header))


class TrackingTests(unittest.TestCase):
    def test_sequence_gap_wrap_and_duplicate(self):
        t = StreamTracker()
        records = tracked(t, packet(seq=65534), packet(seq=65535), packet(seq=0),
                          packet(seq=3), packet(seq=3))
        self.assertEqual(t.stats["sequence_missing"], 2)
        self.assertEqual(t.stats["sequence_gap_events"], 1)
        self.assertEqual(t.stats["duplicate_sequences"], 1)
        self.assertEqual(records[-2]["missing_before"], 2)

    def test_tick_wrap_does_not_make_reboot(self):
        t = StreamTracker()
        out = tracked(t, packet(seq=5, tick=MOD32-10, payload=raw(source=1, accepted=1)),
                      packet(seq=6, tick=20, payload=raw(source=2, accepted=2)))
        self.assertEqual(out[-1]["capture_tick64"], MOD32 + 20)
        self.assertEqual(out[-1]["epoch"], 0)

    def test_status_uptime_anchors_multiple_tick_wraps(self):
        t = StreamTracker()
        uptime = 200000
        tick = uptime * 50000 % MOD32
        out = tracked(t, packet(4, tick=tick, payload=status(uptime)),
                      packet(seq=1, tick=(tick + 50000) % MOD32))
        self.assertEqual(out[-1]["capture_tick64"], uptime * 50000 + 50000)
        self.assertEqual(out[-1]["onboard_uptime_ms_estimate"], uptime + 1)

    def test_cross_type_queue_reorder_across_wrap_uses_status_not_transmit_order(self):
        t = StreamTracker()
        uptime = 86000
        anchor = uptime * 50000 % MOD32
        out = tracked(t, packet(4, seq=50, tick=anchor, payload=status(uptime)),
            packet(2, seq=51, tick=200, payload=pose(3)),
            packet(1, seq=52, tick=MOD32-100, payload=raw(10, 3)),
            packet(3, seq=53, tick=MOD32-50000),
            packet(1, seq=54, tick=100, payload=raw(11, 4)))
        frames = [r for r in out if r["kind"] == "frame"]
        self.assertEqual(t.epoch, 0)
        self.assertEqual(frames[1]["capture_tick64"], MOD32+200)
        self.assertEqual(frames[2]["capture_tick64"], MOD32-100)
        self.assertEqual(frames[3]["capture_tick64"], MOD32-50000)
        self.assertEqual(frames[4]["capture_tick64"], MOD32+100)
        self.assertEqual(t.stats["joined_poses"], 1)
        self.assertEqual(t.stats["sequence_missing"], 0)

    def test_status_reboot_epoch_separates_matching_acceptance_ids(self):
        t = StreamTracker()
        tracked(t, packet(4, seq=100, tick=50000000, payload=status(1000)),
                packet(1, seq=101, tick=50001000))
        out = tracked(t, packet(4, seq=102, tick=100000, payload=status(2)),
                      packet(2, seq=103, tick=150000))
        self.assertEqual(t.epoch, 1)
        self.assertFalse(any(r["kind"] == "pose_raw_join" for r in out))
        self.assertEqual(t.summary()["epochs"][1]["unmatched_poses_at_epoch_end"], 1)

    def test_raw_counter_reset_detects_reboot_before_status(self):
        t = StreamTracker()
        tracked(t, packet(seq=100, tick=100000, payload=raw(1000, 900)),
                packet(seq=101, tick=200000, payload=raw(1, 1)))
        self.assertEqual(t.epoch, 1)
        self.assertEqual(t.current["start_reason"], "raw_source_and_acceptance_counter_reset")

    def test_sequence_and_tick_restart_detects_reboot(self):
        t = StreamTracker()
        out = tracked(t, packet(2, seq=100, tick=50000000), packet(2, seq=0, tick=5000))
        self.assertEqual(out[-1]["epoch"], 1)
        self.assertEqual(t.stats["sequence_missing"], 0)

    def test_source_and_acceptance_wrap_are_not_reboots(self):
        t = StreamTracker()
        tracked(t, packet(seq=65535, payload=raw(0xFFFFFFFF, 0xFFFFFFFF)),
                packet(seq=0, tick=200000, payload=raw(0, 0)))
        self.assertEqual(t.epoch, 0)

    def test_exact_acceptance_join_not_source_id(self):
        t = StreamTracker()
        out = tracked(t, packet(1, payload=raw(source=10, accepted=3)),
                      packet(2, seq=1, tick=150000, payload=pose(accepted=10)),
                      packet(2, seq=2, tick=160000, payload=pose(accepted=3)))
        joins = [r for r in out if r["kind"] == "pose_raw_join"]
        self.assertEqual(len(joins), 1)
        self.assertEqual(joins[0]["accepted_id"], 3)
        self.assertEqual(joins[0]["raw_source_id"], 10)
        self.assertEqual(joins[0]["held_dt_ticks"], 50001)
        self.assertFalse(joins[0]["interpolation"])
        self.assertEqual(t.summary()["epochs"][0]["unmatched_poses_at_epoch_end"], 1)

    def test_pose_before_raw_joins_when_exact_raw_arrives(self):
        t = StreamTracker()
        out = tracked(t, packet(2, seq=0, tick=200000), packet(1, seq=1, tick=100000))
        self.assertEqual(len([r for r in out if r["kind"] == "pose_raw_join"]), 1)

    def test_invalid_or_unaccepted_raw_does_not_join(self):
        for flags in (8, 7):
            with self.subTest(flags=flags):
                t = StreamTracker()
                out = tracked(t, packet(1, payload=raw(flags=flags)), packet(2, seq=1))
                self.assertFalse(any(r["kind"] == "pose_raw_join" for r in out))

    def test_bounded_missing_data_is_not_filled(self):
        t = StreamTracker(join_limit=1)
        out = tracked(t, packet(2, payload=pose(1)), packet(2, seq=1, payload=pose(2)),
                      packet(1, seq=2, payload=raw(accepted=1)))
        self.assertFalse(any(r["kind"] == "pose_raw_join" for r in out))
        self.assertEqual(t.stats["evicted_unmatched_poses"], 1)

    def test_producer_overflow_separate_from_transport_gap(self):
        t = StreamTracker()
        tracked(t, packet(4, payload=status(1000, (1, 2, 3, 4))),
                packet(4, seq=1, payload=status(2000, (5, 7, 9, 0xFFFFFFFF))))
        e = t.summary()["epochs"][0]
        self.assertEqual(e["producer_drop_observed_delta"]["dropped_raw"], 4)
        self.assertEqual(e["producer_drop_cumulative"]["dropped_status"], 0xFFFFFFFF)
        self.assertEqual(t.stats["sequence_missing"], 0)
        self.assertEqual(e["latest_status"]["saturated_drop_counters"], ["dropped_status"])

    def test_first_fault_label_is_frozen_in_summary(self):
        t = StreamTracker()
        tracked(t, packet(3, payload=fault(2)), packet(3, seq=1, payload=fault(8)))
        self.assertEqual(t.summary()["epochs"][0]["first_fault"]["first_cause"], 2)
        self.assertEqual([r["first_cause"] for r in t.summary()["epochs"][0]["fault_captures"]], [2, 8])


class UARTInteroperabilityTests(unittest.TestCase):
    @unittest.skipUnless((BASE.parents[1] / "out" / "B0B1" / "uart_interop.hex").is_file(),
                         "Generate UART serial RTL fixture before running interoperability proof")
    def test_actual_verilog_uart_wire_bytes(self):
        out = BASE.parents[1] / "out" / "B0B1"
        data = bytes(int(token, 16) for token in (out / "uart_interop.hex").read_text().split())
        parser = FrameParser()
        frames = []
        for at in range(0, len(data), 7):
            frames.extend(parser.feed(data[at:at+7]))
        self.assertEqual(len(data), 612)
        self.assertEqual(len(frames), 10)
        self.assertEqual([f["sequence"] for f in frames], list(range(10)))
        self.assertEqual(parser.finish()["crc_errors"], 0)
        self.assertEqual(parser.stats["payload_errors"], 0)
        self.assertEqual(parser.stats["unknown_types"], 0)
        self.assertEqual(parser.stats["discarded_bytes"], 0)
        expected = [(1, 0x10), (2, 0x80), (3, 0), (1, 0x50),
                    (2, 0xA0), (3, 0x90), (3, 0x40)]
        lengths = {1:26, 2:28, 3:88}
        for f, (typ, base) in zip(frames[:7], expected):
            payload = bytearray((base+j) & 255 for j in range(lengths[typ]))
            if typ == 2:
                payload[26] &= 0x3F
            elif typ == 3:
                payload[0] &= 7
                payload[1] %= 10
                payload[48] &= 3
            self.assertEqual(f["type_code"], typ)
            self.assertEqual(data[f["byte_start"]+10:f["byte_end"]-2], bytes(payload))
        status_ticks = [int(token, 16) for token in (out / "uart_status_ticks.hex").read_text().split()]
        self.assertEqual([f["capture_tick"] for f in frames[7:]], status_ticks)
        self.assertEqual(frames[0]["capture_tick"], 0xFFFFFFF0)
        self.assertEqual(frames[3]["capture_tick"], 0x10)
        for f in frames[7:]:
            self.assertEqual(f["payload"]["build_id"], 0xB0B1)
            self.assertEqual(f["payload"]["uptime_ms"], 0x0123456789ABCDEF)
            self.assertEqual(f["payload"]["dropped_raw"], 3)
            self.assertEqual(f["payload"]["dropped_pose"], 3)


class CaptureTests(unittest.TestCase):
    def test_offline_cli_copies_raw_and_never_opens_serial(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp)
            original = packet(1) + packet(2, seq=1) + packet(4, seq=2)
            (p / "input.bin").write_bytes(original)
            with mock.patch.object(capture, "open_read_only_serial", side_effect=AssertionError("serial access")):
                self.assertEqual(capture.main(["--input", str(p / "input.bin"), "--output", str(p / "decoded")]), 0)
            self.assertEqual((p / "decoded" / "raw.bin").read_bytes(), original)
            s = json.loads((p / "decoded" / "summary.json").read_text())
            self.assertFalse(s["serial_writes"])
            self.assertEqual(s["parser"]["valid_frames"], 3)
            self.assertEqual(s["stream"]["stats"]["joined_poses"], 1)
            with self.assertRaises(SystemExit):
                capture.main(["--input", str(p / "input.bin"), "--output", str(p / "decoded")])

    def test_cli_requires_explicit_source(self):
        with self.assertRaises(SystemExit):
            capture.main(["--output", "never_created_without_source"])

    def test_read_error_is_preserved_in_summary(self):
        class FailedInput:
            closed = False
            def read(self, size):
                raise OSError("injected read failure")
            def close(self):
                self.closed = True
        device = FailedInput()
        with tempfile.TemporaryDirectory() as temp:
            output = pathlib.Path(temp) / "failed_capture"
            with mock.patch.object(capture, "open_read_only_serial", return_value=device):
                code = capture.main(["--port", "FAKE_ONLY", "--output", str(output)])
            s = json.loads((output / "summary.json").read_text())
            self.assertEqual(code, 2)
            self.assertEqual(s["read_errors"], 1)
            self.assertEqual(s["capture_errors"], 0)
            self.assertEqual(s["error_phase"], "read")
            self.assertTrue(device.closed)

    def test_fake_serial_successful_read_never_calls_write(self):
        class FakeInput:
            calls = 0
            def read(self, size):
                self.calls += 1
                if self.calls == 1:
                    return packet(1)
                raise KeyboardInterrupt()
            def close(self):
                pass
            def write(self, data):
                raise AssertionError("must never transmit")
        with tempfile.TemporaryDirectory() as temp:
            output = pathlib.Path(temp) / "fake_capture"
            with mock.patch.object(capture, "open_read_only_serial", return_value=FakeInput()):
                code = capture.main(["--port", "FAKE_ONLY", "--output", str(output)])
            s = json.loads((output / "summary.json").read_text())
            self.assertEqual(code, 0)
            self.assertTrue(s["interrupted"])
            self.assertEqual(s["read_errors"], 0)
            self.assertEqual(s["parser"]["valid_frames"], 1)

    def test_modem_lines_inactive_before_fake_open_and_no_transmit(self):
        events = []
        class FakeSerial:
            def __init__(self, **kwargs):
                self.port = kwargs["port"]
                events.append(("construct", kwargs))
            def __setattr__(self, name, value):
                events.append((name, value))
                object.__setattr__(self, name, value)
            def open(self):
                events.append(("open", self.dtr, self.rts, self.port))
        fake_module = type("FakeModule", (), {"Serial": FakeSerial})
        with mock.patch.dict(sys.modules, {"serial": fake_module}):
            capture.open_read_only_serial("FAKE_ONLY", 921600)
        self.assertEqual(events[-1], ("open", False, False, "FAKE_ONLY"))
        self.assertFalse(any(e[0] == "write" for e in events))


class SiKPreparationTests(unittest.TestCase):
    def test_isolated_copy_hash_receipt_b0b1_fallback_control_and_legacy_tests(self):
        location = BASE / "tools" / "prepare_sik_receiver.py"
        spec = importlib.util.spec_from_file_location("b0b1_prepare_sik", location)
        prep = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prep)
        parent = prep.REPOSITORY / "out" / "B0B1"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent, prefix="sik_prepare_test_") as temp:
            output = pathlib.Path(temp) / "receiver"
            receipt = prep.prepare(output)
            self.assertEqual(receipt["source_files_sha256"], prep.file_hashes(prep.REPOSITORY / "ground" / "B0B0"))
            actual = prep.file_hashes(output)
            actual.pop(prep.RECEIPT)
            self.assertEqual(receipt["output_files_sha256"], actual)
            with self.assertRaises(FileExistsError):
                prep.prepare(output)
            with self.assertRaises(ValueError):
                prep.prepare(prep.REPOSITORY / "ground" / "never_create_here")
            check = r'''
from protocol import Dashboard,receiver,decode_info
from nav_protocol import identity_matches,mtf_identity_matches,firmware_label
from analysis import point
from test_height_loss import info
from test_system import primary
from test_ano_control import nav
import binascii,struct
from rotation_protocol import FORMAT
for build in (0xb0b0,0xb0b1):
 assert decode_info(info(build=build))['height_loss_fallback_active']
 d=Dashboard('TEST');d.connection(True)
 for row in receiver().feed(primary(1,flags=127)+info(build=build)):d.ingest(row)
 s=d.snapshot()
 assert s['control_input'] and s['experimental_control'] and s['height_loss_fallback_active']
 assert not s['serial_writes'] and not s['flight_ready']
 assert '手动油门' in s['data']['mode_active']
 for row in receiver().feed(info(build=build,flags=7)+nav(0x3f,roll=-123,collective=1400,target=600)):d.ingest(row)
 body=struct.pack(FORMAT,1,15,1,1000,200,10,1000,0,0,0,0,0,0,0)
 framed=b'\xa5\x83\0\x01'+body
 framed+=binascii.crc_hqx(framed[2:],0xffff).to_bytes(2,'big')
 for row in receiver().feed(framed):d.ingest(row)
 s=d.snapshot()
 assert s['navigation_fresh'] and s['navigation']['xyz_active'] and s['rotation_pair']
 assert s['data']['mode_active']=='光流速度控制 + 高度'
 r=receiver().feed(primary(1,flags=127))[0]
 assert point(dict(row=r,elapsed_s=0,epoch=0,_firmware_build_id=build))['control_input']
 assert identity_matches({'build_id':build},{'version':5})
 assert mtf_identity_matches({'build_id':build},{'version':2})
assert firmware_label(0xb0b1).startswith('B0B1')
'''
            result = subprocess.run([sys.executable, "-B", "-c", check], cwd=output,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([sys.executable, "-B", "-m", "unittest",
                "test_height_loss", "test_ano_control", "-v"], cwd=output,
                text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
