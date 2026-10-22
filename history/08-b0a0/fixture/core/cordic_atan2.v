// Iterative vectoring CORDIC. Inputs/magnitude use the same integer units.
// Angle is signed degrees Q16; 18 iterations, all four quadrants.
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
            magnitude <= compensated[47:16]; // intentional Q16 rescaling
            busy <= 0; finish <= 0; done <= 1;
        end else if (busy) begin
            if (y > 0) begin
                x <= x + (y >>> step); y <= y - (x >>> step);
                z <= z + table_angle(step);
            end else if (y < 0) begin
                x <= x - (y >>> step); y <= y + (x >>> step);
                z <= z - table_angle(step);
            end else begin
                // Continue rotating, including zero y, to preserve CORDIC gain.
                x <= x + (y >>> step); y <= y - (x >>> step);
                z <= z + table_angle(step);
            end
            if (step == 17) finish <= 1;
            else step <= step + 1'b1;
        end
    end
endmodule
