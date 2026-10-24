module imu_pipeline #(
    parameter integer LEVEL_TRIM_ENABLE=0,
    parameter signed [31:0] LEVEL_R00_Q24=16777216,
    parameter signed [31:0] LEVEL_R01_Q24=0,
    parameter signed [31:0] LEVEL_R02_Q24=0,
    parameter signed [31:0] LEVEL_R10_Q24=0,
    parameter signed [31:0] LEVEL_R11_Q24=16777216,
    parameter signed [31:0] LEVEL_R12_Q24=0,
    parameter signed [31:0] LEVEL_R20_Q24=0,
    parameter signed [31:0] LEVEL_R21_Q24=0,
    parameter signed [31:0] LEVEL_R22_Q24=16777216,
    parameter integer CAL_SAMPLES=256,
    parameter integer DATA_TIMEOUT_TICKS=3000000)(
    input wire clk50,rst_n,imu_miso,
    output wire imu_sck,imu_mosi,imu_cs_n,imu_gyro_cs_n,
    output wire yaw_range_ok,
    output wire calibrated,attitude_valid,attitude_update,link_usable,
    output wire [95:0] accepted_raw,
    output wire [31:0] dt_ticks,accepted_count,rejected_count,
    output wire [7:0] reason,who,pwr,attitude_fault,
    output wire [15:0] cal_count,
    output wire signed [15:0] roll,pitch,yaw,bias_x,bias_y,bias_z,
    output wire signed [15:0] filtered_gx,filtered_gy,filtered_gz,
    output wire signed [31:0] filtered_gx_q12,filtered_gy_q12,filtered_gz_q12,
    output wire signed [31:0] world_ax,world_ay,world_az_mmps2,
    output wire linear_accel_valid,
    output wire [31:0] accepted_raw_age_ticks
);
reg[16:0]sample_clock=0;
always@(posedge clk50)if(!rst_n || sample_clock==99999)sample_clock<=0;else sample_clock<=sample_clock+1;
assign attitude_update=rst_n && sample_clock==0;
assign calibrated=rst_n;assign attitude_valid=rst_n;assign link_usable=rst_n;
assign accepted_raw={16'd0,16'd0,16'd2048,48'd0};assign dt_ticks=100000;
assign accepted_count=0;assign rejected_count=0;assign reason=0;assign who=8'h1e;assign pwr=8'h0f;
assign attitude_fault=0;assign cal_count=2048;assign roll=0;assign pitch=0;assign yaw=0;assign yaw_range_ok=1;
assign bias_x=0;assign bias_y=0;assign bias_z=0;
assign filtered_gx=0;assign filtered_gy=0;assign filtered_gz=0;
assign filtered_gx_q12=0;assign filtered_gy_q12=0;assign filtered_gz_q12=0;
assign world_ax=0;assign world_ay=0;assign world_az_mmps2=0;
assign linear_accel_valid=rst_n;assign accepted_raw_age_ticks=0;
endmodule

module rc_ppm(input wire clk,rst_n,ppm_in,
output wire frame_update,valid,output wire[3:0]channel_count,
output wire[15:0]ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,frame_sequence);
reg[15:0]env_ch1=1500,env_ch2=1500,env_ch3=1000,env_ch5=1000;
assign frame_update=0;assign valid=rst_n;assign channel_count=8;
assign ch1=env_ch1;assign ch2=env_ch2;assign ch3=env_ch3;assign ch4=1500;assign ch5=env_ch5;
assign ch6=1000;assign ch7=2000;assign ch8=1000;assign frame_sequence=0;
endmodule
