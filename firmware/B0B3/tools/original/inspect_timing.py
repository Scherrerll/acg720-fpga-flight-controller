"""Read genuine Gowin post-route tables without modifying vendor evidence."""
from pathlib import Path
import sys,re,json,hashlib
R=Path(__file__).resolve().parent;F=R/sys.argv[1] if len(sys.argv)>1 else R
P=F/'source/impl/pnr';base=P/'acg720_ano_port';text=base.with_suffix('.tr').read_text(errors='replace')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def section(start,end):
 return re.search(r'^'+re.escape(start)+r'\s*$(.*?)^'+re.escape(end),text,re.S|re.M)[1]
checks={}
for name,start,end in [('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table'),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table'),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table')]:
 block=section(start,end);entries=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',block,re.M)
 assert entries,(name,block[:300])
 checks[name]=dict(worst_slack_ns=min(float(e[1])for e in entries),reported_paths=len(entries),worst_path=dict(zip(['number','slack_ns','from','to','from_clock','to_clock','relation_ns','skew_ns','data_delay_ns'],entries[0])))
block=section('3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type')
pulses=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+?)\s+(clk50)\s+(\S+)\s*$',block,re.M)
assert pulses
checks['minimum_pulse_width']=dict(worst_slack_ns=min(float(e[1])for e in pulses),reported_paths=len(pulses),worst_path=pulses[0])
clock=re.search(r'^\s+1\s+clk50\s+Base\s+(\d+\.\d+)\s+',text,re.M);assert clock
fmax=re.search(r'^\s+1\s+clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',text,re.M);assert fmax
setup_count=int(re.search(r'<Numbers of Setup Violated Endpoints>:(\d+)',text)[1]);hold_count=int(re.search(r'<Numbers of Hold Violated Endpoints>:(\d+)',text)[1])
log=(F/'verification/gowin.log').read_text(errors='replace')
route_unrouted=re.findall(r'(?i)(?:unrouted\s+(?:nets|connections)|(?:nets|connections)\s+unrouted)\D*(\d+)',log)
out=dict(fixture=str(F),parser_sha256=sha(Path(__file__)),period_ns=float(clock[1]),fmax_mhz=float(fmax[2]),setup_violated_endpoints=setup_count,hold_violated_endpoints=hold_count,checks=checks,
 timing_passed=float(clock[1])==20 and setup_count==0 and hold_count==0 and all(c['worst_slack_ns']>=0 for c in checks.values()),
 route_unrouted_log_matches=route_unrouted,
 timing_constraints_report=text.split('3.8 Timing Constraints Report')[-1].strip(),
 timing_exceptions_report=text.split('3.7 Timing Exceptions Report')[-1].split('3.8 Timing Constraints Report')[0].strip(),
 evidence_sha256={p.name:sha(p)for p in [base.with_suffix('.tr'),base.with_suffix('.pr'),base.with_suffix('.fs'),F/'source/acg720_ano_port.sdc',F/'source/impl/gwsynthesis/acg720_ano_port.vg'] if p.exists()})
(F/'verification/timing_review.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if '--require-pass' in sys.argv:assert out['timing_passed'],'post-route timing not closed'
