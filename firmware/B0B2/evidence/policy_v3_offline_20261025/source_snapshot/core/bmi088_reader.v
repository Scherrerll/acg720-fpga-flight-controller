// Bosch BMI088, independent accelerometer/gyro SPI dies, 50 MHz host.
// Mode 3 / 1 MHz. Accel reads include one dummy byte; gyro reads do not.
// DRDY-low -> DRDY-high qualifies each gyro epoch (DRDY auto-clears).
// Accel STATUS.DRDY qualifies the paired burst; SENSORTIME is NOT a sample ID.
// Serial pairing is not hardware synchronization. See README for bandwidths.
module bmi088_reader #(
    parameter integer BOOT_TICKS=5000000,
    parameter integer RESET_TICKS=2500000,
    parameter integer SETTLE_TICKS=2500000,
    parameter integer WRITE_WAIT_TICKS=2500000,
    parameter integer POLL_TICKS=5000
) (
    input wire clk,rst_n,miso,
    output wire sck,mosi,accel_cs_n,gyro_cs_n,
    output reg record_ready=0,
    output reg record_valid=0,
    output reg config_ok=0,
    output reg [95:0] record_raw=0,
    output reg [95:0] native_raw=0,
    output reg [7:0] accel_id=0,
    output reg [7:0] gyro_id=0,
    output reg [7:0] record_fault=0,
    output reg [31:0] rejected_count=0,
    output reg [31:0] sample_sequence=0,
    output reg [23:0] sensor_time=0,
    output reg [15:0] reset_count=0
);
    localparam BOOT=0,ACC_SPI=1,ACC_SPI_DONE=2,ACC_RESET=3,
        ACC_RESET_DONE=4,RESET_WAIT=5,GYR_RESET=6,GYR_RESET_DONE=7,
        INIT=8,INIT_DONE=9,WRITE_WAIT=10,SETTLE=11,
        HEALTH=12,HEALTH_DONE=13,CHECK=14,GYR_STATUS=15,
        GYR_STATUS_DONE=16,GYR_DATA=17,GYR_DATA_DONE=18,
        ACC_STATUS=19,ACC_STATUS_DONE=20,ACC_DATA=21,
        ACC_DATA_DONE=22,CONVERT=23,PUBLISH=24,POLL=25;
    reg [4:0] state=BOOT,after_wait=ACC_SPI;
    reg [31:0] wait_ticks=BOOT_TICKS;
    reg spi_start=0,selected_gyro=0,acc_reset_done=0,gyro_low_seen=0;
    reg [3:0] index=0,byte_count=2;
    reg [7:0] command=0,write_byte=0;
    reg [1:0] config_fail_streak=0;
    reg [7:0] ac_conf=0,ac_range=0,ac_pc=0,ac_pe=0,ac_error=0;
    reg [7:0] gy_range=0,gy_bw=0,gy_power=0,gy_int=0;
    reg [47:0] acc_data=0,gyro_data=0;
    reg [95:0] converted=0;
    reg conversion_bad=0;
    wire busy,done,spi_cs;
    wire [103:0] result;
    spi_mode3_master_1mhz spi(.clk(clk),.start(spi_start),.command(command),
        .write_byte(write_byte),.byte_count(byte_count),.miso(miso),
        .sck(sck),.mosi(mosi),.cs_n(spi_cs),.busy(busy),.done(done),.result(result));
    // selected_gyro is changed only while !busy, never on host reset.
    // The shared master has no reset port: finish an in-flight transaction
    // on the SAME die before the reset-state machine issues another request.
    assign accel_cs_n=spi_cs | selected_gyro;
    assign gyro_cs_n=spi_cs | !selected_gyro;
    wire ids_good=accel_id==8'h1e && gyro_id==8'h0f;
    wire regs_good=ac_conf==8'h8c && ac_range==8'h02 && ac_pc==0 && ac_pe==4 &&
        gy_range==0 && (gy_bw & 8'h0f)==2 && gy_power==0 && gy_int==8'h80;
    wire error_good=(ac_error & 8'h1d)==0;
    wire [7:0] health_fault={1'b0,!error_good,3'd0,!regs_good,(gyro_id!=8'h0f),(accel_id!=8'h1e)};
    function signed [17:0] normalize_accel;
        input signed [15:0] value;
        reg signed [18:0] product;
        begin
            product=$signed(value)*19'sd3;
            normalize_accel=product<0 ? -((-product+19'sd2)>>>2) : (product+19'sd2)>>>2;
        end
    endfunction
    function signed [17:0] normalize_gyro;
        input signed [15:0] value;
        reg signed [26:0] product;
        begin
            product=$signed(value)*27'sd1025;
            normalize_gyro=product<0 ? -((-product+27'sd512)>>>10) : (product+27'sd512)>>>10;
        end
    endfunction
    wire signed [15:0] native_axis=index<3 ? acc_data[47-index*16 -:16] : gyro_data[47-(index-3)*16 -:16];
    wire signed [17:0] normalized=index<3 ? normalize_accel(native_axis) : normalize_gyro(native_axis);
    wire axis_bad=normalized>18'sd32767 || normalized< -18'sd32767;
    task reject_record;
        input [7:0] fault;
        begin
            record_ready<=1;record_valid<=0;record_fault<=fault;
            if(rejected_count!=32'hffffffff)rejected_count<=rejected_count+1'b1;
            wait_ticks<=POLL_TICKS;state<=POLL;
        end
    endtask
    always @(posedge clk) begin
        spi_start<=0;record_ready<=0;
        if(!rst_n) begin
            state<=BOOT;wait_ticks<=BOOT_TICKS;after_wait<=ACC_SPI;
            acc_reset_done<=0;gyro_low_seen<=0;index<=0;
            record_valid<=0;config_ok<=0;record_raw<=0;native_raw<=0;
            accel_id<=0;gyro_id<=0;record_fault<=0;rejected_count<=0;
            sample_sequence<=0;sensor_time<=0;reset_count<=0;
            config_fail_streak<=0;acc_data<=0;gyro_data<=0;converted<=0;conversion_bad<=0;
            ac_conf<=0;ac_range<=0;ac_pc<=0;ac_pe<=0;ac_error<=0;
            gy_range<=0;gy_bw<=0;gy_power<=0;gy_int<=0;
        end else begin
            // No elapsed-silence reset. Real ID/config/status faults still reject below.
            case(state)
                BOOT:if(wait_ticks==0)state<=ACC_SPI;else wait_ticks<=wait_ticks-1'b1;
                ACC_SPI:if(!busy)begin
                    selected_gyro<=0;command<=8'h80;write_byte<=0;byte_count<=3;
                    spi_start<=1;state<=ACC_SPI_DONE;
                end
                ACC_SPI_DONE:if(done)state<=acc_reset_done ? GYR_RESET : ACC_RESET;
                ACC_RESET:if(!busy)begin
                    selected_gyro<=0;command<=8'h7e;write_byte<=8'hb6;byte_count<=2;
                    spi_start<=1;state<=ACC_RESET_DONE;
                end
                ACC_RESET_DONE:if(done)begin
                    acc_reset_done<=1;wait_ticks<=RESET_TICKS;after_wait<=ACC_SPI;state<=RESET_WAIT;
                    if(reset_count!=16'hffff)reset_count<=reset_count+1'b1;
                end
                RESET_WAIT:if(wait_ticks==0)state<=after_wait;else wait_ticks<=wait_ticks-1'b1;
                GYR_RESET:if(!busy)begin
                    selected_gyro<=1;command<=8'h14;write_byte<=8'hb6;byte_count<=2;
                    spi_start<=1;state<=GYR_RESET_DONE;
                end
                GYR_RESET_DONE:if(done)begin
                    wait_ticks<=RESET_TICKS;after_wait<=INIT;state<=RESET_WAIT;index<=0;
                end
                INIT:if(!busy)begin
                    selected_gyro<=index>=4;byte_count<=2;
                    case(index)
                        0:begin command<=8'h7c;write_byte<=0;end
                        1:begin command<=8'h7d;write_byte<=4;end
                        2:begin command<=8'h40;write_byte<=8'h8c;end
                        3:begin command<=8'h41;write_byte<=2;end
                        4:begin command<=8'h0f;write_byte<=0;end
                        5:begin command<=8'h10;write_byte<=2;end
                        6:begin command<=8'h11;write_byte<=0;end
                        7:begin command<=8'h15;write_byte<=8'h80;end
                    endcase
                    spi_start<=1;state<=INIT_DONE;
                end
                INIT_DONE:if(done)begin wait_ticks<=WRITE_WAIT_TICKS;state<=WRITE_WAIT;end
                WRITE_WAIT:if(wait_ticks!=0)wait_ticks<=wait_ticks-1'b1;
                    else if(index==7)begin wait_ticks<=SETTLE_TICKS;state<=SETTLE;end
                    else begin index<=index+1'b1;state<=INIT;end
                SETTLE:if(wait_ticks==0)begin index<=0;state<=HEALTH;end
                    else wait_ticks<=wait_ticks-1'b1;
                HEALTH:if(!busy)begin
                    write_byte<=0;selected_gyro<=index==1 || (index>=6 && index<=9);
                    byte_count<=(index==1 || (index>=6 && index<=9)) ? 2 : 3;
                    case(index)
                        0,1:command<=8'h80;
                        2:command<=8'hc0;
                        3:command<=8'hc1;
                        4:command<=8'hfc;
                        5:command<=8'hfd;
                        6:command<=8'h8f;
                        7:command<=8'h90;
                        8:command<=8'h91;
                        9:command<=8'h95;
                        10:command<=8'h82; // ACC_ERR_REG; ignore only reserved bits.
                    endcase
                    spi_start<=1;state<=HEALTH_DONE;
                end
                HEALTH_DONE:if(done)begin
                    case(index)
                        0:accel_id<=result[7:0];1:gyro_id<=result[7:0];
                        2:ac_conf<=result[7:0];3:ac_range<=result[7:0];
                        4:ac_pc<=result[7:0];5:ac_pe<=result[7:0];
                        6:gy_range<=result[7:0];7:gy_bw<=result[7:0];
                        8:gy_power<=result[7:0];9:gy_int<=result[7:0];
                        10:ac_error<=result[7:0];
                    endcase
                    if(index==10)state<=CHECK;else begin index<=index+1'b1;state<=HEALTH;end
                end
                CHECK:begin
                    config_ok<=ids_good && regs_good && error_good;
                    if(ids_good && regs_good && error_good)begin config_fail_streak<=0;state<=GYR_STATUS;end
                    else begin
                        reject_record(health_fault);
                        if(config_fail_streak==2)begin
                            config_fail_streak<=0;acc_reset_done<=0;gyro_low_seen<=0;
                            wait_ticks<=BOOT_TICKS;state<=BOOT;
                        end else config_fail_streak<=config_fail_streak+1'b1;
                    end
                end
                GYR_STATUS:if(!busy)begin
                    selected_gyro<=1;command<=8'h8a;write_byte<=0;byte_count<=2;
                    spi_start<=1;state<=GYR_STATUS_DONE;
                end
                GYR_STATUS_DONE:if(done)begin
                    if(!result[7])begin gyro_low_seen<=1;wait_ticks<=POLL_TICKS;after_wait<=GYR_STATUS;state<=RESET_WAIT;end
                    else if(gyro_low_seen)begin gyro_low_seen<=0;state<=GYR_DATA;end
                    else begin wait_ticks<=POLL_TICKS;after_wait<=GYR_STATUS;state<=RESET_WAIT;end
                end
                GYR_DATA:if(!busy)begin
                    selected_gyro<=1;command<=8'h82;write_byte<=0;byte_count<=7;
                    spi_start<=1;state<=GYR_DATA_DONE;
                end
                GYR_DATA_DONE:if(done)begin
                    gyro_data<={result[39:32],result[47:40],result[23:16],result[31:24],result[7:0],result[15:8]};
                    state<=ACC_STATUS;
                end
                ACC_STATUS:if(!busy)begin
                    selected_gyro<=0;command<=8'h83;write_byte<=0;byte_count<=3;
                    spi_start<=1;state<=ACC_STATUS_DONE;
                end
                ACC_STATUS_DONE:if(done)begin
                    if(result[7])state<=ACC_DATA;else reject_record(8'h08);
                end
                ACC_DATA:if(!busy)begin
                    selected_gyro<=0;command<=8'h92;write_byte<=0;byte_count<=11;
                    spi_start<=1;state<=ACC_DATA_DONE;
                end
                ACC_DATA_DONE:if(done)begin
                    // Accel XYZ LE then free-running sensor-time LE24.
                    acc_data<={result[63:56],result[71:64],result[47:40],result[55:48],result[31:24],result[39:32]};
                    sensor_time<={result[7:0],result[15:8],result[23:16]};
                    conversion_bad<=0;index<=0;state<=CONVERT;
                end
                CONVERT:begin
                    converted[95-index*16 -:16]<=normalized[15:0];
                    conversion_bad<=conversion_bad || axis_bad;
                    if(index==5)state<=PUBLISH;else index<=index+1'b1;
                end
                PUBLISH:begin
                    if(conversion_bad)reject_record(8'h20);
                    else begin
                        record_raw<=converted;native_raw<={acc_data,gyro_data};
                        record_valid<=1;record_ready<=1;record_fault<=0;
                        sample_sequence<=sample_sequence+1'b1;
                        wait_ticks<=POLL_TICKS;state<=POLL;
                    end
                end
                POLL:if(wait_ticks==0)begin index<=0;state<=HEALTH;end
                    else wait_ticks<=wait_ticks-1'b1;
                default:begin state<=BOOT;wait_ticks<=BOOT_TICKS;config_ok<=0;acc_reset_done<=0;end
            endcase
        end
    end
endmodule
