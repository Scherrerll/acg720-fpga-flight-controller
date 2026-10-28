`timescale 1ns/1ps
// Maximal-speed transitions are a stress abstraction; production holds are
// longer. The proof obligation is also documented inductively in DESIGN.md.
module tb_mode_gate_invariant;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,valid=1,update=1,health=1;
    reg [15:0] sw=1000,mode_request=1000,c1=1500,c2=1500,c4=1500,c7=1000;
    wire armed,permit,water_mode,water_enabled;
    control_gate #(.LOW_HOLD_TICKS(1),.HIGH_HOLD_TICKS(1)) gate(
        .clk(clk),.rst_n(rst),.rc_valid(valid),.sensor_ok(health && permit),
        .channel_count(4'd8),.ch3(16'd1000),.ch5(sw),.armed(armed),.inhibit_reason(),
        .event_pulse(),.event_code(),.interruption_count(),.revoke_count(),.last_interruption_code(),.last_revoke_code());
    water_drive_control #(.TIMER_DIVISOR(1),.FRESH_TICKS(8),.MODE_HOLD_TICKS(1),.LOW_HOLD_TICKS(1),.HIGH_HOLD_TICKS(1)) arbiter(
        .clk(clk),.rst_n(rst),.rc_valid(valid),.rc_update(update),.channel_count(4'd8),
        .ch1(c1),.ch2(c2),.ch3(16'd1000),.ch4(c4),.ch5(sw),.ch6(mode_request),.ch7(c7),.ch8(16'd1500),
        .flight_armed(armed),.flight_stopped(!armed),.flight_permitted(permit),.water_mode(water_mode),
        .water_enabled(water_enabled),.left_us(),.right_us(),.rc_fresh());
    reg [31:0] lfsr=32'h73a45c19;integer i,flight_arms=0,water_arms=0,mode_edges=0;
    reg old_f=0,old_w=0,old_mode=0;
    always @(posedge clk) begin #2;
        if(rst)begin
            if(!permit && armed)$fatal(1,"mode inhibit and flight armed overlap");
            if(water_mode && armed)$fatal(1,"water mode and flight armed overlap");
            if(water_enabled && armed)$fatal(1,"mutual exclusion violated");
            if(armed && !old_f)flight_arms=flight_arms+1;
            if(water_enabled && !old_w)water_arms=water_arms+1;
            if(water_mode!=old_mode)mode_edges=mode_edges+1;
        end
        old_f=armed;old_w=water_enabled;old_mode=water_mode;
    end
    initial begin
        repeat(3)@(negedge clk);rst=1;
        for(i=0;i<300000;i=i+1)begin
            @(negedge clk);lfsr={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};
            case(lfsr[2:0])0,1,2:sw=1000;3,4,5:sw=2000;6:sw=1500;7:sw=2400;endcase
            mode_request=lfsr[4]?2000:1000;
            c1=lfsr[5:3]==0?1700:1500;c2=lfsr[8:6]==0?1800:1500;c4=lfsr[11:9]==0?1300:1500;
            c7=lfsr[15:12]==0?0:1000;valid=lfsr[20:16]!=0;update=lfsr[22:21]!=0;health=lfsr[27:23]!=0;
            if(i%10007==0)rst=0;else rst=1;
        end
        repeat(3)@(negedge clk);
        if(flight_arms<100 || water_arms<10 || mode_edges<100)$fatal(1,"stress coverage too low %0d/%0d/%0d",flight_arms,water_arms,mode_edges);
        $display("PASS 300000 arbitration cycles: flight arms=%0d water arms=%0d mode edges=%0d; inhibited=>unarmed; no enabled overlap",flight_arms,water_arms,mode_edges);$finish;
    end
endmodule
