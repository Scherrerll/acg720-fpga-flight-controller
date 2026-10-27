`timescale 1ns/1ps
module tb;
reg clk=0,rst_n=0,sample_update=0,position_update=0,height_update=0;
reg signed[31:0]vx=0,vy=0;
always #10 clk=~clk;
wire signed[15:0]nr,np,br,bp,nd,bd;wire signed[63:0]nix,niy,bix,biy;
wire pub,bpub,zpub,bzpub,blocked,bb,active,ba;wire[15:0]nc,bc;
wire signed[31:0]nz,bz,nh,bh;
contended candidate(clk,rst_n,sample_update,position_update,height_update,vx,vy,nr,np,nix,niy,pub,zpub,blocked,active,nc,nd,nz,nh);
isolated baseline(clk,rst_n,sample_update,position_update,height_update,vx,vy,br,bp,bix,biy,bpub,bzpub,bb,ba,bc,bd,bz,bh);
integer cycles=0,samples=0,npubs=0,bpubs=0,nzpubs=0,bzpubs=0,xychecked=0,zchecked=0;
integer input_start=0,work_start=0,zinput_start=0,max_xy_total=0,max_xy_work=0,max_z_total=0,latency;
reg awaiting_xy=0,awaiting_z=0,previous_work=0,saw_i=0,saw_active=0,saw_z_i=0;
reg signed[15:0] broll[0:31],bpitch[0:31];reg signed[63:0]bx[0:31],by[0:31];
reg[95:0]bheight[0:127],nheight[0:127];
always @(negedge clk)begin
 sample_update<=0;position_update<=0;height_update<=0;
 if(rst_n)begin
  cycles=cycles+1;
  // 10x faster input arrival than physical time, but retain nominal dt:
  // 1ms sticks, 11ms Z callback and 20ms XY callback. This is intentionally
  // more contention pressure than the nominal real callback cadence.
  if(cycles%5000==0)begin
   samples=samples+1;sample_update<=1;
   if(samples%11==0)height_update<=1;
   if(samples%20==0)position_update<=1;
  end
 end
end
always @(posedge clk)begin #1;
 if(rst_n)begin
  if(blocked || bb)$fatal(1,"controller blocked: candidate reason=%0d/%0d baseline=%0d/%0d",candidate.dut.reason,candidate.dut.height_reason,baseline.dut.reason,baseline.dut.height_reason);
  if(position_update && candidate.dut.tracking && !candidate.dut.xy_cancel)begin
   if(awaiting_xy)$fatal(1,"XY input overlapped uncompleted callback");
   awaiting_xy=1;input_start=cycles;
  end
  // The first height update establishes tracking/origin and is not a Z
  // calculation. Only height_due marks an accepted calculation request.
  if(height_update && candidate.dut.height_due && !candidate.dut.cancel)begin
   if(awaiting_z)$fatal(1,"height input overlapped uncompleted callback");
   awaiting_z=1;zinput_start=cycles;
  end
  if(candidate.dut.work_xy && !previous_work)work_start=cycles;
  previous_work=candidate.dut.work_xy;
  if(bpub)begin broll[bpubs]=br;bpitch[bpubs]=bp;bx[bpubs]=bix;by[bpubs]=biy;bpubs=bpubs+1;end
  if(pub)begin
   if(npubs>=bpubs)$fatal(1,"isolated callback is not available");
   if(nr!==broll[npubs] || np!==bpitch[npubs] || nix!==bx[npubs] || niy!==by[npubs])$fatal(1,"contention changed callback n=%0d angles=%0d,%0d baseline=%0d,%0d I=%0d,%0d vs%0d,%0d",npubs,nr,np,broll[npubs],bpitch[npubs],nix,niy,bx[npubs],by[npubs]);
   if(!awaiting_xy)$fatal(1,"XY publication has no request");
   latency=cycles-input_start;if(latency>max_xy_total)max_xy_total=latency;
   latency=cycles-work_start;if(latency>max_xy_work)max_xy_work=latency;
   awaiting_xy=0;npubs=npubs+1;xychecked=xychecked+1;
   if(nix!=0 && niy!=0)saw_i=1;
   if(active)saw_active=1;
   $display("XY n=%0d roll=%0d pitch=%0d I=%0d,%0d total_clocks=%0d work_clocks=%0d",npubs,nr,np,nix,niy,cycles-input_start,cycles-work_start);$fflush();
  end
  if(bzpub)begin bheight[bzpubs]={bc,bd,bz,bh};bzpubs=bzpubs+1;end
  if(zpub)begin
   if(candidate.dut.iz!=0)saw_z_i=1;
   nheight[nzpubs]={nc,nd,nz,nh};nzpubs=nzpubs+1;
   if(!awaiting_z)$fatal(1,"Z publication has no request");
   latency=cycles-zinput_start;if(latency>max_z_total)max_z_total=latency;
   awaiting_z=0;
  end
  while(zchecked<nzpubs && zchecked<bzpubs)begin
   if(nheight[zchecked]!==bheight[zchecked])$fatal(1,"height callback changed n=%0d candidate=%h baseline=%h",zchecked,nheight[zchecked],bheight[zchecked]);
   zchecked=zchecked+1;
  end
 end
end
task pubs;input integer n;integer target;begin target=npubs+n;wait(npubs>=target);@(negedge clk);end endtask
integer k;
initial begin
 repeat(8)@(negedge clk);rst_n=1;
 pubs(2);vx=400*65536;vy=-600*65536;pubs(4);
 vx=-400*65536;vy=600*65536;pubs(4);
 vx=0;vy=0;pubs(2);
 if(!saw_i || !saw_active || !saw_z_i || xychecked!=12 || zchecked<10)$fatal(1,"insufficient control evidence");
 if(max_xy_total>=1000000 || max_z_total>=55000)$fatal(1,"callback exceeded deadline");
 for(k=0;k<3;k=k+1)begin
  if(candidate.mcounts[k]<100 || candidate.dcounts[k]<100)$fatal(1,"dummy client not continuously serviced");
  $display("DUMMY client=%0d multiply_completions=%0d divide_completions=%0d",k,candidate.mcounts[k],candidate.dcounts[k]);
 end
 $display("PASS XY_callbacks=%0d Z_callbacks=%0d max_XY_request_to_publish_clocks=%0d max_XY_work_clocks=%0d max_Z_request_to_publish_clocks=%0d ns_per_clock=20",xychecked,zchecked,max_xy_total,max_xy_work,max_z_total);$fflush();$finish;
end
initial begin #40000000;$fatal(1,"contention timeout XY=%0d Z=%0d state=%0d",npubs,nzpubs,candidate.dut.state);end
endmodule
module contended(input wire clk,rst_n,sample_update,position_update,height_update,
 input wire signed[31:0]vx,vy,
 output wire signed[15:0]roll,pitch,output wire signed[63:0]ix,iy,
 output wire published,zpublished,blocked,active,output wire[15:0]collective,
 output wire signed[15:0]delta,output wire signed[31:0]climb,height);
 wire enabled=1,rc_valid=1,taking_off=1,origin=0,sensor_valid=1;wire[15:0]ch7=2000;
 wire mreq,mcancel,dreq,dcancel;wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
 wire[3:0]mbusy,mdone,merror,dbusy,ddone,derror;
 mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
 .xy_p_value(16'd1250),.xy_i_value(16'd2500),.parameter_boundary(),
 
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1600),.ch4(16'd1500),.ch7(ch7),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),
 .acc_valid(sensor_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),
 .auto_takeoff(),.reason(),.height_reason(),.collective_target_us(collective),
 .roll_target(roll),.pitch_target(pitch),.throttle_delta(delta),.requested_climb_mmps(climb),.target_height_mm(height),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy[3]),.math_mul_done(mdone[3]),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy[3]),.math_div_done(ddone[3]),.math_div_error(derror[3]),.math_div_result(dresult));
 
 // Each dummy reissues only after busy withdraws; operands stay constant
 // throughout acceptance, queue wait, ownership, completion and reissue.
 wire[3:0]mr={mreq,~mbusy[2:0]},dr={dreq,~dbusy[2:0]};
 wire[3:0]mc={mcancel,3'b000},dc={dcancel,3'b000};
 wire[255:0]m_a={ma,64'sd2147483647,-64'sd6789,64'sd123456789};
 wire[255:0]m_b={mb,-64'sd7,64'sd12345,64'sd37};
 wire[255:0]d_a={da,64'sd9000000000,-64'sd840000,64'sd1234567890};
 wire[255:0]d_b={{32'd0,db},64'd300,64'd32,64'd10};
 integer mcounts[0:2],dcounts[0:2];integer k;
 initial for(k=0;k<3;k=k+1)begin mcounts[k]=0;dcounts[k]=0;end
 always @(posedge clk)begin #1;
  if(rst_n)begin
   for(k=0;k<3;k=k+1)begin
    if(mdone[k])begin
     mcounts[k]=mcounts[k]+1;
     if(mresult!==(k==0?64'sd4567901193:k==1?-64'sd83810205:-64'sd15032385529))$fatal(1,"dummy multiplication corrupt client=%0d result=%0d",k,mresult);
    end
    if(ddone[k])begin
     dcounts[k]=dcounts[k]+1;
     if(derror[k] || dresult!==(k==0?64'sd123456789:k==1?-64'sd26250:64'sd30000000))$fatal(1,"dummy division corrupt client=%0d result=%0d",k,dresult);
    end
   end
   if(merror[3] || derror[3])$fatal(1,"controller service error");
  end
 end

 nav_math_service #(.CLIENTS(4),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mr),.cancel(mc),
 .operand_a(m_a),.operand_b(m_b),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(4),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dr),.cancel(dc),
 .operand_a(d_a),.operand_b(d_b),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 assign ix=dut.ix;assign iy=dut.iy;assign blocked=dut.blocked||dut.xy_blocked;
 assign published=dut.command_seen && dut.command_age==0;
 assign zpublished=dut.height_command_seen && dut.height_command_age==0;
 endmodule
module isolated(input wire clk,rst_n,sample_update,position_update,height_update,
 input wire signed[31:0]vx,vy,
 output wire signed[15:0]roll,pitch,output wire signed[63:0]ix,iy,
 output wire published,zpublished,blocked,active,output wire[15:0]collective,
 output wire signed[15:0]delta,output wire signed[31:0]climb,height);
 wire enabled=1,rc_valid=1,taking_off=1,origin=0,sensor_valid=1;wire[15:0]ch7=2000;
 wire mreq,mcancel,dreq,dcancel;wire signed[63:0]ma,mb,mresult,da,dresult;wire[31:0]db;
 wire[0:0]mbusy,mdone,merror,dbusy,ddone,derror;
 mtf_xyz_hold_control #(.CAL_MASK(8'hff),.VELOCITY_FRAC_BITS(16))dut(
 .xy_p_value(16'd1250),.xy_i_value(16'd2500),.parameter_boundary(),
 
 .clk(clk),.rst_n(rst_n),.origin_reset(origin),.rc_valid(rc_valid),.channel_count(4'd8),
 .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1600),.ch4(16'd1500),.ch7(ch7),
 .enabled(enabled),.taking_off(taking_off),.position_valid(sensor_valid),.height_valid(sensor_valid),
 .position_update(position_update),.height_update(height_update),
 .sample_update(sample_update),.sample_dt_us(32'd1000),.position_age(32'd0),.position_dt_us(32'd20000),
 .x_q8(32'sd0),.y_q8(32'sd0),.vx(vx),.vy(vy),.height_mm(32'sd1000),.vz(32'sd0),.yaw_cdeg(16'sd0),
 .acc_valid(sensor_valid),.ax_mmps2(32'sd0),.ay_mmps2(32'sd0),.az_mmps2(32'sd0),.collective_us(16'd1500),
 .requested(),.ready(),.active(active),.height_requested(),.height_ready(),.height_active(),
 .auto_takeoff(),.reason(),.height_reason(),.collective_target_us(collective),
 .roll_target(roll),.pitch_target(pitch),.throttle_delta(delta),.requested_climb_mmps(climb),.target_height_mm(height),
 .pilot_norm_x(),.pilot_norm_y(),.pilot_norm_update(),.pilot_norm_valid(),.pilot_norm_dt_us(),
 .math_mul_start(mreq),.math_mul_cancel(mcancel),.math_mul_a(ma),.math_mul_b(mb),
 .math_mul_busy(mbusy[0]),.math_mul_done(mdone[0]),.math_mul_result(mresult),
 .math_div_start(dreq),.math_div_cancel(dcancel),.math_div_numerator(da),.math_div_denominator(db),
 .math_div_busy(dbusy[0]),.math_div_done(ddone[0]),.math_div_error(derror[0]),.math_div_result(dresult));
 
 wire[0:0]mr=mreq,dr=dreq,mc=mcancel,dc=dcancel;
 wire[63:0]m_a=ma,m_b=mb,d_a=da,d_b={32'd0,db};

 nav_math_service #(.CLIENTS(1),.DIVIDE(0))mul(.clk(clk),.rst_n(rst_n),.request(mr),.cancel(mc),
 .operand_a(m_a),.operand_b(m_b),.busy(mbusy),.done(mdone),.error(merror),.result(mresult),.grant());
 nav_math_service #(.CLIENTS(1),.DIVIDE(1))div(.clk(clk),.rst_n(rst_n),.request(dr),.cancel(dc),
 .operand_a(d_a),.operand_b(d_b),.busy(dbusy),.done(ddone),.error(derror),.result(dresult),.grant());
 assign ix=dut.ix;assign iy=dut.iy;assign blocked=dut.blocked||dut.xy_blocked;
 assign published=dut.command_seen && dut.command_age==0;
 assign zpublished=dut.height_command_seen && dut.height_command_age==0;
 endmodule
