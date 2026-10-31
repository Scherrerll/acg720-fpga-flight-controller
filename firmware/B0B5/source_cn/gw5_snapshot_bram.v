// 自写的高云存储原语封装；SP 原语名称与参数属于厂商接口，保持原样。
// WIDTH 位输入在 enable 有效的时钟沿更新，q 在其他时钟保持上一份快照。
// 自写快照存储封装：显式实例化 GW5A BSRAM，保持零初值及同沿更新语义。
// READ_MODE=0 选择旁路输出而非流水输出；WRITE_MODE=01
// 在使能写入沿将 DI 送到 DO，与带使能触发器的更新行为一致。
// AD[3:0]=1111 为字节使能，字地址 AD[13:5] 固定为零。
module gw5_snapshot_bram #(parameter integer WIDTH=32)(
 input wire clk,enable,input wire[WIDTH-1:0] data,output wire[WIDTH-1:0] q
);
`ifdef __ICARUS__
 `ifdef GW5_USE_VENDOR_BRAM
 localparam integer SIMULATION_BYPASS=0;
 `else
 localparam integer SIMULATION_BYPASS=1;
 `endif
`else
 localparam integer SIMULATION_BYPASS=0;
`endif
 generate if(SIMULATION_BYPASS)begin: portable_simulation
  reg[WIDTH-1:0] held=0;
  always @(posedge clk)if(enable)held<=data;
  assign q=held;
 end else begin: hardware_bram
  localparam integer BANKS=(WIDTH+31)/32;
  wire[BANKS*32-1:0] padded_data={{(BANKS*32-WIDTH){1'b0}},data};
  wire[BANKS*32-1:0] padded_q;
  genvar bank;for(bank=0;bank<BANKS;bank=bank+1)begin:banks
   SP #(.READ_MODE(1'b0),.WRITE_MODE(2'b01),.BIT_WIDTH(32),
        .BLK_SEL(3'b000),.RESET_MODE("SYNC")) memory(
    .DO(padded_q[bank*32+:32]),.DI(padded_data[bank*32+:32]),
    .BLKSEL(3'b000),.AD(14'h000f),.WRE(1'b1),.CLK(clk),
    .CE(enable),.OCE(1'b1),.RESET(1'b0));
  end
  assign q=padded_q[WIDTH-1:0];
 end endgenerate
endmodule
