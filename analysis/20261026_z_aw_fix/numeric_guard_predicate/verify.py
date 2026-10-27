"""Check the actual v6 two-state range predicates; record the X caveat."""
from pathlib import Path
import hashlib, json, os, re, subprocess

O=Path(__file__).resolve().parent
R=O.parents[2]
S=R/'out/z_aw_fix_20261026/compact_aw_v6/canonical/source'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
B=Path(r'C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['position/mtf_shared_height_fusion.v','mtf_xyz_navigation_control.v']
expected=['69b386c20fc04ce24904ad871d8e36168d4ea8e813f3eccb3b48b8cea90b2dc0','f826345ebd2c2fa97477042b0eaea8aa888683911c95cb3907314ebcfc508fea']
assert [sha(S/n) for n in names]==expected
before={str(root):{p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()} for root in (S,OLD)}
assert all(len(x)==55 for x in before.values())
(O/'inputs.json').write_text(json.dumps(before,indent=2)+'\n')
modules=[]
for i,n in enumerate(names):
    text=(S/n).read_text()
    fs=re.findall(r'function accel_in_range;.*?endfunction',text,re.S)
    assert len(fs)==1
    modules.append(f'module predicate_{i}(input signed[31:0]x,output result);\n'+fs[0]+'\nassign result=accel_in_range(x);\nendmodule\n')
(O/'actual_functions.v').write_text(''.join(modules))
tb=r'''`timescale 1ns/1ps
module tb;
reg signed[31:0]x=0;wire h,w;
wire ref_ok=x>=-32'sd30000 && x<=32'sd30000;
predicate_0 height_fn(x,h);predicate_1 wrapper_fn(x,w);
integer lo,hi,j,k,checked=0;reg[15:0]upper,lower;reg[31:0]rng=32'h472dca19;
task check;begin #1;if(h!==ref_ok || w!==ref_ok)$fatal(1,"known-value mismatch x=%h ref=%b h=%b w=%b",x,ref_ok,h,w);checked=checked+1;end endtask
initial begin
 // All low words for both possible sign-extended uppers and six bad uppers.
 for(j=0;j<8;j=j+1)begin
  case(j)0:upper=0;1:upper=16'hffff;2:upper=1;3:upper=16'hfffe;4:upper=16'h7fff;5:upper=16'h8000;6:upper=16'h5555;7:upper=16'haaaa;endcase
  for(lo=0;lo<65536;lo=lo+1)begin x={upper,lo[15:0]};check;end
 end
 // All high words with threshold neighbours, sign edges, and zero.
 for(k=0;k<12;k=k+1)begin
  case(k)0:lower=0;1:lower=1;2:lower=16'd29999;3:lower=16'd30000;4:lower=16'd30001;5:lower=16'h7fff;
   6:lower=16'h8000;7:lower=-16'sd30001;8:lower=-16'sd30000;9:lower=-16'sd29999;10:lower=16'hffff;11:lower=16'hfffe;endcase
  for(hi=0;hi<65536;hi=hi+1)begin x={hi[15:0],lower};check;end
 end
 for(j=0;j<100000;j=j+1)begin rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);x=rng;check;end
 $display("PASS two-state actual_functions=2 checked_vectors=%0d",checked);
 x={16'h0001,16'b000000000000000x};#1;
 if(ref_ok!==1'bx || h!==1'b0 || w!==1'b0)$fatal(1,"X qualification example changed");
 $display("EXPECTED_FOUR_STATE_DIFFERENCE original=X factored=0; equivalence claim is two-state only");
 $finish;
end
endmodule
'''
(O/'predicate_tb.v').write_text(tb)
tmp=O/'tmp';tmp.mkdir(exist_ok=True)
env=dict(os.environ,TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
c=subprocess.run([str(B/'iverilog.exe'),'-g2012','-s','tb','-o',str(O/'predicate.vvp'),str(O/'predicate_tb.v'),str(O/'actual_functions.v')],capture_output=True,text=True,env=env)
(O/'compile.log').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stdout+c.stderr
with (O/'simulation.log').open('w') as log:
    c=subprocess.run([str(B/'vvp.exe'),str(O/'predicate.vvp')],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=180)
text=(O/'simulation.log').read_text();print(text,flush=True)
assert c.returncode==0 and 'checked_vectors=1410720' in text and 'EXPECTED_FOUR_STATE_DIFFERENCE' in text
assert before=={str(root):{p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()} for root in (S,OLD)}
out={'passed':True,'actual_exit_code':c.returncode,'two_actual_source_functions':2,'known_vectors':1410720,'source55_before_after_unchanged':True,
 'scope':'Two-state proof plus finite RTL enumeration; all low16 for8 high words, all high16 for12 boundary lows,100000 deterministic random full32. This is not enumeration of all2^32; algebraic sign-extension proof covers remaining pairs. Four-state X difference deliberately demonstrated, not hidden.',
 'sha256':{p.name:sha(p) for p in [Path(__file__),O/'inputs.json',O/'actual_functions.v',O/'predicate_tb.v',O/'compile.log',O/'simulation.log']}}
(O/'results.json').write_text(json.dumps(out,indent=2)+'\n')
