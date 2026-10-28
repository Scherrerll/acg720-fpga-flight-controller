`timescale 1ns/1ps
// Measure production prescaler without force, then check terminal states.
module tb_water_timer_limits;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,update=1;reg [15:0] sw=1000;
    wire enabled,fresh,mode;
    water_drive_control dut(.clk(clk),.rst_n(rst),.rc_update(update),.rc_valid(1'b1),.channel_count(4'd8),
        .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch5(sw),.ch6(16'd2000),.ch7(16'd1000),.ch8(16'd1500),
        .flight_armed(1'b0),.flight_stopped(1'b1),.flight_permitted(),.water_mode(mode),.water_enabled(enabled),.left_us(),.right_us(),.rc_fresh(fresh));
    integer clocks=0,last_tick=0,ticks_seen=0;reg check_period=1;
    always @(posedge clk)begin
        clocks=clocks+1;
        if(rst && dut.timer_tick && check_period)begin
            if(ticks_seen!=0 && clocks-last_tick!=50000)$fatal(1,"production divider period");
            last_tick=clocks;ticks_seen=ticks_seen+1;
        end
    end
    task tick;begin @(posedge clk);#1;end endtask
    task terminal_tick;begin
        @(negedge clk);force dut.timer_phase=49998;tick;release dut.timer_phase;
        tick;tick;
    end endtask
    initial begin
        if(dut.FRESH_TICKS!=5000000 || dut.MODE_HOLD_TICKS!=1250000 || dut.LOW_HOLD_TICKS!=25000000 || dut.HIGH_HOLD_TICKS!=25000000)$fatal(1,"production timer constants");
        if(dut.TIMER_DIVISOR!=50000 || dut.FRESH_LIMIT!=100 || dut.MODE_LIMIT!=25 || dut.LOW_LIMIT!=500 || dut.HIGH_LIMIT!=500)$fatal(1,"production quantization");
        if($bits(dut.timer_phase)!=16 || $bits(dut.age)!=7 || $bits(dut.mode_hold)!=5 || $bits(dut.hold_count)!=9)$fatal(1,"timer widths");
        tick;@(negedge clk);rst=1;repeat(100005)tick;
        if(ticks_seen!=2 || mode)$fatal(1,"prescaler or early mode");check_period=0;
        force dut.mode_hold=24;tick;release dut.mode_hold;
        terminal_tick;if(mode)$fatal(1,"mode accepted partial first interval");
        terminal_tick;if(!mode)$fatal(1,"mode terminal");
        force dut.hold_count=499;tick;release dut.hold_count;
        terminal_tick;if(dut.low_ready)$fatal(1,"low confirmation early");
        terminal_tick;if(!dut.low_ready)$fatal(1,"low terminal");
        @(negedge clk);sw=2000;force dut.hold_count=499;tick;release dut.hold_count;
        terminal_tick;if(enabled)$fatal(1,"high confirmation early");
        terminal_tick;if(!enabled)$fatal(1,"high terminal");
        @(negedge clk);update=0;force dut.age=99;tick;release dut.age;
        if(!fresh || !enabled)$fatal(1,"freshness expired between timer ticks");
        terminal_tick;if(fresh || enabled)$fatal(1,"100ms upper bound did not revoke live enable");
        tick;if(dut.armed || dut.low_ready)$fatal(1,"freshness did not clear rearm state");
        $display("PASS production50MHz divider=50000clocks; widths16+7+5+9; conservative hold terminals and live expiry");$finish;
    end
endmodule
