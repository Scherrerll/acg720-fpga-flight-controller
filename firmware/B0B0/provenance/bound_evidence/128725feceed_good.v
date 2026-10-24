module sink(input [15:0] collective,input valid,output [15:0] c,output v);assign c=collective;assign v=valid;endmodule
module good(input a,input [15:0] x,output [15:0] c,output v,output pub);
wire [15:0] selected_throttle;wire rate_fresh;
sink s(.collective(selected_throttle),.valid(rate_fresh),.c(c),.v(v));
assign selected_throttle=x;assign rate_fresh=a;assign pub=rate_fresh;
endmodule
