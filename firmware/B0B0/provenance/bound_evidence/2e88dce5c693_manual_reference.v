
`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,sample=0,outer=0,en=0,mode=0;reg[15:0]c1=1500,c2=1500;
wire nu,nv,nb,nf,mu,mb;wire[15:0]nd;wire[7:0]mf;wire signed[17:0]nx,ny;wire signed[15:0]r,p,sr,sp;
ano_xy_stick fs(.clk(clk),.rst_n(rst_n),.enabled(1'b1),.sample_update(sample),.sample_dt_us(32'd1000),.ch1(c1),.ch2(c2),.nx(nx),.ny(ny),.busy(nb),.fault(nf),.update(nu),.valid(nv),.output_dt_us(nd));
ano_manual_angles dut(.clk(clk),.rst_n(rst_n),.sample_update(nu),.norm_valid(nv),.outer_update(outer),.enabled(en),.att_stab(!mode),
 .norm_roll_q16(ny),.norm_pitch_q16(nx),.norm_dt_us(nd),.outer_dt_ticks(32'd300000),.roll_cdeg(-16'sd315),.pitch_cdeg(16'sd190),.loc_override(1'b0),.loc_roll_cdeg(16'sd0),.loc_pitch_cdeg(16'sd0),
 .manual_roll_cdeg(r),.manual_pitch_cdeg(p),.snapshot_roll_cdeg(sr),.snapshot_pitch_cdeg(sp),.update(mu),.busy(mb),.fault(mf));
integer f,g,rv,a,b,c,d,msidx=0,last_outer=0;
always @(negedge clk)if(rst_n && mu)begin
 if(sr!=-315 || sp!=190)$fatal(1,"outer feedback tuple");
 $fwrite(g,"%d %d %d %d %d\n",last_outer,r,-p,dut.tr,dut.tp);
end
initial begin
 f=$fopen("manual_rtl_inputs.txt","r");g=$fopen("manual_rtl.txt","w");
 repeat(3)@(negedge clk);rst_n=1;
 while(!$feof(f))begin
  rv=$fscanf(f,"%d %d %d %d\n",a,b,c,d);
  if(rv==4)begin
   msidx=msidx+1;c1=a;c2=b;mode=c;en=d;sample=1;outer=msidx%6==0;if(outer)last_outer=msidx;
   @(negedge clk);sample=0;outer=0;repeat(1999)@(negedge clk);
   if(nf || mf || nb || mb)$fatal(1,"shared manual chain failed its source period");
  end
 end
 $fclose(g);$display("manual source trace complete");$finish;
end
endmodule
