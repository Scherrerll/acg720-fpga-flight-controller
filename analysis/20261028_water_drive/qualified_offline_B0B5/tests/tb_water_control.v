`timescale 1ns/1ps
module tb_water_control;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,valid=1,updates=1;
    reg [3:0] count=8;
    reg [15:0] c1=1500,c2=1500,c3=1000,c4=1500,c5=1000,c6=1000,c7=1000,c8=1500;
    reg flight_armed=0,flight_stopped=1;
    wire fp,wm,we,fresh;wire [15:0] l,r;
    reg update=0;integer beat=0;
    always @(negedge clk) begin beat=beat+1;update=updates && beat%5==0;end
    water_drive_control #(.TIMER_DIVISOR(1),.FRESH_TICKS(50),.MODE_HOLD_TICKS(8),.LOW_HOLD_TICKS(20),.HIGH_HOLD_TICKS(20)) dut(
        .clk(clk),.rst_n(rst_n),.rc_update(update),.rc_valid(valid),.channel_count(count),
        .ch1(c1),.ch2(c2),.ch3(c3),.ch4(c4),.ch5(c5),.ch6(c6),.ch7(c7),.ch8(c8),
        .flight_armed(flight_armed),.flight_stopped(flight_stopped),
        .flight_permitted(fp),.water_mode(wm),.water_enabled(we),.left_us(l),.right_us(r),.rc_fresh(fresh));
    task tick;begin @(posedge clk);#1;end endtask
    task cycles;input integer n;integer i;begin for(i=0;i<n;i=i+1)tick;@(negedge clk);end endtask
    task rearm;begin c1=1500;c2=1500;c3=1000;c4=1500;c5=1000;cycles(35);c5=2000;cycles(25);if(!we)$fatal(1,"rearm failed");end endtask
    task stopped;begin #1;if(we)$fatal(1,"water unexpectedly enabled");end endtask
    task mix;input [15:0] t,y,el,er;begin c2=t;c4=y;cycles(6);if(l!=el || r!=er)$fatal(1,"mixer %0d/%0d -> %0d/%0d expected %0d/%0d",t,y,l,r,el,er);end endtask
    always @(posedge clk) if(rst_n && we && fp)$fatal(1,"mutual exclusion failed");
    initial begin
        cycles(2);rst_n=1;cycles(15);if(!fp || wm || we)$fatal(1,"startup flight selection");
        // A request in armed flight must never cut or enter water.
        flight_armed=1;flight_stopped=0;c5=2000;c6=2000;cycles(35);
        if(!fp || wm || we)$fatal(1,"in-air CH6 request changed flight");
        flight_armed=0;flight_stopped=1;c5=1000;c2=1700;cycles(20);
        if(fp || wm || we)$fatal(1,"rejected ground request did not block flight");
        c2=1500;c3=1500;cycles(20);if(wm)$fatal(1,"high flight throttle switched mode");
        c3=1000;flight_stopped=0;cycles(20);if(wm)$fatal(1,"live flight output switched mode");
        flight_stopped=1;cycles(17);if(!wm || fp || we)$fatal(1,"stopped water selection");
        c5=2000;cycles(25);stopped; // no full low preparation yet
        rearm;
        mix(1500,1500,1500,1500);mix(1530,1470,1500,1500);
        mix(1531,1469,1500,1562);mix(2000,1500,2000,2000);
        mix(1000,1500,1000,1000);mix(1500,2000,2000,1000);
        mix(1500,1000,1000,2000);mix(2000,2000,2000,1500);
        mix(1000,1000,1000,1500);mix(2200,800,1500,2000);
        // Invalid data and timeout clear preparation. High recovery cannot restart.
        c2=2201;cycles(2);stopped;c2=1500;cycles(30);stopped;
        rearm;updates=0;cycles(52);if(fresh)$fatal(1,"stale receiver still fresh");stopped;
        updates=1;cycles(30);stopped;
        rearm;count=6;cycles(2);stopped;count=8;cycles(30);stopped;
        rearm;valid=0;cycles(2);stopped;valid=1;cycles(30);stopped;
        rearm;c7=0;cycles(2);stopped;c7=1000;cycles(30);stopped;
        rearm;c8=0;cycles(2);stopped;c8=1500;cycles(30);stopped;
        rearm;c6=1500;cycles(2);stopped;c6=2000;cycles(30);stopped;
        rearm;c5=1500;cycles(2);stopped;c5=2000;cycles(30);stopped;
        rearm;c3=1500;cycles(2);stopped;c3=1000;cycles(30);stopped;
        rearm;c6=1000;cycles(30);stopped;if(!wm || fp)$fatal(1,"armed request switched mode");
        c5=1000;c1=1700;cycles(20);if(!wm)$fatal(1,"nonneutral mode exit");
        c1=1500;cycles(20);if(wm || !fp)$fatal(1,"stopped flight return failed");
        c6=2000;cycles(20);rearm;rst_n=0;cycles(2);stopped;rst_n=1;cycles(35);stopped;
        $display("PASS water interlock, 100ms-age counter boundary (scaled), low/high rearm, channel faults, mixer/deadband/saturation");$finish;
    end
    initial begin #1000000;$fatal(1,"timeout");end
endmodule
