"""Same audited v4 VG/three LOGIC priorities; P3->documented timing-priority P2 only."""
from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_data_routing_followup';R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='physical_p3r0_data_route_01';new='physical_p2r0_data_route_01';assert not (O/new).exists()
for src,dst in [('run_physical.py','run_p2.py'),('launch_physical_hidden.py','launch_p2_hidden.py'),('seal_terminal.py','seal_p2.py'),('independent_raw_review.py','independent_p2_raw_review.py')]:
    t=(O/src).read_text().replace(old,new)
    if src=='run_physical.py':
        needle="'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else line";assert t.count(needle)==1
        t=t.replace(needle,"'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else 'set_option -place_option 2' if line=='set_option -place_option 3' else line")
        t=t.replace("('place_option','3')","('place_option','2')").replace("'place':3","'place':2").replace('P3/R0','P2/R0')
    if src=='launch_physical_hidden.py':t=t.replace("PLACE='3'","PLACE='2'").replace("BASE/'run_physical.py'","BASE/'run_p2.py'")
    ast.parse(t);(O/dst).write_text(t)
p=O/'physical_snapshot.py';t=p.read_text();needle="for label in ['physical_p3r0_data_route_01']:";assert t.count(needle)==1;t=t.replace(needle,"for label in ['physical_p3r0_data_route_01','physical_p2r0_data_route_01']:");ast.parse(t);p.write_text(t)
(O/new).mkdir()
report=R/'out/z_aw_fix_20261026/compact_aw_v4'/old/'source/impl/pnr/acg720_ano_port.rpt.txt';raw=report.read_text(errors='replace');s=raw[raw.index('Global Clock Signals'):];s=s[:s.index('7. Pinout by Port Name')]
obs={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_report_sha256':sha(report),'raw_global_routing_table':s,
    'actual_requested_data_nets':{'previous_pose_valid':'LW','height_fallback_active':'LW','nav_xy_ready':'LW'},
    'note':'Actual vendor report places requested BUFG=LOGIC data priorities on LW, not PRIMARY. No claim of new FF clocks; exact mapped all-FF clk50 audit and original20ns SDC remain. P3 failed306 unrouted, so no TR/Fmax claim.'}
(O/old/'ROUTING_RESOURCE_OBSERVATION.json').write_text(json.dumps(obs,indent=2)+'\n')
(O/'P2_PREPARATION.json').write_text(json.dumps({'scope':'Exact same v4 VG/source55/three combined-CST LOGIC priorities; place3->2 only. No resynthesis or hardware.',
    'basis':'P3 normal actual1/306unrouted. Vendor raw report confirms all three prioritized data nets use LW. Try documented timing-priority P2 placement for the same topology; no timing acceptance inferred.',
    'period_ns':20,'physical_options':{'place':2,'route':0,'route_maxfan':23},'source_freeze_sha256':sha(O/'source_freeze.json'),'declaration_sha256':sha(O/'DATA_ROUTE_DECLARATION.json'),
    'PNR_started':False,'scripts':{n:sha(O/n) for n in ['run_p2.py','launch_p2_hidden.py','seal_p2.py','independent_p2_raw_review.py']}},indent=2)+'\n')
print('Prepared data-priority P2 only; P3 raw LW observation saved.')
