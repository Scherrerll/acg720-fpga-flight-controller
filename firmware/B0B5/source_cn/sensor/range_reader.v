// TFmini-S 默认 UART 帧读取顶层，时钟 50 MHz、115200 波特、8N1。
// range_rx 为异步串口输入，rst_n 为低有效异步复位；内部先收字节再解析 0x59 0x59 帧。
// distance_cm 保持 TFmini 默认协议的厘米单位，strength 为原始信号强度；
// temp_raw 保持协议小端无符号原始字，未换算为摄氏度。
// 完整合法帧一次性发布，sample_valid 脉冲一拍；错误不发布半帧或距离哨兵值，
// 上次正确数据继续可见，其 source_age_ticks 继续增长，link_ok 同时反映最新帧可用性。
// STALE_TICKS/INTERBYTE_TICKS/source_age_ticks 单位为 20 ns 时钟拍；
// sample_sequence 按 32 位回绕，good_count/error_count 及各错误分类计数在全 1 时饱和。
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
    output wire [31:0] sample_sequence, output wire [31:0] good_count,
    output wire [199:0] diagnostics
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
        .good_count(good_count), .diagnostics(diagnostics)
    );
endmodule

// TFmini 9 字节帧解析器：两字节 0x59 帧头、6 字节载荷、前 8 字节累加和的低 8 位校验。
// rx_valid/串口错误由上一级产生一拍脉冲；输出距离/强度/温度仅在校验和门限均通过时更新。
// 距离必须非零、低于 0xFF00 且处于 MIN_DISTANCE_CM..MAX_DISTANCE_CM，强度须达到 MIN_STRENGTH。
// source_age_ticks 仅在接受帧时归零；错误会撤销 last_frame_usable，恢复须等待下一完整正确帧。
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
    output reg [31:0] good_count = 0,
    output wire [199:0] diagnostics
);
    // 按解析优先级互斥统计错误，不反馈到接收路径；原因码 1 帧格式、2 校验、3 超时、4 距离、5 强度。
    // diagnostics 从高到低为 5 个 32 位分类计数、8 位原因、16 位拒绝距离和 16 位拒绝强度。
    reg [31:0] framing_errors=0,checksum_errors=0,timeout_errors=0;
    reg [31:0] distance_errors=0,strength_errors=0;
    reg [7:0] last_reject_reason=0;
    reg [15:0] last_reject_distance=0,last_reject_strength=0;
    assign diagnostics={framing_errors,checksum_errors,timeout_errors,
        distance_errors,strength_errors,last_reject_reason,
        last_reject_distance,last_reject_strength};
    function [31:0] increment; input [31:0] value;
        begin increment=value==32'hFFFFFFFF ? value:value+1'b1;end
    endfunction
    // 状态 0/1 搜索双帧头，2..7 累积载荷，8 消费校验；byte_age 约束半帧字节间隔。
    reg [3:0] frame_state = 0;
    reg [7:0] sum = 0;
    reg [47:0] frame_bytes = 0;
    reg [31:0] byte_age = 0;
    reg sample_seen = 0, last_frame_usable = 0;
    // 接收移位寄存器按先后顺序保存 6 字节；每个 16 位协议字段再按小端重组。
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
            framing_errors<=0;checksum_errors<=0;timeout_errors<=0;
            distance_errors<=0;strength_errors<=0;last_reject_reason<=0;
            last_reject_distance<=0;last_reject_strength<=0;
        end else begin
            sample_valid <= 0;
            if (source_age_ticks != 32'hFFFFFFFF)
                source_age_ticks <= source_age_ticks + 1'b1;
            if (frame_state != 0 && byte_age != 32'hFFFFFFFF)
                byte_age <= byte_age + 1'b1;

            // 错误优先级为串口帧错误、新字节处理、最后字节间超时；每次只记一类拒绝原因。
            if (rx_frame_error) begin
                frame_state <= 0; byte_age <= 0; last_frame_usable <= 0;
                framing_errors<=increment(framing_errors);last_reject_reason<=1;
                last_reject_distance<=0;last_reject_strength<=0;
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
                        if(rx_byte!=sum) begin
                            checksum_errors<=increment(checksum_errors);
                            last_reject_reason<=2;last_reject_distance<=0;last_reject_strength<=0;
                        end else begin
                            // 只有校验正确时才在拒绝诊断中保留载荷数值，避免把坏字节当作距离/强度证据。
                            last_reject_distance<=pending_distance;last_reject_strength<=pending_strength;
                            if(pending_distance==0 || pending_distance>=16'hFF00 ||
                               pending_distance<MIN_DISTANCE_CM || pending_distance>MAX_DISTANCE_CM) begin
                                distance_errors<=increment(distance_errors);last_reject_reason<=4;
                            end else begin
                                strength_errors<=increment(strength_errors);last_reject_reason<=5;
                            end
                        end
                        if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
                    end
                    // 当前字节已作为校验消费，不能再用作下一帧帧头；合法校验 0x59 后紧接
                    // 下一帧 0x59 0x59 时，否则会导致载荷错位一字节。
                    // 若传输丢字节，此恢复策略可能需要再等待一帧。
                    frame_state <= 0;
                end
            end else if (frame_state != 0 && byte_age >= INTERBYTE_TICKS - 1) begin
                frame_state <= 0; byte_age <= 0; last_frame_usable <= 0;
                timeout_errors<=increment(timeout_errors);last_reject_reason<=3;
                last_reject_distance<=0;last_reject_strength<=0;
                if (error_count != 32'hFFFFFFFF) error_count <= error_count + 1'b1;
            end
        end
    end
endmodule

// 保留原 434 个时钟拍一位的 UART 接收时序，对应 50 MHz/115200、8N1。
// rx 先经过两级同步；检测低电平后约 1.5 位时采第 0 位，再按位周期采 8 位，最低位先行。
// 停止位为高才发布 data 和一拍 valid；为低则仅发一拍 frame_error 供解析器丢弃半帧。
// rst_n 为低有效异步复位；停止后等待 RX 回高，再重新搜索起始位。
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
            // 0 搜索起始位，1 接收数据，2 检查停止位，3 等待总线回高。
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
