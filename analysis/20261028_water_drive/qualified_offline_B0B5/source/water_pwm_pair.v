`timescale 1ns/1ps
// Fixed neutral is a DESIGN ASSUMPTION, not an ESC measurement.
// On revocation finish the current complete pulse (<=2 ms), then neutral at
// the next 20 ms boundary. Never splice reverse/forward widths in a frame.
module water_pwm_pair #(
    parameter integer TICKS_PER_US=50,
    parameter integer FRAME_US=20000,
    parameter integer REVERSE_NEUTRAL_FRAMES=15
)(
    input wire clk,rst_n,enable,
    input wire [15:0] left_us,right_us,
    output reg left_pwm=0,
    output reg right_pwm=0,
    output reg [15:0] latched_left_us=0,
    output reg [15:0] latched_right_us=0,
    output reg frame_active=0,
    output wire neutral_output
);
    localparam integer SUB_BITS=TICKS_PER_US>1?$clog2(TICKS_PER_US):1;
    localparam integer PHASE_BITS=$clog2(FRAME_US);
    reg [SUB_BITS-1:0] sub=0;
    reg [PHASE_BITS-1:0] phase=0;
    reg interrupted=1;
    reg [4:0] neutral_frames=0;
    reg [1:0] last_left_dir=0,last_right_dir=0;
    function [15:0] clamp;
        input [15:0] c;
        begin clamp=c<1000?16'd1000:c>2000?16'd2000:c; end
    endfunction
    function [1:0] direction;
        input [15:0] c;
        begin direction=c<1500?2'd1:c>1500?2'd2:2'd0; end
    endfunction
    wire [15:0] next_left=clamp(left_us),next_right=clamp(right_us);
    wire [1:0] left_dir=direction(next_left),right_dir=direction(next_right);
    wire reversing=(left_dir!=0 && last_left_dir!=0 && left_dir!=last_left_dir) ||
        (right_dir!=0 && last_right_dir!=0 && right_dir!=last_right_dir);
    assign neutral_output=latched_left_us==1500 && latched_right_us==1500;
    wire reverse_ready=neutral_frames>=REVERSE_NEUTRAL_FRAMES;
    always @(posedge clk) begin
        if(!rst_n) begin
            sub<=0;phase<=0;interrupted<=1;frame_active<=0;
            latched_left_us<=0;latched_right_us<=0;
            neutral_frames<=0;last_left_dir<=0;last_right_dir<=0;
        end else begin
            if(!enable) interrupted<=1;
            if(sub==TICKS_PER_US-1) begin
                sub<=0;
                if(phase==FRAME_US-1) begin
                    phase<=0;
                    // Count COMPLETED full neutral frames, not elapsed partial pulses.
                    if(neutral_output) begin
                        if(!reverse_ready) neutral_frames<=neutral_frames+1'b1;
                    end else neutral_frames<=0;
                    if(reverse_ready) begin last_left_dir<=0;last_right_dir<=0;end
                    if(enable && !interrupted && (!reversing || reverse_ready)) begin
                        latched_left_us<=next_left;latched_right_us<=next_right;
                        last_left_dir<=left_dir==0 ? (reverse_ready?2'd0:last_left_dir):left_dir;
                        last_right_dir<=right_dir==0 ? (reverse_ready?2'd0:last_right_dir):right_dir;
                        frame_active<=1;
                        if(left_dir!=0 || right_dir!=0) neutral_frames<=0;
                    end else begin
                        latched_left_us<=1500;latched_right_us<=1500;frame_active<=0;
                    end
                    interrupted<=!enable;
                end else phase<=phase+1'b1;
            end else sub<=sub+1'b1;
        end
    end
    // Dedicated output FFs avoid combinational binary-counter decode glitches
    // reaching ESC pins. Reset silences pins asynchronously; a release still
    // waits for the first complete frame boundary before any rising edge.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin left_pwm<=0;right_pwm<=0;end
        else if(sub==TICKS_PER_US-1) begin
            if(phase==FRAME_US-1) begin left_pwm<=1;right_pwm<=1;end
            else begin
                if(phase==latched_left_us-1'b1)left_pwm<=0;
                if(phase==latched_right_us-1'b1)right_pwm<=0;
            end
        end
    end
endmodule
