from pathlib import Path
import re, difflib, hashlib, json, subprocess, os
D=Path(__file__).resolve().parent
R=D.parent.parent
nav=R/'fixture/mtf_xyz_navigation_control.v'
top=R/'fixture/acg720_ano_port.v'
original=nav.read_text(); original_top=top.read_text()
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (nav,top)}
old='if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;'
new='''if(STARTUP_ONLY_DIAGNOSTIC_RESET)begin
   // Caller must guarantee reset starts low and never reasserts.
   // Preserve initialized payload until reset releases; never delay captures.
   if(rst_n && !diagnostic_hold)diagnostic_q<=diagnostic_next;
  end else begin
   if(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;else if(!diagnostic_hold)diagnostic_q<=diagnostic_next;
  end'''
assert original.count(old)==1
candidate=original.replace('PROOF_CONTROLLER=0,PRECHECKED_YAW_RANGE=0','PROOF_CONTROLLER=0,PRECHECKED_YAW_RANGE=0,STARTUP_ONLY_DIAGNOSTIC_RESET=0').replace(old,new)
candidate_top=original_top.replace('.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1)) native_navigation(','.PROOF_CONTROLLER(1),.PRECHECKED_YAW_RANGE(1),.STARTUP_ONLY_DIAGNOSTIC_RESET(1)) native_navigation(')
assert candidate_top!=original_top
(D/'mtf_xyz_navigation_control.proposed.v').write_text(candidate)
(D/'acg720_ano_port.proposed.v').write_text(candidate_top)
patch=''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/fixture/mtf_xyz_navigation_control.v',tofile='b/fixture/mtf_xyz_navigation_control.v'))
patch+=''.join(difflib.unified_diff(original_top.splitlines(True),candidate_top.splitlines(True),fromfile='a/fixture/acg720_ano_port.v',tofile='b/fixture/acg720_ano_port.v'))
(D/'proposed.patch').write_text(patch)
def bank(text,name,param=''):
    start=text.index(' localparam [719:0] RESET_DIAGNOSTIC=')
    return 'module '+name+param+'(input clk,rst_n,diagnostic_hold,input [719:0] diagnostic_next,output [719:0] diagnostic_body);\n'+text[start:text.index('endmodule',start)]+'endmodule\n'
(D/'banks.v').write_text(bank(original,'reference')+bank(candidate,'proposal','#(parameter STARTUP_ONLY_DIAGNOSTIC_RESET=0)'))
boot=re.search(r' reg \[7:0\] boot=0;always @\(posedge clk50\) if\(boot!=255\) boot<=boot\+1\x27b1;\n wire rst_n=boot==255;',original_top).group()
bench='''module tb;
reg clk50=0;always #5 clk50=~clk50;
BOOT
reg generic_reset=0,hold=0,origin_reset=0;
reg [719:0] payload=0;
wire [719:0] a,b,c,d;
reference ref_boot(clk50,rst_n,hold,payload,a);
proposal #(1) new_boot(clk50,rst_n,hold,payload,b);
reference ref_generic(clk50,generic_reset,hold,payload,c);
proposal new_generic(clk50,generic_reset,hold,payload,d);
integer i,j; reg released=0;reg [31:0] random_state=32'h386941ab;
task check;
begin
 if(a!==b || ref_boot.diagnostic_q!==new_boot.diagnostic_q)$fatal(1,"startup bank mismatch");
 if(c!==d || ref_generic.diagnostic_q!==new_generic.diagnostic_q)$fatal(1,"generic bank mismatch");
end endtask
initial begin
 #1;check;
 for(i=0;i<50000;i=i+1)begin
  @(negedge clk50);
  for(j=0;j<720;j=j+1)begin
   random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
   payload[j]=random_state[0];
  end
  origin_reset=random_state[7];
  // Origin reset is outside this bank's interface: arbitrary payload changes
  // cover its upstream effects, including changes while held.
  hold=(i<300) ? 1'b1 : (i%997<120 ? 1'b1:random_state[4]);
  generic_reset=(i>255 && i%701>27);
  @(posedge clk50);#1;
  if(released && !rst_n)$fatal(1,"top reset reasserted");
  released=released||rst_n;
  check;
 end
 if(!released)$fatal(1,"boot never released");
 $display("PASS 50000 cycles: full 720-bit bank/output, boot/init/hold/random payload; generic repeated reset unchanged");
 $finish;
end
endmodule
'''.replace('BOOT',boot)
(D/'tb.v').write_text(bench)
ws=next(p for p in R.parents if (p/'.tools/iverilog/app/bin/iverilog.exe').is_file())
iv=ws/'.tools/iverilog/app/bin/iverilog.exe'
env=dict(os.environ,PATH=str(iv.parent)+os.pathsep+os.environ['PATH'],TMP=str(D),TEMP=str(D),TMPDIR=str(D))
commands=[[str(iv),'-g2012','-s','tb','-o',str(D/'study.vvp'),str(D/'banks.v'),str(D/'tb.v')],[str(iv.with_name('vvp.exe')),str(D/'study.vvp')]]
logs=[]
for command in commands:
 p=subprocess.run(command,capture_output=True,text=True,cwd=D,env=env,timeout=120)
 logs.append(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(logs[-1])
(D/'simulation.log').write_text('\n'.join(logs))
assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (nav,top)}
report={'passed':True,'cycles':50000,'source_sha256':hashes,'commands':commands,'scope':'Extracted exact RTL snapshot bank and output mask only; not full top/UART or synthesized equivalence','top_invariant':'boot initialized 0, saturates at255; rst_n=(boot==255), no other boot assignments','origin_reset':'Not a snapshot-bank input. Arbitrary 720-bit diagnostic_next changes cover upstream origin effects; no integrated origin-reset simulation claimed.','init_acceptance_required':'Compare all retained diagnostic_q physical FF INIT bits and output mappings before/after Gowin, including DFFSE-to-DFFE changes, constant-folded bits and RESET_DIAGNOSTIC. Confirm no shared control/history changes, reset removal and correct CE gating. Run full-top exact UART bytes/acceptance cycles/hold comparison before acceptance.'}
(D/'proof.json').write_text(json.dumps(report,indent=2))
print(logs[-1])
