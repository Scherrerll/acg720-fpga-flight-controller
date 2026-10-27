`timescale 1ns/1ps
`default_nettype none
module extension_bram_tb;
 reg clk=0;always #10 clk=~clk; // Original 50MHz clock.
 reg enable=0;reg[887:0]data=0;
 reg[887:0]reference_q=0;
 wire[887:0]q;
 GSR GSR(.GSRI(1'b1));
 gw5_snapshot_bram #(.WIDTH(888)) dut(.clk(clk),.enable(enable),.data(data),.q(q));
 always @(posedge clk)if(enable)reference_q<=data;
 integer cycles=0,writes=0,holds=0,unknown_enable_holds=0,x_payload_writes=0,z_payload_writes=0;
 integer checks=0,offedge_checks=0,walking_bits=0,random_vectors=0;
 reg[31:0]rng=32'h16c3bd71;
 reg[887:0]value;
 integer i,j,k;
 time last_rise=0;
 genvar bank;
 generate for(bank=0;bank<28;bank=bank+1)begin:real_sp_contract
  initial begin
   #1;
   if(dut.hardware_bram.banks[bank].memory.BIT_WIDTH!==32 ||
      dut.hardware_bram.banks[bank].memory.READ_MODE!==1'b0 ||
      dut.hardware_bram.banks[bank].memory.WRITE_MODE!==2'b01 ||
      dut.hardware_bram.banks[bank].memory.RESET_MODE!="SYNC")
    $fatal(1,"Actual SP parameters differ bank=%0d",bank);
  end
 end endgenerate
 task check;begin
  checks=checks+1;
  if(q!==reference_q)$fatal(1,"BRAM/FF mismatch cycle=%0d enable=%b q=%h reference=%h",cycles,enable,q,reference_q);
  if(dut.hardware_bram.padded_q[895:888]!==8'd0)$fatal(1,"Last physical bank padding is not zero");
 end endtask
 always @(posedge clk)begin
  last_rise=$time;cycles=cycles+1;
  if(enable===1'b1)begin
   writes=writes+1;
   if(data==={888{1'bx}})x_payload_writes=x_payload_writes+1;
   if(data==={888{1'bz}})z_payload_writes=z_payload_writes+1;
  end else begin holds=holds+1;if(enable===1'bx || enable===1'bz)unknown_enable_holds=unknown_enable_holds+1;end
  #1;check();
 end
 always @(negedge clk)begin #1;check();offedge_checks=offedge_checks+1;end
 // Public output may settle in delta cycles at a write edge, never midcycle.
 always @(q)begin
  if($time>1 && $time!=last_rise)$fatal(1,"BRAM public output changed away from rising edge time=%0t",$time);
 end
 task drive;input e;input[887:0]d;begin
  @(negedge clk);enable=e;data=d;
  #9;check();offedge_checks=offedge_checks+1; // Before the next enabled edge.
  @(posedge clk);#2;check(); // Same edge, with no extra output clock.
 end endtask
 task random_data;integer n;begin
  value=0;
  for(n=0;n<28;n=n+1)begin
   rng=rng*32'd1664525+32'd1013904223;
   if(n<27)value[n*32+:32]=rng;else value[887:864]=rng[23:0];
  end
 end endtask
 initial begin
  #1;
  if(dut.SIMULATION_BYPASS!==0)$fatal(1,"Portable FF bypass selected; vendor proof invalid");
  check();if(q!==888'd0 || reference_q!==888'd0)$fatal(1,"Initial output before first clock is not zero");
  #2;data={888{1'b1}};#1;check(); // No startup read/write used to manufacture INIT0.
  drive(0,0);drive(1,0);drive(1,{888{1'b1}});drive(0,0);
  for(i=0;i<888;i=i+1)begin
   value=0;value[i]=1'b1;drive(1,value);walking_bits=walking_bits+1;
   drive(0,~value);drive(1,~value);
  end
  // Exercise every bank/byte boundary, including the 24-bit final bank.
  for(i=0;i<112;i=i+1)begin
   value=0;
   for(j=0;j<8;j=j+1)if(i*8+j<888)value[i*8+j]=1'b1;
   drive(1,value);drive(0,~value);drive(1,~value);
  end
  // Verilog if treats X/Z enable as no update; SP CE must preserve that behavior.
  drive(1,{888{1'b1}});drive(1'bx,0);drive(1'bz,0);drive(0,{888{1'bx}});
  drive(1,{888{1'bx}});drive(0,0);drive(1'bx,{888{1'b1}});drive(1'bz,{888{1'b1}});
  drive(1,{888{1'bz}});drive(0,0);drive(1'bx,{888{1'bx}});drive(1'bz,{888{1'bx}});
  value=0;for(i=0;i<888;i=i+1)case(i%4)0:value[i]=0;1:value[i]=1;2:value[i]=1'bx;3:value[i]=1'bz;endcase
  drive(1,value);drive(0,~value);drive(1'bx,~value);drive(1'bz,~value);drive(1,0);
  for(k=0;k<16000;k=k+1)begin
   random_data();random_vectors=random_vectors+1;
   case(k%11)
    0,1:drive(0,value);
    2:drive(1'bx,value);
    3:drive(1'bz,value);
    default:drive(1,value);
   endcase
  end
  // Long initial-style hold after a nonzero write; repeated input activity cannot leak.
  drive(1,{888{1'b1}});
  for(k=0;k<257;k=k+1)begin random_data();drive(0,value);end
  drive(1,0);drive(0,{888{1'b1}});
  if(walking_bits!=888 || random_vectors!=16000 || x_payload_writes<1 || z_payload_writes<1 || unknown_enable_holds<1000 || writes<10000 || holds<5000 || checks<50000)
   $fatal(1,"Proof coverage incomplete cycles=%0d writes=%0d holds=%0d unknown_holds=%0d checks=%0d",cycles,writes,holds,unknown_enable_holds,checks);
  $display("PASS WIDTH=888 actual_SP=28 GSR=1 SIMULATION_BYPASS=0 CLK_HZ=50000000 initial_before_first_clock=0 same_edge_capture=1 cycles=%0d writes=%0d holds=%0d unknown_enable_holds=%0d walking_bits=%0d random_vectors=%0d X_payload_writes=%0d Z_payload_writes=%0d checks=%0d offedge_checks=%0d no_DUT_force_or_preload=1",cycles,writes,holds,unknown_enable_holds,walking_bits,random_vectors,x_payload_writes,z_payload_writes,checks,offedge_checks);$finish;
 end
 initial begin #1000000;$fatal(1,"Bounded standalone proof timeout");end
endmodule
`default_nettype wire
