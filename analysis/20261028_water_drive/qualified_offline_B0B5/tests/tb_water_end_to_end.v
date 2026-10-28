`timescale 1ns/1ps
// Coherent virtual 1MHz scale: all us/frame/hold/freshness relationships scale
// together. Separate real50 test proves the production 50MHz pulse counters.
module tb_water_end_to_end;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,ppm=0,send_ppm=1;
    reg [15:0] pilot2=1500,pilot4=1500,pilot5=1000,pilot6=2000;
    wire valid,update,armed,permit,mode,enabled,lp,rp,fly,fly_active;
    wire [3:0] count;wire [15:0] c1,c2,c3,c4,c5,c6,c7,c8,seq,l,r,ll,lr;
    rc_ppm #(.CLK_HZ(1000000),.FRESH_TICKS(500000)) rx(.clk(clk),.rst_n(rst),.ppm_in(ppm),
        .frame_update(update),.valid(valid),.channel_count(count),.ch1(c1),.ch2(c2),.ch3(c3),.ch4(c4),.ch5(c5),.ch6(c6),.ch7(c7),.ch8(c8),.frame_sequence(seq));
    control_gate #(.LOW_HOLD_TICKS(500000),.HIGH_HOLD_TICKS(500000)) gate(.clk(clk),.rst_n(rst),
        .rc_valid(valid),.sensor_ok(permit),.channel_count(count),.ch3(c3),.ch5(c5),.armed(armed),.inhibit_reason(),
        .event_pulse(),.event_code(),.interruption_count(),.revoke_count(),.last_interruption_code(),.last_revoke_code());
    water_drive_control #(.TIMER_DIVISOR(1000),.FRESH_TICKS(100000),.MODE_HOLD_TICKS(25000),.LOW_HOLD_TICKS(500000),.HIGH_HOLD_TICKS(500000)) control(
        .clk(clk),.rst_n(rst),.rc_update(update),.rc_valid(valid),.channel_count(count),
        .ch1(c1),.ch2(c2),.ch3(c3),.ch4(c4),.ch5(c5),.ch6(c6),.ch7(c7),.ch8(c8),
        .flight_armed(armed),.flight_stopped(!armed && !fly_active),.flight_permitted(permit),.water_mode(mode),.water_enabled(enabled),.left_us(l),.right_us(r),.rc_fresh());
    water_pwm_pair #(.TICKS_PER_US(1)) water(.clk(clk),.rst_n(rst),.enable(enabled),.left_us(l),.right_us(r),
        .left_pwm(lp),.right_pwm(rp),.latched_left_us(ll),.latched_right_us(lr),.frame_active(),.neutral_output());
    // Existing flight PWM with a committed 1300us command fixture.
    motor_pwm #(.TICKS_PER_US(1),.FRAME_US(2500),.MAX_US(2000)) flight(.clk(clk),.rst_n(rst),.enabled(armed),
        .m1_us(16'd1300),.m2_us(16'd1300),.m3_us(16'd1300),.m4_us(16'd1300),
        .pre_ticks1(32'd0),.pre_ticks2(32'd0),.pre_ticks3(32'd0),.pre_ticks4(32'd0),.motor1_pwm(fly),.motor2_pwm(),.motor3_pwm(),.motor4_pwm(),
        .effective1_us(),.effective2_us(),.effective3_us(),.effective4_us(),.frame_latched1_us(),.frame_latched2_us(),.frame_latched3_us(),.frame_latched4_us(),.frame_active(fly_active),.limited());
    integer clock_ticks=0,last_edge=0;
    always @(posedge clk)clock_ticks=clock_ticks+1;
    task cycles;input integer n;integer j;begin for(j=0;j<n;j=j+1)@(negedge clk);end endtask
    task gap;input integer n;begin while(clock_ticks-last_edge<n)cycles(1);ppm=1;last_edge=clock_ticks;cycles(1);ppm=0;end endtask
    task transmit;reg [15:0] a,b,s,m;begin
        a=pilot2;b=pilot4;s=pilot5;m=pilot6;
        gap(1500);gap(a);gap(1000);gap(b);gap(s);gap(m);gap(1000);gap(1500);gap(4000);
    end endtask
    reg restart_ppm=0;
    initial begin wait(rst);gap(4000);forever begin
        if(send_ppm)begin if(restart_ppm)gap(4000);restart_ppm=0;transmit;end
        else begin restart_ppm=1;cycles(100);end
    end end
    task frames;input integer n;integer j;begin for(j=0;j<n;j=j+1)@(posedge update);cycles(5);end endtask
    task tick;begin @(posedge clk);#1;end endtask
    task water_frame;input integer el,er;integer j,lc,rc;begin
        tick;while(water.phase!=0)tick;lc=0;rc=0;
        for(j=0;j<20000;j=j+1)begin if(lp)lc=lc+1;if(rp)rc=rc+1;tick;end
        if(lc!=el || rc!=er)$fatal(1,"end-to-end PWM %0d/%0d expected %0d/%0d",lc,rc,el,er);
    end endtask
    always @(posedge clk)begin #2;if(rst)begin
        if(armed && (!permit || mode || enabled))$fatal(1,"integrated arbitration invariant");
        if(armed && (ll!=1500 || lr!=1500))$fatal(1,"flight started before complete water neutralization");
    end end
    integer j,fc;
    initial begin
        cycles(5);rst=1;frames(40);if(!mode || permit)$fatal(1,"water selection/low preparation");
        pilot5=2000;frames(40);if(!enabled || armed)$fatal(1,"water arm");
        pilot2=1700;pilot4=1600;frames(4);water_frame(1800,1600);
        pilot2=1200;pilot4=1500;frames(30);water_frame(1200,1200);
        send_ppm=0;wait(!enabled);water_frame(1500,1500);
        send_ppm=1;frames(40);if(enabled)$fatal(1,"high recovery auto-restarted after full confirmation interval");
        pilot2=1500;pilot4=1500;pilot5=1000;frames(40);pilot5=2000;frames(40);if(!enabled)$fatal(1,"water rearm");
        pilot2=1700;pilot4=1600;frames(4);water_frame(1800,1600);
        pilot6=1000;frames(4);if(enabled || !mode || armed)$fatal(1,"unsafe high-switch mode exit");
        pilot2=1500;pilot4=1500;pilot5=1000;frames(40);if(mode || !permit)$fatal(1,"flight return");
        pilot5=2000;frames(40);if(!armed || enabled)$fatal(1,"flight rearm");
        water_frame(1500,1500);tick;while(flight.phase!=0)tick;fc=0;
        for(j=0;j<2500;j=j+1)begin if(fly)fc=fc+1;tick;end
        if(fc!=1300)$fatal(1,"flight fixture PWM after return");
        $display("PASS end-to-end actual PPM/FSM/PWM: 1800/1600 differential, 1200/1200 reverse after neutral dwell, loss=>1500, high recovery blocked, water neutral before flight1300");$finish;
    end
    initial begin #200000000;$fatal(1,"end-to-end timeout");end
endmodule
