"""Actual Host/Recorder/decoder with an in-memory serial link, never hardware.

Safety evidence uses valid A586-v3 and A588-v5 frames made from the existing
seed, rather than a mocked Dashboard snapshot. The bank replies are a transport
emulator, not a new RTL/flight proof. The 0.25s transaction timeout only keeps
negative offline tests short. All logs live in temporary directories.
"""
import binascii
from contextlib import ExitStack
import json
from pathlib import Path
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import ground_server as server
import protocol
from xy_pi_control import XYPIController, XYPIError, encode_request


HERE = Path(__file__).resolve().parent
DECODER = protocol.base.viewer.load_decoder(protocol.ROOT / 'support/monitor_control.py')
SEED = json.loads((HERE / 'fixtures/seed_primary.jsonl').read_text(encoding='utf8').splitlines()[0])['row']


def primary(sequence=1, armed=False, embedded=None):
    row = dict(SEED)
    row.update(sequence=sequence, flags=14 | (16 if armed else 0), accepted_count=10000 + sequence,
               pose_age_ticks=0, gate_last_interruption_pose_age_ticks=0,
               gate_last_revoke_pose_age_ticks=0)
    row['mode_requested'] = row['mode_requested_code']
    row['mode_active'] = row['mode_active_code']
    body = bytearray(struct.pack(DECODER.BASE_FMT, *[row[k] for k in DECODER.BASE_FIELDS])
                     + struct.pack(DECODER.EXT_FMT, *[row[k] for k in DECODER.EXT_FIELDS]))
    if embedded is not None:
        # Gyro/mixer diagnostic slots; no header, age-reserved slot or identity
        # byte is changed. This is only a central-framing adversarial fixture.
        body[40:40 + len(embedded)] = embedded
    check = 0
    for byte in body:
        check ^= byte
    return b'\xa5\x86' + body + bytes([check])


def info(sequence=1, uptime=1000):
    body = struct.pack('>HBBIQHQBBBBIBB', sequence, 5, 0, 0xb0b2, uptime,
                       0, 0, 0, 0, 0, 0, 0, 0, 0)
    return b'\xa5\x88' + body + binascii.crc_hqx(body, 0xffff).to_bytes(2, 'big')


def reply(opcode, sequence, p=1000, i=350, generation=0, status=0):
    body = struct.pack('>BBBBIHHII', 1, opcode, 24, status, sequence, p, i, generation, 0xb0b4)
    return b'\xa5\x91' + body + binascii.crc_hqx(body, 0xffff).to_bytes(2, 'big')


def wait_for(predicate, message, timeout=3):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(.002)
    raise AssertionError(message)


class FakeSerial:
    def __init__(self, factory, settings):
        self.factory = factory
        self.settings = settings
        self.port = None
        self.dtr = self.rts = True
        self.opened = self.closed = False
        self.buffer = bytearray()
        self.feed_history = []
        self.lock = threading.Lock()
        self.allow_read = threading.Event(); self.allow_read.set()
        self.read_blocked = threading.Event()
        self.read_failure = False
        self.read_count = 0
        self.calls = []

    def open(self):
        assert self.dtr is False and self.rts is False
        self.opened = True
        self.calls.append(('open', threading.get_ident()))

    @property
    def in_waiting(self):
        with self.lock:
            return len(self.buffer)

    def feed(self, data):
        with self.lock:
            self.buffer.extend(data)
            self.feed_history.append(bytes(data))

    def read(self, count):
        self.calls.append(('read', threading.get_ident()))
        self.read_count += 1
        if not self.allow_read.is_set():
            self.read_blocked.set()
            self.allow_read.wait(2)
        if self.read_failure:
            self.read_failure = False
            raise OSError('mock cable disconnected')
        with self.lock:
            data = bytes(self.buffer[:min(count, 7)])
            del self.buffer[:len(data)]
        if not data:
            time.sleep(.003)
        return data

    def write(self, packet):
        self.calls.append(('write', threading.get_ident()))
        return self.factory.write(self, bytes(packet))

    def close(self):
        self.calls.append(('close', threading.get_ident()))
        self.closed = True


class FakeFactory:
    def __init__(self):
        self.ports = []
        self.writes = []
        self.p, self.i, self.generation = 1000, 350, 0
        self.silent_get = self.silent_set = False
        self.set_failure = None

    def __call__(self, **settings):
        port = FakeSerial(self, settings)
        self.ports.append(port)
        return port

    def write(self, port, packet):
        assert len(packet) == 16 and packet[:2] == b'\xa5\x90'
        assert int.from_bytes(packet[-2:], 'big') == binascii.crc_hqx(packet[2:-2], 0xffff)
        version, opcode, length, reserved, sequence, p, i = struct.unpack('>BBBBIHH', packet[2:-2])
        assert (version, length, reserved) == (1, 16, 0)
        self.writes.append(dict(packet=packet, opcode=opcode, sequence=sequence,
                                p=p, i=i, thread=threading.get_ident()))
        if opcode == 2:
            if self.set_failure == 'partial':
                return 7
            self.p, self.i = p, i
            self.generation = (self.generation + 1) & 0xffffffff
            if self.set_failure == 'timeout':
                # A real write timeout cannot establish how many bytes reached
                # the peer. This emulator commits first to exercise that risk.
                raise server.serial.SerialTimeoutException('mock write timeout')
            if self.silent_set:
                return 16
        if not (opcode == 1 and self.silent_get):
            port.feed(reply(opcode, sequence, self.p, self.i, self.generation))
        return 16


class Harness:
    def __init__(self, source='SiK', no_serial=False, enabled=True):
        self.stack = ExitStack()
        self.factory = FakeFactory()
        self.source = source
        self.no_serial = no_serial
        self.enabled = enabled

    def __enter__(self):
        directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix='b0b4-pi-transport-'))
        # Any accidentally bypassed device enumeration or real serial call must
        # fail immediately. The owner uses only the explicit mock factory.
        self.stack.enter_context(patch.object(server.serial.tools.list_ports, 'comports', side_effect=AssertionError('device enumeration forbidden')))
        self.stack.enter_context(patch.object(server, 'ports', side_effect=AssertionError('offline enumeration forbidden') if self.no_serial else None,
                                             return_value=[]))
        self.stack.enter_context(patch.object(server.serial, 'Serial', side_effect=AssertionError('real serial forbidden') if self.no_serial else self.factory))
        self.stack.enter_context(patch.object(server, 'XYPIController', side_effect=lambda enabled=False: XYPIController(enabled=enabled, sequence_start=100, timeout=.25)))
        self.host = server.Host(directory, dict(port='MOCK-ONLY', baud=115200, source=self.source),
                                no_serial=self.no_serial, enable_xy_pi=self.enabled)
        if not self.no_serial:
            wait_for(lambda: self.host.transport_connected, 'mock owner did not connect')
        return self

    def __exit__(self, *exc):
        try:
            for port in self.factory.ports:
                port.allow_read.set()
            self.host.close()
        finally:
            self.stack.close()

    @property
    def port(self):
        return self.factory.ports[-1]

    @property
    def epoch(self):
        return self.host.transport_epoch

    def pair(self, sequence=1, uptime=1000):
        self.port.feed(primary(sequence) + info(sequence, uptime))
        wait_for(lambda: self.host.primary_epoch == self.epoch and self.host.info_epoch == self.epoch
                 and self.host.parameter_stopped_guard()[0], 'real v3 frames did not establish stopped context')

    def query(self, request_id='get'):
        operation = self.host.pi.request_get(request_id, self.epoch)
        wait_for(lambda: not self.host.pi.snapshot()['busy'], 'GET did not complete')
        state = self.host.pi.snapshot()
        assert state['result']['code'] == 'queried', state
        return operation


class TransportTests(unittest.TestCase):
    def test_actual_owner_full_transaction_exact_packets_and_token_free_tx_log(self):
        with Harness() as h:
            h.pair()
            self.assertEqual(h.host.dashboard.snapshot()['flight_info']['build_id'], 0xb0b2)
            h.query()
            operation = h.host.pi.request_set('0.15', '0.10', 'set', 0, h.epoch)
            wait_for(lambda: not h.host.pi.snapshot()['busy'], 'SET/readback did not complete')
            state = h.host.pi.snapshot()
            self.assertEqual((state['result']['code'], state['operation_id']), ('verified', operation))
            self.assertEqual([w['packet'] for w in h.factory.writes], [
                encode_request(1, 100), encode_request(2, 101, 1500, 1000), encode_request(1, 102)])
            self.assertEqual({w['thread'] for w in h.factory.writes}, {h.host.worker.ident})
            self.assertEqual(h.port.settings['write_timeout'], .5)
            self.assertTrue(all(thread == h.host.worker.ident for _, thread in h.port.calls))
            h.host.recorder.capture_snapshot()
            events_text = (h.host.recorder.path / 'events.jsonl').read_text(encoding='utf8')
            events = [json.loads(line) for line in events_text.splitlines()]
            tx = [r['detail'] for r in events if r['kind'] == 'xy_pi_tx']
            attempts = [r['detail'] for r in events if r['kind'] == 'xy_pi_tx_attempt']
            self.assertEqual([bytes.fromhex(r['packet_hex']) for r in tx], [w['packet'] for w in h.factory.writes])
            self.assertEqual([bytes.fromhex(r['packet_hex']) for r in attempts], [w['packet'] for w in h.factory.writes])
            self.assertTrue(all('token' not in r and r['bytes_written'] == 16 for r in tx))
            self.assertTrue(all('token' not in r for r in attempts))
            self.assertNotIn(h.host.pi_token, events_text)
            meta = json.loads((h.host.recorder.path / 'meta.json').read_text(encoding='utf8'))
            self.assertEqual((meta['serial_writes_enabled'], meta['serial_writes'], meta['read_only']), (True, True, False))
            self.assertEqual((meta['serial_write_scope'], meta['serial_write_attempts'], meta['serial_complete_frames']), ('xy_pi_only', 3, 3))
            self.assertEqual((h.host.recorder.path / 'raw.bin').read_bytes(), b''.join(h.port.feed_history))
            decoded = [json.loads(line)['row'] for line in (h.host.recorder.path / 'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertEqual([r['_protocol'] for r in decoded], ['a579', 'a580', 'a591', 'a591', 'a591'])
            self.assertEqual(h.host.dashboard.frames, 1)

    def test_parameter_only_is_not_primary_and_embedded_header_cannot_ack(self):
        with Harness() as h:
            h.query()
            state = h.host.dashboard.snapshot()
            self.assertFalse(state['fresh'])
            self.assertIsNone(state['data'])
            self.assertEqual(h.host.dashboard.frames, 0)
            h.factory.silent_get = True
            h.host.pi.request_get('second-get', h.epoch)
            wait_for(lambda: len(h.factory.writes) == 2, 'second GET not written')
            sequence = h.factory.writes[-1]['sequence']
            h.port.feed(primary(2, embedded=reply(1, sequence, p=9999)) + info(2))
            wait_for(lambda: h.host.dashboard.frames == 1, 'outer primary not decoded')
            self.assertTrue(h.host.pi.snapshot()['busy'])
            self.assertEqual(h.host.pi.snapshot()['active']['p_wire'], 1000)
            h.port.feed(reply(1, sequence))
            wait_for(lambda: not h.host.pi.snapshot()['busy'], 'standalone response not decoded')
            self.assertEqual(h.host.pi.snapshot()['active']['p_wire'], 1000)
            self.assertEqual(h.host.dashboard.frames, 1)
            h.host.recorder.capture_snapshot()
            rows = [json.loads(line)['row'] for line in (h.host.recorder.path / 'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertEqual(sum(r['_protocol'] == 'a591' for r in rows), 2)

    def test_central_decoder_fragment_corruption_and_mixed_real_v3(self):
        rx = protocol.receiver()
        self.assertTrue({bytes.fromhex(x) for x in ('a585', 'a586', 'a587', 'a588', 'a589', 'a591')} <= set(rx.protocols))
        corrupted = bytearray(reply(1, 99)); corrupted[-1] ^= 1
        wire = b'noise' + corrupted + primary(3, embedded=reply(1, 98)) + reply(1, 100) + info(3)
        rows = []
        for start in range(0, len(wire), 7):
            rows.extend(rx.feed(wire[start:start + 7]))
        self.assertEqual([(r['_protocol'], r['sequence']) for r in rows], [('a579', 3), ('a591', 100), ('a580', 3)])
        self.assertEqual(rows[0]['_age_policy'], 'no_pose_age_v3')
        self.assertIsNone(rows[0]['pose_age_ticks'])
        self.assertEqual(rows[2]['build_id'], 0xb0b2)
        self.assertGreater(rx.checksum_errors, 0)

    def test_partial_and_serial_timeout_never_retry_set(self):
        for failure in ('partial', 'timeout'):
            with self.subTest(failure=failure), Harness() as h:
                h.pair(); h.query()
                h.factory.set_failure = failure
                h.host.pi.request_set('0.15', '0.10', 'set', 0, h.epoch)
                wait_for(lambda: not h.host.transport_connected, 'write failure did not disconnect')
                self.assertEqual(h.host.pi.snapshot()['result']['code'], 'unknown')
                self.assertFalse(h.host.pi.snapshot()['supported'])
                time.sleep(.03)
                self.assertEqual([w['opcode'] for w in h.factory.writes], [1, 2])
                h.host.recorder.capture_snapshot()
                event_text = (h.host.recorder.path / 'events.jsonl').read_text(encoding='utf8')
                events = [json.loads(line) for line in event_text.splitlines()]
                attempts = [r['detail'] for r in events if r['kind'] == 'xy_pi_tx_attempt']
                errors = [r['detail'] for r in events if r['kind'] == 'xy_pi_tx_error']
                self.assertEqual([bytes.fromhex(r['packet_hex']) for r in attempts], [w['packet'] for w in h.factory.writes])
                self.assertEqual(len(errors), 1)
                self.assertEqual(bytes.fromhex(errors[0]['packet_hex']), h.factory.writes[-1]['packet'])
                self.assertTrue(all('token' not in r for r in attempts + errors))
                self.assertNotIn(h.host.pi_token, event_text)
                meta = json.loads((h.host.recorder.path / 'meta.json').read_text(encoding='utf8'))
                self.assertEqual((meta['serial_writes'], meta['serial_write_attempts'], meta['serial_complete_frames']), (True, 2, 1))

    def test_lost_ack_and_lost_readback_are_unknown_without_set_retry(self):
        for lose_ack in (True, False):
            with self.subTest(lose_ack=lose_ack), Harness() as h:
                h.pair(); h.query()
                h.factory.silent_set = lose_ack
                h.factory.silent_get = not lose_ack
                h.host.pi.request_set('0.15', '0.10', 'set', 0, h.epoch)
                wait_for(lambda: not h.host.pi.snapshot()['busy'], 'silent peer did not time out')
                self.assertEqual(h.host.pi.snapshot()['result']['code'], 'unknown')
                self.assertEqual(sum(w['opcode'] == 2 for w in h.factory.writes), 1)
                self.assertEqual([w['opcode'] for w in h.factory.writes], [1, 2] if lose_ack else [1, 2, 1])
                h.factory.silent_get = h.factory.silent_set = False
                h.query('recover')
                self.assertEqual((h.host.pi.snapshot()['active']['p_wire'], h.host.pi.snapshot()['active']['generation']), (1500, 1))

    def test_reconnect_rejects_old_epoch_queued_reply(self):
        with Harness() as h:
            h.query()
            old_epoch = h.epoch
            h.port.read_failure = True
            wait_for(lambda: not h.host.transport_connected, 'mock disconnect not observed')
            wait_for(lambda: len(h.factory.ports) == 2 and h.host.transport_connected, 'mock reconnect not observed')
            self.assertGreater(h.epoch, old_epoch)
            self.assertFalse(h.host.pi.snapshot()['supported'])
            h.factory.silent_get = True
            h.host.pi.request_get('new-connection', h.epoch)
            wait_for(lambda: len(h.factory.writes) == 2, 'new epoch GET not written')
            response = reply(1, h.factory.writes[-1]['sequence'])
            self.assertTrue(h.host.recorder.put('chunk_epoch', (old_epoch, response)))
            h.host.recorder.capture_snapshot()
            self.assertTrue(h.host.pi.snapshot()['busy'])
            self.assertFalse(h.host.pi.snapshot()['supported'])
            h.port.feed(response)
            wait_for(lambda: not h.host.pi.snapshot()['busy'], 'current epoch response not accepted')
            self.assertTrue(h.host.pi.snapshot()['supported'])
            self.assertFalse(h.host.parameter_stopped_guard()[0])

    def test_fpga_uptime_regression_invalidates_then_new_epoch_works(self):
        with Harness() as h:
            h.pair(); h.query()
            old_epoch = h.epoch
            h.factory.silent_set = True
            h.host.pi.request_set('0.15', '0.10', 'set', 0, old_epoch)
            wait_for(lambda: len(h.factory.writes) == 2, 'SET not attempted')
            h.port.feed(primary(2) + info(2, uptime=1))
            wait_for(lambda: h.epoch != old_epoch, 'FPGA uptime rollback did not change transport epoch')
            self.assertEqual(h.host.pi.snapshot()['result']['code'], 'unknown')
            self.assertFalse(h.host.pi.snapshot()['supported'])
            self.assertFalse(h.host.parameter_stopped_guard()[0])
            before = h.port.read_count
            wait_for(lambda: h.port.read_count > before, 'owner did not refresh epoch after reboot')
            h.pair(sequence=3, uptime=2)
            h.query('after-reboot')
            self.assertEqual(h.host.pi.snapshot()['active']['p_wire'], 1500)
            self.assertEqual(sum(w['opcode'] == 2 for w in h.factory.writes), 1)

    def test_stop_revoked_after_queue_before_owner_write(self):
        with Harness() as h:
            h.pair(); h.query()
            h.port.allow_read.clear(); h.port.read_blocked.clear()
            wait_for(h.port.read_blocked.is_set, 'owner did not reach controlled read barrier')
            self.assertTrue(h.host.parameter_stopped_guard()[0])
            h.host.pi.request_set('0.15', '0.10', 'set', 0, h.epoch)
            # Inject an already-received chunk at the real recorder boundary
            # while the owner is paused: deterministic queue-to-send revocation.
            h.host.recorder.put('chunk_epoch', (h.epoch, primary(2, armed=True) + info(2)))
            h.host.recorder.capture_snapshot()
            self.assertFalse(h.host.parameter_stopped_guard()[0])
            h.port.allow_read.set()
            wait_for(lambda: not h.host.pi.snapshot()['busy'], 'owner did not cancel revoked SET')
            self.assertEqual(h.host.pi.snapshot()['result']['code'], 'cancelled')
            self.assertEqual([w['opcode'] for w in h.factory.writes], [1])

    def test_usb_and_offline_never_send_or_enumerate_real_devices(self):
        def readonly_metadata(h):
            h.host.recorder.capture_snapshot()
            meta = json.loads((h.host.recorder.path / 'meta.json').read_text(encoding='utf8'))
            self.assertEqual((meta['read_only'], meta['serial_writes'], meta['serial_writes_enabled']), (True, False, False))
            self.assertEqual((meta['serial_write_scope'], meta['serial_write_attempts'], meta['serial_complete_frames']), ('none', 0, 0))

        with Harness(enabled=False) as h:
            h.pair()
            self.assertTrue(h.host.dashboard.snapshot()['fresh'])
            self.assertFalse(h.host.pi.snapshot()['enabled'])
            with self.assertRaises(XYPIError) as caught:
                h.host.pi.request_get('disabled', h.epoch)
            self.assertEqual(caught.exception.code, 'unsupported')
            self.assertEqual(h.factory.writes, [])
            readonly_metadata(h)
        with Harness(source='USB') as h:
            with self.assertRaises(XYPIError) as caught:
                h.host.pi.request_get('usb', h.epoch)
            self.assertEqual(caught.exception.code, 'unsupported')
            self.assertEqual(h.factory.writes, [])
            readonly_metadata(h)
        with Harness(no_serial=True) as h:
            self.assertFalse(h.host.worker.is_alive())
            self.assertEqual(h.factory.ports, [])
            with self.assertRaises(XYPIError) as caught:
                h.host.pi.request_get('offline', h.epoch)
            self.assertEqual(caught.exception.code, 'notconnected')
            with self.assertRaises(ValueError):
                h.host.switch(dict(port='FORBIDDEN', baud=115200, source='SiK'))
            readonly_metadata(h)


if __name__ == '__main__':
    unittest.main()
