from test_tools import *
rows=[]
def span(ms,arm=1,thr=1500,c1=1500,c2=1500,mode=0):rows.extend([(arm,c1,c2,thr,mode,23.4,0,0,350)]*ms)
span(100,0,1000);span(1400,thr=1000,c1=1580,c2=1420);span(500,thr=1555,c1=1580,c2=1420)
span(400,c1=2000,c2=2000);span(400,c1=1000,c2=1800)
span(400,c1=1600,c2=1400,mode=1);span(400,c1=1600,c2=1400)
span(400,c1=1551,c2=1449);span(100,0,1000)
trace=ROOT/'tests/manual_inputs.txt';trace.write_text('\n'.join(' '.join(map(str,r))for r in rows)+'\n')
p=subprocess.run([str(ROOT/'tests/reference_oracle.exe'),'manual'],input=trace.read_text(),capture_output=True,text=True,check=True)
ref=[l.split()for l in p.stdout.splitlines()];(ROOT/'tests/manual_reference.txt').write_text(p.stdout)
(ROOT/'tests/manual_rtl_inputs.txt').write_text('\n'.join(f'{r[1]} {r[2]} {r[4]} {c[2]}'for r,c in zip(rows,ref))+'\n')
bench=r'''
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
'''
(ROOT/'tests/manual_reference.v').write_text(bench)
simulate('manual_reference',[FIX/n for n in ['position/ano_xy_stick.v','position/ano_xy_divide36.v','core/rtl/ano_manual_angles.v']],ROOT/'tests/manual_reference.v')
obs=[list(map(int,l.split()))for l in (ROOT/'tests/manual_rtl.txt').read_text().splitlines()]
err=[0.,0.,0.,0.];bad=[]
for ms,r,p,tr,tp in obs:
 c=ref[ms-1];on=int(c[2])!=0
 exp=[float(c[17])*100 if on else 0,float(c[18])*100 if on else 0,float(c[19])*100,float(c[20])*100]
 actual=[r,p,tr/65536,-tp/65536]
 e=[abs(a-b)for a,b in zip(actual,exp)];err=[max(a,b)for a,b in zip(err,e)]
 if any(a>b for a,b in zip(e,[2,2,1,1])):bad.append([ms,e,actual,exp])
report=dict(samples=len(obs),max_abs_error_cdeg=err,allowed=[2,2,1,1],passed=not bad,differences=bad[:10],reference='original Flight_State_Task1ms, manual Loc20ms, original Att_2level_Ctrl angle/trim6ms prefix')
(ROOT/'tests/manual_reference.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
print('Original C manual angle/trim comparison passed',err)
