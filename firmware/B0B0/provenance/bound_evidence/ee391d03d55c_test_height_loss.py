import binascii
import csv
import io
import json
import struct
import tempfile
import unittest
from protocol import receiver, decode_info, Dashboard
from recorder import Recorder
from analysis import export_csv
from test_system import primary


def info(sequence=1, flags=19, version=4, build=0xb0af):
    body=struct.pack('>HBBIQHQBBBBIBB',sequence,version,flags,build,1000,0,0,0,0,0,0,0,0,0)
    return b'\xa5\x80'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')


class HeightLossTests(unittest.TestCase):
    def test_b0b0_identity(self):
        self.assertTrue(decode_info(info(build=0xb0b0))['height_loss_fallback_active'])

    def test_version_flags_identity(self):
        d=decode_info(info())
        self.assertTrue(d['height_loss_fallback_active'])
        self.assertTrue(d['taking_off'])
        self.assertTrue(d['motor_prepared'])
        for packet in [info(flags=32), info(version=3), info(build=0xb0ae)]:
            with self.assertRaises(ValueError):decode_info(packet)

    def test_readonly_dashboard_manual_label_and_stop_priority(self):
        dashboard=Dashboard('TEST');dashboard.connection(True)
        packets=receiver().feed(primary(1,flags=127)+info())
        for row in packets:dashboard.ingest(row)
        s=dashboard.snapshot()
        self.assertTrue(s['height_loss_fallback_active'])
        self.assertIn('手动油门',s['data']['mode_active'])
        self.assertFalse(s['serial_writes'])
        for row in receiver().feed(primary(2,flags=15)):dashboard.ingest(row)
        s=dashboard.snapshot()
        self.assertFalse(s['height_loss_fallback_active'])
        self.assertEqual(s['data']['mode_active'],'待机')

    def test_recorder_replay_csv_retains_fallback_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec=Recorder(tmp,dict(port='TEST',source='TEST',baud=115200),Dashboard('TEST'))
            rec.put('chunk',primary(1,flags=127)+info());rec.close()
            self.assertIsNone(rec.error)
            stream=io.StringIO();export_csv(rec.path,stream)
            rows=list(csv.DictReader(io.StringIO(stream.getvalue())))
            row=next(r for r in rows if r['protocol']=='a580')
            self.assertEqual(row['height_loss_fallback_active'],'True')
            self.assertEqual(int(row['build_id']),0xb0af)
            self.assertEqual(row['motor_prepared'],'True')
            saved=[json.loads(line)['row'] for line in (rec.path/'telemetry.jsonl').read_text(encoding='utf8').splitlines()]
            self.assertTrue(any(r.get('height_loss_fallback_active') for r in saved))


if __name__=='__main__':unittest.main()
