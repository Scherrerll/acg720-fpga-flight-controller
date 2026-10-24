import binascii
import json
from pathlib import Path
import struct
import tempfile
import unittest
import io
from protocol import decode_info, receiver, Dashboard
from rotation_protocol import decode_rotation
from recorder import Recorder
from analysis import export_csv

ROOT=Path(__file__).resolve().parent

def diagnostic_info(sequence,uptime,build=0xb0ad,version=2,takeover=False,yaw=0):
    body=struct.pack('>HBBIQHQBBBBIBB',sequence,version,int(takeover),build,
                     uptime,0,0,0,0,0,0,0,0,yaw)
    return b'\xa5\x80'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')

class ReviewFixes(unittest.TestCase):
    def record_diagnostics(self,packets):
        with tempfile.TemporaryDirectory() as folder:
            rec=Recorder(folder,dict(port='TEST',source='TEST',baud=115200),Dashboard('TEST'))
            rec.put('chunk',b''.join(packets));rec.close()
            self.assertIsNone(rec.error)
            rows=[json.loads(s) for s in (rec.path/'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
            events=[json.loads(s) for s in (rec.path/'events.jsonl').read_text(encoding='utf8').splitlines()]
            return rows,events

    def test_diagnostic_events_follow_build_epoch(self):
        rows,events=self.record_diagnostics([
            diagnostic_info(1,1000,build=0xb0ac,version=1),
            diagnostic_info(2,2000,takeover=True,yaw=4),
            diagnostic_info(3,2010,yaw=8)])
        self.assertEqual([r['epoch'] for r in rows],[0,1,1])
        boundary=next(e for e in events if e['kind']=='reported_build_changed')
        diagnostic=[e for e in events if e['kind'] in ('throttle_takeover','sticky_yaw_controller_fault')]
        self.assertEqual([e['epoch'] for e in diagnostic],[1,1,1,1])
        self.assertTrue(all(e['record_order']>boundary['record_order'] for e in diagnostic))
        self.assertEqual([e['detail']['active'] for e in diagnostic if e['kind']=='throttle_takeover'],[True,False])
        yaw=[e['detail'] for e in diagnostic if e['kind']=='sticky_yaw_controller_fault']
        self.assertEqual([(e['code'],e['retained']) for e in yaw],[(4,True),(8,False)])

    def test_diagnostic_state_reseeded_after_uptime_restart(self):
        # The first state after restart can equal the previous boot's final
        # state. It still belongs to the new source and must be retained there.
        rows,events=self.record_diagnostics([
            diagnostic_info(1,1000,takeover=True,yaw=4),
            diagnostic_info(2,10,takeover=True,yaw=4),
            diagnostic_info(3,20,yaw=8)])
        self.assertEqual([r['epoch'] for r in rows],[0,1,1])
        boundary=next(e for e in events if e['kind']=='reported_uptime_restart')
        diagnostic=[e for e in events if e['kind'] in ('throttle_takeover','sticky_yaw_controller_fault')]
        self.assertEqual([e['epoch'] for e in diagnostic],[0,0,1,1,1,1])
        current=[e for e in diagnostic if e['epoch']==1]
        self.assertTrue(all(e['record_order']>boundary['record_order'] for e in current))
        self.assertEqual([e['detail']['active'] for e in current if e['kind']=='throttle_takeover'],[True,False])
        yaw=[e['detail'] for e in diagnostic if e['kind']=='sticky_yaw_controller_fault']
        self.assertEqual([(e['code'],e['retained']) for e in yaw],[(4,True),(4,True),(8,False)])

    def test_legacy_v1_restart_does_not_invent_diagnostic_events(self):
        rows,events=self.record_diagnostics([
            diagnostic_info(1,1000,build=0xb0ac,version=1),
            diagnostic_info(2,10,build=0xb0ac,version=1)])
        self.assertEqual([r['epoch'] for r in rows],[0,1])
        self.assertTrue(all(r['row']['sticky_yaw_fault'] is None for r in rows))
        self.assertFalse(any(e['kind'] in ('throttle_takeover','sticky_yaw_controller_fault') for e in events))

    def test_actual_rtl_frames(self):
        data=bytes(int(x,16) for x in (ROOT/'fixtures/telemetry_wire.hex').read_text().split())
        self.assertEqual(len(data),1136)
        expected=[(b'\xa5\x79',224),(b'\xa5\x7a',32),(b'\xa5\x80',40),
                  (b'\xa5\x81',128),(b'\xa5\x82',96),(b'\xa5\x83',48)]
        for cycle in range(2):
            offset=cycle*568
            for header,size in expected:
                packet=data[offset:offset+size];offset+=size
                self.assertEqual(packet[:2],header)
                self.assertEqual(int.from_bytes(packet[2:4],'big'),cycle)
                if header[1]>=0x80:
                    self.assertEqual(binascii.crc_hqx(packet[2:-2],0xffff),int.from_bytes(packet[-2:],'big'))
                else:
                    check=0
                    for b in packet[2:-1]:check^=b
                    self.assertEqual(check,packet[-1])
                if header==b'\xa5\x80':
                    r=decode_info(packet)
                    self.assertTrue(r['throttle_takeover_active'])
                    self.assertEqual(r['sticky_yaw_fault'],4)
                if header==b'\xa5\x83':
                    r=decode_rotation(packet)
                    self.assertEqual(r['pair_sequence'],321)
                    self.assertEqual(r['pickup_us'],1850)
                    self.assertAlmostEqual(r['gx_deg_s'],1,places=4)
                    self.assertAlmostEqual(r['gy_deg_s'],-2,places=4)
                    self.assertEqual(r['body_forward_mm_s'],44.6)
                    self.assertEqual(r['body_right_mm_s'],223)
                    self.assertFalse(r['exposure_time_aligned'])
                    bad=bytearray(packet);bad[22]^=1
                    with self.assertRaises(ValueError):decode_rotation(bad)
        # Raw UART bytes can be fragmented at ANY byte boundary.
        rx=receiver();seen=[]
        for b in data:seen.extend(rx.feed(bytes([b])))
        new=[r for r in seen if r['_protocol'] in ('a580','a583')]
        self.assertEqual(len(new),4)
        d=Dashboard('offline');d.clock=lambda:10;d.connection(True)
        for row in new:d.ingest(row)
        s=d.snapshot()
        self.assertTrue(s['throttle_takeover_active']);self.assertEqual(s['throttle_pickup_us'],1850)
        self.assertEqual(s['sticky_yaw_fault'],4)
        d.connection(False)
        self.assertFalse(d.snapshot()['throttle_takeover_active'])
        self.assertIsNone(d.snapshot()['rotation_pair'])
        with tempfile.TemporaryDirectory() as folder:
            d=Dashboard('TEST');rec=Recorder(folder,dict(port='TEST',source='TEST',baud=115200),d)
            valid=data[256:296]+data[520:568]
            rec.put('chunk',valid);rec.close()
            saved=[json.loads(s)['row'] for s in (rec.path/'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertEqual([s['_protocol'] for s in saved],['a580','a583'])
            self.assertEqual(saved[1]['gx_counts_q12'],67174)
            event_kinds=[json.loads(s)['kind'] for s in (rec.path/'events.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertIn('sticky_yaw_controller_fault',event_kinds)
            self.assertIn('throttle_takeover',event_kinds)
            csv=io.StringIO();export_csv(rec.path,csv)
            self.assertIn('sticky_yaw_fault',csv.getvalue())
            self.assertIn('67174',csv.getvalue())

    def test_legacy_version_and_unknown_rejection(self):
        from test_system import info
        self.assertIsNone(decode_info(info(4))['sticky_yaw_fault'])
        self.assertFalse(decode_info(info(4))['throttle_takeover_active'])
        p=bytearray(info(4));p[4]=3;p[-2:]=binascii.crc_hqx(p[2:-2],0xffff).to_bytes(2,'big')
        with self.assertRaises(ValueError):decode_info(p)

if __name__=='__main__':unittest.main()
