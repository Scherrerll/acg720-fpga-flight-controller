`timescale 1ns/1ps
// Unforced complete intervals at every divider phase. Faults between enables
// must revoke immediately, rather than waiting for the next millisecond.
module tb_water_quantized_timers;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,update=1,valid=1;reg [15:0] sw=1000,request=1000;
    wire mode,enabled,fresh;integer clocks=0,phase,start,elapsed,guard;
    always @(posedge clk)clocks=clocks+1;
    water_drive_control #(.TIMER_DIVISOR(7),.FRESH_TICKS(70),.MODE_HOLD_TICKS(17),.LOW_HOLD_TICKS(101),.HIGH_HOLD_TICKS(103)) dut(
        .clk(clk),.rst_n(rst),.rc_update(update),.rc_valid(valid),.channel_count(4'd8),
        .ch1(16'd1500),.ch2(16'd1500),.ch3(16'd1000),.ch4(16'd1500),.ch5(sw),.ch6(request),.ch7(16'd1000),.ch8(16'd1500),
        .flight_armed(1'b0),.flight_stopped(1'b1),.flight_permitted(),.water_mode(mode),.water_enabled(enabled),.left_us(),.right_us(),.rc_fresh(fresh));
    task tick;begin @(posedge clk);#1;end endtask
    task wait_low;begin
        start=clocks;guard=0;
        while(!dut.low_ready)begin tick;guard=guard+1;if(guard>125)$fatal(1,"low hold stalled");end
        elapsed=clocks-start;if(elapsed<101 || elapsed>118)$fatal(1,"low hold bounds %0d",elapsed);
    end endtask
    task wait_high;begin
        @(negedge clk);sw=2000;start=clocks;guard=0;
        while(!enabled)begin tick;guard=guard+1;if(guard>125)$fatal(1,"high hold stalled");end
        elapsed=clocks-start;if(elapsed<103 || elapsed>120)$fatal(1,"high hold bounds %0d",elapsed);
    end endtask
    initial begin
        for(phase=0;phase<7;phase=phase+1)begin
            @(negedge clk);rst=0;valid=1;update=1;sw=1000;request=1000;repeat(3)tick;
            @(negedge clk);rst=1;repeat(7+phase)tick;
            @(negedge clk);request=2000;start=clocks;guard=0;
            while(!mode)begin tick;guard=guard+1;if(guard>40)$fatal(1,"mode stalled");end
            elapsed=clocks-start;if(elapsed<17 || elapsed>34)$fatal(1,"mode bounds %0d",elapsed);
            wait_low;wait_high;
            while(dut.timer_phase!=2)tick;
            @(negedge clk);valid=0;#1;if(enabled)$fatal(1,"inter-tick fault did not mask output");
            tick;if(dut.armed || dut.low_ready)$fatal(1,"inter-tick fault retained preparation");
            @(negedge clk);valid=1;repeat(250)begin tick;if(enabled)$fatal(1,"high recovery restarted");end
            @(negedge clk);sw=1000;wait_low;wait_high;
            @(negedge clk);update=0;start=clocks;guard=0;
            while(fresh)begin tick;guard=guard+1;if(guard>70)$fatal(1,"freshness exceeds nominal upper bound");end
            elapsed=clocks-start;if(elapsed<64 || elapsed>70 || enabled)$fatal(1,"freshness phase bounds %0d",elapsed);
            tick;if(dut.armed || dut.low_ready)$fatal(1,"expiry retained preparation");
        end
        $display("PASS all7 timer phases: nondivisible minimum holds, timeout upper bound, inter-tick fault clear, high recovery blocked");$finish;
    end
    initial begin #1000000;$fatal(1,"quantized timer test timeout");end
endmodule
