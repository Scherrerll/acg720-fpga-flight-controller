`timescale 1ns/1ps
module tb_candidate_real50;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,en=0;
    wire lp,rp;wire [15:0] ll,lr;
    water_pwm_pair dut(.clk(clk),.rst_n(rst_n),.enable(en),.left_us(16'd1000),.right_us(16'd2000),
        .left_pwm(lp),.right_pwm(rp),.latched_left_us(ll),.latched_right_us(lr),.frame_active(),.neutral_output());
    task tick;begin @(posedge clk);#1;end endtask
    task frame;input integer el,er;integer i,lc,rc;begin lc=0;rc=0;
        for(i=0;i<1000000;i=i+1)begin if(lp)lc=lc+1;if(rp)rc=rc+1;tick;end
        if(lc!=el || rc!=er)$fatal(1,"real50 widths %0d/%0d",lc,rc);
    end endtask
    initial begin
        tick;rst_n=1;tick;while(dut.phase!=0 || dut.sub!=0)tick;
        frame(75000,75000);en=1;frame(75000,75000);frame(75000,75000);frame(50000,100000);
        $display("PASS real 50MHz candidate: period=1000000 ticks; 1/1.5/2 ms = 50000/75000/100000 ticks");$finish;
    end
endmodule
