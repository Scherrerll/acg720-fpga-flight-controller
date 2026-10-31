// 迭代向量模式 CORDIC，用于计算 atan2(y,x) 和向量模长；输入与模长使用相同整数单位。
// 角度输出为有符号“度”的 Q16 定点数；固定 18 次迭代，覆盖四个象限。
// start 仅在 busy=0 时锁存 x_in/y_in；done 为结果提交单拍，复位同步清除内部迭代。
module cordic_atan2 (
    input wire clk, rst_n, start,
    input wire signed [31:0] x_in, y_in,
    output reg busy = 0,
    output reg done = 0,
    output reg signed [31:0] angle_q16 = 0,
    output reg [31:0] magnitude = 0
);
    reg signed [35:0] x = 0, y = 0;
    reg signed [31:0] z = 0;
    reg [4:0] step = 0;
    reg finish = 0;
    // 39797/65536 为固定增益补偿近似值；中间向量扩展为 36 位以容纳迭代增益。
    wire signed [63:0] compensated = x * 32'sd39797;
    function signed [31:0] table_angle;
        input [4:0] i;
        begin
            case(i)
                0: table_angle=2949120; 1: table_angle=1740967;
                2: table_angle=919879; 3: table_angle=466945;
                4: table_angle=234379; 5: table_angle=117304;
                6: table_angle=58666; 7: table_angle=29335;
                8: table_angle=14668; 9: table_angle=7334;
                10: table_angle=3667; 11: table_angle=1833;
                12: table_angle=917; 13: table_angle=458;
                14: table_angle=229; 15: table_angle=115;
                16: table_angle=57; 17: table_angle=29;
                default: table_angle=0;
            endcase
        end
    endfunction
    always @(posedge clk) begin
        done <= 0;
        if (!rst_n) begin
            busy <= 0; finish <= 0; angle_q16 <= 0; magnitude <= 0;
            x <= 0; y <= 0; z <= 0; step <= 0;
        // 输入位于左半平面时先整体反向并补偿正/负 180 度，随后采用统一向量迭代。
        end else if (start && !busy) begin
            busy <= 1; finish <= 0; step <= 0;
            if (x_in < 0) begin
                x <= -{{4{x_in[31]}},x_in};
                y <= -{{4{y_in[31]}},y_in};
                z <= y_in >= 0 ? 32'sd11796480 : -32'sd11796480;
            end else begin
                x <= {{4{x_in[31]}},x_in};
                y <= {{4{y_in[31]}},y_in}; z <= 0;
            end
        end else if (busy && finish) begin
            angle_q16 <= z;
            magnitude <= compensated[47:16]; // 此处有意按 Q16 比例缩放，补偿 CORDIC 增益。
            busy <= 0; finish <= 0; done <= 1;
        // 每拍按 y 的符号选旋转方向并累加查表角，最后另用一拍发布角度和模长。
        end else if (busy) begin
            if (y > 0) begin
                x <= x + (y >>> step); y <= y - (x >>> step);
                z <= z + table_angle(step);
            end else if (y < 0) begin
                x <= x - (y >>> step); y <= y + (x >>> step);
                z <= z - table_angle(step);
            end else begin
                // 即使 y 恰为零也继续旋转，以保持与统一增益补偿系数一致。
                x <= x + (y >>> step); y <= y - (x >>> step);
                z <= z + table_angle(step);
            end
            if (step == 17) finish <= 1;
            else step <= step + 1'b1;
        end
    end
endmodule
