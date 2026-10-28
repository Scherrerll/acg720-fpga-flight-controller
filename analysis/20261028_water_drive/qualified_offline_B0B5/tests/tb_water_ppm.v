`timescale 1ns/1ps
// Actual receiver and water controller, with clock-count scales reduced only
// for simulation. No force on receiver validity, update or channel outputs.
module tb_water_ppm;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,ppm=0;
    wire valid,update;wire [3:0] count;
    wire [15:0] c1,c2,c3,c4,c5,c6,c7,c8,seq;
    wire enabled,mode,flight;
    reg [15:0] sw=1000,thrust=1500;
    rc_ppm #(.CLK_HZ(1000000),.FRESH_TICKS(60000)) receiver(
        .clk(clk),.rst_n(rst),.ppm_in(ppm),.frame_update(update),.valid(valid),.channel_count(count),
        .ch1(c1),.ch2(c2),.ch3(c3),.ch4(c4),.ch5(c5),.ch6(c6),.ch7(c7),.ch8(c8),.frame_sequence(seq));
    water_drive_control #(.TIMER_DIVISOR(1),.FRESH_TICKS(50000),.MODE_HOLD_TICKS(10),.LOW_HOLD_TICKS(100),.HIGH_HOLD_TICKS(100)) control(
        .clk(clk),.rst_n(rst),.rc_update(update),.rc_valid(valid),.channel_count(count),
        .ch1(c1),.ch2(c2),.ch3(c3),.ch4(c4),.ch5(c5),.ch6(c6),.ch7(c7),.ch8(c8),
        .flight_armed(1'b0),.flight_stopped(1'b1),.flight_permitted(flight),.water_mode(mode),.water_enabled(enabled),.left_us(),.right_us(),.rc_fresh());
    task cycles;input integer n;integer i;begin for(i=0;i<n;i=i+1)@(negedge clk);end endtask
    integer clock_ticks=0,last_edge=0;
    always @(posedge clk)clock_ticks=clock_ticks+1;
    task gap;input integer n;begin
        while(clock_ticks-last_edge<n)cycles(1);
        ppm=1;last_edge=clock_ticks;cycles(1);ppm=0;
    end endtask
    task frame;input integer n;begin
        gap(1500);gap(thrust);gap(1000);gap(1500);gap(sw);
        if(n>=6)gap(2000);if(n>=7)gap(1000);if(n>=8)gap(1500);
        gap(4000);
    end endtask
    initial begin
        cycles(4);rst=1;gap(4000);frame(8);cycles(200);
        if(!mode || flight || enabled)$fatal(1,"PPM low preparation failed");
        sw=2000;frame(8);cycles(200);if(!enabled)$fatal(1,"PPM high failed");
        // Partial frame never changes the committed CH2; invalid interval revokes.
        thrust=1800;gap(1500);gap(thrust);cycles(5);
        if(c2!=1500)$fatal(1,"partial PPM command leaked");
        gap(700);cycles(5);if(valid || enabled)$fatal(1,"bad PPM interval did not stop");
        gap(4000);frame(8);cycles(200);if(enabled)$fatal(1,"high recovery rearmed");
        thrust=1500;sw=1000;frame(8);cycles(200);sw=2000;frame(8);cycles(200);if(!enabled)$fatal(1,"PPM rearm failed");
        frame(5);cycles(10);if(!valid || count!=5 || enabled)$fatal(1,"accepted five-channel frame did not inhibit water");
        frame(8);cycles(200);if(enabled)$fatal(1,"missing-channel recovery rearmed");
        sw=1000;frame(8);cycles(200);sw=2000;frame(8);cycles(200);if(!enabled)$fatal(1,"second PPM rearm failed");
        cycles(50010);if(enabled || control.rc_fresh)$fatal(1,"PPM freshness timeout failed");
        $display("PASS actual PPM decoder + water FSM: atomic frames, malformed interval, missing channels, freshness, fault rearm");$finish;
    end
    initial begin #10000000;$fatal(1,"PPM test timeout");end
endmodule
