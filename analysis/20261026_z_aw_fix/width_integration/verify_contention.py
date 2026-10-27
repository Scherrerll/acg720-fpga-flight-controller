"""Reuse the frozen substantive four-client contention test with B4 sources."""
from pathlib import Path
import hashlib,json,os,re,subprocess,shutil
REPO=Path(__file__).resolve().parents[3];R=REPO/'out/z_aw_fix_20261026/compact_aw_v4/canonical'
O=Path(__file__).resolve().parent/'contention';O.mkdir(exist_ok=True)
T=O/'tmp';T.mkdir(exist_ok=True);B=Path(r'C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=REPO/'firmware/B0B3/proofs/review/contention/contention_tb.v'
fixture_text=fixture.read_text()
assert fixture_text.count(".ch3(16'd1500)")==2
fixture_text=fixture_text.replace(".ch3(16'd1500)",".ch3(16'd1600)")
assert 'previous_work=0,saw_i=0,saw_active=0;' in fixture_text
fixture_text=fixture_text.replace('previous_work=0,saw_i=0,saw_active=0;','previous_work=0,saw_i=0,saw_active=0,saw_z_i=0;',1)
fixture_text=fixture_text.replace('if(zpub)begin','if(zpub)begin\n   if(candidate.dut.iz!=0)saw_z_i=1;',1)
fixture_text=fixture_text.replace('if(!saw_i || !saw_active || xychecked!=12','if(!saw_i || !saw_active || !saw_z_i || xychecked!=12',1)
(O/'contention_tb.v').write_text(fixture_text)
(O/'adaptation.json').write_text(json.dumps({'frozen_fixture_sha256':sha(fixture),'changes':'Original four-client assertions retained; bothCH3=1600 and require nonzeroZintegral in addition to nonzeroXYI; newv2 source and output paths','hardware':False},indent=2)+'\n')
sources=[R/'source/position/mtf_xyz_hold_control.v',R/'source/nav_math_service.v',R/'source/position/position_math.v',R/'source/position/ano_xy_stick.v',R/'source/position/ano_xy_divide36.v',R/'source/position/ano_z_stick.v']
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'contention.vvp'),str(O/'contention_tb.v'),*map(str,sources)],env=env,capture_output=True,text=True)
(O/'compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
with (O/'simulation.log').open('w')as log:c=subprocess.run([str(B/'vvp.exe'),str(O/'contention.vvp')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
s=(O/'simulation.log').read_text();print(s);assert c.returncode==0,s
match=re.search(r'PASS XY_callbacks=(\d+) Z_callbacks=(\d+) max_XY_request_to_publish_clocks=(\d+) max_XY_work_clocks=(\d+) max_Z_request_to_publish_clocks=(\d+)',s);assert match
v=list(map(int,match.groups()))
result=dict(passed=True,XY_callbacks=v[0],Z_callbacks=v[1],max_XY_request_to_publish_clocks=v[2],max_XY_work_clocks=v[3],max_Z_request_to_publish_clocks=v[4],max_XY_request_to_publish_us=v[2]*.02,max_XY_work_us=v[3]*.02,max_Z_request_to_publish_us=v[4]*.02,
 P=.125,I=.25,controller_client=3,dummy_clients=[0,1,2],dummy_request_policy='reissue immediately when own busy deasserts; constant legal operands; all returned results checked',comparison='exact ordinal XY angles/integrals and Z collective/delta/climb/height vs actual controller with CLIENTS=1',cadence='50MHz simulation, 10x accelerated arrivals; dt remains 1ms sticks /11ms Z /20ms XY',scope='actual RTL and arithmetic service contention; no aircraft dynamics or physical timing proof',source_sha256={str(p.relative_to(R)):sha(p)for p in sources},evidence_sha256={p.name:sha(p)for p in [Path(__file__),O/'contention_tb.v',O/'compile.log',O/'simulation.log']})
(O/'results.json').write_text(json.dumps(result,indent=2))
