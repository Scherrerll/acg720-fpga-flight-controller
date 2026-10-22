// ACG720 GW5AT-60: first power-on / programming smoke test.
// 50 MHz board clock -> LED2 toggles every 0.5 s (1 Hz full cycle).
// No motor, sensor, or receiver pins are driven by this design.
module acg720_smoke (
    input  wire clk50,
    output reg  led2 = 1'b0
);
    reg [24:0] count = 25'd0;

    always @(posedge clk50) begin
        if (count == 25'd24_999_999) begin
            count <= 25'd0;
            led2  <= ~led2;
        end else begin
            count <= count + 1'b1;
        end
    end
endmodule
