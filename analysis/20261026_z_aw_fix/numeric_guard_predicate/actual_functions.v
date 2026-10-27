module predicate_0(input signed[31:0]x,output result);
function accel_in_range;
  input signed [31:0] x;
  begin
   accel_in_range=(x[31:16]=={16{x[15]}}) &&
    $signed(x[15:0])>=-16'sd30000 && $signed(x[15:0])<=16'sd30000;
  end
 endfunction
assign result=accel_in_range(x);
endmodule
module predicate_1(input signed[31:0]x,output result);
function accel_in_range;
  input signed [31:0] x;
  begin
   accel_in_range=(x[31:16]=={16{x[15]}}) &&
    $signed(x[15:0])>=-16'sd30000 && $signed(x[15:0])<=16'sd30000;
  end
 endfunction
assign result=accel_in_range(x);
endmodule
