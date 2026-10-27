module old_uart_tx_115200 (
    input wire clk,
    input wire start,
    input wire [7:0] data,
    output reg tx = 1'b1,
    output reg busy = 1'b0
);
    reg [8:0] baud = 0;
    reg [3:0] bit_index = 0;
    reg [7:0] shift = 0;
    always @(posedge clk) begin
        if (!busy) begin
            tx <= 1'b1;
            if (start) begin
                busy <= 1'b1;
                tx <= 1'b0;
                baud <= 9'd433;
                bit_index <= 0;
                shift <= data;
            end
        end else if (baud != 0) baud <= baud - 1'b1;
        else begin
            baud <= 9'd433;
            if (bit_index < 4'd8) begin
                tx <= shift[0];
                shift <= {1'b0, shift[7:1]};
                bit_index <= bit_index + 1'b1;
            end else if (bit_index == 4'd8) begin
                tx <= 1'b1;
                bit_index <= 4'd9;
            end else busy <= 1'b0;
        end
    end
endmodule
