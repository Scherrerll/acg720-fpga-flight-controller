"""SiK A585 strict decode, isolated receiver, freshness and disk logging tests."""
from pathlib import Path
import binascii
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

FW=Path(__file__).resolve().parents[1]
REPO=FW.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module
D=load('b0b2_sik_decoder',FW/'ground/protocol.py')
PREP=load('b0b2_sik_prepare',FW/'tools/prepare_sik_receiver.py')

def packet(**changes):
    fields=dict(zip(D.KEYS,(1000,0xb0b2,100,90,80,7,3000000,89,50000,2000000,
        0x40,0x80,0x20,0x0f,4,1,0,0,123456,0x32,4,0x80,4,3000000)))
    fields.update(changes)
    body=b'\xa5\x85'+struct.pack('>BBHI',1,1,12,0x12345678)+struct.pack(D.FORMAT,*(fields[k] for k in D.KEYS))
    return body+binascii.crc_hqx(body[2:],0xffff).to_bytes(2,'big')

def repair(body):return body[:-2]+binascii.crc_hqx(body[2:-2],0xffff).to_bytes(2,'big')

def info(build=0xb0b2,uptime=1000):
    body=b'\xa5\x80'+struct.pack('>HBBIQHQBBBBIBB',12,4,1,build,uptime,1,900,0x32,1,0x80,4,3000000,4,8)
    return body+binascii.crc_hqx(body[2:],0xffff).to_bytes(2,'big')

class DecoderTests(unittest.TestCase):
    def test_exact_fields_and_units(self):
        p=packet();self.assertEqual(len(p),76);r=D.decode(p)
        self.assertEqual(r['max_pose_gap_ms'],60);self.assertEqual(r['held_dt_ms'],1)
        self.assertEqual(r['first_diagnostic_cause'],0)
        self.assertEqual(r['first_protection_code'],0x32)
        self.assertEqual(r['capture_tick'],0x12345678)
    def test_crc_corruption(self):
        p=bytearray(packet());p[20]^=1
        with self.assertRaises(ValueError):D.decode(p)
    def test_length_and_header(self):
        for p in (packet()[:-1],b'XX'+packet()[2:],packet()+b'X'):
            with self.assertRaises(ValueError):D.decode(p)
    def test_version_and_removed_usb_profile(self):
        for index,value in ((2,2),(3,2),(3,0)):
            p=bytearray(packet());p[index]=value
            with self.assertRaises(ValueError):D.decode(repair(p))
    def test_build_identity(self):
        with self.assertRaises(ValueError):D.decode(packet(build_id=0xb0b1))
    def test_reserved_and_invalid_diagnostic(self):
        for fields in ({'latest_pose_flags':0xc0},{'first_diagnostic_trigger':8},{'first_diagnostic_cause':10}):
            with self.assertRaises(ValueError):D.decode(packet(**fields))
    def test_protection_predicate(self):
        for code in (0x34,0x22,0x10):
            with self.assertRaises(ValueError):D.decode(packet(first_protection_code=code))
        self.assertEqual(D.decode(packet(first_protection_code=0))['first_protection_code'],0)
    def test_actual_rtl_wire_fixture(self):
        path=REPO/'out/B0B2/sik/sik_wire.hex'
        if not path.exists():self.skipTest('run run_sik_tests.py to generate RTL wire fixture')
        wire=bytes.fromhex(path.read_text());r=D.decode(wire[-76:])
        self.assertEqual(r['uptime_ms'],0x0102030405060708)
        self.assertEqual(r['raw_count'],100);self.assertEqual(r['consumed_accepted_id'],89)
        self.assertEqual(r['first_protection_time_ms_low32'],123456)

class ReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=REPO/'out/B0B2';base.mkdir(parents=True,exist_ok=True)
        cls.temp=tempfile.TemporaryDirectory(prefix='sik_receiver_test_',dir=base)
        cls.output=Path(cls.temp.name)/'receiver'
        cls.before=PREP.file_hashes(REPO/'ground/B0B0')
        cls.receipt=PREP.prepare(cls.output)
        sys.path.insert(0,str(cls.output))
        cls.P=load('protocol',cls.output/'protocol.py')
        cls.R=load('recorder',cls.output/'recorder.py')
    @classmethod
    def tearDownClass(cls):
        assert PREP.file_hashes(REPO/'ground/B0B0')==cls.before
        sys.path.remove(str(cls.output));cls.temp.cleanup()
    def test_preparation_hashes_and_no_overwrite(self):
        self.assertFalse(self.receipt['serial_opened']);self.assertFalse(self.receipt['serial_writes'])
        self.assertEqual(self.receipt['source_files_sha256'],self.before)
        self.assertEqual(self.receipt['output_files_sha256']['sik_diagnostic_protocol.py'],PREP.sha((FW/'ground/protocol.py').read_bytes()))
        with self.assertRaises(FileExistsError):PREP.prepare(self.output)
        with self.assertRaises(ValueError):PREP.prepare(REPO/'out/B0B1/forbidden')
    def test_identity_and_mixed_fragmented_stream(self):
        rx=self.P.receiver();rows=[];stream=b'junk'+info()+packet()
        for b in stream:rows+=rx.feed(bytes([b]))
        self.assertEqual([r['_protocol'] for r in rows],['a580','a585'])
        self.assertEqual(rows[0]['build_id'],0xb0b2)
        self.assertEqual(set(rx.protocols),{bytes.fromhex(x) for x in ('a579','a57a','a57b','a580','a581','a582','a583','a585')})
    def test_bad_crc_resynchronizes(self):
        p=bytearray(packet());p[-1]^=1;rx=self.P.receiver()
        rows=rx.feed(bytes(p)+info()+packet())
        self.assertEqual([r['_protocol'] for r in rows],['a580','a585']);self.assertGreater(rx.checksum_errors,0)
    def test_auxiliary_does_not_replace_primary(self):
        d=self.P.Dashboard('offline');d.connection(True)
        rows=self.P.receiver().feed(info()+packet())
        before=d.latest
        for row in rows:d.ingest(row)
        self.assertIs(d.latest,before)
        snap=d.snapshot();self.assertTrue(snap['imu_diagnostic_fresh'])
        self.assertEqual(snap['imu_diagnostic']['first_protection_code'],0x32)
        d.connection(False);self.assertFalse(d.snapshot()['imu_diagnostic_fresh'])
    def test_source_switch_and_firmware_reset_clear_freshness(self):
        d=self.P.Dashboard('offline');d.connection(True)
        for row in self.P.receiver().feed(info()+packet()):d.ingest(row)
        for row in self.P.receiver().feed(info(uptime=1)):d.ingest(row)
        self.assertFalse(d.snapshot()['imu_diagnostic_fresh'])
        d.clear_source('new');self.assertIsNone(d.snapshot()['imu_diagnostic'])
    def test_source_clear_between_snapshot_lock_regions(self):
        d=self.P.Dashboard('offline');d.connection(True)
        for row in self.P.receiver().feed(info()+packet()):d.ingest(row)
        original=self.P.LegacyDashboard.snapshot
        def switch_between(model):
            result=original(model)
            model.clear_source('new-source')
            return result
        with patch.object(self.P.LegacyDashboard,'snapshot',switch_between):
            self.assertFalse(d.snapshot()['imu_diagnostic_fresh'])
    def test_recorder_keeps_diagnostic_jsonl(self):
        d=self.P.Dashboard('offline')
        with tempfile.TemporaryDirectory(dir=Path(self.temp.name)) as logs:
            rec=self.R.Recorder(Path(logs),{'source':'fixture','baud':115200},d)
            rec.put('connection',(True,None));rec.put('chunk',info()+packet());rec.close()
            self.assertIsNone(rec.error)
            rows=[json.loads(line)['row'] for line in (rec.path/'telemetry.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual([r['_protocol'] for r in rows],['a580','a585'])
            self.assertEqual(rows[-1]['first_diagnostic_cause'],0)
            self.assertEqual((rec.path/'raw.bin').read_bytes(),info()+packet())

if __name__=='__main__':unittest.main()
