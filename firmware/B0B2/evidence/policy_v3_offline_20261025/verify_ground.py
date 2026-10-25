from pathlib import Path
import binascii,hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent/'github_publish/acg720-fpga-flight-controller'
RECEIVER=REPO/'out/B0B2/timeout_policy_receiver_20261025'
sys.path.insert(0,str(RECEIVER))
import protocol
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
wire=bytes.fromhex((ROOT/'wire.hex').read_text());assert len(wire)==644
receiver=protocol.receiver();rows=receiver.feed(wire)
assert len(rows)==7 and not receiver.buffer and receiver.checksum_errors==receiver.discarded_bytes==0
assert [r['_protocol']for r in rows]==['a579','a57a','a580','a581','a582','a583','a585']
by={r['_protocol']:r for r in rows}
assert [by[k].get('_wire_protocol')for k in ['a579','a57a','a580','a583']]==['a586','a587','a588','a589']
for k in ['a579','a57a','a580','a583','a585']:
    row=by[k];assert row['_age_policy']=='no_pose_age_v3'
    for field in row['unavailable_fields']:assert row[field]is None,(k,field)
assert by['a580']['version']==5 and by['a583']['version']==2 and by['a585']['version']==3
assert by['a585']['capabilities']['latest_rejected_source_id']and by['a585']['capabilities']['first_protection_time_ms_low32']
dashboard=protocol.Dashboard('offline');dashboard.connection(True)
for row in rows:dashboard.ingest(row)
snapshot=dashboard.snapshot();assert snapshot['data']['pose_age_ms']is None and snapshot['data']['pose_age_available']is False
json.dumps(snapshot,allow_nan=False)
model=protocol.base.viewer
primary=dict(by['a579'],flags=6,roll_cdeg=123,pitch_cdeg=-456)
data,_=model.normalize(primary)
assert data['roll_deg']==1.23 and data['pitch_deg']==-4.56 and data['pose_age_ms']is None
legacy=dict(primary);legacy.pop('_age_policy');legacy['pose_age_ticks']=3000000
legacy_data,_=model.normalize(legacy);assert legacy_data['roll_deg']is None
acc=dict(by['a57a'],accel_flags=3,raw_age_ticks=4000000)
fields=model.acceleration_fields(acc,primary,0)
assert fields['linear_accel_valid']and fields['sensor_accel_valid']and fields['linear_accel_age_ms']is None
badseq=dict(acc,sequence=acc['sequence']+1)
assert not model.acceleration_fields(badseq,primary,0)['linear_accel_valid']
assert not model.acceleration_fields(acc,primary,1)['linear_accel_valid']
def crc_packet(packet):return packet[:-2]+binascii.crc_hqx(packet[2:-2],0xffff).to_bytes(2,'big')
offset=0;packets={}
for length in [224,32,40,128,96,48,76]:
    packet=wire[offset:offset+length];packets[packet[:2]]=packet;offset+=length
assert offset==len(wire)
def rejected(fn,*args):
    try:fn(*args)
    except ValueError:return
    raise AssertionError('Malformed packet accepted')
mtf_packet=packets[b'\xa5\x81'];decode_mtf=receiver.protocols[b'\xa5\x81'][1]
for age,online,metric in [(199,True,True),(200,True,False),(999,True,False),(1000,False,False)]:
    b=bytearray(mtf_packet);b[18:22]=age.to_bytes(4,'big')
    b[5]=(b[5]&~7)|(int(online))|(6 if metric else 0)
    row=decode_mtf(crc_packet(bytes(b)))
    assert row['module_online']==online and row['link_valid']==metric,(age,row)
    assert row['metric_freshness_limit_ms']==200 and row['control_source_freshness_limit_ms']==100
b=bytearray(mtf_packet);b[18:22]=(999).to_bytes(4,'big');b[5]&=~7
rejected(decode_mtf,crc_packet(bytes(b)))
diag=packets[b'\xa5\x85'];b=bytearray(diag);b[-3]=1
rejected(receiver.protocols[b'\xa5\x85'][1],crc_packet(bytes(b)))
for header in [b'\xa5\x86',b'\xa5\x87',b'\xa5\x88',b'\xa5\x89',b'\xa5\x85']:
    b=bytearray(packets[header]);b[-1]^=1
    rejected(receiver.protocols[header][1],bytes(b))
bad=bytearray(packets[b'\xa5\x87']);bad[-1]^=1
r=protocol.receiver();out=r.feed(bytes(bad))
assert out and out[0].get('_acceleration_invalid')and out[0]['_protocol']=='a57a'
assert r.acceleration_checksum_errors==1
# Historical real RTL output remains decodable with its original measured ages.
historical=REPO/'firmware/B0B2/evidence/source_revisions/copy99_v1/completed_sik_v1/sik_wire.hex'
old=bytes.fromhex(historical.read_text());r=protocol.receiver()
# This historical serializer fixture deliberately used non-profile test values
# for info/nav/MTF/rotation. Check the three authentic compatible layouts;
# do not claim that arbitrary other fixture fields form valid sensor records.
oldprimary=r.protocols[b'\xa5\x79'][1](old[:224])
oldacc=r.protocols[b'\xa5\x7a'][1](old[224:256])
olddiag=r.protocols[b'\xa5\x85'][1](old[-76:])
assert olddiag['version']==1 and isinstance(oldprimary['pose_age_ticks'],int)
assert isinstance(oldacc['pose_age_ticks'],int) and olddiag['first_protection_pose_age_ticks']is not None
# The offline checker must accept the new schema and keep unavailable ages null.
path=REPO/'firmware/B0B2/tools/analyze_bench.py';spec=importlib.util.spec_from_file_location('policy_bench',path);bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)
unavailable,provided=bench.diagnostic_capabilities(by['a585']);assert tuple(unavailable)==('first_protection_pose_age_ticks',)and provided
malformed=dict(by['a585'],first_protection_pose_age_ticks=0)
rejected(bench.diagnostic_capabilities,malformed)
inputs=[ROOT/'wire.hex',ROOT/'protocol_capture_commands.json',ROOT/'capture_protocol_tb.v',ROOT/'capture_protocol.py',ROOT/'behavior_verification.json',REPO/'support/server.py',REPO/'support/monitor_control.py',path,REPO/'firmware/B0B2/ground/protocol.py',REPO/'firmware/B0B2/ground/policy_protocol.py',REPO/'firmware/B0B2/tools/prepare_sik_receiver.py']
inputs+=list(RECEIVER.glob('*.py'))
result=dict(passed=True,wire_bytes=len(wire),decoded_frames=len(rows),crc_errors=receiver.checksum_errors,discarded_bytes=receiver.discarded_bytes,new_age_values='None/unavailable, never zero freshness',historical_v1_primary_acceleration_summary_decode_passed=True,policy_display_and_frame_coherence_passed=True,module_online_1000ms_metric_200ms_passed=True,metadata_corruption_rejection_passed=True,source_sha256={p.relative_to(ROOT/'candidate').as_posix():sha(p)for p in(ROOT/'candidate').rglob('*')if p.is_file()},evidence_sha256={str(p):sha(p)for p in inputs},hardware_accessed=False,serial_opened=False)
(ROOT/'protocol_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS age-free RTL644-byte stream,7 frames, explicit unavailable ages, display/coherence, metric200ms/online1s, corruption rejection and historical v1 bytes')
