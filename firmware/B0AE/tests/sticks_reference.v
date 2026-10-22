
`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,update=0,taking_off=0;reg[15:0]c1=1500,c2=1500,c3=1000;
wire xb,zb,xf,zf;wire signed[17:0]nx,ny,nz;wire signed[28:0]speed;
ano_xy_stick xy(.clk(clk),.rst_n(rst_n),.enabled(1'b1),.sample_update(update),.sample_dt_us(32'd1000),.ch1(c1),.ch2(c2),.nx(nx),.ny(ny),.busy(xb),.fault(xf));
ano_z_stick z(.clk(clk),.rst_n(rst_n),.enabled(1'b1),.taking_off(taking_off),.sample_update(update),.sample_dt_us(32'd1000),.ch3(c3),.norm_q16(nz),.speed_q16(speed),.busy(zb),.update(),.fault(zf));
integer f,g,rv,a,b,c,t;
initial begin
 f=$fopen("stick_rtl_inputs.txt","r");g=$fopen("stick_rtl.txt","w");
 repeat(2)@(negedge clk);rst_n=1;
 while(!$feof(f))begin
  rv=$fscanf(f,"%d %d %d %d\n",a,b,c,t);
  if(rv==4)begin
   c1=a;c2=b;c3=c;taking_off=t;update=1;@(negedge clk);update=0;
   repeat(999)@(negedge clk);
   if(xb || zb || xf || zf)$fatal(1,"stick task failed or exceeded1ms budget");
   $fwrite(g,"%d %d %d %d\n",nx,ny,nz,speed);
  end
 end
 $fclose(g);$display("stick trace complete");$finish;
end
endmodule
