// B0B2 输入策略：传输与配置有效性由读取器及 base_ok 判定。
// 合法加速度或角速度发生变化，本身不能证明 SPI 传输损坏。
// 不因运动幅度拒收整个六轴记录，以免对振动相位产生选择偏差。
// 估计器继续按加速度模长决定是否使用重力修正，
// 同时保持陀螺积分。
//
// 保留原有三时钟快照延迟及显式重入故障。
// 启动资格由守卫负责，源数据年龄不再使其过期；本级
// 不刷新超时期限、不伪造样本，也不以旧陀螺值替换新记录。
// record_ready 为输入单拍事件，checked_ready 为延迟三拍的结果事件；raw 仍按六个 16 位轴字段整体保存。
// diag_tick 的单位沿用输入时钟拍；bias/calibrated 及 QUIET/MOTION/CONFIRM 参数仅为接口兼容保留。
module imu_temporal_check #(
    // 为兼容原有源接口而保留的弃用参数；B0B2 中均不影响样本接受判定。
    parameter integer QUIET_SAMPLES=16,
    parameter integer QUIET_GYRO_DELTA=12,
    parameter integer QUIET_ACCEL_DELTA=32,
    parameter integer MOTION_GYRO_DELTA=1024,
    parameter integer MOTION_ACCEL_DELTA=1024,
    parameter integer CONFIRM_GYRO_DELTA=1024,
    parameter integer CONFIRM_ACCEL_DELTA=256
) (
    input wire clk,rst_n,record_ready,base_ok,calibrated,
    input wire [95:0] raw,
    input wire signed [15:0] bias_x,bias_y,bias_z,
    output reg checked_ready=0,
    output reg [7:0] reject_detail=0,
    // 保留诊断接口布局；已移除的运动候选策略不工作，因此相关输出固定为零。
    output wire [7:0] quiet_count,
    output wire candidate_pending,
    output reg [95:0] checked_raw=0,
    input wire [31:0] diag_source_id_in,diag_tick_in,
    input wire [9:0] diag_reader_meta_in,
    output reg [31:0] diag_source_id_out=0,
    output reg [31:0] diag_tick_out=0,
    output reg [9:0] diag_reader_meta_out=0,
    output reg [95:0] diag_trusted_out=0,
    output wire [95:0] diag_candidate_out,
    output reg checked_base_ok=0
);
    localparam IDLE=0, WAIT_ONE=1, WAIT_TWO=2, DECIDE=3;
    reg [1:0] state=IDLE;
    reg [95:0] held_raw=0,held_trusted=0,trusted=0;
    reg held_base_ok=0;
    reg [31:0] held_source_id=0,held_tick=0;
    reg [9:0] held_reader_meta=0;
    assign quiet_count=0;
    assign candidate_pending=0;
    assign diag_candidate_out=0;

    always @(posedge clk) begin
        checked_ready<=0;
        if(!rst_n) begin
            state<=IDLE;reject_detail<=0;checked_raw<=0;checked_base_ok<=0;
            held_raw<=0;held_base_ok<=0;held_trusted<=0;trusted<=0;
            held_source_id<=0;held_tick<=0;held_reader_meta<=0;
            diag_source_id_out<=0;diag_tick_out<=0;diag_reader_meta_out<=0;
            diag_trusted_out<=0;
        end else if(record_ready && state!=IDLE) begin
            // 若输入节奏异常，在未完成处理时又来记录，则保持失效关闭行为：
            // 丢弃未完成快照，输出发生冲突的这笔输入并用 0x80 标记重入。
            state<=IDLE;checked_ready<=1;checked_raw<=raw;
            checked_base_ok<=base_ok;reject_detail<=8'h80;
            diag_source_id_out<=diag_source_id_in;diag_tick_out<=diag_tick_in;
            diag_reader_meta_out<=diag_reader_meta_in;diag_trusted_out<=trusted;
        end else case(state)
            // 空闲时原子锁存记录、基础资格与诊断元数据；两个等待态后统一发布，不混用不同来源。
            IDLE:if(record_ready) begin
                held_raw<=raw;held_base_ok<=base_ok;held_trusted<=trusted;
                held_source_id<=diag_source_id_in;held_tick<=diag_tick_in;
                held_reader_meta<=diag_reader_meta_in;state<=WAIT_ONE;
            end
            WAIT_ONE:state<=WAIT_TWO;
            WAIT_TWO:state<=DECIDE;
            // 正常决定阶段清空拒收详情；仅基础检查合格的记录更新可信诊断快照。
            DECIDE:begin
                state<=IDLE;checked_ready<=1;checked_raw<=held_raw;
                checked_base_ok<=held_base_ok;reject_detail<=0;
                diag_source_id_out<=held_source_id;diag_tick_out<=held_tick;
                diag_reader_meta_out<=held_reader_meta;
                diag_trusted_out<=held_trusted;
                if(held_base_ok)trusted<=held_raw;
            end
            default:state<=IDLE;
        endcase
    end
endmodule
