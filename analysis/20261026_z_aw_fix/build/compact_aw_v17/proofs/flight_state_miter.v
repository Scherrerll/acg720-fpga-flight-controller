`timescale 1ns/1ps
module pair #(parameter T=1)(input clk,rst_n,armed,input[15:0] ch3,hold_collective_us,fallback_unmasked_collective,input height_fallback_active,
 output reg saw_prepared,saw_takeoff,saw_flying,saw_land);
initial begin saw_prepared=0;saw_takeoff=0;saw_flying=0;saw_land=0;end
wire[15:0] fallback_collective=height_fallback_active ?fallback_unmasked_collective:16'd1000;
wire[15:0] selected_throttle=height_fallback_active ?fallback_collective:hold_collective_us;
    (* syn_keep = 1 *) wire fallback_collective_below_landing=fallback_unmasked_collective<1250;
    (* syn_keep = 1 *) wire auto_collective_below_landing=hold_collective_us<1250;
    wire selected_collective_below_landing=height_fallback_active ?fallback_collective_below_landing:auto_collective_below_landing;
legacy_ano_flight_state #(.TICKS_PER_MS(T)) old(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle));
ano_flight_state #(.TICKS_PER_MS(T)) def(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(1'b0));
ano_flight_state #(.TICKS_PER_MS(T),.PRECHECKED_COLLECTIVE(1)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(selected_collective_below_landing));
wire[80:0] ov={old.phase,old.half,old.preparation_ms,old.flying_ms,old.landing_ms,old.landing_delay,old.normal_unlock,old.motor_prepared,old.taking_off,old.flying,old.land_lock,old.preparation_mask};
wire[80:0] dv={dut.phase,dut.half,dut.preparation_ms,dut.flying_ms,dut.landing_ms,dut.landing_delay,dut.normal_unlock,dut.motor_prepared,dut.taking_off,dut.flying,dut.land_lock,dut.preparation_mask};
wire[80:0] fv={def.phase,def.half,def.preparation_ms,def.flying_ms,def.landing_ms,def.landing_delay,def.normal_unlock,def.motor_prepared,def.taking_off,def.flying,def.land_lock,def.preparation_mask};
always @(posedge clk)begin
 #1;
 if(ov!==dv || ov!==fv)$fatal(1,"FSM mismatch T=%0d old=%h new=%h default=%h",T,ov,dv,fv);
 if(selected_collective_below_landing!==(selected_throttle<1250))$fatal(1,"threshold distributivity mismatch T=%0d",T);
 if(old.motor_prepared)saw_prepared<=1;if(old.taking_off)saw_takeoff<=1;if(old.flying)saw_flying<=1;if(old.land_lock)saw_land<=1;
end
endmodule
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,armed=0,active=0;
reg[15:0] ch3=1000,auto_value=1000,unmasked=1000;
wire[3:0] p1,p3,p7;
pair #(.T(1)) a(clk,rst_n,armed,ch3,auto_value,unmasked,active,p1[3],p1[2],p1[1],p1[0]);
pair #(.T(3)) b(clk,rst_n,armed,ch3,auto_value,unmasked,active,p3[3],p3[2],p3[1],p3[0]);
pair #(.T(7)) c(clk,rst_n,armed,ch3,auto_value,unmasked,active,p7[3],p7[2],p7[1],p7[0]);
reg healthy=0,height=1,automatic_valid=0;
wire actual_active;wire[15:0] actual_public,actual_unmasked;
height_loss_fallback #(.SLEW_TICKS(3)) fall(.clk(clk),.rst_n(rst_n),.healthy(healthy),.armed(armed),.taking_off(a.old.taking_off),.height_available(height),.automatic_valid(automatic_valid),.automatic_collective_us(auto_value),.ch3(ch3),.active(actual_active),.collective_us(actual_public),.unmasked_collective_us(actual_unmasked));
integer cycles=0,k,j;reg saw_actual_fallback=0;
reg[31:0] rng=32'h6d15a3c7;
function[15:0] boundary;input integer i;begin case(i)
0:boundary=0;1:boundary=1000;2:boundary=1249;3:boundary=1250;4:boundary=1251;5:boundary=1850;6:boundary=2000;default:boundary=65535;
endcase end endfunction
always @(posedge clk)begin
 #2;cycles=cycles+1;
 if(actual_active)begin saw_actual_fallback=1;if(actual_public!==actual_unmasked)$fatal(1,"active public/unmasked implication failed");end
 if(((actual_active ?actual_public:auto_value)<1250)!==(actual_active ?(actual_unmasked<1250):(auto_value<1250)))$fatal(1,"actual fallback comparison failed");
end
task run;input integer n;integer i;begin for(i=0;i<n;i=i+1)@(negedge clk);end endtask
initial begin
 run(4);rst_n=1;armed=1;healthy=1;automatic_valid=1;ch3=1800;auto_value=1400;unmasked=1400;
 run(21000);height=0;active=1;run(400);ch3=1000;auto_value=1249;unmasked=1249;
 run(8000);unmasked=1250;run(70);unmasked=1249;run(14000);
 if(p1!==15 || p3!==15 || p7!==15 || !saw_actual_fallback)$fatal(1,"directed flight/preparation/landing/fallback coverage missing %b %b %b %b",p1,p3,p7,saw_actual_fallback);
 armed=0;run(17);rst_n=0;run(3);rst_n=1;
 // Every16bit value in both numeric branches, against eight independent opposite-branch boundaries and both selections.
 for(k=0;k<65536;k=k+1)begin
  for(j=0;j<8;j=j+1)begin
   auto_value=k;unmasked=boundary(j);active=0;run(1);active=1;run(1);
   auto_value=boundary(j);unmasked=k;active=0;run(1);active=1;run(1);
  end
 end
 // General state/input transitions, resets and revocation, reproducible LFSR stream.
 for(k=0;k<100000;k=k+1)begin
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  rst_n=(k%997)!=0;armed=rng[0];active=rng[1];healthy=rng[2];height=rng[3];automatic_valid=rng[4];
  ch3=rng[31:16];auto_value=rng[15:0];unmasked=rng[31:16];run(1);
 end
 $display("PASS v17 completeFSM old/new/default T=1/3/7, all state bits, directed preparation/takeoff/flying/landing/revoke, actual fallback implication, 2097152 threshold vectors,100000 random transitions cycles=%0d",cycles);$finish;
end
initial begin #60000000;$fatal(1,"miter timeout cycles=%0d",cycles);end
endmodule
