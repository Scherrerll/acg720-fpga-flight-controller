"""Read-only source/storage and mapped-pin inventory; no synthesis or RTL edit."""
from pathlib import Path
import collections,difflib,hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;H=R.parent/'handoff_xy_pi_runtime_20261026/workspace_snapshot/timing_closure_20261025';B=H/'v15_xy_p005_i0_syn/fixture';C=R/'candidates/response_compact/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=['ix_store','iy_store','saved_ix','saved_iy','saved_afx','saved_afy','work_p','work_i','ux_store','uy_store','ma_store','mb_store','value_store','active_p','active_i']
def inventory(path,module):
 text=path.read_text(errors='replace');m=re.search(r'^module\s+'+module+r'\s*\(.*?^endmodule',text,re.M|re.S)
 if not m:return {'present':False}
 body=m[0];cells={};loads=collections.defaultdict(list);regs={};groups=collections.defaultdict(list)
 outputs={'F','Q','O','G','V','SUM','COUT'}
 for cell in re.finditer(r'^  (\S+)\s+(\S+)\s*\((.*?)\)\s*;',body,re.M|re.S):
  typ,name,cons=cell.groups();pins=dict(re.findall(r'\.(\S+)\(([^()]*)\)',cons));cells[name]={'type':typ,'pins':pins}
  for pin,net in pins.items():
   if pin not in outputs:loads[net].append((name,pin,typ))
  if typ.startswith('DFF'):
   q=pins['Q'];base=q.split('[')[0];row={'cell':name,'type':typ,**pins};regs[name]=row;groups[base].append(row)
 def group(name,alias_base=None):
  rows=groups[name]if alias_base is None else[r for r in regs.values()if r['Q']in[f'parameter_response_{alias_base+i}'for i in range(16)]]
  indices=sorted(int(re.search(r'\[(\d+)\]',r['Q'])[1])for r in rows if '['in r['Q'])if alias_base is None else sorted(int(r['Q'].split('_')[-1])-alias_base for r in rows)
  sr=collections.Counter((p,r[p])for r in rows for p in ['RESET','SET']if p in r);ce=collections.Counter(r.get('CE','<none>')for r in rows);fan={r['Q']:len(loads[r['Q']])for r in rows}
  high=[r for r in rows if r['Q'].endswith(('[14]','[15]'))]if alias_base is None else[r for r in rows if r['Q']in[f'parameter_response_{alias_base+i}'for i in [14,15]]]
  return dict(mapped_FF=len(rows),indices=indices,FF_types=dict(collections.Counter(r['type']for r in rows)),SR_pin_nets={p+' '+net:n for(p,net),n in sr.items()},CE_nets=dict(ce),CE_total_direct_pins={net:len(loads[net])for net in ce if net!='<none>'},Q_logical_pin_loads=fan,high14_15_cells=high)
 details={name:group(name)for name in selected}
 if module=='xy_pi_parameters':
  # Synthesis aliases the pure response concatenation's coefficient fields.
  details['active_p']=group('active_p',96);details['active_i']=group('active_i',80)
 srnets=collections.Counter(r[p]for r in regs.values()for p in ['RESET','SET']if p in r)
 qualifier=[]
 for net,n in srnets.most_common(8):
  drivers=[{'cell':name,**cell}for name,cell in cells.items()if any(cell['pins'].get(pin)==net for pin in ['F','O'])]
  for d in drivers:
   init=re.search(r'defparam\s+'+re.escape(d['cell'])+r'\.INIT=([^;]+)',body)
   if init:d['INIT']=init[1]
  qualifier.append(dict(net=net,SR_pins=n,all_input_pins=len(loads[net]),pin_counts=dict(collections.Counter(p for _,p,_ in loads[net])),SR_Q_groups=dict(collections.Counter(r['Q'].split('[')[0]for r in regs.values()if any(r.get(p)==net for p in ['RESET','SET']))),driver=drivers))
 return dict(present=True,all_mapped_FF=len(regs),FF_group_counts={k:len(v)for k,v in groups.items()},selected_registers=details,largest_SR_qualifiers=qualifier,bank_coefficient_alias='active_p[15:0]=parameter_response_111..96, active_i[15:0]=parameter_response_95..80'if module=='xy_pi_parameters'else None)
files={'baseline_hold':B/'position/mtf_xyz_hold_control.v','current_hold':C/'position/mtf_xyz_hold_control.v','live_hold':R/'source/position/mtf_xyz_hold_control.v','current_bank':C/'xy_pi_parameters.v','baseline_VG':B/'impl/gwsynthesis/acg720_ano_port.vg','current_VG':C/'impl/gwsynthesis/acg720_ano_port.vg','baseline_XML':B/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml','current_XML':C/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'}
assert sha(files['baseline_hold'])=='78952264bf5a507f2f9e080e53fe0dd41b940cf13c699a134fb5aa12be539258'
assert sha(files['current_hold'])==sha(files['live_hold'])=='d79d31b434045b2da0711dd54d801646959b4c17d51b1d3fa8cd10eb284f872e'
before=inventory(files['baseline_VG'],'mtf_xyz_hold_control');after=inventory(files['current_VG'],'mtf_xyz_hold_control');bank=inventory(files['current_VG'],'xy_pi_parameters')
counts_before=before['FF_group_counts'];counts_after=after['FF_group_counts'];delta={k:{'baseline':counts_before.get(k,0),'runtime':counts_after.get(k,0),'delta':counts_after.get(k,0)-counts_before.get(k,0)}for k in counts_before.keys()|counts_after.keys()if counts_before.get(k,0)!=counts_after.get(k,0)}
sources={}
for label in ['baseline_hold','current_hold','current_bank']:
 lines=files[label].read_text().splitlines();sources[label]=[{'line':i+1,'text':l}for i,l in enumerate(lines)if any(re.search(r'\b'+n+r'\b',l)for n in selected)]
(O/'runtime_storage_controller.diff').write_text(''.join(difflib.unified_diff(files['baseline_hold'].read_text().splitlines(True),files['current_hold'].read_text().splitlines(True),fromfile='frozen_P005_I0/mtf_xyz_hold_control.v',tofile='response_compact/mtf_xyz_hold_control.v')))
out=dict(scope='read-only source proof and direct mapped-pin counts for existing frozen VGs; no RTL edit, simulation, synthesis, PNR or physical-unrouted identity inferred',files={k:{'path':str(v),'sha256':sha(v)}for k,v in files.items()},mathematical_bounds=dict(gain_legal_min=0,gain_legal_max=10000,unsigned14_max=16383,unsigned13_max=8191,integral_min=-65536000,integral_max=65536000,signed27_min=-(1<<26),signed27_max=(1<<26)-1,signed26_min=-(1<<25),signed26_max=(1<<25)-1,legal_dt_min_us=1000,legal_dt_max_us=100000,error_rail_q16=32768000,max_legal_increment_q16=(32768000*100000//1000000)*10000//1000,max_preclip_sum_q16=65536000+(32768000*100000//1000000)*10000//1000,positive_rail_truncated_signed26=((65536000+(1<<25))%(1<<26))-(1<<25),negative_rail_truncated_signed26=((-65536000+(1<<25))%(1<<26))-(1<<25)),source_mentions=sources,baseline_controller=before,runtime_controller=after,runtime_bank=bank,changed_controller_mapped_FF_groups=delta,source_ideal_FF_saving=dict(active_pair16_to14=4,work_pair16_to14=4,integral_already27=0,total_maximum=8))
(O/'runtime_storage_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(files=out['files'],controller_FF={'baseline':before['all_mapped_FF'],'runtime':after['all_mapped_FF']},changed_groups=delta,baseline_SR=before['largest_SR_qualifiers'],runtime_SR=after['largest_SR_qualifiers'],selected_current={k:after['selected_registers'][k]for k in ['ix_store','saved_ix','work_p']},bank_active={k:bank['selected_registers'][k]for k in ['active_p','active_i']}),indent=2))
