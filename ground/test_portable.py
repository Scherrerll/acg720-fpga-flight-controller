"""Synthetic offline proof: no listening sockets, serial devices or original logs."""
import binascii
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from protocol import base, receiver, decode_info
from ground_server import Host, make_server
from analysis import analyze, export_csv
from verify_log import verify


def info(sequence=1):
    body = struct.pack('>HBBIQHQBBBBIBB', sequence, 3, 0, 0xb0ae,
                       1000, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    return b'\xa5\x80' + body + binascii.crc_hqx(body, 0xffff).to_bytes(2, 'big')


def primary(sequence=1):
    decoder = base.viewer.load_decoder(base.DECODER_PATH)
    row = dict(zip(decoder.BASE_FIELDS, struct.unpack(decoder.BASE_FMT, bytes(110))))
    row.update(zip(decoder.EXT_FIELDS, struct.unpack(decoder.EXT_FMT, bytes(111))))
    row.update(sequence=sequence, flags=14, who=0x1e, pwr=0x0f)
    row.update({f'ch{i}': 1500 for i in range(1, 9)})
    row.update({f'm{i}_us': 1000 for i in range(1, 5)})
    body = struct.pack(decoder.BASE_FMT, *[row[k] for k in decoder.BASE_FIELDS])
    body += struct.pack(decoder.EXT_FMT, *[row[k] for k in decoder.EXT_FIELDS])
    checksum = 0
    for byte in body:
        checksum ^= byte
    return b'\xa5\x79' + body + bytes([checksum])


class NoListenServer:
    def __init__(self, address, handler):
        self.server_port = address[1]
        self.RequestHandlerClass = handler
        self.server_name = 'localhost'


class MemoryConnection:
    def __init__(self, request):
        self.request = io.BytesIO(request)
        self.response = bytearray()

    def makefile(self, *_args, **_kwargs):
        return self.request

    def sendall(self, body):
        self.response.extend(body)


def request(server, route, method='GET', body=None, host='127.0.0.1:8765'):
    data = json.dumps(body).encode() if body is not None else b''
    wire = (f'{method} {route} HTTP/1.0\r\nHost: {host}\r\n'
            f'Content-Length: {len(data)}\r\nContent-Type: application/json\r\n\r\n').encode() + data
    connection = MemoryConnection(wire)
    server.RequestHandlerClass(connection, ('127.0.0.1', 1), server)
    headers, body = bytes(connection.response).split(b'\r\n\r\n', 1)
    return int(headers.split(b' ')[1]), body


class PortableTests(unittest.TestCase):
    def test_crc_fragmentation_resync(self):
        good = primary() + info()
        bad = bytearray(info(2)); bad[-1] ^= 1
        rx = receiver(); rows = []
        wire = b'noise' + bad + good
        for offset in range(0, len(wire), 7):
            rows.extend(rx.feed(wire[offset:offset + 7]))
        self.assertEqual([r['_protocol'] for r in rows], ['a579', 'a580'])
        self.assertGreater(rx.checksum_errors, 0)
        self.assertEqual(decode_info(info())['build_id'], 0xb0ae)

    def test_logging_http_analysis_and_exports_without_hardware(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch('ground_server.ports', side_effect=AssertionError('device enumeration forbidden')), \
             patch('ground_server.serial.Serial', side_effect=AssertionError('serial open forbidden')), \
             patch.object(base.viewer, 'ThreadingHTTPServer', NoListenServer):
            host = Host(tmp, dict(port='offline', baud=115200, source='SiK'), no_serial=True)
            try:
                host.recorder.put('connection', (True, None))
                wire = primary() + info()
                host.recorder.put('chunk', wire)
                snapshot = host.recorder.capture_snapshot()  # writer barrier
                self.assertIn('raw.bin', snapshot['sizes'])
                self.assertIsNone(host.recorder.error)
                self.assertEqual(host.recorder.frames, 2)
                server = make_server(host, 8765)
                self.assertEqual(request(server, '/api/ports')[1],
                                 json.dumps(dict(ports=[], config=host.config), ensure_ascii=False, allow_nan=False).encode())
                for route in ('/', '/logs', '/dashboard.js', '/logs.js', '/ui.css',
                              '/mtf-ui.js', '/telemetry-ui.js', '/api/health', '/api/state'):
                    self.assertEqual(request(server, route)[0], 200, route)
                status = json.loads(request(server, '/api/state')[1])
                self.assertFalse(status['serial_writes'])
                self.assertTrue(status['read_only'])
                self.assertEqual(request(server, '/api/calibration/apply', 'POST', {})[0], 403)
                self.assertEqual(request(server, '/api/aircraft/command', 'POST', {})[0], 403)
                self.assertEqual(request(server, '/api/connection', 'POST',
                                         dict(port='COM1', source='SiK', baud=115200))[0], 400)
                self.assertEqual(request(server, '/api/state', host='untrusted.example')[0], 403)
                self.assertEqual(request(server, '/api/mark', 'POST', dict(text='synthetic marker'))[0], 200)
                route = '/api/logs/' + host.recorder.id
                analysis = json.loads(request(server, route + '/analysis')[1])
                self.assertEqual(analysis['primary_samples'], 1)
                csv_status, csv_data = request(server, route + '/download?format=csv')
                self.assertEqual(csv_status, 200)
                self.assertIn(b'throttle_us', csv_data)
                zip_status, zip_data = request(server, route + '/download?format=zip')
                self.assertEqual(zip_status, 200)
                archive = Path(tmp) / 'synthetic.zip'; archive.write_bytes(zip_data)
                self.assertTrue(verify(archive)['passed'])
            finally:
                host.close()
            self.assertEqual((host.recorder.path / 'raw.bin').read_bytes(), wire)
            self.assertIsNone(host.recorder.error)
            self.assertEqual(analyze(host.recorder.path)['primary_samples'], 1)
            csv_out = io.StringIO(); export_csv(host.recorder.path, csv_out)
            self.assertIn('throttle_us', csv_out.getvalue())


if __name__ == '__main__':
    unittest.main()
