from test_tools import *
import random

rows=[]
def span(ms,arm=0,thr=1000,collective=350):
 rows.extend([(arm,1500,1500,thr,1,23.4,0,0,collective)]*ms)
span(100);span(1800,1);span(1100,1,1554);span(100,1,1555);span(1200,1,1500)
span(200,1,2000);span(1900,1,1000,200);span(100)
# Interrupted preparation, high-stick arm adapter input, boundary chatter.
span(450,1);span(20);span(900,1,2000);span(1100,1,1500);span(20)
random.seed(81021)
for _ in range(40):
 span(random.randrange(2,120),1,random.choice([1000,1150,1200,1201,1406,1554,1555,1593,1594,2000]),random.choice([200,250,350]))
span(1600,1,1000,200);span(30)
trace=ROOT/'tests/state_inputs.txt';trace.write_text('\n'.join(' '.join(map(str,row))for row in rows)+'\n')
p=subprocess.run([str(ROOT/'tests/reference_oracle.exe'),'state'],input=trace.read_text(),capture_output=True,text=True,check=True)
(ROOT/'tests/state_reference.txt').write_text(p.stdout)
ref=[line.split()for line in p.stdout.splitlines()]
bench=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,armed=0;reg [15:0]ch3=1000,collective=1350;
wire prep,takeoff,flying,land;wire[3:0]mask;
ano_flight_state #(.TICKS_PER_MS(20)) dut(.clk(clk),.rst_n(rst_n),.armed(armed),.ch3(ch3),.collective_us(collective),.motor_prepared(prep),.taking_off(takeoff),.flying(flying),.land_lock(land),.preparation_mask(mask));
integer f,g,k,rv,a,c1,c2,c3,fl;real h,v,acc,t;
initial begin
 f=$fopen("state_inputs.txt","r");g=$fopen("state_rtl.txt","w");
 repeat(2)@(negedge clk);rst_n=1;
 while(!$feof(f))begin
  rv=$fscanf(f,"%d %d %d %d %d %f %f %f %f\n",a,c1,c2,c3,fl,h,v,acc,t);
  if(rv==9)begin
   armed=a;ch3=c3;collective=1000+$rtoi(t);
   repeat(20)@(negedge clk);
   $fwrite(g,"%d %d %d %d %d\n",prep,takeoff,flying,land,mask);
  end
 end
 $fclose(g);$display("state trace completed");$finish;
end
endmodule
'''
(ROOT/'tests/state_reference.v').write_text(bench)
simulate('state_reference',[FIX/'core/ano_flight_state.v'],ROOT/'tests/state_reference.v')
rtl=[list(map(int,line.split()))for line in (ROOT/'tests/state_rtl.txt').read_text().splitlines()]
assert len(ref)==len(rtl)==len(rows)
diff=[]
for i,(c,v)in enumerate(zip(ref,rtl)):
 expected=list(map(int,c[1:5]))
 expected[3]=expected[3] if rows[i][0] else 0
 # The physical adapter clears immediately; the source clears motor prep in
 # its2ms task. Compare state at all2ms boundaries and every armed1ms task.
 if rows[i][0] or (i+1)%2==0:
  if expected!=v[:4]:diff.append((i+1,expected,v[:4]))
report=dict(samples=len(rows),differences=diff[:40],passed=not diff,reference='unchanged Flight_State_Task, land_discriminat, Motor_Ctrl_Task',hardware_accessed=False)
(ROOT/'tests/state_reference.json').write_text(json.dumps(report,indent=2))
assert not diff,report
print('ANO original C state comparison passed:',len(rows),'ms')
