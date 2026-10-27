"""Extract actual old/new functions and actual new signed alias into a miter."""
from pathlib import Path
import hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs_attempt01/alias';D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source/position/mtf_xyz_hold_control.v'
N=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source/position/mtf_xyz_hold_control.v'
old=P.read_text();new=N.read_text()
pattern=r' function signed \[31:0\] quantized_climb_q16;.*? end endfunction'
f0=re.findall(pattern,old,re.S);f1=re.findall(pattern,new,re.S);assert len(f0)==len(f1)==1 and f0==f1
alias=re.findall(r' wire signed \[31:0\] quantized_climb_logic_q16 /\* synthesis syn_dspstyle="logic" \*/;\n assign quantized_climb_logic_q16=quantized_climb_q16\(speed_z_tick_store\);',new)
assert len(alias)==1
oldrhs=re.findall(r'alt_speed<=([^;]+);',old);newrhs=re.findall(r'alt_speed<=([^;]+);',new)
assert len(oldrhs)==len(newrhs)==2 # one reset and one publication
assert oldrhs[-1]==newrhs[-1].replace('quantized_climb_logic_q16','quantized_climb_q16(speed_z_tick_store)')
def module(name,fn,declaration,rhs):
 return f'module {name}(input signed [28:0] speed_z_tick_store,input signed [31:0] next_auto_speed,input taking_off,output signed [31:0] q,alt);\n{fn}\n{declaration}\nassign q=quantized_climb_q16(speed_z_tick_store);\nassign alt={rhs};\nendmodule\n'
(D/'actual_functions.v').write_text(module('old_actual',f0[0],'',oldrhs[-1])+module('new_actual',f1[0],alias[0],newrhs[-1]),encoding='utf8')
tb=r'''`timescale 1ns/1ps
module tb;
reg signed [28:0] v=0;reg signed [31:0] next_auto_speed=0;reg taking_off=0;
wire signed [31:0] oq,nq,oa,na;
old_actual old(v,next_auto_speed,taking_off,oq,oa);new_actual newx(v,next_auto_speed,taking_off,nq,na);
integer i,j,k,n=0,two=0,four=0;reg signed [63:0] reference;reg [31:0] random_word;
task check;input integer known;begin
 #1;n=n+1;
 if(oq!==nq || oa!==na)$fatal(1,"actual function/alias mismatch v=%h next=%h taking=%b q=%h/%h alt=%h/%h",v,next_auto_speed,taking_off,oq,nq,oa,na);
 if(known)begin
  reference=$signed(v);reference=reference/64'sd65536;reference=reference/64'sd10;reference=reference*64'sd655360;
  if(oq!==reference[31:0])$fatal(1,"independent signed64 reference mismatch v=%h got=%h ref=%h",v,oq,reference);
  two=two+1;
 end else four=four+1;
end endtask
initial begin
 // Every upper13 bit pattern, both equivalence classes of lower16 |reduction,
 // plus multiple concrete nonzero patterns, including every signed boundary.
 for(i=0;i<8192;i=i+1)for(j=0;j<4;j=j+1)begin
  v={i[12:0],16'd0};
  case(j)1:v[15:0]=1;2:v[15:0]=16'h8000;3:v[15:0]=16'hffff;endcase
  next_auto_speed=i-4096;taking_off=j[0];check(1);
 end
 // X/Z at every bit; fractional low bits cover known-one dominance and unknown OR.
 for(i=0;i<29;i=i+1)for(j=0;j<4;j=j+1)begin
  v=j[1]?29'h1fffffff:0;v[i]=j[0]?1'bz:1'bx;
  next_auto_speed=32'sd0;taking_off=1;check(0);
  taking_off=1'bx;check(0);taking_off=1'bz;check(0);
 end
 for(i=0;i<10000;i=i+1)begin
  v=$random;next_auto_speed=$random;taking_off=i[0];check(1);
  for(k=0;k<29;k=k+1)begin random_word=$random;v[k]=random_word[1:0]==0?1'b0:random_word[1:0]==1?1'b1:random_word[1:0]==2?1'bx:1'bz;end
  for(k=0;k<32;k=k+1)begin random_word=$random;next_auto_speed[k]=random_word[1:0]==0?1'b0:random_word[1:0]==1?1'b1:random_word[1:0]==2?1'bx:1'bz;end
  taking_off=i%4==0?1'b0:i%4==1?1'b1:i%4==2?1'bx:1'bz;check(0);
 end
 $display("PASS actual_alias vectors=%0d signed64=%0d fourstate=%0d all_upper13=8192 low16_reduction_classes=2 function_byte_identical=1",n,two,four);$finish;
end
endmodule
'''
(D/'alias_tb.v').write_text(tb,encoding='utf8')
(D/'STRUCTURAL_IDENTITY.json').write_text(json.dumps({'passed':True,'source_controller_sha256':{'v20':sha(P),'v22':sha(N)},'actual_function_byte_identical':True,'function_sha256':hashlib.sha256(f0[0].encode()).hexdigest(),'actual_wire_declaration_and_assignment':alias[0],'actual_old_alt_rhs':oldrhs[-1],'actual_new_alt_rhs':newrhs[-1],'signed_widths':{'input':29,'whole_mm':14,'cm':10,'result_and_alias':32,'next_auto_speed':32,'constant':32},'universal_argument':'For every 29-bit four-state input and every four-state next_auto_speed/taking_off, substituting the exact continuous signed32 alias into the new sampled expression reconstructs the exact old signed32 expression. The function text and sizing context are identical. This is a structural universal identity, not a claim that simulation enumerates 4**29 inputs.','simulation_two_state_partition':'Function depends on all upper13 bits and only zero/nonzero of lower16. Every upper13 pattern and both lower reduction classes tested against independent signed64 truncation arithmetic; X/Z samples additionally test exact actual-function propagation.','sampling':'speed_z_tick_store is only captured in state0, never assigned in state61 where alias is sampled; no new FF, delay or edge.'},indent=2)+'\n')
