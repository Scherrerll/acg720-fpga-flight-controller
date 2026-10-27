"""Independent local mock HTTP/Host/Recorder proof; no real serial or fixed ports."""
from pathlib import Path
import binascii
import copy
import http.client
import importlib.util
import json
import struct
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import ground_server as gs
from protocol import Dashboard,base
from xy_pi_control import XYPIController,decode_parameter_response
from xy_pi_service import stopped_guard


def response_packet(command,p=1000,i=350,generation=5,status=0,build=0xb0b4):
    body=struct.pack('>BBBBIHHII',1,command['opcode'],24,status,
                     command['sequence'],p,i,generation,build)
    return b'\xa5\x91'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')


def primary(sequence=7):
    decoder=base.viewer.load_decoder(base.DECODER_PATH)
    row=dict(zip(decoder.BASE_FIELDS,struct.unpack(decoder.BASE_FMT,bytes(110))))
    row.update(zip(decoder.EXT_FIELDS,struct.unpack(decoder.EXT_FMT,bytes(111))))
    row.update(sequence=sequence,flags=14,who=0x1e,pwr=0x0f)
    row.update({f'ch{i}':1500 for i in range(1,9)})
    row.update({f'm{i}_us':1000 for i in range(1,5)})
    body=struct.pack(decoder.BASE_FMT,*[row[k]for k in decoder.BASE_FIELDS])
    body+=struct.pack(decoder.EXT_FMT,*[row[k]for k in decoder.EXT_FIELDS])
    checksum=0
    for byte in body:checksum^=byte
    return b'\xa5\x79'+body+bytes([checksum])


def info(sequence=7,uptime=1000):
    body=struct.pack('>HBBIQHQBBBBIBB',sequence,5,0,0xb0b2,
                     uptime,0,0,0,0,0,0,0,0,0)
    return b'\xa5\x88'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')


def safe_snapshot():
    return dict(connected=True,fresh=True,sequence=7,flight_info_fresh=True,
                flight_info=dict(sequence=7,taking_off=False),
                data=dict(armed=False,controller_enabled=False,command_fresh=False,
                          pwm_us=[1000]*4,rc_valid=True,rc_us=[1500]*8),
                program_label='B0B2 telemetry is not parameter capability')


class FakeClock:
    def __init__(self):self.now=100.0
    def __call__(self):return self.now


class FakeDashboard:
    def __init__(self):self.state=safe_snapshot()
    def snapshot(self):return copy.deepcopy(self.state)
    def connection(self,connected,error=None):
        self.state['connected']=connected
        if not connected:self.state['fresh']=False


class FakeRecorder:
    closed=False
    error=None
    dropped_chunks=0
    id='20000101T000000Z_00000000'
    def status(self):return dict(active=True,id=self.id)


class FakeHost:
    """HTTP gets no serial object; the real pure controller is retained."""
    def __init__(self):
        self.clock=FakeClock();self.dashboard=FakeDashboard()
        self.pi=XYPIController(enabled=True,clock=self.clock,sequence_start=100)
        self.pi.connection(7,True,'SiK',115200)
        self.pi_token='independent-local-http-test-token'
        self.config=dict(port='FAKE_NO_DEVICE',source='SiK',baud=115200)
        self.no_serial=True;self.recorder=FakeRecorder()
    def parameter_stopped_guard(self):return stopped_guard(self.dashboard.snapshot())


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.host=FakeHost();self.counter=0
        self.no_ports=patch.object(gs,'ports',side_effect=AssertionError('Real device enumeration forbidden'))
        self.no_serial=patch.object(gs.serial,'Serial',side_effect=AssertionError('Real serial open forbidden'))
        self.no_ports.start();self.no_serial.start()
        self.server=gs.make_server(self.host,0)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs=dict(poll_interval=.01),daemon=True)
        self.thread.start();self.origin=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
        self.no_serial.stop();self.no_ports.stop()
        self.assertFalse(self.thread.is_alive())
    def request(self,path,method='GET',data=None,raw=None,headers=None,extra_headers=()):
        payload=raw if raw is not None else(json.dumps(data).encode()if data is not None else b'')
        values={'Host':f'127.0.0.1:{self.server.server_port}'}
        if method=='POST':values.update(Origin=self.origin,**{'X-XY-PI-Token':self.host.pi_token,'Content-Type':'application/json','Content-Length':str(len(payload))})
        for key,value in(headers or{}).items():
            if value is None:values.pop(key,None)
            else:values[key]=value
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        try:
            connection.putrequest(method,path,skip_host=True,skip_accept_encoding=True)
            for key,value in list(values.items())+list(extra_headers):connection.putheader(key,value)
            connection.endheaders(payload);reply=connection.getresponse();body=reply.read()
            try:parsed=json.loads(body)
            except ValueError:parsed=body.decode(errors='replace')
            return reply.status,parsed,dict(reply.getheaders())
        finally:connection.close()
    def query_body(self):
        self.counter+=1;return dict(request_id=f'http-query-{self.counter}',epoch=7)
    def set_body(self,**changes):
        self.counter+=1
        body=dict(request_id=f'http-set-{self.counter}',epoch=7,expected_generation=5,p='0.1500',i='0.1000',confirmed_stopped=True)
        body.update(changes);return body
    def take(self):
        command=self.host.pi.take_write(7);self.assertIsNotNone(command)
        self.host.pi.write_result(command['token'],16);return command
    def answer(self,command,**values):self.host.pi.response(decode_parameter_response(response_packet(command,**values)),7)
    def prime(self):
        code,_,_=self.request('/api/xy-pi/query','POST',self.query_body());self.assertEqual(code,202)
        command=self.take();self.assertEqual(command['opcode'],1);self.answer(command)
        self.assertTrue(self.host.pi.snapshot()['supported'])
    def status(self):
        code,state,_=self.request('/api/xy-pi/status');self.assertEqual(code,200);return state

    def test_session_and_cached_status_are_local_and_never_queue_a_write(self):
        code,value,headers=self.request('/api/xy-pi/session')
        self.assertEqual((code,value),(200,dict(token=self.host.pi_token)))
        self.assertEqual(headers.get('Cache-Control'),'no-store')
        state=self.status();self.assertTrue(state['can_query']);self.assertFalse(state['can_set'])
        self.assertIsNone(self.host.pi.take_write(7));self.assertNotIn('token',state)
        self.assertEqual(self.request('/api/xy-pi/session',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
        self.assertEqual(self.request('/api/xy-pi/status',headers={'Host':'remote.example'})[0],403)

    def test_api_state_and_assets_do_not_disclose_the_control_token(self):
        code,value,headers=self.request('/api/state');self.assertEqual(code,200)
        self.assertNotIn(self.host.pi_token,json.dumps(value));self.assertNotIn('token',value)
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        code,html,_=self.request('/');self.assertEqual(code,200);self.assertNotIn(self.host.pi_token,html)

    def test_write_security_host_origin_token_and_fetch_site(self):
        cases=[{'Host':'remote.example'},{'Origin':None},{'Origin':'https://remote.example'},
               {'Origin':'null'},{'X-XY-PI-Token':None},{'X-XY-PI-Token':'wrong'},
               {'X-XY-PI-Token':'\xe9'},{'X-XY-PI-Token':'x'*201},
               {'Sec-Fetch-Site':'cross-site'},{'Sec-Fetch-Site':'same-site'}]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request('/api/xy-pi/query','POST',raw=b'',headers=headers)[0],403)
                self.assertFalse(self.host.pi.snapshot()['busy'])

    def test_bounded_body_transport_and_content_type_validation(self):
        cases=[{'Transfer-Encoding':'chunked'},{'Content-Encoding':'gzip'},
               {'Content-Type':'text/plain'},{'Content-Length':None},{'Content-Length':'0'},
               {'Content-Length':'2049'},{'Content-Length':'-1'},{'Content-Length':'nope'},
               {'Content-Length':'\xb2'}]
        for headers in cases:
            with self.subTest(headers=headers):
                # Invalid framing must be rejected from headers alone. Sending
                # unread bytes as well can make Windows reset a closed socket.
                self.assertEqual(self.request('/api/xy-pi/query','POST',raw=b'',headers=headers)[0],400)
        self.assertEqual(self.request('/api/xy-pi/query','POST',raw=b'',extra_headers=[('Content-Length','1')])[0],400)
        self.assertFalse(self.host.pi.snapshot()['busy'])

    def test_json_object_exact_keys_finite_values_and_no_duplicate_keys(self):
        raw_cases=[b'null',b'[]',b'1',b'"text"',b'{',b'{"request_id":"x","epoch":NaN}',
                   b'{"request_id":"x","epoch":Infinity}',b'{"request_id":"x","epoch":7,"epoch":7}']
        for body in raw_cases:
            with self.subTest(raw=body):self.assertEqual(self.request('/api/xy-pi/query','POST',raw=body)[0],400)
        for body in [{},dict(self.query_body(),unexpected=True),dict(request_id='q',epoch=True),dict(request_id=1,epoch=7)]:
            with self.subTest(body=body):self.assertEqual(self.request('/api/xy-pi/query','POST',body)[0],400)
        self.assertFalse(self.host.pi.snapshot()['busy'])

    def test_oversized_decimal_content_length_rejects_without_uncaught_conversion(self):
        # This legal header length exceeds Python's int text-conversion limit.
        # Reject it from framing alone, without reading a body or queueing work.
        with patch.object(self.server,'handle_error')as handler_error:
            self.assertEqual(self.request('/api/xy-pi/query','POST',raw=b'',
                             headers={'Content-Length':'9'*5000})[0],400)
        handler_error.assert_not_called()
        self.assertFalse(self.host.pi.snapshot()['busy'])

    def test_disabled_disconnected_and_wrong_transport_are_unavailable(self):
        self.host.pi=XYPIController(enabled=False,clock=self.host.clock)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],503)
        self.host.pi=XYPIController(enabled=True,clock=self.host.clock)
        self.host.pi.connection(7,False)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],503)
        self.host.pi.connection(7,True,'USB',115200)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],503)
        self.assertFalse(self.status()['can_query'])
        self.host.pi.connection(7,True,'SiK',57600)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],503)

    def test_old_telemetry_label_cannot_enable_set_and_query_does_not_need_stopped(self):
        self.host.dashboard.state['program_label']='B0B4 installed (untrusted display text)'
        self.assertFalse(self.status()['can_set'])
        self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body())[0],503)
        self.host.dashboard.state['data']['armed']=True
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],202)

    def test_busy_epoch_and_generation_conflicts(self):
        self.assertEqual(self.request('/api/xy-pi/query','POST',dict(request_id='stale',epoch=6))[0],409)
        self.prime()
        self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body(expected_generation=4))[0],409)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],202)
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],409)

    def test_pending_identical_request_returns_original_operation_without_resend(self):
        body=self.query_body();code,value,_=self.request('/api/xy-pi/query','POST',body)
        self.assertEqual(code,202)
        self.assertEqual(self.request('/api/xy-pi/query','POST',body)[:2],(202,value))
        command=self.take()
        self.assertEqual(self.request('/api/xy-pi/query','POST',body)[:2],(202,value))
        self.assertIsNone(self.host.pi.take_write(7));self.answer(command)

    def test_exact_decimal_grid_types_range_and_confirmation(self):
        self.prime()
        for changes in [dict(p=.15),dict(i=True),dict(p='NaN'),dict(i='Infinity'),
                        dict(p='0.05001'),dict(i='-0.0001'),dict(p='1.0001'),
                        dict(expected_generation=True),dict(confirmed_stopped=False),dict(confirmed_stopped=1)]:
            with self.subTest(changes=changes):
                self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body(**changes))[0],400)
                self.assertFalse(self.host.pi.snapshot()['busy'])

    def test_stopped_guard_all_unknown_stale_active_pwm_and_ch5_conditions(self):
        self.prime();original=safe_snapshot()
        changes=[lambda s:s.pop('fresh'),lambda s:s.update(fresh=False),lambda s:s.update(connected=False),
                 lambda s:s.pop('data'),lambda s:s['data'].pop('armed'),lambda s:s['data'].update(armed=True),
                 lambda s:s['data'].pop('controller_enabled'),lambda s:s['data'].update(controller_enabled=True),
                 lambda s:s['data'].pop('command_fresh'),lambda s:s['data'].update(command_fresh=True),
                 lambda s:s.update(flight_info_fresh=False),lambda s:s['flight_info'].pop('taking_off'),
                 lambda s:s['flight_info'].update(taking_off=True),lambda s:s['flight_info'].update(sequence=8),
                 lambda s:s['data'].pop('pwm_us'),lambda s:s['data'].update(pwm_us=[1000]*3),
                 lambda s:s['data'].update(pwm_us=[1000,1000,1000,1200]),lambda s:s['data'].update(pwm_us=[1000]*3+[True]),
                 lambda s:s['data'].pop('rc_valid'),lambda s:s['data'].update(rc_us=[1500]*4),
                 lambda s:s['data'].update(rc_us=[1500]*4+[1800]),lambda s:s['data'].update(rc_us=[1500]*4+[2200])]
        for n,change in enumerate(changes):
            with self.subTest(case=n):
                self.host.dashboard.state=copy.deepcopy(original);change(self.host.dashboard.state)
                self.assertFalse(self.status()['can_set'])
                self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body())[0],403)
                self.assertFalse(self.host.pi.snapshot()['busy'])
        self.host.dashboard.state=copy.deepcopy(original);self.host.dashboard.state['data']['rc_valid']=False
        self.host.dashboard.state['data'].pop('rc_us');self.assertTrue(self.status()['can_set'])

    def test_set_ack_independent_get_and_completed_idempotency(self):
        self.prime();body=self.set_body();code,value,_=self.request('/api/xy-pi/set','POST',body)
        self.assertEqual(code,202);operation=value['operation_id'];command=self.take();self.assertEqual(command['opcode'],2)
        self.answer(command,p=1500,i=1000,generation=6)
        self.assertEqual(self.status()['phase'],'queued_verify_get')
        verify=self.take();self.assertEqual(verify['opcode'],1);self.answer(verify,p=1500,i=1000,generation=6)
        state=self.status();self.assertEqual(state['result']['code'],'verified');self.assertEqual(state['active']['generation'],6)
        self.assertEqual((state['active']['p_text'],state['active']['i_text']),('0.1500','0.1000'))
        self.assertEqual(self.request('/api/xy-pi/set','POST',body)[:2],(202,dict(operation_id=operation)))
        self.assertIsNone(self.host.pi.take_write(7))

    def test_fpga_locked_nack_and_unknown_timeout_have_no_automatic_set_retry(self):
        self.prime();self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body())[0],202)
        command=self.take();self.answer(command,status=4)
        self.assertEqual(self.status()['result']['code'],'locked');self.assertIsNone(self.host.pi.take_write(7))
        self.assertEqual(self.request('/api/xy-pi/set','POST',self.set_body())[0],202);self.take()
        self.host.clock.now+=4;state=self.status();self.assertEqual(state['result']['code'],'unknown')
        self.assertFalse(state['can_set']);self.assertIsNone(self.host.pi.take_write(7))
        self.assertEqual(self.request('/api/xy-pi/query','POST',self.query_body())[0],202)
        recovery=self.take();self.assertEqual(recovery['opcode'],1);self.answer(recovery,p=1500,i=1000,generation=6)
        self.assertEqual(self.status()['result']['code'],'queried')

    def test_ack_then_disconnect_keeps_unknown_and_invalidates_capability(self):
        self.prime();self.request('/api/xy-pi/set','POST',self.set_body());command=self.take()
        self.answer(command,p=1500,i=1000,generation=6)
        self.assertEqual(self.status()['phase'],'queued_verify_get')
        self.host.pi.connection(8,False);self.host.pi.connection(9,False)
        state=self.status();self.assertEqual(state['result']['code'],'unknown');self.assertFalse(state['supported']);self.assertFalse(state['can_set'])
        self.assertIsNone(self.host.pi.take_write(9))

    def test_independent_get_generation_mismatch_is_not_success_or_auto_retry(self):
        self.prime();self.request('/api/xy-pi/set','POST',self.set_body());command=self.take()
        self.answer(command,p=1500,i=1000,generation=6)
        verify=self.take();self.assertEqual(verify['opcode'],1)
        self.answer(verify,p=1500,i=1000,generation=7)
        state=self.status();self.assertEqual(state['result']['code'],'mismatch')
        self.assertFalse(state['can_set']);self.assertIsNone(state['active']);self.assertIsNone(self.host.pi.take_write(7))

    def test_old_build_a591_does_not_establish_capability(self):
        self.request('/api/xy-pi/query','POST',self.query_body());command=self.take()
        for build in (0xb0b2,0xb0b3):
            with self.subTest(build=build),self.assertRaises(ValueError):
                decode_parameter_response(response_packet(command,build=build))
        state=self.status();self.assertFalse(state['supported']);self.assertEqual(state['phase'],'await_get')
        self.host.clock.now+=4;state=self.status()
        self.assertEqual(state['result']['code'],'timeout');self.assertFalse(state['can_set'])


class HostRecorderTests(unittest.TestCase):
    def test_no_serial_constructor_ports_endpoint_and_source_switch_never_enumerate(self):
        with tempfile.TemporaryDirectory()as folder,patch.object(gs,'ports',side_effect=AssertionError('enumeration forbidden')),patch.object(gs.serial,'Serial',side_effect=AssertionError('serial forbidden')):
            host=gs.Host(folder,dict(port='offline',source='SiK',baud=115200),no_serial=True,enable_xy_pi=False)
            server=None
            try:
                self.assertFalse(host.worker.is_alive())
                server=gs.make_server(host,0);thread=threading.Thread(target=server.serve_forever,kwargs=dict(poll_interval=.01),daemon=True);thread.start()
                connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                try:
                    connection.request('GET','/api/ports');reply=connection.getresponse();self.assertEqual(reply.status,200);self.assertEqual(json.loads(reply.read())['ports'],[])
                finally:connection.close()
                with self.assertRaises(ValueError):host.switch(dict(port='FAKE',source='SiK',baud=115200))
            finally:
                if server:server.shutdown();server.server_close();thread.join(timeout=2)
                host.close()

    def test_real_host_guard_requires_current_group_epochs_and_healthy_recorder(self):
        with tempfile.TemporaryDirectory()as folder,patch.object(gs,'ports',side_effect=AssertionError('enumeration forbidden')),patch.object(gs.serial,'Serial',side_effect=AssertionError('serial forbidden')):
            host=gs.Host(folder,dict(port='offline',source='SiK',baud=115200),no_serial=True)
            try:
                host.dashboard=FakeDashboard();epoch=host._transport(True)
                self.assertFalse(host.parameter_stopped_guard()[0])
                host.primary_epoch=epoch;host.info_epoch=epoch;self.assertTrue(host.parameter_stopped_guard()[0])
                host.info_epoch=epoch-1;self.assertFalse(host.parameter_stopped_guard()[0]);host.info_epoch=epoch
                host.recorder.error='synthetic failure';self.assertFalse(host.parameter_stopped_guard()[0]);host.recorder.error=None
                host.recorder.dropped_chunks=1;self.assertFalse(host.parameter_stopped_guard()[0]);host.recorder.dropped_chunks=0
            finally:host.close()

    def test_mixed_a591_does_not_refresh_main_and_old_epoch_is_ignored(self):
        with tempfile.TemporaryDirectory()as folder,patch.object(gs,'ports',side_effect=AssertionError('enumeration forbidden')),patch.object(gs.serial,'Serial',side_effect=AssertionError('serial forbidden')):
            host=gs.Host(folder,dict(port='offline',source='SiK',baud=115200),no_serial=True,enable_xy_pi=True)
            try:
                epoch=host._transport(True)
                host.recorder.put('chunk_epoch',(epoch,primary()+info()));host.recorder.capture_snapshot()
                self.assertIsNone(host.recorder.error);frames=host.dashboard.frames;stamp=host.dashboard.latest_time;raw_count=len(host.dashboard.raw_history)
                self.assertEqual(frames,1)
                self.assertEqual((host.primary_epoch,host.info_epoch,host.last_uptime),(epoch,epoch,1000))
                op=host.pi.request_get('mixed-query',epoch);command=host.pi.take_write(epoch);host.pi.write_result(command['token'],16)
                packet=response_packet(command)
                corrupt=bytearray(packet);corrupt[-1]^=1
                host.recorder.put('chunk_epoch',(epoch,bytes(corrupt)));host.recorder.capture_snapshot()
                self.assertFalse(host.pi.snapshot()['supported']);self.assertEqual(host.pi.snapshot()['phase'],'await_get')
                self.assertEqual(host.dashboard.frames,frames);self.assertEqual(host.dashboard.latest_time,stamp)
                for offset in range(0,len(packet),3):host.recorder.put('chunk_epoch',(epoch,packet[offset:offset+3]))
                host.recorder.capture_snapshot()
                self.assertIsNone(host.recorder.error);self.assertEqual(host.dashboard.frames,frames);self.assertEqual(host.dashboard.latest_time,stamp)
                self.assertEqual(len(host.dashboard.raw_history),raw_count);self.assertTrue(host.pi.snapshot()['supported']);self.assertEqual(host.pi.snapshot()['result']['operation_id'],op)
                decoded=[json.loads(line)['row']['_protocol']for line in(host.recorder.path/'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
                self.assertIn('a591',decoded)
                new_epoch=host._transport(True)
                host.recorder.put('chunk_epoch',(epoch,primary(8)+packet));host.recorder.capture_snapshot()
                self.assertEqual(host.dashboard.frames,frames);self.assertFalse(host.pi.snapshot()['supported'])
                self.assertIsNone(host.primary_epoch);self.assertIsNone(host.info_epoch);self.assertNotEqual(new_epoch,epoch)
            finally:host.close()

    def test_fpga_uptime_restart_invalidates_parameter_session_without_port_reopen(self):
        with tempfile.TemporaryDirectory()as folder,patch.object(gs,'ports',side_effect=AssertionError('enumeration forbidden')),patch.object(gs.serial,'Serial',side_effect=AssertionError('serial forbidden')):
            host=gs.Host(folder,dict(port='offline',source='SiK',baud=115200),no_serial=True,enable_xy_pi=True)
            try:
                epoch=host._transport(True);host.recorder.put('chunk_epoch',(epoch,primary()+info()));host.recorder.capture_snapshot()
                self.assertEqual((host.primary_epoch,host.info_epoch,host.last_uptime),(epoch,epoch,1000))
                host.pi.request_get('before-reset',epoch);command=host.pi.take_write(epoch);host.pi.write_result(command['token'],16)
                host.recorder.put('chunk_epoch',(epoch,response_packet(command)));host.recorder.capture_snapshot();self.assertTrue(host.pi.snapshot()['supported'])
                host.recorder.put('chunk_epoch',(epoch,info(8,uptime=1)));host.recorder.capture_snapshot()
                self.assertIsNone(host.recorder.error);self.assertGreater(host.transport_epoch,epoch)
                self.assertFalse(host.pi.snapshot()['supported']);self.assertIsNone(host.primary_epoch);self.assertIsNone(host.info_epoch)
                self.assertFalse(host.parameter_stopped_guard()[0]);self.assertFalse(host.worker.is_alive())
            finally:host.close()


class PublicBoundaryTests(unittest.TestCase):
    def test_existing_public_bridge_has_no_parameter_upstream_or_post_route(self):
        root=HERE.parents[1];path=root/'web/flight-console/local/bridge.py';name='_b0b4_test_readonly_bridge'
        spec=importlib.util.spec_from_file_location(name,path);bridge=importlib.util.module_from_spec(spec);sys.modules[name]=bridge
        sys.path.insert(0,str(path.parent))
        try:spec.loader.exec_module(bridge)
        finally:sys.path.remove(str(path.parent))
        client=bridge.HTTPClient(bridge.Config())
        with patch.object(client,'_read',side_effect=AssertionError('network forbidden'))as network:
            for path in ['/api/xy-pi/status','/api/xy-pi/session','/api/xy-pi/query','/api/xy-pi/set']:
                with self.subTest(path=path),self.assertRaises(bridge.BridgeError):client.get(path)
            network.assert_not_called()
        source=(root/'web/flight-console/local/bridge.py').read_text(encoding='utf8')
        self.assertNotIn('/api/xy-pi',source)
        self.assertIn('self.path not in ("/api/share/log", "/api/sharing")',source)


if __name__=='__main__':unittest.main(verbosity=2)
