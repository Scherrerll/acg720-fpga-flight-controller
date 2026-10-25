// Same-edge zero-initialized snapshot storage using explicit GW5A BSRAM.
// READ_MODE=0 selects the bypass (not pipeline) output; WRITE_MODE=01
// forwards DI to DO on the enabled write edge, exactly as an enabled FF.
// AD[3:0]=1111 are byte enables; word address AD[13:5] remains zero.
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
