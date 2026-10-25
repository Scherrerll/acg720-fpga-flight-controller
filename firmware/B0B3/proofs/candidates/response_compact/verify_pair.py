"""Cycle-exact real old/new banks: 121 shipping vectors plus ownership resets."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
C=Path(__file__).resolve().parent;R=C.parents[1];O=C/'verification';T=O/'tmp';B=R.parent/'.tools/iverilog/app/bin'
sys.path.insert(0,str(R));from xy_pi_cli import encode_request,decode_response
base=(R/'verification/protocol_tb.v').read_text()
needle="xy_pi_parameters #(.TIMEOUT_TICKS(100))dut(clk,rst_n,rx_valid,rx_error,data,write_safe,boundary,p,i,gen,valid,resp,ready);"
assert base.count(needle)==1
monitor='''
wire[15:0]oldp,oldi;wire[31:0]oldgen;wire oldvalid;wire[191:0]oldresp;
xy_pi_parameters_before #(.TIMEOUT_TICKS(100))previous(clk,rst_n,rx_valid,rx_error,data,write_safe,boundary,oldp,oldi,oldgen,oldvalid,oldresp,ready);
integer cycle_checks=0,valid_word_checks=0,crc_body_checks=0;
always @(posedge clk)begin #1;
 cycle_checks=cycle_checks+1;
 if({p,i,gen,valid}!=={oldp,oldi,oldgen,oldvalid})$fatal(1,"cycle mismatch gains/gen/valid p=%0d/%0d i=%0d/%0d gen=%0d/%0d valid=%b/%b",p,oldp,i,oldi,gen,oldgen,valid,oldvalid);
 if(valid)begin
  valid_word_checks=valid_word_checks+1;
  if(resp!==oldresp)$fatal(1,"valid full response differs candidate=%048h old=%048h",resp,oldresp);
 end
 if(dut.state==4 || dut.state==5)begin
  crc_body_checks=crc_body_checks+1;
  if(resp[175:16]!==oldresp[175:16])$fatal(1,"CRC input body differs");
  if(dut.state==4 && (dut.crc_index<2 || dut.crc_index>21))$fatal(1,"CRC consumed its own tail/header");
 end
end
'''
tb=base.replace(needle,needle+monitor)
def frame(op,seq,p=0,i=0):return "128'h"+encode_request(op,seq,p,i).hex()
extra=f'''
// Reset during CRC: active write occurred, but no ACK escaped; defaults return.
send_frame({frame(2,300,1200,900)});wait(dut.state==4);repeat(5)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;
send_frame({frame(1,301)});check(0,500,0,0);
// Reset while valid is backpressured: old and new valid both withdraw.
send_frame({frame(2,302,900,1000)});wait(valid);repeat(35)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;
send_frame({frame(1,303)});check(0,500,0,0);
// Reset abandons an uncommitted pair held at a blocked boundary.
boundary=0;send_frame({frame(2,304,800,700)});wait(dut.state==2);repeat(10)@(negedge clk);
rst_n=0;repeat(3)@(negedge clk);rst_n=1;boundary=1;
send_frame({frame(1,305)});check(0,500,0,0);
// A complete premature request cannot overwrite the held response fields.
send_frame({frame(2,306,8000,9000)});wait(valid);
send_frame({frame(1,307)});repeat(30)@(negedge clk);check(0,8000,9000,1);
send_frame({frame(1,308)});check(0,8000,9000,1);
$display("PAIR cycles=%0d valid_words=%0d CRC_body_cycles=%0d",cycle_checks,valid_word_checks,crc_body_checks);
'''
needle='$display("PASS protocol registers replay CRC range reset timeout lock race atomic-boundary backpressure");$finish;end'
assert tb.count(needle)==1;tb=tb.replace(needle,extra+needle)
(O/'pair_tb.v').write_text(tb)
env=dict(os.environ,TMP=str(T),TEMP=str(T),TMPDIR=str(T))
c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'pair.vvp'),str(O/'pair_tb.v'),str(O/'bank_before.v'),str(C/'source/xy_pi_parameters.v')],env=env,capture_output=True,text=True)
(O/'pair.compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
c=subprocess.run([str(B/'vvp.exe'),str(O/'pair.vvp')],env=env,capture_output=True,text=True,timeout=120)
(O/'pair.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
rows=[decode_response(bytes.fromhex(l.split()[1]))for l in c.stdout.splitlines()if l.startswith('RESPONSE ')]
assert len(rows)==126,len(rows)
match=re.search(r'PAIR cycles=(\d+) valid_words=(\d+) CRC_body_cycles=(\d+)',c.stdout);assert match
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(passed=True,shipping_protocol_cases=121,total_checked_responses=len(rows),cycle_checks=int(match[1]),full_192bit_valid_word_checks=int(match[2]),CRC_input_body_cycle_checks=int(match[3]),extra_cases=['reset during CRC','reset while valid/backpressured','reset while commit boundary pending','premature complete GET cannot alter held SET response','fresh GET after release'],scope='two real bank RTL instances driven identically; compare P/I/generation/valid every clock including reset, all192 response bits whenever valid; valid0 response bits intentionally unconstrained',evidence_sha256={p.relative_to(C).as_posix():sha(p)for p in [Path(__file__),O/'pair_tb.v',O/'bank_before.v',O/'pair.compile.log',O/'pair.log',C/'source/xy_pi_parameters.v']},shipping_vector_fixture_sha256=sha(R/'verification/protocol_tb.v'))
(O/'pair_results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
