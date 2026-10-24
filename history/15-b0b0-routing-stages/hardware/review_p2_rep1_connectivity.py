from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET,datetime
r=Path(__file__).resolve().parents[1];f=r/'variants/p2_r2_rep1/fixture'
vg=f/'impl/gwsynthesis/acg720_ano_port.vg';log=f/'impl/gwsynthesis/acg720_ano_port.log';cmd=f/'impl/pnr/cmd.do';prj=f/'impl/gwsynthesis/acg720_ano_port.prj'
t=vg.read_text();l=log.read_text();c=cmd.read_text();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bad=re.findall(r'Undeclared symbol|EX3638|EX1998|ERROR\s*\(',l);assert not bad
assert 'GowinSynthesis finish' in (f/'build_console.txt').read_text()
parent=json.loads((r/'hardware/p1_r1_synthesis_connectivity.json').read_text());e=[]
for old in parent['evidence']:
 text=old['text'];assert t.count(text)==1, text[:80]
 line=t[:t.index(text)].count('\n')+1
 e.append({'start_line':line,'end_line':line+text.count('\n'),'text':text})
opts={x.attrib.get('type'):x.attrib.get('value') for x in ET.parse(prj).findall('.//Option')}
for k,v in {'map_option':'2','opt_goal':'area','max_fanout':'200'}.items():assert opts[k]==v
assert float(opts['global_freq'])==50
for pattern in [r'^-route_maxfan 23\s*$',r'^-replicate\s*$',r'^-timing\s*$',r'^-place_option 2\s*$',r'^-route_option 2\s*$',r'^-global_freq 50\.000\s*$']:assert re.search(pattern,c,re.M)
proof=json.loads((r/'hardware/p2_rep1_hierarchical_rename_review.json').read_text());assert proof['passed'] and proof['sha256'][1]==sha(vg)
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'hardware_accessed':False,'target_warning_count':0,'evidence':e,'netlist_sha256':sha(vg),'log_sha256':sha(log),'cmd_sha256':sha(cmd),'prj_sha256':sha(prj),'actual_pnr_cmd':c,'actual_synthesis_options':{k:opts[k] for k in ['map_option','opt_goal','max_fanout','global_freq']},'structural_comparison_report_sha256':sha(r/'hardware/p2_rep1_hierarchical_rename_review.json'),'conclusion':'Repaired age/seen/controller freshness path and PWM/telemetry connectivity exactly match inspected p1_r1 snippets; full emitted netlist matches p1_r1 under two internal pose_time_adapter renames. Actual PNR replication enabled, place2 route2 route_maxfan23 50MHz. Routing acceptance remains pending.'}
(r/'hardware/p2_rep1_synthesis_connectivity.json').write_text(json.dumps(result,indent=2));print('p2_rep1 clean diagnostics, exact freshness/PWM snippets, structural comparison and actual options PASS')

