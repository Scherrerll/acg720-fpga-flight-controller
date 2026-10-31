"""Disposable UI preview: loopback HTTP, synthetic telemetry, no serial or POSTs.

Run ``python -B ground/B0B4/preview_ui.py --http-port 0``. All recordings live
in a TemporaryDirectory and disappear on exit. This tool never reads user logs.
Visit /__preview?scenario=live (or stale, disconnected, b0b5, pi-ready,
pi-busy, pi-unknown, logs-empty, empty); add &view=logs or &view=parameters for those screens.
The simulation is presentation evidence, never a device/protocol qualification.
"""
from contextlib import ExitStack
import argparse
import copy
import json
import math
import struct
import tempfile
import threading
import urllib.parse
from unittest.mock import patch

import ground_server as gs
from protocol import base


SCENARIOS = ('empty', 'live', 'stale', 'disconnected', 'b0b5', 'pi-ready',
             'pi-busy', 'pi-unknown', 'logs-empty')


def primary_packet(sequence):
    """Construct a new, stopped telemetry packet without an old log/fixture."""
    decoder = base.viewer.load_decoder(base.DECODER_PATH)
    row = dict(zip(decoder.BASE_FIELDS, struct.unpack(decoder.BASE_FMT, bytes(110))))
    row.update(zip(decoder.EXT_FIELDS, struct.unpack(decoder.EXT_FMT, bytes(111))))
    row.update(sequence=sequence, flags=14, who=0x1e, pwr=0x0f,
               roll_cdeg=int(math.sin(sequence / 5) * 400),
               pitch_cdeg=int(math.cos(sequence / 7) * 250),
               accepted_count=sequence + 100, run_min_us=1200, run_max_us=2000)
    row.update({f'ch{i}': 1500 for i in range(1, 9)})
    row.update({f'm{i}_us': 1000 for i in range(1, 5)})
    row.update({f'physical_m{i}_us': 1000 for i in range(1, 5)})
    body = struct.pack(decoder.BASE_FMT, *[row[k] for k in decoder.BASE_FIELDS])
    body += struct.pack(decoder.EXT_FMT, *[row[k] for k in decoder.EXT_FIELDS])
    check = 0
    for byte in body:
        check ^= byte
    return b'\xa5\x79' + body + bytes([check])


class Preview:
    def __init__(self, host):
        self.host = host
        self.scenario = 'empty'
        self.seeded = False
        self.lock = threading.RLock()

    def choose(self, scenario):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown preview scenario')
        with self.lock:
            self.scenario = scenario
            if scenario not in ('empty', 'logs-empty') and not self.seeded:
                self.host.recorder.put('connection', (True, 'SYNTHETIC UI PREVIEW'))
                for n in range(32):
                    self.host.recorder.put('chunk', primary_packet(n))
                self.host.recorder.put('mark', 'SYNTHETIC UI PREVIEW; no device attached')
                # A recorder snapshot is an ordered flush barrier, not a sleep.
                ready, box = threading.Event(), {}
                self.host.recorder.put('snapshot', (ready, box))
                if not ready.wait(3):
                    raise RuntimeError('Temporary recorder did not flush')
                self.seeded = True

    def state(self):
        with self.lock:
            scenario = self.scenario
        result = self.host.dashboard.snapshot()
        result.update(source=self.host.config, recording=self.host.recorder.status(),
                      preview_only=True, synthetic=scenario not in ('empty', 'logs-empty'))
        if scenario in ('empty', 'logs-empty'):
            # Even after another scenario, show the actual initial empty state.
            result.update(connected=False, fresh=False, data=None, history=[],
                          navigation=None, navigation_values={}, navigation_fresh=False,
                          mtf_sensor=None, mtf_values={}, mtf_fresh=False,
                          flight_info=None, flight_info_fresh=False, frame_age_ms=None)
            return result
        fresh = scenario not in ('stale', 'disconnected')
        data = copy.deepcopy(result.get('data') or {})
        data.update(attitude_valid=True, sensor_ok=True, roll_deg=3.8, pitch_deg=-1.6,
                    yaw_relative_deg=-112.7, armed=False, rc_valid=True,
                    controller_enabled=False, command_fresh=False,
                    mode_active='自稳', pwm_us=[1000]*4,
                    rc_us=[1500, 1500, 1100, 1500, 1000, 1500, 1500, 1500],
                    inhibit_text='合成停机状态 · 无设备连接')
        result.update(connected=scenario != 'disconnected', fresh=fresh, data=data,
                      sequence=31, frame_age_ms=80 if fresh else 5200,
                      flight_info_fresh=fresh, flight_ready=False,
                      flight_info=dict(sequence=31, build_id=0xb0b5 if scenario=='b0b5' else 0xb0b4,
                                       taking_off=False, motor_prepared=False),
                      navigation_fresh=fresh, mtf_fresh=fresh,
                      navigation=dict(height_fusion_ready=True, provisional_world_velocity_ready=True,
                                      velocity_fusion_ready=True, xyz_active=False, xyz_requested=False,
                                      xyz_ready=True, mapping_verified=False, rotation_verified=False),
                      navigation_values=dict(nav_fused_height_mm=214, nav_target_height_mm=200,
                                             nav_fused_vz_mm_s=0, nav_body_vx_mm_s=12,
                                             nav_body_vy_mm_s=-8, nav_fused_vx_mm_s=9,
                                             nav_fused_vy_mm_s=-6, nav_source_age_ms=30),
                      mtf_sensor=dict(range_provisionally_valid=True, flow_provisionally_valid=True),
                      mtf_values=dict(mtf_range_cm=21.5, mtf_quality=97),
                      history=[dict(t=n/5, roll_deg=math.sin(n/13)*4,
                                    pitch_deg=math.cos(n/19)*2.5,
                                    yaw_relative_deg=-112.7+math.sin(n/31)*1.5)
                               for n in range(301)])
        return result

    def pi_status(self):
        with self.lock:
            scenario = self.scenario
        ready = scenario in ('pi-ready', 'pi-busy', 'pi-unknown')
        busy = scenario == 'pi-busy'
        result = dict(enabled=ready, connected=ready, source='SiK', baud=115200,
                      epoch=1, supported=ready, busy=busy, phase='await_verify_get' if busy else 'idle',
                      operation_id='synthetic-operation' if busy else None,
                      active=None, result=None, can_query=ready and not busy,
                      can_set=ready and not busy, block_reason='离线合成预览；所有 POST 均被拒绝',
                      preview_only=True, synthetic=True)
        if ready:
            result['active'] = dict(p_text='0.1000', i_text='0.0350', p_wire=1000, i_wire=350,
                                    generation=3, build='0000B0B4', age_ms=50)
        if scenario == 'pi-unknown':
            result['result'] = dict(operation_id='synthetic-previous', code='unknown',
                                    message='合成超时；先查询确认，不自动重发')
        if scenario == 'b0b5':
            result['block_reason'] = 'B0B5 不属于 B0B4 参数协议；没有参数支持证据'
        return result


def make_preview(host, port=0):
    server = gs.make_server(host, port)
    assert server.server_address[0] == '127.0.0.1'
    original = server.RequestHandlerClass
    preview = Preview(host)

    class Handler(original):
        def do_GET(self):
            if not self.local_host():
                self.send_error(403)
                return
            url = urllib.parse.urlsplit(self.path)
            if url.path == '/__preview':
                args = urllib.parse.parse_qs(url.query)
                try:
                    preview.choose(args.get('scenario', ['empty'])[0])
                except (ValueError, RuntimeError) as exc:
                    self.json_response(400, dict(error=str(exc)))
                    return
                self.send_response(303)
                self.send_header('Location', {'logs': '/logs', 'parameters': '/parameters'}.get(args.get('view', [''])[0], '/'))
                self.end_headers()
                return
            if url.path == '/api/state':
                self.json_response(200, preview.state())
                return
            if url.path == '/api/xy-pi/status':
                self.json_response(200, preview.pi_status())
                return
            if url.path == '/api/logs' and preview.scenario == 'logs-empty':
                self.json_response(200, dict(sessions=[], fields=gs.FIELDS))
                return
            super().do_GET()

        def do_POST(self):
            # Consume ordinary small JSON bodies before closing; otherwise a
            # TCP reset can hide the intended 403 from fetch on Windows.
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                length = -1
            if 0 <= length <= 4096:
                self.rfile.read(length)
            self.close_connection = True
            self.json_response(403, dict(code='preview_only', error='合成 UI 预览拒绝所有 POST；未连接设备'))

    server.RequestHandlerClass = Handler
    server.preview = preview
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--http-port', type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.http_port <= 65535:
        parser.error('Invalid HTTP port')
    with ExitStack() as stack:
        stack.enter_context(patch.object(gs.serial, 'Serial', side_effect=AssertionError('No serial in UI preview')))
        stack.enter_context(patch.object(gs, 'ports', side_effect=AssertionError('No device enumeration in UI preview')))
        root = stack.enter_context(tempfile.TemporaryDirectory(prefix='gmfly-ui-preview-'))
        host = gs.Host(root, dict(port='SYNTHETIC_NO_DEVICE', source='SiK', baud=115200), no_serial=True)
        stack.callback(host.close)
        server = make_preview(host, args.http_port)
        stack.callback(server.server_close)
        print(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}', preview_only=True,
                              serial_writes=False, all_posts_rejected=True, scenarios=SCENARIOS)), flush=True)
        try:
            server.serve_forever(poll_interval=.2)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
