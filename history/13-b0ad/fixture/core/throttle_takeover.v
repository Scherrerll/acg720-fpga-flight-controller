// Manual throttle pickup after losing/leaving XYZ. Does not estimate height.
// Hold the last COMMITTED collective until the physical stick stick_matches it for
// 100 ms. SWA/RC/IMU safety is the separate live healthy input and wins immediately.
// There is deliberately no timed cut-off: a timer must not turn a descent stick
// into a motor stop. Pickup is announced in telemetry and blocks XYZ re-entry.
module throttle_takeover #(
 parameter integer MIN_US=1200,MAX_US=2000,PICKUP_TICKS=5000000,
 parameter integer MATCH_US=20
)(
 input wire clk,rst_n,healthy,auto_active,commit,
 input wire [15:0] committed_us,manual_us,auto_us,
 output wire retain_running,
 output wire waiting,
 // Internal bookkeeping only. Physical safety remains the healthy-masked
 // waiting/retain_running outputs; these two outputs are never motor enables.
 output wire pending_state,
 output wire [15:0] retained_us,
 output wire [15:0] selected_us,
 output wire [15:0] pickup_us
);
 localparam integer COUNT_BITS=$clog2(PICKUP_TICKS+1);
 reg previous_auto=0,latched=0;
 reg [15:0] last_committed=1000,held=1000;
 reg [COUNT_BITS-1:0] dwell=0;
 wire falling=previous_auto && !auto_active && last_committed>=MIN_US;
 wire pending=latched || falling;
 wire [15:0] reference_us=latched ? held:last_committed;
 assign pending_state=pending;
 assign retained_us=reference_us;
 wire stick_matches=manual_us>=MIN_US && manual_us<=MAX_US &&
  ({1'b0,manual_us}+MATCH_US>={1'b0,reference_us}) &&
  ({1'b0,reference_us}+MATCH_US>={1'b0,manual_us});
 assign waiting=healthy && pending;
 assign retain_running=waiting;
 assign pickup_us=waiting ? reference_us:16'd0;
 // Before the falling edge is registered, the same held value already selects
 // the data and maintains low-stick eligibility; no one-clock validity hole.
 assign selected_us=!healthy ? 16'd1000:
  auto_active ? (auto_us<MIN_US ? MIN_US:auto_us>MAX_US ? MAX_US:auto_us):
  pending ? reference_us:manual_us;
 initial if(PICKUP_TICKS<1 || MATCH_US<0 || MATCH_US>50 ||
  MIN_US<1000 || MAX_US<=MIN_US || MAX_US>2000)$fatal(1,"Invalid takeover policy");
 always @(posedge clk)begin
  if(!rst_n || !healthy)begin
   previous_auto<=0;latched<=0;last_committed<=1000;held<=1000;dwell<=0;
  end else begin
   previous_auto<=auto_active;
   if(commit)last_committed<=committed_us;
   if(auto_active)begin latched<=0;dwell<=0;end
   else if(falling)begin held<=last_committed;latched<=1;dwell<=0;end
   else if(latched)begin
    if(!stick_matches)dwell<=0;
    else if(dwell==PICKUP_TICKS-1)begin latched<=0;dwell<=0;end
    else dwell<=dwell+1'b1;
   end
  end
 end
endmodule
