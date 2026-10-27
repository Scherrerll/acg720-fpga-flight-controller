"""Focused end-to-end proof without touching a serial port or FPGA."""
from pathlib import Path
import binascii
import io
import json
import random
import queue
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile

from protocol import ROOT,base,receiver,decode_info,Dashboard
from recorder import Recorder
from ground_server import Host,make_server
from analysis import analyze,records,export_csv
from verify_log import verify

DEC=base.viewer.load_decoder(ROOT/'support/monitor_control.py')
OUT=Path(__file__).resolve().parent/'test_output'
(OUT/'tmp').mkdir(parents=True,exist_ok=True)


def primary(sequence,accepted=10000,flags=14):
    row=SEED.copy();row.update(sequence=sequence,accepted_count=accepted,flags=flags)
    row['mode_requested']=row['mode_requested_code'];row['mode_active']=row['mode_active_code']
    body=struct.pack(DEC.BASE_FMT,*[row[k] for k in DEC.BASE_FIELDS])+struct.pack(DEC.EXT_FMT,*[row[k] for k in DEC.EXT_FIELDS])
    check=0
    for byte in body:check^=byte
    return b'\xa5\x79'+body+bytes([check])


def info(sequence,uptime=1000,event=1):
    body=struct.pack('>HBBIQHQBBBBIBB',sequence,1,0,0xb0a0,uptime,event,900,0x31,0,0,0,25000,0,0)
    return b'\xa5\x80'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')


SEED=next(r['row'] for r in records(Path(__file__).with_name('fixtures')/'seed_primary.jsonl')
          if r.get('row',{}).get('_protocol')=='a579')


class GroundTests(unittest.TestCase):
    def test_fragment_corruption_and_resync(self):
        good=primary(10)+info(10)
        bad=bytearray(info(9));bad[-1]^=1
        stream=b'garbage'+bytes(bad)+good
        r=receiver();rows=[];rng=random.Random(12)
        while stream:
            n=rng.randrange(1,19);rows.extend(r.feed(stream[:n]));stream=stream[n:]
        self.assertEqual([(v['_protocol'],v['sequence']) for v in rows],[('a579',10),('a580',10)])
        self.assertGreater(r.checksum_errors,0)
        self.assertEqual(decode_info(info(4))['build_id'],0xb0a0)

    def test_raw_replay_epochs_missing_and_invalid_fields(self):
        with tempfile.TemporaryDirectory(dir=OUT/'tmp') as tmp:
            d=Dashboard('TEST');rec=Recorder(tmp,dict(port='TEST',baud=115200,source='SiK'),d)
            rec.put('connection',(True,None))
            wire=primary(65534)+info(65534,1000)+primary(65535,10001)+info(65535,1100)+primary(0,10002)+info(0,1200)+primary(2,10003)+info(2,1300)
            wire+=primary(0,accepted=1,flags=0)+info(0,uptime=1,event=0)
            for start in range(0,len(wire),23):rec.put('chunk',wire[start:start+23])
            rec.put('mark','test event');rec.close()
            self.assertIsNone(rec.error);self.assertEqual((rec.path/'raw.bin').read_bytes(),wire)
            rows=list(records(rec.path/'telemetry.jsonl'));fresh=receiver().feed(wire)
            self.assertEqual([r['row'] for r in rows],fresh)
            self.assertEqual(rec.missing,1);self.assertEqual(rec.epoch,1)
            self.assertEqual(d.snapshot()['flight_info']['build_id'],0xb0a0)
            d.connection(False)
            self.assertFalse(d.snapshot()['fresh']);self.assertIsNone(d.snapshot()['flight_info'])
            result=analyze(rec.path,'yaw_deg')
            self.assertEqual(result['primary_samples'],5)
            self.assertEqual(result['missing_sequence_estimate'],1)
            self.assertEqual(result['epoch_changes'],1)
            self.assertIsNone(result['points'][-1]['yaw_deg'])
            csv=io.StringIO();export_csv(rec.path,csv)
            self.assertIn('elapsed_s',csv.getvalue());self.assertIn('TEST',json.dumps(rec.meta))
            events=list(records(rec.path/'events.jsonl'))
            self.assertTrue(any(e['kind']=='retained_source_event' for e in events))
            self.assertTrue(any(e['kind']=='operator_mark' for e in events))
            self.assertEqual(json.loads((rec.path/'summary.json').read_text())['missing_primary_frames'],1)
            self.assertFalse(rec.put('mark','cannot write a closed session'))

    def test_analysis_gap_bound_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);seed=receiver().feed(primary(0))[0]
            with (path/'telemetry.jsonl').open('w',encoding='utf-8') as out:
                for i in range(5000):
                    r=dict(seed,sequence=(i*2)&65535)
                    out.write(json.dumps(dict(elapsed_s=i*.6,epoch=0,row=r))+'\n')
            result=analyze(path,limit=20)
            self.assertLessEqual(len(result['points']),20)
            self.assertEqual(result['missing_sequence_estimate'],4999)
            self.assertTrue(any(p['gap'] for p in result['points']))
            with self.assertRaises(ValueError):analyze(path,start=float('nan'))

    def test_disk_failure_stops_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Dashboard('TEST');rec=Recorder(tmp,dict(port='TEST',baud=115200,source='USB'),d)
            with patch.object(rec,'_json',side_effect=OSError('simulated disk full')):
                rec.put('chunk',primary(0))
                rec.thread.join(timeout=3)
            self.assertFalse(rec.thread.is_alive());self.assertTrue(rec.closed)
            self.assertIn('disk full',rec.error);self.assertFalse(d.snapshot()['fresh'])
            self.assertFalse(rec.put('chunk',b'not saved'))
            self.assertEqual((rec.path/'raw.bin').read_bytes(),primary(0))

    def test_queue_overflow_is_explicit_and_raw_remains_replayable(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate=threading.Event();started=threading.Event();original=Recorder.run
            def delayed_run(rec):
                started.set();gate.wait(3);original(rec)
            with patch.object(Recorder,'run',delayed_run):
                rec=Recorder(tmp,dict(port='TEST',baud=115200,source='USB'),Dashboard('TEST'))
                self.assertTrue(started.wait(1));rec.queue=queue.Queue(maxsize=1)
                self.assertTrue(rec.put('chunk',primary(4)))
                self.assertFalse(rec.put('chunk',b'dropped'))
                gate.set();rec.close()
            self.assertEqual(rec.dropped_bytes,7);self.assertEqual(rec.dropped_chunks,1)
            self.assertIsNotNone(rec.error)
            self.assertEqual((rec.path/'raw.bin').read_bytes(),primary(4))
            self.assertTrue(any(e['kind']=='ingest_overflow' for e in records(rec.path/'events.jsonl')))

    def test_http_downloads_api_and_path_guards(self):
        with tempfile.TemporaryDirectory(dir=OUT/'tmp') as tmp:
            host=Host(tmp,dict(port='TEST',baud=115200,source='SiK'),no_serial=True)
            host.recorder.put('connection',(True,None));host.recorder.put('chunk',primary(100)+info(100))
            end=time.monotonic()+3
            while host.recorder.primary<1 and time.monotonic()<end:time.sleep(.01)
            host.recorder.flush()
            server=make_server(host,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            url=f'http://127.0.0.1:{server.server_port}'
            def get(path):
                with urllib.request.urlopen(url+path,timeout=5) as response:return response.read()
            try:
                self.assertIn(b'dashboard.js',get('/'));self.assertIn(b'logs.js',get('/logs'))
                self.assertIn(b'--cyan',get('/ui.css'));self.assertIn(b'/api/state',get('/dashboard.js'))
                state=json.loads(get('/api/state'));self.assertTrue(state['fresh']);self.assertFalse(state['serial_writes'])
                self.assertEqual(state['receiver_profile'],'mtf01p.b0b2_timeout_policy.v3')
                session=host.recorder.id
                self.assertEqual(json.loads(get('/api/logs'))['sessions'][0]['id'],session)
                self.assertEqual(json.loads(get(f'/api/logs/{session}/analysis'))['primary_samples'],1)
                self.assertIn(b'elapsed_s',get(f'/api/logs/{session}/download?format=csv'))
                with zipfile.ZipFile(io.BytesIO(get(f'/api/logs/{session}/download?format=zip'))) as zipped:
                    self.assertEqual(zipped.read('raw.bin'),primary(100)+info(100));self.assertIn('manifest.json',zipped.namelist())
                blob=get(f'/api/logs/{session}/download?format=zip')
                self.assertEqual(verify(io.BytesIO(blob))['primary_frames'],1)
                req=urllib.request.Request(url+'/api/calibration/apply',data=b'{}',headers={'Content-Type':'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as exc:urllib.request.urlopen(req)
                self.assertEqual(exc.exception.code,403)
                with self.assertRaises(ValueError):host.logpath('../outside')
                with self.assertRaises(ValueError):host.switch(dict(port='COM18',baud=115200,source='USB'))
            finally:server.shutdown();thread.join();server.server_close();host.close()


if __name__=='__main__':unittest.main(verbosity=2)
