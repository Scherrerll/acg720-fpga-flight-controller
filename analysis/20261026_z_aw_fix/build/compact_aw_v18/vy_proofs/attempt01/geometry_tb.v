`timescale 1ns/1ps
`default_nettype none
module geometry_pair #(parameter SWAP=0,NX=0,NY=0)(
 input wire clk,rst_n,origin_reset,sample_valid,range_valid,flow_valid,pose_valid,
 input wire[31:0]distance_mm,dt_ms,input wire signed[31:0]vx_x100,vy_x100,
 input wire signed[15:0]roll_cdeg,pitch_cdeg,body_yaw_cdeg,input wire wrong_select,
 output wire hr,fr,busy,update);
 wire correct_predicate=vx_x100>=-32'sd1000000 && vx_x100<=32'sd1000000 && vy_x100>=-32'sd1000000 && vy_x100<=32'sd1000000;
 wire irrelevant_predicate=wrong_select ?1'bx:!correct_predicate;
 wire old_ms,old_mc,old_mb,old_md;wire signed[63:0]old_ma,old_mba,old_mr;
 old_mtf_shared_geometry #(.AGE_LIMIT(4096),.MAX_COMPUTE_TICKS(4000),.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500),.SWAP_AXES(SWAP),.NEGATE_X(NX),.NEGATE_Y(NY)) old(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),.range_valid(range_valid),.flow_valid(flow_valid),.pose_valid(pose_valid),
 .distance_mm(distance_mm),.dt_ms(dt_ms),.vx_x100(vx_x100),.vy_x100(vy_x100),
 .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(body_yaw_cdeg),.body_yaw_range_ok(1'b0),.body_tilt4500_ok(1'b0),.body_tilt1500_ok(1'b0),
 .math_mul_start(old_ms),.math_mul_cancel(old_mc),.math_mul_a(old_ma),.math_mul_b(old_mba),.math_mul_busy(old_mb),.math_mul_done(old_md),.math_mul_result(old_mr));
 nav_math_service #(.DIVIDE(0),.CLIENTS(1)) math_old(.clk(clk),.rst_n(rst_n),.request(old_ms),.cancel(old_mc),.operand_a(old_ma),.operand_b(old_mba),.busy(old_mb),.done(old_md),.error(),.result(old_mr),.grant());
 wire[511:0] public_old={old.update,old.height_ready,old.flow_ready,old.reason,old.height_mm,old.body_vx_q16,old.body_vy_q16,old.world_vx_q16,old.world_vy_q16,old.dt_us,old.busy,old.mapping_verified,old.rotation_compensated,old.control_verified,old.math_mul_start,old.math_mul_cancel,old.math_mul_a,old.math_mul_b,old.height_ready_state_numeric_tail,old.height_ready_state_numeric_tail_without_live_flags};
 wire[2047:0] state_old={old.seen,old.flow_seen,old.transaction_epoch_ok,old.flow_epoch_ok,old.output_velocity_fault,old.pending_velocity_fault,old.publication_age,old.compute_age,old.fault,old.state,old.return_state,old.private_cancel,old.held_pitch,old.held_yaw,old.held_distance,old.held_dt,old.held_vx100_store,old.held_vy100_store,old.cr,old.cp,old.cy,old.sy,old.pending_height_store,old.pending_bx_store,old.pending_by_store,old.pending_wx_store,old.pending_wy_store,old.rot_tmp_store,old.mul_start,old.div_start,old.trig_start,old.ma_store,old.value_store,old.mb_store,old.num_store,old.scale_mode,old.angle_q20};
 wire checked_ms,checked_mc,checked_mb,checked_md;wire signed[63:0]checked_ma,checked_mba,checked_mr;
 new_mtf_shared_geometry #(.AGE_LIMIT(4096),.MAX_COMPUTE_TICKS(4000),.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500),.SWAP_AXES(SWAP),.NEGATE_X(NX),.NEGATE_Y(NY),.PRECHECKED_INPUT_VELOCITY(1)) checked(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),.range_valid(range_valid),.flow_valid(flow_valid),.pose_valid(pose_valid),
 .distance_mm(distance_mm),.dt_ms(dt_ms),.vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(correct_predicate),
 .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(body_yaw_cdeg),.body_yaw_range_ok(1'b0),.body_tilt4500_ok(1'b0),.body_tilt1500_ok(1'b0),
 .math_mul_start(checked_ms),.math_mul_cancel(checked_mc),.math_mul_a(checked_ma),.math_mul_b(checked_mba),.math_mul_busy(checked_mb),.math_mul_done(checked_md),.math_mul_result(checked_mr));
 nav_math_service #(.DIVIDE(0),.CLIENTS(1)) math_checked(.clk(clk),.rst_n(rst_n),.request(checked_ms),.cancel(checked_mc),.operand_a(checked_ma),.operand_b(checked_mba),.busy(checked_mb),.done(checked_md),.error(),.result(checked_mr),.grant());
 wire[511:0] public_checked={checked.update,checked.height_ready,checked.flow_ready,checked.reason,checked.height_mm,checked.body_vx_q16,checked.body_vy_q16,checked.world_vx_q16,checked.world_vy_q16,checked.dt_us,checked.busy,checked.mapping_verified,checked.rotation_compensated,checked.control_verified,checked.math_mul_start,checked.math_mul_cancel,checked.math_mul_a,checked.math_mul_b,checked.height_ready_state_numeric_tail,checked.height_ready_state_numeric_tail_without_live_flags};
 wire[2047:0] state_checked={checked.seen,checked.flow_seen,checked.transaction_epoch_ok,checked.flow_epoch_ok,checked.output_velocity_fault,checked.pending_velocity_fault,checked.publication_age,checked.compute_age,checked.fault,checked.state,checked.return_state,checked.private_cancel,checked.held_pitch,checked.held_yaw,checked.held_distance,checked.held_dt,checked.held_vx100_store,checked.held_vy100_store,checked.cr,checked.cp,checked.cy,checked.sy,checked.pending_height_store,checked.pending_bx_store,checked.pending_by_store,checked.pending_wx_store,checked.pending_wy_store,checked.rot_tmp_store,checked.mul_start,checked.div_start,checked.trig_start,checked.ma_store,checked.value_store,checked.mb_store,checked.num_store,checked.scale_mode,checked.angle_q20};
 wire defaulted_ms,defaulted_mc,defaulted_mb,defaulted_md;wire signed[63:0]defaulted_ma,defaulted_mba,defaulted_mr;
 new_mtf_shared_geometry #(.AGE_LIMIT(4096),.MAX_COMPUTE_TICKS(4000),.HEIGHT_TILT_LIMIT_CDEG(4500),.FLOW_TILT_LIMIT_CDEG(1500),.SWAP_AXES(SWAP),.NEGATE_X(NX),.NEGATE_Y(NY)) defaulted(
 .clk(clk),.rst_n(rst_n),.origin_reset(origin_reset),.sample_valid(sample_valid),.range_valid(range_valid),.flow_valid(flow_valid),.pose_valid(pose_valid),
 .distance_mm(distance_mm),.dt_ms(dt_ms),.vx_x100(vx_x100),.vy_x100(vy_x100),.velocity_range_ok(irrelevant_predicate),
 .roll_cdeg(roll_cdeg),.pitch_cdeg(pitch_cdeg),.body_yaw_cdeg(body_yaw_cdeg),.body_yaw_range_ok(1'b0),.body_tilt4500_ok(1'b0),.body_tilt1500_ok(1'b0),
 .math_mul_start(defaulted_ms),.math_mul_cancel(defaulted_mc),.math_mul_a(defaulted_ma),.math_mul_b(defaulted_mba),.math_mul_busy(defaulted_mb),.math_mul_done(defaulted_md),.math_mul_result(defaulted_mr));
 nav_math_service #(.DIVIDE(0),.CLIENTS(1)) math_defaulted(.clk(clk),.rst_n(rst_n),.request(defaulted_ms),.cancel(defaulted_mc),.operand_a(defaulted_ma),.operand_b(defaulted_mba),.busy(defaulted_mb),.done(defaulted_md),.error(),.result(defaulted_mr),.grant());
 wire[511:0] public_defaulted={defaulted.update,defaulted.height_ready,defaulted.flow_ready,defaulted.reason,defaulted.height_mm,defaulted.body_vx_q16,defaulted.body_vy_q16,defaulted.world_vx_q16,defaulted.world_vy_q16,defaulted.dt_us,defaulted.busy,defaulted.mapping_verified,defaulted.rotation_compensated,defaulted.control_verified,defaulted.math_mul_start,defaulted.math_mul_cancel,defaulted.math_mul_a,defaulted.math_mul_b,defaulted.height_ready_state_numeric_tail,defaulted.height_ready_state_numeric_tail_without_live_flags};
 wire[2047:0] state_defaulted={defaulted.seen,defaulted.flow_seen,defaulted.transaction_epoch_ok,defaulted.flow_epoch_ok,defaulted.output_velocity_fault,defaulted.pending_velocity_fault,defaulted.publication_age,defaulted.compute_age,defaulted.fault,defaulted.state,defaulted.return_state,defaulted.private_cancel,defaulted.held_pitch,defaulted.held_yaw,defaulted.held_distance,defaulted.held_dt,defaulted.held_vx100_store,defaulted.held_vy100_store,defaulted.cr,defaulted.cp,defaulted.cy,defaulted.sy,defaulted.pending_height_store,defaulted.pending_bx_store,defaulted.pending_by_store,defaulted.pending_wx_store,defaulted.pending_wy_store,defaulted.rot_tmp_store,defaulted.mul_start,defaulted.div_start,defaulted.trig_start,defaulted.ma_store,defaulted.value_store,defaulted.mb_store,defaulted.num_store,defaulted.scale_mode,defaulted.angle_q20};

 assign hr=old.height_ready;assign fr=old.flow_ready;assign busy=old.busy;assign update=old.update;
 integer checks=0,pubs=0,invalid_inputs=0,overlaps=0,expiry=0;
 always @(posedge clk)begin
  #1;checks=checks+1;
  if(public_old!==public_checked || public_old!==public_defaulted || state_old!==state_checked || state_old!==state_defaulted)
   $fatal(1,"geometry cycle miter SWAP=%0d NX=%0d NY=%0d cycle=%0d state=%0d vx=%h vy=%h",SWAP,NX,NY,checks,old.state,vx_x100,vy_x100);
  if(old.input_velocity_ok!==correct_predicate || checked.input_velocity_ok!==correct_predicate || defaulted.input_velocity_ok!==correct_predicate)
   $fatal(1,"geometry default/prechecked selector mismatch");
  if(update)pubs=pubs+1;if(!correct_predicate)invalid_inputs=invalid_inputs+1;
  if(old.fault[5])overlaps=overlaps+1;if(old.seen && old.publication_age>=4096)expiry=expiry+1;
 end
endmodule
module geometry_tb;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,origin_reset=0,sample_valid=0,range_valid=1,flow_valid=1,pose_valid=1,wrong_select=0;
 reg[31:0]distance_mm=1000,dt_ms=10;reg signed[31:0]vx_x100=0,vy_x100=0;
 reg signed[15:0]roll_cdeg=0,pitch_cdeg=0,body_yaw_cdeg=0;
 wire[2:0]hr,fr,busy,update;
 geometry_pair #(.SWAP(0),.NX(0),.NY(0)) a(.*,.hr(hr[0]),.fr(fr[0]),.busy(busy[0]),.update(update[0]));
 geometry_pair #(.SWAP(1),.NX(0),.NY(1)) b(.*,.hr(hr[1]),.fr(fr[1]),.busy(busy[1]),.update(update[1]));
 geometry_pair #(.SWAP(1),.NX(1),.NY(1)) c(.*,.hr(hr[2]),.fr(fr[2]),.busy(busy[2]),.update(update[2]));
 integer cycles=0,k;reg[31:0]rng=32'h731cfe05;
 always @(negedge clk)begin cycles=cycles+1;wrong_select=~wrong_select;end
 task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
 task clear;begin sample_valid=0;origin_reset=1;clocks(3);origin_reset=0;clocks(3);end endtask
 task frame;input signed[31:0]x,y;begin
  clear();vx_x100=x;vy_x100=y;sample_valid=1;clocks(1);sample_valid=0;clocks(2000);
  if(hr!==3'b111 || busy!==0)$fatal(1,"geometry actual transaction failed to publish height x=%0d y=%0d hr=%b busy=%b",x,y,hr,busy);
 end endtask
 initial begin
  clocks(5);rst_n=1;clocks(5);
  frame(999999,0);frame(-999999,0);frame(1000000,0);frame(-1000000,0);frame(1000001,0);frame(-1000001,0);
  frame(0,999999);frame(0,-999999);frame(0,1000000);frame(0,-1000000);frame(0,1000001);frame(0,-1000001);
  frame(32'sh80000000,0);frame(32'sh7fffffff,0);frame(0,32'sh80000000);frame(0,32'sh7fffffff);
  frame(12345,-54321);if(fr!==3'b111)$fatal(1,"geometry valid flow did not establish");
  // Live revoke occurs between edges; height remains usable on pure flow withdrawal.
  flow_valid=0;#1;if(fr!==0 || hr!==3'b111)$fatal(1,"geometry flow live revoke changed height");clocks(2);flow_valid=1;clocks(2);
  frame(12345,-54321);vx_x100=1000001;#1;if(fr!==0 || hr!==3'b111)$fatal(1,"geometry velocity live revoke mismatch");clocks(2);
  frame(12345,-54321);range_valid=0;#1;if(hr!==0 || fr!==0)$fatal(1,"geometry range live revoke mismatch");clocks(2);range_valid=1;
  frame(12345,-54321);pose_valid=0;#1;if(hr!==0 || fr!==0)$fatal(1,"geometry pose live revoke mismatch");clocks(2);pose_valid=1;
  frame(12345,-54321);roll_cdeg=1501;#1;if(fr!==0 || hr!==3'b111)$fatal(1,"geometry flow tilt live revoke mismatch");clocks(2);roll_cdeg=0;
  frame(12345,-54321);clocks(5000);if(hr!==0 || fr!==0)$fatal(1,"geometry publication age expiry missing");
  clear();sample_valid=1;clocks(1);sample_valid=0;clocks(10);if(busy!==3'b111)$fatal(1,"geometry overlap setup not busy");sample_valid=1;clocks(1);sample_valid=0;clocks(5);
  if(!a.old.fault[5] || !b.old.fault[5] || !c.old.fault[5])$fatal(1,"geometry overlap fault missing");
  clear();sample_valid=1;clocks(1);sample_valid=0;clocks(10);rst_n=0;clocks(3);rst_n=1;clocks(3);
  for(k=0;k<20000;k=k+1)begin
   rng=rng*32'd1664525+32'd1013904223;
   sample_valid=(k%101)==0;origin_reset=(k%257)==0;rst_n=(k%997)!=0;
   range_valid=rng[0];flow_valid=rng[1];pose_valid=rng[2];dt_ms=rng[8:3];distance_mm=rng[21:9];
   vx_x100=$signed(rng);vy_x100=-$signed(rng);roll_cdeg=$signed(rng[31:16]);pitch_cdeg=$signed(rng[15:0]);body_yaw_cdeg=$signed(rng[31:16]);clocks(1);
  end
  rst_n=1;sample_valid=0;origin_reset=0;range_valid=1;flow_valid=1;pose_valid=1;distance_mm=1000;dt_ms=10;roll_cdeg=0;pitch_cdeg=0;body_yaw_cdeg=0;
  clear();vx_x100=32'bx;vy_x100=0;clocks(3);vx_x100=0;vy_x100=32'bx;clocks(3);vx_x100=0;vy_x100=0;
  frame(0,0);
  if(a.pubs<20 || b.pubs<20 || c.pubs<20 || a.invalid_inputs<20 || a.overlaps==0 || a.expiry==0)$fatal(1,"geometry coverage missing pubs=%0d/%0d/%0d overlap=%0d expiry=%0d",a.pubs,b.pubs,c.pubs,a.overlaps,a.expiry);
  $display("PASS geometry actual_old_prechecked_default=1 real_math_services=9 mappings=3 all_public_and_FSM_state=1 cycles=%0d publications=%0d/%0d/%0d overlap=%0d expiry=%0d random_transitions=20000 no_DUT_force=1 CLK_HZ=50000000",cycles,a.pubs,b.pubs,c.pubs,a.overlaps,a.expiry);$finish;
 end
 initial begin #10000000;$fatal(1,"geometry timeout");end
endmodule
`default_nettype wire
