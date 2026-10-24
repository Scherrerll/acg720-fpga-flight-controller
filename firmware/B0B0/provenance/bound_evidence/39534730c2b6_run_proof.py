"""Prepared only. Run once after root explicitly authorizes post-route proof."""
from pathlib import Path
import re,json,hashlib,random,subprocess,os
D=Path(__file__).resolve().parent;P=D.parent;H=P.parent;W=H.parents[2]
B=H/'range_age_prechecked_multiply7_plan/synthesis_only/20261023T233128_740589Z';N=P/'synthesis_only/20261024T005225_383171Z'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((D/'prepared_inputs.json').read_text());assert all(sha(p)==h for p,h in manifest['bindings'].items())
 old=(B/'core/ano_attitude_estimator.v').read_text();new=(N/'core/ano_attitude_estimator.v').read_text()
 # Reverse exactly the flag-only estimator delta, proving every original numeric/state statement unchanged.
 projection=new.replace(",\n output reg tilt4500_ok=1'b1",'')
 projection=projection.replace(' wire signed [15:0] publication_roll_word=pending_roll[15:0],publication_pitch_word=pending_pitch[15:0];\n','')
 expr=re.search(r'wire publication_tilt4500=(.*?);',new)[1]
 projection=projection.replace(' wire publication_tilt4500='+expr+';\n','').replace("tilt4500_ok<=1'b1;",'').replace('tilt4500_ok<=publication_tilt4500;','')
 assert projection==old
 assert re.findall(r'roll_cdeg\s*<=\s*([^;]+);',old)==['0','pending_roll']
 assert re.findall(r'pitch_cdeg\s*<=\s*([^;]+);',old)==['0','pending_pitch']
 assert re.findall(r'tilt4500_ok\s*<=\s*([^;]+);',new)==["1'b1",'publication_tilt4500']
 assert "PUBLISH:begin\n    roll_cdeg<=pending_roll;pitch_cdeg<=pending_pitch;yaw_cdeg<=pending_yaw;yaw_range_ok<=publication_yaw_range;tilt4500_ok<=publication_tilt4500;" in new
 # Exhaustive individual-axis signed16 membership equivalence, including body-pitch negation modulo16.
 for word in range(65536):
  angle=word if word<32768 else word-65536
  numeric=-4500<=angle<=4500
  old_bits=(word&32767)>=28268 if word&32768 else (word&32767)<=4500
  negword=(-angle)&65535;negangle=negword if negword<32768 else negword-65536
  assert numeric==old_bits==(-4500<=negangle<=4500)
 # Defaultoff/non4500 must retain literal old numeric guard.
 g=(N/'sensor/mtf_shared_geometry.v').read_text();assert 'PRECHECKED_HEIGHT_TILT4500=0' in g
 match=re.search(r'wire live_height_tilt_ok=\(PRECHECKED_HEIGHT_TILT4500 && HEIGHT_TILT_LIMIT_CDEG==4500\) \?body_tilt4500_ok:\((.*?)\);',g);assert match
 numericexpr='roll_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && roll_cdeg<=HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg<=HEIGHT_TILT_LIMIT_CDEG';assert match[1]==numericexpr
 assert 'FLOW_TILT_LIMIT_CDEG' in g and 'wire flow_pose_ok=roll_cdeg>=-FLOW_TILT_LIMIT_CDEG' in g
 # Local producer boundary uses exact pending16 words and exact new expression. PUBLISH hold/reset are source-projected above.
 sv="""`timescale 1ns/1ps
module producer(input wire clk,rst_n,publish,input wire signed[31:0]pending_roll,pending_pitch,output reg signed[15:0]roll_cdeg=0,pitch_cdeg=0,output reg tilt4500_ok=1);
wire signed[15:0]publication_roll_word=pending_roll[15:0],publication_pitch_word=pending_pitch[15:0];
wire publication_tilt4500=EXPR;
always @(posedge clk) if(!rst_n)begin roll_cdeg<=0;pitch_cdeg<=0;tilt4500_ok<=1;end else if(publish)begin roll_cdeg<=pending_roll;pitch_cdeg<=pending_pitch;tilt4500_ok<=publication_tilt4500;end
endmodule
module tb;reg clk=0,rst_n=1,publish=0;reg signed[31:0]pr=0,pp=0;wire signed[15:0]r,p;wire f;integer checks=0;producer u(clk,rst_n,publish,pr,pp,r,p,f);reg signed[15:0]er=0,ep=0;
task check;begin #1;if(r!==er || p!==ep || f!==((er>=-4500)&&(er<=4500)&&(ep>=-4500)&&(ep<=4500)))$fatal(1,"producer check %0d",checks);checks=checks+1;end endtask
task step(input rr,pub,input signed[31:0]a,b);begin clk=0;rst_n=rr;publish=pub;pr=a;pp=b;if(!rr)begin er=0;ep=0;end else if(pub)begin er=a[15:0];ep=b[15:0];end #1;clk=1;check();clk=0;end endtask
initial begin check();
""".replace('EXPR',expr)
 vectors=[]
 for a in [-32768,-4501,-4500,-4499,0,4499,4500,4501,32767,65536+4500,65536+4501,-65536-4500,0x7fffffff,-2147483648]:
  for b in [-32768,-4501,-4500,0,4500,4501,32767]:vectors.extend([(1,1,a,b),(1,0,-b,-a),(0,1,a,b)])
 rng=random.Random(4500)
 for _ in range(1000):vectors.append((int(rng.randrange(16)!=0),rng.randrange(2),rng.randrange(-2**31,2**31),rng.randrange(-2**31,2**31)))
 for rr,pub,a,b in vectors:sv+=f"step(1'b{rr},1'b{pub},32'h{a&0xffffffff:08x},32'h{b&0xffffffff:08x});\n"
 sv+='$display("PASS tilt producer checks=%0d",checks);$finish;end endmodule\n';(D/'tb.v').write_text(sv)
 iv=W/'.tools/iverilog/app/bin';env=os.environ.copy();env['PATH']=str(iv)+os.pathsep+env['PATH'];env['TEMP']=env['TMP']=env['TMPDIR']=str(D);logs=[]
 for cmd in [[str(iv/'iverilog.exe'),'-g2012','-s','tb','-o','proof.vvp','tb.v'],[str(iv/'vvp.exe'),'proof.vvp']]:
  p=subprocess.run(cmd,cwd=D,env=env,capture_output=True,text=True,timeout=60);logs.append(p.stdout+p.stderr);(D/'run.log').write_text('\n'.join(logs));assert p.returncode==0,logs[-1]
 assert 'PASS tilt producer' in logs[-1];assert all(sha(p)==h for p,h in manifest['bindings'].items())
 report=dict(status='PASS scoped source projection/membership/local producer boundary',bindings=manifest['bindings'],axis_exhaustive_words=65536,joint_steps=len(vectors),limits=['No full estimator/FSM simulation','Local boundary not whole mapped proof','Mapped flag connections only read-only literal inventory, not CE/D/reset cone equivalence','No wholecore/parser/RC/host/hardware/timing acceptance'],synthesis_run=False,pnr_run=False)
 report['evidence_hashes']={p.name:sha(p) for p in [D/'run_proof.py',D/'prepared_inputs.json',D/'tb.v',D/'run.log']};(D/'proof.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
