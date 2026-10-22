// TFmini-S default UART frame reader (50 MHz / 115200 / 8N1).
// Distance retains the default TFmini protocol unit: centimeters. Temperature
// remains the unsigned raw little-endian protocol word, not degrees Celsius.
// Valid frames are published atomically. Errors never publish partially received
// or sentinel distances; the previous good value remains visible with its age.
module range_reader #(
    parameter integer STALE_TICKS = 5_000_000,
    parameter integer INTERBYTE_TICKS = 100_000,
    parameter integer MIN_DISTANCE_CM = 10,
    parameter integer MAX_DISTANCE_CM = 1200,
    parameter integer MIN_STRENGTH = 100
)(
    input wire clk50, input wire rst_n, input wire range_rx,
    output wire [15:0] distance_cm, output wire [15:0] strength,
    output wire [15:0] temp_raw, output wire sample_valid, output wire link_ok,
    output wire [31:0] source_age_ticks, output wire [31:0] error_count,
    output wire [31:0] sample_sequence, output wire [31:0] good_count
);
    wire [7:0] rx_byte;
    wire rx_valid, rx_frame_error;
    range_uart_rx_115200 rx_unit (
        .clk(clk50), .rst_n(rst_n), .rx(range_rx), .data(rx_byte),
        .valid(rx_valid), .frame_error(rx_frame_error)
    );
    range_frame_parser #(
        .STALE_TICKS(STALE_TICKS), .INTERBYTE_TICKS(INTERBYTE_TICKS),
        .MIN_DISTANCE_CM(MIN_DISTANCE_CM), .MAX_DISTANCE_CM(MAX_DISTANCE_CM),
        .MIN_STRENGTH(MIN_STRENGTH)
    ) parser (
        .clk50(clk50), .rst_n(rst_n), .rx_byte(rx_byte), .rx_valid(rx_valid),
        .rx_frame_error(rx_frame_error), .distance_cm(distance_cm),
        .strength(strength), .temp_raw(temp_raw), .sample_valid(sample_valid),
        .link_ok(link_ok), .source_age_ticks(source_age_ticks),
        .error_count(error_count), .sample_sequence(sample_sequence),
        .good_count(good_count)
    );
endmodule

module range_frame_parser #(
    parameter integer STALE_TICKS = 5_000_000,
    parameter integer INTERBYTE_TICKS = 100_000,
    parameter integer MIN_DISTANCE_CM = 10,
    parameter integer MAX_DISTANCE_CM = 1200,
    parameter integer MIN_STRENGTH = 100
)(
    input wire clk50, input wire rst_n, input wire [7:0] rx_byte,
    input wire rx_valid, input wire rx_frame_error,
    output reg [15:0] distance_cm = 0, output reg [15:0] strength = 0,
    output reg [15:0] temp_raw = 0, output reg sample_valid = 0,
    output wire link_ok,
    output reg [31:0] source_age_ticks = 32'hFFFFFFFF,
    output reg [31:0] error_count = 0, output reg [31:0] sample_sequence = 0,
    output reg [31:0] good_count = 0
);
    reg [3:0] frame_state = 0;
    reg [7:0] sum = 0;
    reg [47:0] frame_bytes = 0;
    reg [31:0] byte_age = 0;
    reg sample_seen = 0, last_frame_usable = 0;
    wire [15:0] pending_distance = {frame_bytes[39:32], frame_bytes[47:40]};
    wire [15:0] pending_strength = {frame_bytes[23:16], frame_bytes[31:24]};
    wire [15:0] pending_temperature = {frame_bytes[7:0], frame_bytes[15:8]};
    wire pending_usable = pending_distance != 0 &&
        pending_distance < 16'hFF00 && pending_distance >= MIN_DISTANCE_CM &&
        pending_distance <= MAX_DISTANCE_CM &&
        pending_strength >= MIN_STRENGTH;
    assign link_ok = sample_seen && last_frame_usable &&
                     source_age_ticks < STALE_TICKS;

    always @(posedge clk50 or negedge rst_n) begin
        if (!rst_n) begin
            frame_state <= 0; sum <= 0; frame_bytes <= 0; byte_age <= 0;
            distance_cm <= 0; strength <= 0; temp_raw <= 0; sample_valid <= 0;
            source_age_ticks <= 32'hFFFFFFFF; error_count <= 0;
            sample_sequence <= 0; good_count <= 0;
            sample_seen <= 0; last_frame_usable <= 0;
        end else begin
            sample_valid <= 0;
            if (source_age_ticks != 32'hFFFFFFFF)
                source_age_ticks <= source_age_ticks + 1'b1;
            if (frame_state != 0 && byte_age != 32'hFFFFFFFF)
                byte_age <= byte_age + 1'b1;

            if (rx_frame_error) begin
                frame_state <= 0; byte_age <= 0; last_frame_usable <= 0;
                if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
            end else if (rx_valid) begin
                byte_age <= 0;
                if (frame_state == 0) begin
                    if (rx_byte == 8'h59) begin
                        frame_state <= 1; sum <= 8'h59;
                    end
                end else if (frame_state == 1) begin
                    if (rx_byte == 8'h59) begin
                        frame_state <= 2; sum <= 8'hB2; frame_bytes <= 0;
                    end else frame_state <= 0;
                end else if (frame_state < 8) begin
                    frame_bytes <= {frame_bytes[39:0], rx_byte};
                    sum <= sum + rx_byte;
                    frame_state <= frame_state + 1'b1;
                end else begin
                    if (rx_byte == sum && pending_usable) begin
                        distance_cm <= pending_distance;
                        strength <= pending_strength;
                        temp_raw <= pending_temperature;
                        sample_sequence <= sample_sequence + 1'b1;
                        if (good_count != 32'hFFFFFFFF) good_count <= good_count + 1'b1;
                        sample_valid <= 1; sample_seen <= 1; last_frame_usable <= 1;
                        source_age_ticks <= 0;
                    end else begin
                        last_frame_usable <= 0;
                        if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
                    end
                    // This byte has been consumed as checksum. Never seed a
                    // new header from it: legitimate checksum 59 followed by
                    // the next 59 59 frame must not shift the payload by one.
                    // After a dropped byte, recovery can take one more frame.
                    frame_state <= 0;
                end
            end else if (frame_state != 0 && byte_age >= INTERBYTE_TICKS - 1) begin
                frame_state <= 0; byte_age <= 0; last_frame_usable <= 0;
                if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
            end
        end
    end
endmodule

// Original 434-clock bit timing is retained; explicit reset and a bad-stop
// pulse are added for parser recovery and honest diagnostics.
module range_uart_rx_115200 (
    input wire clk, input wire rst_n, input wire rx,
    output reg [7:0] data = 0, output reg valid = 0,
    output reg frame_error = 0
);
    reg [1:0] sync = 2'b11, state = 0;
    reg [9:0] timer = 0;
    reg [2:0] bit_index = 0;
    reg [7:0] shift = 0;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync <= 2'b11; state <= 0; timer <= 0; bit_index <= 0;
            shift <= 0; data <= 0; valid <= 0; frame_error <= 0;
        end else begin
            sync <= {sync[0], rx}; valid <= 0; frame_error <= 0;
            case (state)
                2'd0: if (!sync[1]) begin
                    timer <= 10'd650; bit_index <= 0; state <= 1;
                end
                2'd1: if (timer == 0) begin
                    shift[bit_index] <= sync[1]; timer <= 10'd433;
                    if (bit_index == 7) state <= 2;
                    else bit_index <= bit_index + 1'b1;
                end else timer <= timer - 1'b1;
                2'd2: if (timer == 0) begin
                    if (sync[1]) begin data <= shift; valid <= 1; end
                    else frame_error <= 1;
                    state <= 3;
                end else timer <= timer - 1'b1;
                2'd3: if (sync[1]) state <= 0;
            endcase
        end
    end
endmodule
