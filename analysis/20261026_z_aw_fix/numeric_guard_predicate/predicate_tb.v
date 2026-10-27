`timescale 1ns/1ps
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
