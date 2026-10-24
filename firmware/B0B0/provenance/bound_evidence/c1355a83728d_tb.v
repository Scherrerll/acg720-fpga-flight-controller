module tb;
reg clk50=0;always #5 clk50=~clk50;
 reg [7:0] boot=0;always @(posedge clk50) if(boot!=255) boot<=boot+1'b1;
 wire rst_n=boot==255;
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
