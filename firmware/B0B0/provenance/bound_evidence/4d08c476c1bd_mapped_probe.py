"""Probe actual mapped startup and serializer labels using the vendor primitives. No clocks or hardware."""
from pathlib import Path
import json,re,subprocess,os,argparse
C=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--netlist',type=Path);args=parser.parse_args()
V=args.netlist or Path(json.loads((C/'synthesis_study.json').read_text())['folder'])/'impl/gwsynthesis/acg720_ano_port.vg'
H=C/'hardware/mapped_probe';H.mkdir(exist_ok=True)
s=re.search(r'module mtf_xyz_navigation_control \(.*?endmodule',V.read_text(),re.S).group();cells=[]
for m in re.finditer(r'(?m)^  (DFF\w+) (diagnostic_q_(\d+)_\w+)\s*\((.*?)\);\s*defparam.*?INIT=(.*?);',s,re.S):
 typ,name,n,body,init=m.groups();pins={a:b.strip()for a,b in re.findall(r'\.([^\s(]+)\((.*?)\)',body,re.S)};cells.append(dict(type=typ,name=name,bit=int(n),pins=pins,init=init))
assert cells and len({c['bit']for c in cells})==len(cells)
lines=['`timescale 1ns/1ps','module tb;',"acg720_ano_port dut(.clk50(1'b0),.imu_miso(1'b0),.rc_ppm_in(1'b0),.range_rx(1'b1));",'integer i,phase;',"initial begin #10; force dut.telemetry.sending_nav=1;force dut.telemetry.sending_rotation=0;",'for(phase=0;phase<14;phase=phase+1)begin','if(phase>0)begin']
for c in cells:
 bit=c['bit'];q=c['pins']['Q'];expr="(phase==13 ? 1'b0 : 1'b1)" if bit==85 else f"((phase==2 || phase==13) ? 1'b1 : (phase>=3 && phase<=12 ? (({bit+1} >> (phase-3)) & 1) : 1'b0))"
 lines.append('force dut.native_navigation.'+q+' = '+expr+';')
lines+=['end','for(i=0;i<12;i=i+1)begin force dut.telemetry.index=i*8;#10;$display("BANK %0d %0d %016h",phase,i,dut.telemetry.decoded_bank);end','end','$finish;end endmodule']
(H/'tb.v').write_text('\n'.join(lines));(H/'bank_cells.json').write_text(json.dumps(cells,indent=2))
IV=Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin/iverilog.exe');lib=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v');tmp=C/'tmp';env=dict(os.environ,PATH=str(IV.parent)+os.pathsep+os.environ['PATH'],TMP=str(tmp),TMPDIR=str(tmp),TEMP=str(tmp))
p=subprocess.run([str(IV),'-g2012','-s','tb','-o',str(H/'sim.vvp'),str(H/'tb.v'),str(V),str(lib)],capture_output=True,text=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=300);(H/'compile.log').write_text(p.stdout+p.stderr)
if p.returncode:raise RuntimeError(p.stderr[-2500:])
print('Actual mapped primitive probe compiled',flush=True)
p=subprocess.run([str(IV.with_name('vvp.exe')),str(H/'sim.vvp')],capture_output=True,text=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=180);(H/'sim.log').write_text(p.stdout+p.stderr)
if p.returncode:raise RuntimeError(p.stdout+p.stderr)
assert len(re.findall(r'^BANK \d+ \d+ [0-9a-f]{16}$',p.stdout,re.M))==168
print('Actual mapped primitive probe completed14x12banks; compare with BDD via mapped_review.py',flush=True)
