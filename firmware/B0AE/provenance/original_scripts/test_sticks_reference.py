from test_tools import *
import math
rows=[]
def span(ms,arm=1,c1=1500,c2=1500,thr=1500):rows.extend([(arm,c1,c2,thr,1,23.4,0,0,350)]*ms)
span(100,0,thr=1000);span(1400,thr=1000);span(700,c1=2000,c2=2000,thr=1555)
span(700,c1=1000,c2=2000,thr=2000);span(500,c1=1500,c2=1500,thr=1500)
span(500,c1=1300,c2=1400,thr=1000);span(100,0,thr=1000)
trace=ROOT/'tests/stick_inputs.txt';trace.write_text('\n'.join(' '.join(map(str,r))for r in rows)+'\n')
p=subprocess.run([str(ROOT/'tests/reference_oracle.exe'),'state'],input=trace.read_text(),capture_output=True,text=True,check=True)
ref=[line.split()for line in p.stdout.splitlines()]
(ROOT/'tests/stick_reference.txt').write_text(p.stdout)
inp=ROOT/'tests/stick_rtl_inputs.txt';inp.write_text('\n'.join(f'{r[1]} {r[2]} {r[3]} {c[2]}'for r,c in zip(rows,ref))+'\n')
bench=r'''
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
'''
(ROOT/'tests/sticks_reference.v').write_text(bench)
simulate('sticks_reference',[FIX/'position/ano_xy_stick.v',FIX/'position/ano_xy_divide36.v',FIX/'position/ano_z_stick.v',FIX/'position/position_math.v'],ROOT/'tests/sticks_reference.v')
rtl=[list(map(int,l.split()))for l in (ROOT/'tests/stick_rtl.txt').read_text().splitlines()]
errors=[0.,0.,0.,0.]
for r,c,v in zip(rows,ref,rtl):
 limit=max(50,min(150,1.5*r[5]))
 # Immediate hardware lock supersedes the source's final1ms speed assignment
 # before it clears taking_off at the end of Flight_State_Task.
 expected=[float(c[8])/limit,-float(c[9])/limit,float(c[7]),float(c[6])*10 if r[0] else 0]
 actual=[x/65536 for x in v]
 for j in range(4):errors[j]=max(errors[j],abs(expected[j]-actual[j]))
report=dict(samples=len(rows),max_abs_errors=dict(zip(['nx','ny','z_lpf','z_speed_mmps'],errors)),tolerances=[.001,.001,.0001,.5],reference='unchanged Flight_State_Task, my_deadzone, length_limit',passed=all(a<=b for a,b in zip(errors,[.001,.001,.0001,.5])))
(ROOT/'tests/sticks_reference.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
print(report)
