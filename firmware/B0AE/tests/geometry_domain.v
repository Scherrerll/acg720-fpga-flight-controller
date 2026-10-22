
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg rst_n=0,sample=0,range_ok=1,flow_ok=1;
reg signed[15:0]roll=0,pitch=0;
wire update,hr,fr,ms,mc,mb,md;wire signed[31:0]height;wire signed[63:0]ma,mba,mr;
mtf_shared_geometry #(.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500)) dut(
 .clk(clk),.rst_n(rst_n),.origin_reset(1'b0),.sample_valid(sample),.range_valid(range_ok),.flow_valid(flow_ok),
 .distance_mm(32'd1000),.dt_ms(32'd10),.vx_x100(32'sd12345),.vy_x100(-32'sd54321),
 .pose_valid(1'b1),.pose_age_ticks(32'd0),.roll_cdeg(roll),.pitch_cdeg(pitch),.body_yaw_cdeg(16'sd0),.body_yaw_range_ok(1'b1),
 .update(update),.height_ready(hr),.flow_ready(fr),.height_mm(height),
 .math_mul_start(ms),.math_mul_cancel(mc),.math_mul_a(ma),.math_mul_b(mba),.math_mul_busy(mb),.math_mul_done(md),.math_mul_result(mr));
nav_math_service #(.DIVIDE(0),.CLIENTS(1)) mul(.clk(clk),.rst_n(rst_n),.request(ms),.cancel(mc),.operand_a(ma),.operand_b(mba),.busy(mb),.done(md),.error(),.result(mr),.grant());
integer r,p,n=0;real expected,error,maxerror=0;
task frame;
begin
 @(negedge clk);sample=1;@(negedge clk);sample=0;
 wait(update);@(negedge clk);
end endtask
initial begin
 repeat(4)@(negedge clk);rst_n=1;repeat(4)@(negedge clk);
 for(r=-4500;r<=4500;r=r+1500)for(p=-4500;p<=4500;p=p+1500)begin
  roll=r;pitch=p;frame();
  expected=1000*$cos(r*3.141592653589793/18000)*$cos(p*3.141592653589793/18000);
  error=height-expected;if(error<0)error=-error;if(error>maxerror)maxerror=error;
  if(!hr || error>3)$fatal(1,"height tilt domain r=%d p=%d height=%d error=%f",r,p,height,error);
  if(fr !== (r>=-1500 && r<=1500 && p>=-1500 && p<=1500))$fatal(1,"independent flow qualification");
  n=n+1;
 end
 roll=0;pitch=0;frame();flow_ok=0;#1;if(!hr || fr)$fatal(1,"flow loss must preserve height");
 frame();if(!hr || fr)$fatal(1,"height publication while flow unavailable");
 range_ok=0;#1;if(hr || fr)$fatal(1,"range loss immediate revoke");
 repeat(4)@(negedge clk);range_ok=1;flow_ok=1;repeat(4)@(negedge clk);frame();if(!hr || !fr)$fatal(1,"range recovery");
 roll=4501;#1;if(hr || fr)$fatal(1,"outside45deg remains ineligible");
 $display("GEOMETRY_DOMAIN_PASS %d roll/pitch pairs, maxerror=%fmm; flow loss preserves Z; range/tilt revoke",n,maxerror);$finish;
end
initial begin #100000000;$fatal(1,"geometry timeout");end
endmodule
