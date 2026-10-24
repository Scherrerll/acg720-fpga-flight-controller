"""MTF-specific end-to-end proof with synthetic data, no serial or FPGA writes."""
from pathlib import Path
import binascii
import io
import json
import random
import struct
import tempfile
import threading
import time
import unittest
import urllib.request

from mtf_protocol import FORMAT,decode_mtf,decode_micolink
from protocol import receiver,Dashboard
from test_system import primary
from ground_server import Host,make_server
from analysis import analyze,export_csv
from verify_log import verify

OUT=Path(__file__).resolve().parent.parent

def module_frame(seq=1,t=10,d=177,x=-3,y=5,status=1):
    payload=struct.pack('<IIBBBBhhBBH',t,d,50,2,status,0,x,y,80,status,0)
    wire=bytes((0xef,1,1,0x51,seq,20))+payload
    return wire+bytes((sum(wire)&255,))

def mtf(sequence=1,age=0,status=1,restarts=0,position=-30000):
    raw=module_frame(seq=sequence&255,t=sequence*10,status=status)
    flags=(0x1f if status==1 and age<200 else 0x10|(1 if age<200 else 0))
    body=struct.pack(FORMAT,1,flags,sequence*200,sequence,age,
        0,0,0,0,0,0,restarts,raw,10,-531 if flags&4 else 0,885 if flags&4 else 0,
        position,50000,1,bytes(17))
    wire=b'\xa5\x81'+sequence.to_bytes(2,'big')+body
    return wire+binascii.crc_hqx(wire[2:],0xffff).to_bytes(2,'big')

def info(sequence):
    body=struct.pack('>HBBIQHQBBBBIBB',sequence,1,0,0xb0a7,sequence*200,0,0,0,0,0,0,0,0,0)
    return b'\xa5\x80'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')

class MtfTests(unittest.TestCase):
    def test_real_layout_and_signed_units(self):
        r=decode_mtf(mtf())
        self.assertEqual(r['distance_mm'],177);self.assertEqual(r['normalized_flow_x'],-3)
        self.assertEqual(r['vx_mmps_x100'],-531);self.assertEqual(r['x_mm_x100000'],-30000)
        self.assertFalse(r['status_qualified']);self.assertFalse(r['control_input'])
        self.assertEqual(decode_micolink(bytes.fromhex(r['module_raw_hex']))['flow_status'],1)
        unknown=decode_mtf(mtf(status=2));self.assertFalse(unknown['flow_provisionally_valid'])

    def test_crc_fragment_resync_and_stale(self):
        bad=bytearray(mtf());bad[25]^=1
        r=receiver();rows=[];wire=b'noise'+bytes(bad)+info(2)+mtf(2)+primary(2)
        rng=random.Random(92)
        while wire:
            n=rng.randint(1,43);rows.extend(r.feed(wire[:n]));wire=wire[n:]
        self.assertEqual([p['_protocol'] for p in rows],['a580','a581','a579'])
        d=Dashboard('TEST');d.connection(True)
        for row in rows:d.ingest(row)
        s=d.snapshot();self.assertTrue(s['mtf_fresh']);self.assertTrue(s['motor_stop_lock_expected'])
        self.assertEqual(s['mtf_values']['mtf_range_cm'],17.7)
        self.assertEqual(s['mtf_values']['mtf_vx_mm_s'],-5.31)
        self.assertEqual(s['mtf_values']['mtf_x_mm'],-.3)
        old=d.mtf_time;d.mtf_time=old-1
        s=d.snapshot();self.assertFalse(s['mtf_fresh']);self.assertIsNone(s['mtf_values']['mtf_vx_mm_s'])
        d.connection(False);self.assertFalse(d.snapshot()['mtf_fresh'])
        self.assertFalse(decode_mtf(mtf(age=200))['link_valid'])

    def test_logging_http_csv_curves_download_replay(self):
        with tempfile.TemporaryDirectory(dir=OUT/'tmp') as tmp:
            host=Host(tmp,dict(port='TEST',baud=115200,source='USB'),no_serial=True)
            server=make_server(host,0);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                host.recorder.put('connection',(True,None))
                wire=b''.join(primary(i)+info(i)+mtf(i,restarts=1 if i==3 else 0) for i in (1,2,3))
                for start in range(0,len(wire),19):host.recorder.put('chunk',wire[start:start+19])
                host.recorder.capture_snapshot()
                base=f'http://127.0.0.1:{server.server_port}'
                session=host.recorder.id
                def get(route):
                    with urllib.request.urlopen(base+route,timeout=5) as r:return r.read()
                state=json.loads(get('/api/state'))
                self.assertTrue(state['mtf_fresh']);self.assertFalse(state['mtf_sensor']['status_qualified'])
                self.assertIn(b'/dashboard.js',get('/'));self.assertIn(b'fetch',get('/dashboard.js'))
                result=json.loads(get(f'/api/logs/{session}/analysis?field=mtf_x_mm'))
                self.assertEqual(result['primary_samples'],3);self.assertEqual(result['sample_protocol'],'a581')
                self.assertTrue(result['points'][-1]['gap'])
                archive=OUT/'tmp/mtf_synthetic_log.zip';archive.write_bytes(get(f'/api/logs/{session}/download?format=zip'))
                proof=verify(archive);self.assertTrue(proof['passed']);self.assertEqual(proof['decoded_frames'],9)
                csv=get(f'/api/logs/{session}/download?format=csv').decode('utf-8-sig')
                self.assertIn('mtf_vx_mm_s',csv);self.assertIn('a581',csv);self.assertIn('-5.31',csv)
                meta=json.loads((host.recorder.path/'meta.json').read_text(encoding='utf-8'))
                self.assertFalse(meta['mtf_sensor']['status_qualified']);self.assertFalse(meta['serial_writes'])
                (OUT/'host_synthetic_proof.json').write_text(json.dumps(dict(passed=True,synthetic=True,
                    physical_sensor_verified=False,actual_wireless_verified=False,raw_replay=proof),indent=2)+'\n')
            finally:server.shutdown();server.server_close();host.close();worker.join(timeout=5)

if __name__=='__main__':unittest.main(verbosity=2)
