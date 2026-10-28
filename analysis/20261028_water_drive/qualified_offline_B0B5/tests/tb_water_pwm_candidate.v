`timescale 1ns/1ps
module tb_water_pwm_candidate;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,en=0;
    reg [15:0] l=1000,r=2000;
    wire lp,rp,active,neutral;wire [15:0] ll,lr;
    water_pwm_pair #(.TICKS_PER_US(1),.REVERSE_NEUTRAL_FRAMES(3)) dut(
        .clk(clk),.rst_n(rst_n),.enable(en),.left_us(l),.right_us(r),
        .left_pwm(lp),.right_pwm(rp),.latched_left_us(ll),.latched_right_us(lr),.frame_active(active),.neutral_output(neutral));
    task tick;begin @(posedge clk);#1;end endtask
    task boundary;begin tick;while(dut.phase!=0)tick;end endtask
    task frame;input integer el,er;integer i,lc,rc;begin
        lc=0;rc=0;for(i=0;i<20000;i=i+1)begin if(lp)lc=lc+1;if(rp)rc=rc+1;tick;end
        if(lc!=el || rc!=er)$fatal(1,"width expected %0d/%0d actual %0d/%0d",el,er,lc,rc);
    end endtask
    reg last_l=0,last_r=0;
    always @(posedge clk) begin #2;
        if(rst_n && ((lp&&!last_l)||(rp&&!last_r)) && dut.phase!=0)$fatal(1,"mid-frame pulse restart");
        last_l=lp;last_r=rp;
    end
    integer i,j,n;
    initial begin
        tick;rst_n=1;tick;if(lp||rp)$fatal(1,"startup partial pulse");boundary;
        frame(1500,1500);en=1;frame(1500,1500);frame(1500,1500);frame(1000,2000);
        l=0;r=65535;frame(1000,2000);frame(1000,2000);
        // Request one-motor reversal. Both must remain neutral for >=3 full frames.
        l=2000;r=2000;boundary;n=0;
        while(ll==1500 && lr==1500)begin frame(1500,1500);n=n+1;if(n>6)$fatal(1,"reversal never released");end
        if(n<3)$fatal(1,"reversal neutral dwell too short");frame(2000,2000);
        // Stop/re-enable at pulse phases on both sides of neutral and falling edges.
        for(j=0;j<7;j=j+1)begin
            case(j)0:n=1;1:n=999;2:n=1000;3:n=1499;4:n=1500;5:n=1999;default:n=2500;endcase
            for(i=0;i<n;i=i+1)tick;
            en=0;tick;en=1;boundary;frame(1500,1500);frame(2000,2000);
        end
        en=0;boundary;frame(1500,1500);frame(1500,1500);
        rst_n=0;#1;if(lp||rp)$fatal(1,"reset not silent");
        $display("PASS candidate PWM: bounds, frame coherence, no restart, seven interruption phases, paired reversal neutral dwell");$finish;
    end
endmodule
