"""Pure protocol/controller tests; no serial devices, HTTP or live services."""
import argparse
import binascii
import concurrent.futures
import struct
import unittest

from xy_pi_control import XYPIController, XYPIError, decode_parameter_response, encode_request, gain


def packet(op=1, seq=10, p=500, i=0, generation=0, status=0, build=0xb0b3,
           version=1, length=24):
    body = struct.pack('>BBBBIHHII', version, op, length, status, seq, p, i, generation, build)
    return b'\xa5\x91' + body + binascii.crc_hqx(body, 0xffff).to_bytes(2, 'big')


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class CodecTests(unittest.TestCase):
    def test_exact_decimal_grid_and_request(self):
        for text, expected in [('0', 0), ('0.0001', 1), ('0.05', 500), ('0.10', 1000), ('1', 10000)]:
            self.assertEqual(gain(text), expected)
        for text in ['0.00001', '-0.0001', '1.0001', 'NaN', 'Infinity', 'bad']:
            with self.assertRaises(argparse.ArgumentTypeError):
                gain(text)
        value = encode_request(2, 0x12345678, 500, 1000)
        self.assertEqual(value[:14], bytes.fromhex('a590010210001234567801f403e8'))
        self.assertEqual(int.from_bytes(value[-2:], 'big'), binascii.crc_hqx(value[2:-2], 0xffff))

    def test_response_strict_identity_crc_opcode_status(self):
        row = decode_parameter_response(packet())
        self.assertEqual((row['_protocol'], row['build'], row['p_wire']), ('a591', '0000B0B3', 500))
        variants = [packet(build=0xb0b2), packet(version=2), packet(length=23),
                    packet(op=3), packet(status=7), packet(p=10001), packet(i=10001),
                    packet()[:-1], b'\xa5\x79' + packet()[2:]]
        bad_crc = bytearray(packet()); bad_crc[8] ^= 1; variants.append(bytes(bad_crc))
        for value in variants:
            with self.subTest(value=value.hex()), self.assertRaises(ValueError):
                decode_parameter_response(value)
        for status in range(7):
            self.assertEqual(decode_parameter_response(packet(status=status))['status'], status)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.c = XYPIController(enabled=True, clock=self.clock, sequence_start=10, timeout=3)
        self.c.connection(1, True)

    def error(self, code, function, *args):
        with self.assertRaises(XYPIError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code, code)

    def send(self):
        command = self.c.take_write(1)
        self.assertIsNotNone(command)
        self.assertEqual(len(command['packet']), 16)
        self.assertIsNone(self.c.take_write(1))
        self.c.write_result(command['token'], 16)
        return command

    def respond(self, command, **kwargs):
        self.c.response(decode_parameter_response(packet(op=command['opcode'], seq=command['sequence'], **kwargs)), 1)

    def query(self, request_id='get'):
        operation = self.c.request_get(request_id, 1)
        command = self.send()
        self.respond(command)
        self.assertEqual(self.c.snapshot()['result']['code'], 'queried')
        return operation

    def start_set(self):
        self.query()
        operation = self.c.request_set('0.15', '0.10', 'set', 0, 1)
        command = self.send()
        return operation, command

    def test_query_and_snapshot_isolation(self):
        operation = self.query()
        state = self.c.snapshot()
        self.assertEqual(state['operation_id'], operation)
        self.assertTrue(state['supported'])
        self.assertEqual((state['active']['p_text'], state['active']['i_text']), ('0.0500', '0.0000'))
        self.clock.now += .125
        self.assertEqual(self.c.snapshot()['active']['age_ms'], 125)
        state['active']['p_wire'] = 9999
        state['result']['code'] = 'fake'
        self.assertEqual(self.c.snapshot()['active']['p_wire'], 500)
        self.assertNotIn('token', str(self.c.snapshot()))

    def test_set_ack_requires_independent_get(self):
        operation, command = self.start_set()
        self.assertEqual(self.c.snapshot()['phase'], 'await_set_ack')
        self.assertIsNone(self.c.snapshot()['active'])
        self.respond(command, p=1500, i=1000, generation=1)
        state = self.c.snapshot()
        self.assertTrue(state['busy'])
        self.assertEqual(state['phase'], 'queued_verify_get')
        self.assertIsNone(state['result'])
        self.error('busy', self.c.request_get, 'interleaved', 1)
        verification = self.send()
        self.assertEqual((verification['opcode'], verification['sequence']), (1, command['sequence'] + 1))
        self.assertEqual(verification['packet'][10:14], b'\0' * 4)
        self.respond(verification, p=1500, i=1000, generation=1)
        state = self.c.snapshot()
        self.assertEqual((state['result']['code'], state['operation_id']), ('verified', operation))
        self.assertEqual((state['active']['p_wire'], state['active']['i_wire'], state['active']['generation']), (1500, 1000, 1))
        self.assertEqual(self.c.request_set('0.15', '0.10', 'set', 0, 1), operation)
        self.assertIsNone(self.c.take_write(1))

    def test_idempotency_during_and_after_complete_conflict(self):
        operation = self.c.request_get('same', 1)
        self.assertEqual(self.c.request_get('same', 1), operation)
        self.error('invalid', self.c.request_set, '0.05', '0', 'same', 0, 1)
        command = self.send(); self.respond(command)
        self.assertEqual(self.c.request_get('same', 1), operation)
        self.assertIsNone(self.c.take_write(1))
        set_op = self.c.request_set('0.05', '0', 'same-set', 0, 1)
        self.assertEqual(self.c.request_set('0.05', '0', 'same-set', 0, 1), set_op)
        self.error('invalid', self.c.request_set, '0.0500', '0', 'same-set', 0, 1)

    def test_concurrent_duplicate_and_distinct_busy(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(lambda _: self.c.request_get('one', 1), range(16)))
        self.assertEqual(len(set(ids)), 1)
        self.error('busy', self.c.request_get, 'different', 1)
        self.assertEqual(self.send()['sequence'], 10)

    def test_cache_is_bounded_to_32(self):
        for index in range(33):
            self.c.request_get(str(index), 1)
            command = self.send(); self.respond(command)
        self.assertEqual(self.c.request_get('32', 1), 33)
        self.assertEqual(self.c.request_get('0', 1), 34)
        self.assertEqual(self.send()['sequence'], 43)

    def test_connection_feature_and_generation_guards(self):
        self.error('unsupported', self.c.request_set, '0.05', '0', 's', 0, 1)
        self.query()
        self.error('stale', self.c.request_set, '0.05', '0', 's', 1, 1)
        self.error('stale', self.c.request_get, 'old-epoch', 2)
        self.c.connection(2, False)
        self.error('notconnected', self.c.request_get, 'disconnected', 2)
        self.c.connection(3, True, source='USB')
        self.error('unsupported', self.c.request_get, 'usb', 3)
        self.c.connection(4, True, baud=57600)
        self.error('unsupported', self.c.request_get, 'baud', 4)
        disabled = XYPIController(); disabled.connection(1, True)
        self.error('unsupported', disabled.request_get, 'disabled', 1)

    def test_invalid_input_never_queues(self):
        self.query()
        for p, i, generation in [(0.05, '0', 0), ('0.00001', '0', 0), ('NaN', '0', 0),
                                  ('0.05', '0', True), ('0.05', '0', -1)]:
            self.error('invalid', self.c.request_set, p, i, 'bad', generation, 1)
        self.error('invalid', self.c.request_get, '', 1)
        self.assertIsNone(self.c.take_write(1))

    def test_unsolicited_wrong_epoch_opcode_and_sequence_ignored(self):
        self.c.response(decode_parameter_response(packet()), 1)
        self.assertFalse(self.c.snapshot()['supported'])
        self.c.request_get('get', 1)
        command = self.send()
        self.c.response(decode_parameter_response(packet(seq=command['sequence'])), 2)
        self.c.response(decode_parameter_response(packet(seq=99)), 1)
        self.c.response(decode_parameter_response(packet(op=2)), 1)
        self.c.response({'_protocol': 'a579'}, 1)
        self.assertEqual(self.c.snapshot()['phase'], 'await_get')
        self.respond(command)
        self.c.response(decode_parameter_response(packet(p=9999)), 1)
        self.assertEqual(self.c.snapshot()['active']['p_wire'], 500)

    def test_nacks_never_retry_set(self):
        for status, code in [(1, 'nack'), (2, 'nack'), (3, 'nack'), (4, 'locked'), (5, 'stale_sequence'), (6, 'nack')]:
            with self.subTest(status=status):
                self.setUp()
                _, command = self.start_set()
                self.respond(command, status=status)
                self.assertEqual(self.c.snapshot()['result']['code'], code)
                self.assertIsNone(self.c.take_write(1))

    def test_get_nack_does_not_establish_capability(self):
        self.c.request_get('get', 1)
        command = self.send(); self.respond(command, status=2)
        self.assertFalse(self.c.snapshot()['supported'])
        self.assertIsNone(self.c.snapshot()['active'])

    def test_short_write_error_and_stale_write_token(self):
        _, command = self.start_set()
        self.c.write_result(command['token'] + 99, 0)
        self.assertTrue(self.c.snapshot()['busy'])
        self.c.write_result(command['token'], 7)
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.assertFalse(self.c.snapshot()['supported'])
        self.assertIsNone(self.c.take_write(1))
        self.c.request_get('recover', 1)
        command = self.c.take_write(1)
        self.c.write_result(command['token'], 0, OSError('mock transport failure'))
        self.assertEqual(self.c.snapshot()['result']['code'], 'cancelled')

    def test_get_timeout_then_fresh_get_recovers(self):
        self.c.request_get('get', 1)
        command = self.send()
        self.clock.now += 3; self.c.tick()
        self.assertEqual(self.c.snapshot()['result']['code'], 'timeout')
        self.assertFalse(self.c.snapshot()['supported'])
        self.respond(command)
        self.assertIsNone(self.c.snapshot()['active'])
        self.query('recover')

    def test_set_ack_and_readback_timeout_are_unknown(self):
        for acknowledge in (False, True):
            with self.subTest(acknowledge=acknowledge):
                self.setUp(); _, command = self.start_set()
                if acknowledge:
                    self.respond(command, p=1500, i=1000, generation=1)
                    self.send()
                self.clock.now += 3; self.c.tick()
                self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
                self.assertFalse(self.c.snapshot()['supported'])
                self.error('unsupported', self.c.request_set, '0.15', '0.10', 'new', 1, 1)
                self.assertIsNone(self.c.take_write(1))

    def test_mismatch_and_readback_nack(self):
        for change in ({'p': 1400}, {'i': 900}, {'generation': 2}, {'status': 2}):
            with self.subTest(change=change):
                self.setUp(); _, command = self.start_set()
                self.respond(command, p=1500, i=1000, generation=1)
                readback = self.send()
                values = dict(p=1500, i=1000, generation=1); values.update(change)
                self.respond(readback, **values)
                self.assertEqual(self.c.snapshot()['result']['code'], 'unknown' if change.get('status') else 'mismatch')
                self.assertFalse(self.c.snapshot()['supported'])
        self.setUp(); _, command = self.start_set()
        self.respond(command, p=500)
        self.assertEqual(self.c.snapshot()['result']['code'], 'mismatch')
        self.assertIsNone(self.c.take_write(1))

    def test_epoch_disconnect_unsent_and_sent_set(self):
        self.query()
        self.c.request_set('0.15', '0.10', 'queued', 0, 1)
        self.c.connection(2, False)
        self.assertEqual(self.c.snapshot()['result']['code'], 'cancelled')
        self.assertIsNone(self.c.snapshot()['active'])
        self.assertIsNone(self.c.take_write(1))
        self.setUp(); _, command = self.start_set()
        self.c.connection(2, True)
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.respond(command, p=1500, i=1000, generation=1)
        self.assertFalse(self.c.snapshot()['supported'])
        self.assertEqual(self.c.request_set('0.15', '0.10', 'set', 0, 1), 2)
        self.assertIsNone(self.c.take_write(2))

    def test_invalidate_cancels_and_source_change_invalidates(self):
        self.query()
        self.c.connection(1, True)
        self.assertTrue(self.c.snapshot()['supported'])
        self.c.connection(1, True, source='USB')
        self.assertFalse(self.c.snapshot()['supported'])
        self.setUp(); _, command = self.start_set()
        self.c.invalidate('ingest overflow')
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.assertIsNone(self.c.take_write(1))
        self.c.write_result(command['token'], 16)

    def test_later_disconnect_cannot_downgrade_unknown_outcome(self):
        _, command = self.start_set()
        self.c.write_result(command['token'], 0, OSError('mock'))
        self.c.connection(2, False)
        self.c.invalidate('log failure')
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.assertIsNone(self.c.snapshot()['active'])

    def test_disconnect_while_verification_is_queued_stays_unknown(self):
        _, command = self.start_set()
        self.respond(command, p=1500, i=1000, generation=1)
        self.assertEqual(self.c.snapshot()['phase'], 'queued_verify_get')
        self.c.connection(2, False)
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.assertIsNone(self.c.take_write(2))

    def test_unsent_deadlines_are_bounded(self):
        self.query()
        self.c.request_set('0.15', '0.10', 'queued', 0, 1)
        self.clock.now += 3
        self.assertEqual(self.c.snapshot()['result']['code'], 'cancelled')
        self.assertIsNone(self.c.take_write(1))

    def test_sequence_exhaustion_without_wrap_or_set_retransmission(self):
        self.c = XYPIController(enabled=True, clock=self.clock, sequence_start=0xfffffffe)
        self.c.connection(1, True)
        self.query()
        self.c.request_set('0.15', '0.10', 'last', 0, 1)
        command = self.send()
        self.assertEqual(command['sequence'], 0xffffffff)
        self.respond(command, p=1500, i=1000, generation=1)
        self.assertEqual(self.c.snapshot()['result']['code'], 'unknown')
        self.assertIsNone(self.c.take_write(1))
        self.error('invalid', self.c.request_get, 'exhausted', 1)
        self.assertFalse(self.c.snapshot()['busy'])
        for value in [-1, 0x100000000, True]:
            self.error('invalid', XYPIController, True, self.clock, value)


if __name__ == '__main__':
    unittest.main()
