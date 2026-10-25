// B0B1 passive observability only. No output feeds producer/control predicates.
module imu_diagnostic_tap #(parameter integer STARTUP_ONLY_RESET=0)(
 input wire clk,rst_n,taking_off,gate_event,record_ready,
 input wire checked_ready,checked_base_ok,
 input wire [95:0] checked_raw,trusted,candidate,
 input wire [31:0] source_id,source_tick,
 input wire [9:0] reader_meta,
 input wire [7:0] temporal_detail,quiet_count,
 input wire candidate_pending,accepted,
 input wire [31:0] accepted_count,accepted_age,
 input wire link_usable,guard_qualified,guard_stale,
 input wire [31:0] recovery_count,
 input wire attitude_update,attitude_valid,linear_accel_valid,calibrated,initialized,ready,reseed,
 input wire [7:0] reseed_count,estimator_state,resume_state,first_cause,attitude_fault,
 input wire [31:0] consumed_id,held_dt,
 input wire signed [31:0] world_ax,world_ay,world_az,
 input wire signed [15:0] roll,pitch,yaw,
 output reg raw_valid=0,
 output reg pose_valid=0,
 output reg fault_valid=0,
 output reg [207:0] raw_body=0,
 output reg [223:0] pose_body=0,
 output reg [703:0] fault_body=0,
 output reg [31:0] raw_tick=0,
 output reg [31:0] pose_tick=0,
 output reg [31:0] fault_tick=0,
 output reg [31:0] clock_ticks=0,
 output reg [31:0] max_accept_gap=0,
 output reg [31:0] raw_count=0,
 output reg [31:0] pose_count=0
);
 reg decision_pending=0,accepted_seen=0,valid_pose_seen=0;
 reg previous_valid=0,previous_taking_off=0;
 reg [31:0] last_accept_tick=0,last_pose_tick=0,busy_age=0;
 reg [95:0] pending_raw=0;
 reg [31:0] pending_id=0,pending_tick=0;
 reg [9:0] pending_reader=0;
 reg pending_base=0,pending_candidate=0;
 reg [7:0] pending_detail=0,pending_quiet=0;
 reg [31:0] rejected_id=0;
 reg [95:0] rejected_raw=0,rejected_trusted=0,rejected_candidate=0;
 reg [7:0] rejected_detail=0,rejected_quiet=0,rejected_reader_fault=0;
 wire [31:0] accept_gap=clock_ticks-last_accept_tick;
 wire [31:0] current_max_gap=accepted_seen && accept_gap>max_accept_gap ?accept_gap:max_accept_gap;
 wire new_reject=checked_ready && temporal_detail!=0;
 wire [7:0] recovery_byte=recovery_count>255 ?8'hff:recovery_count[7:0];
 wire [7:0] raw_flags={pending_candidate,attitude_valid,guard_qualified,link_usable,
                       accepted,pending_base,pending_reader[1:0]};
 wire [7:0] pose_flags={2'b00,reseed,ready,initialized,calibrated,linear_accel_valid,attitude_valid};
 wire [15:0] state_flags={6'd0,(estimator_state!=0),attitude_valid,candidate_pending,
                         guard_stale,guard_qualified,link_usable,reseed,ready,initialized,calibrated};
 wire [7:0] triggers={5'd0,gate_event,(previous_valid && !attitude_valid),
                     1'b0};
 always @(posedge clk) begin
  raw_valid<=0;pose_valid<=0;
  if(!STARTUP_ONLY_RESET && !rst_n)begin
   clock_ticks<=0;max_accept_gap<=0;raw_count<=0;pose_count<=0;
   raw_body<=0;pose_body<=0;fault_body<=0;raw_tick<=0;pose_tick<=0;fault_tick<=0;fault_valid<=0;
   decision_pending<=0;accepted_seen<=0;valid_pose_seen<=0;
   previous_valid<=0;previous_taking_off<=0;last_accept_tick<=0;last_pose_tick<=0;busy_age<=0;
   pending_raw<=0;pending_id<=0;pending_tick<=0;pending_reader<=0;pending_base<=0;
   pending_candidate<=0;pending_detail<=0;pending_quiet<=0;
   rejected_id<=0;rejected_raw<=0;rejected_trusted<=0;rejected_candidate<=0;
   rejected_detail<=0;rejected_quiet<=0;rejected_reader_fault<=0;
  end else if(rst_n)begin
   clock_ticks<=clock_ticks+1'b1;
   previous_valid<=attitude_valid;previous_taking_off<=taking_off;
   if(record_ready && raw_count!=32'hffffffff)raw_count<=raw_count+1'b1;
   if(estimator_state==0)busy_age<=0;
   else if(busy_age!=32'hffffffff)busy_age<=busy_age+1'b1;
   max_accept_gap<=current_max_gap;
   if(accepted)begin accepted_seen<=1;last_accept_tick<=clock_ticks;end
   // checked_ready precedes the guard's registered acceptance by one clock.
   // Hold the exact source tuple; build raw after that guard decision commits.
   decision_pending<=checked_ready;
   if(checked_ready)begin
    pending_raw<=checked_raw;pending_id<=source_id;pending_tick<=source_tick;
    pending_reader<=reader_meta;pending_base<=checked_base_ok;
    pending_detail<=temporal_detail;pending_quiet<=quiet_count;pending_candidate<=candidate_pending;
   end
   if(decision_pending)begin
    raw_valid<=1;raw_tick<=pending_tick;
    raw_body<={pending_id,pending_raw,accepted_count,pending_detail,pending_reader[9:2],
               raw_flags,pending_quiet,recovery_byte,estimator_state};
   end
   if(new_reject)begin
    rejected_id<=source_id;rejected_raw<=checked_raw;rejected_trusted<=trusted;rejected_candidate<=candidate;
    rejected_detail<=temporal_detail;rejected_quiet<=quiet_count;rejected_reader_fault<=reader_meta[9:2];
   end
   if(attitude_update)begin
    pose_valid<=1;pose_tick<=clock_ticks;last_pose_tick<=clock_ticks;
    if(pose_count!=32'hffffffff)pose_count<=pose_count+1'b1;
    if(attitude_valid)valid_pose_seen<=1;
    pose_body<={consumed_id,held_dt,world_ax,world_ay,world_az,roll,pitch,yaw,pose_flags,attitude_fault};
   end
   // New window always has at least one low-valid clock for the UART rearm.
   if(taking_off && !previous_taking_off)begin fault_valid<=0;fault_body<=0;fault_tick<=0;end
   else if(!fault_valid && valid_pose_seen && triggers!=0)begin
    fault_valid<=1;fault_tick<=clock_ticks;
    fault_body<={triggers,first_cause,attitude_fault,(new_reject ?temporal_detail:rejected_detail),
      (new_reject ?source_id:rejected_id),accepted_count,consumed_id,pose_count,
      last_accept_tick,last_pose_tick,current_max_gap,busy_age,32'd0,accepted_age,
      estimator_state,resume_state,recovery_byte,reseed_count,state_flags,
      (new_reject ?quiet_count:rejected_quiet),(new_reject ?reader_meta[9:2]:rejected_reader_fault),
      (new_reject ?checked_raw:rejected_raw),(new_reject ?trusted:rejected_trusted),
      (new_reject ?candidate:rejected_candidate)};
   end
  end
 end
endmodule
