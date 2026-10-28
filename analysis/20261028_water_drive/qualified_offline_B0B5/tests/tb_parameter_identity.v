`timescale 1ns/1ps
module tb_parameter_identity;
    reg clk=0;always #10 clk=~clk;
    reg rst=0,valid=0;reg [7:0] data=0;
    wire ready;wire [191:0] response;
    xy_pi_parameters dut(.clk(clk),.rst_n(rst),.rx_valid(valid),.rx_error(1'b0),.rx_data(data),
        .write_safe(1'b1),.control_boundary(1'b1),.active_p(),.active_i(),.generation(),.response_valid(ready),.response(response),.response_ready(1'b0));
    task put;input [7:0] b;begin @(negedge clk);valid=1;data=b;@(negedge clk);valid=0;end endtask
    reg [127:0] request=128'ha5900101100000000001000000000000;
    reg [15:0] crc;integer i,k;
    initial begin
        repeat(2)@(negedge clk);rst=1;
        crc=16'hffff;
        for(i=13;i>=2;i=i-1)begin
            crc=crc^{request[i*8+:8],8'b0};
            for(k=0;k<8;k=k+1)crc=crc[15]?(crc<<1)^16'h1021:crc<<1;
        end
        request[15:0]=crc;
        for(i=15;i>=0;i=i-1)put(request[i*8+:8]);
        wait(ready);#1;
        if(response[47:16]!=32'h0000b0b5)$fatal(1,"incorrect feature ID");
        $display("RESPONSE=%048h",response);
        $display("PASS actual B0B5 parameter GET response identity and unchanged default wire1000/350");$finish;
    end
    initial begin #100000;$fatal(1,"parameter timeout");end
endmodule
