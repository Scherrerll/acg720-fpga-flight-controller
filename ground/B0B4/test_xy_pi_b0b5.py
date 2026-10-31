"""Explicit B0B5 parameter support, offline only; no hardware or live services."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ground_server as gs
import xy_pi_control as control
from test_xy_pi_control import packet, Clock


class SelectedCodecTests(unittest.TestCase):
    def test_default_remains_b0b4_and_selection_is_exact(self):
        self.assertEqual(control.decode_parameter_response(packet())['build'], '0000B0B4')
        for selected, foreign in [('B0B4', 0xb0b5), ('B0B5', 0xb0b4)]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                control.decode_parameter_response(packet(build=foreign), selected)
        for selected in ('B0B3', 'B0B6', 'b0b5', '', None):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                control.XYPIController(build=selected)

    def test_manifest_bound_rtl_get_evidence(self):
        # Exact response preserved in qualified_offline_B0B5/evidence/parameter_identity.log.
        wire = bytes.fromhex('a591010118000000000103e8015e000000000000b0b56295')
        row = control.decode_parameter_response(wire, 'B0B5')
        self.assertEqual((row['build'], row['p_wire'], row['i_wire'], row['generation']),
                         ('0000B0B5', 1000, 350, 0))
        for variant in (packet(build=0xb0b6), packet(build=0xb0b5, op=3),
                        packet(build=0xb0b5, status=7), packet(build=0xb0b5, p=10001),
                        packet(build=0xb0b5, version=2), wire[:-1], wire[:-1]+b'\0'):
            with self.subTest(variant=variant.hex()), self.assertRaises(ValueError):
                control.decode_parameter_response(variant, 'B0B5')

    def test_changed_b0b5_codec_fails_closed_before_import(self):
        with tempfile.TemporaryDirectory(prefix='b0b5-codec-proof-') as work:
            changed = Path(work)/'changed.py'; changed.write_text('raise RuntimeError("must not execute")')
            with patch.dict(control._CODECS, {'B0B4': control._CODEC}, clear=True), \
                 patch.object(control, '_B0B5_CODEC_PATH', changed):
                with self.assertRaisesRegex(ValueError, 'differs from the reviewed package'):
                    control.XYPIController(build='B0B5')


class SelectedControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock()
        self.c=control.XYPIController(enabled=True, clock=self.clock, sequence_start=10, build='B0B5')
        self.c.connection(1, True)

    def send(self):
        command=self.c.take_write(1);self.assertIsNotNone(command)
        self.c.write_result(command['token'], len(command['packet']))
        return command

    def respond(self, command, **fields):
        wire=packet(op=command['opcode'], seq=command['sequence'], build=0xb0b5, **fields)
        self.c.response(self.c.decode_parameter_response(wire), 1)

    def query(self):
        self.c.request_get('get', 1); command=self.send();self.respond(command)
        self.assertEqual(self.c.snapshot()['result']['code'], 'queried')

    def test_selected_build_refuses_foreign_row_even_if_parser_bypassed(self):
        self.c.request_get('get', 1); command=self.send()
        foreign=control.decode_parameter_response(packet(seq=command['sequence']))
        self.c.response(foreign,1)
        self.assertTrue(self.c.snapshot()['busy'])
        self.assertFalse(self.c.snapshot()['supported'])
        self.respond(command)
        self.assertEqual(self.c.snapshot()['expected_build'], '0000B0B5')
        self.assertEqual(self.c.snapshot()['active']['build'], '0000B0B5')

    def test_b0b5_set_requires_ack_and_matching_independent_get(self):
        self.query()
        self.c.request_set('0.1200','0.0400','set',0,1); command=self.send()
        self.respond(command,p=1200,i=400,generation=1)
        self.assertEqual(self.c.snapshot()['phase'],'queued_verify_get')
        verification=self.send()
        self.assertEqual(verification['opcode'],1)
        self.respond(verification,p=1200,i=400,generation=1)
        self.assertEqual(self.c.snapshot()['result']['code'],'verified')
        self.assertEqual(self.c.snapshot()['active']['build'],'0000B0B5')
        self.assertIsNone(self.c.take_write(1))

    def test_b0b5_locked_or_timeout_never_becomes_success_or_retry(self):
        self.query(); self.c.request_set('0.1200','0.0400','locked',0,1)
        command=self.send();self.respond(command,status=4)
        self.assertEqual(self.c.snapshot()['result']['code'],'locked')
        self.assertIsNone(self.c.take_write(1))
        self.c.request_set('0.1200','0.0400','timeout',0,1);self.send()
        self.clock.now+=4; self.c.tick()
        self.assertEqual(self.c.snapshot()['result']['code'],'unknown')
        self.assertFalse(self.c.snapshot()['supported'])
        self.assertIsNone(self.c.take_write(1))

    def test_default_controller_refuses_b0b5_rows(self):
        default=control.XYPIController(enabled=True, sequence_start=10)
        default.connection(1,True);default.request_get('get',1);command=default.take_write(1)
        row=self.c.decode_parameter_response(packet(seq=command['sequence'],build=0xb0b5))
        default.response(row,1)
        self.assertFalse(default.snapshot()['supported'])
        self.assertTrue(default.snapshot()['busy'])


class SelectedHostTests(unittest.TestCase):
    def test_host_decoder_is_instance_local_and_does_not_open_or_enumerate(self):
        with tempfile.TemporaryDirectory(prefix='b0b5-host-proof-') as work, \
             patch.object(gs,'ports',side_effect=AssertionError('enumeration forbidden')), \
             patch.object(gs.serial,'Serial',side_effect=AssertionError('serial forbidden')):
            hosts=[]
            try:
                config=dict(port='OFFLINE',source='SiK',baud=115200)
                selected=gs.Host(Path(work)/'selected',config,no_serial=True,enable_xy_pi=True,xy_pi_build='B0B5');hosts.append(selected)
                default=gs.Host(Path(work)/'default',config,no_serial=True);hosts.append(default)
                self.assertFalse(selected.worker.is_alive())
                b5=packet(build=0xb0b5); b4=packet()
                self.assertEqual(selected.recorder.receiver.feed(b4),[])
                self.assertEqual(selected.recorder.receiver.feed(b5)[0]['build'],'0000B0B5')
                self.assertEqual(default.recorder.receiver.feed(b5),[])
                self.assertEqual(default.recorder.receiver.feed(b4)[0]['build'],'0000B0B4')
                selected.no_serial=False
                # Exercise recorder replacement without starting a serial loop.
                with patch.object(selected,'receive',return_value=None), \
                     patch.object(gs,'ports',return_value=[dict(port='OFFLINE2',selectable=True)]), \
                     patch.object(gs,'bind_config',side_effect=lambda config:config):
                    selected.switch(dict(port='OFFLINE2',source='SiK',baud=115200))
                    selected.worker.join(timeout=1)
                self.assertEqual(selected.recorder.receiver.feed(b4),[])
                self.assertEqual(selected.recorder.receiver.feed(b5)[0]['build'],'0000B0B5')
            finally:
                for host in hosts:host.close()


if __name__=='__main__':unittest.main()
