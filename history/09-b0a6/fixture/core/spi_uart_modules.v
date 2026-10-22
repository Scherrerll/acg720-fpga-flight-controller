module spi_mode3_master_1mhz (
    input wire clk,
    input wire start,
    input wire [7:0] command,
    input wire [7:0] write_byte,
    input wire [3:0] byte_count,
    input wire miso,
    output reg sck = 1'b1,
    output wire mosi,
    output reg cs_n = 1'b1,
    output reg busy = 1'b0,
    output reg done = 1'b0,
    output reg [103:0] result = 104'd0
);
    // Keep CS high for at least 10 us after every SPI transaction.  The
    // original short gap is not a confirmed datasheet violation; this is an
    // A/B diagnostic to test sensitivity to transaction spacing.
    reg [2:0] state = 3'd0;
    reg [8:0] cs_high_count = 9'd0;
    reg [5:0] div = 6'd0;
    reg [7:0] bits_left = 8'd0;
    reg first_bit = 1'b0;
    reg [103:0] tx_shift = 104'd0, rx_shift = 104'd0;
    assign mosi = tx_shift[103];
    always @(posedge clk) begin
        done <= 1'b0;
        case (state)
            3'd0: if (start) begin
                tx_shift <= {command, write_byte, 88'd0};
                rx_shift <= 104'd0;
                bits_left <= {1'b0, byte_count, 3'b000};
                div <= 6'd24;
                sck <= 1'b1;
                cs_n <= 1'b0;
                busy <= 1'b1;
                first_bit <= 1'b1;
                state <= 3'd1;
            end
            3'd1: if (div == 0) begin
                sck <= 1'b0;
                if (first_bit) first_bit <= 1'b0;
                else tx_shift <= {tx_shift[102:0], 1'b0};
                div <= 6'd24;
                state <= 3'd2;
            end else div <= div - 1'b1;
            3'd2: if (div == 0) begin
                sck <= 1'b1;
                rx_shift <= {rx_shift[102:0], miso};
                div <= 6'd24;
                if (bits_left == 8'd1) state <= 3'd3;
                else begin
                    bits_left <= bits_left - 1'b1;
                    state <= 3'd1;
                end
            end else div <= div - 1'b1;
            3'd3: if (div == 0) begin
                result <= rx_shift;
                cs_n <= 1'b1;
                // Stay busy until the guard expires so the top-level REQ
                // states cannot issue a one-cycle start pulse too early.
                busy <= 1'b1;
                done <= 1'b1;
                cs_high_count <= 9'd499;
                state <= 3'd4;
            end else div <= div - 1'b1;
            3'd4: if (cs_high_count == 0) begin
                busy <= 1'b0;
                state <= 3'd0;
            end else cs_high_count <= cs_high_count - 1'b1;
        endcase
    end
endmodule

module uart_tx_115200 (
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
