"""Preserve reported critical-cell placement; regionally move three late launch FFs."""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent/'compact_aw_v4_partial_floorplan_followup';D=O.parent/'compact_aw_v4_p3mf60_followup';R=O.parents[3]
assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v4';VG=ROOT/'build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg';TR=ROOT/'physical_p3r0_01/source/impl/pnr/acg720_ano_port.tr'
reader=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026/tools/read_cones.py');sp=importlib.util.spec_from_file_location('raw_cell_binding',reader);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);g=m.Graph(VG)
t=TR.read_text(errors='replace');core=t[t.index('Note:Core Timing Report'):];a=core.index('3.3.1 Setup Analysis');b=core.index('3.3.2 Hold Analysis',a);t=core[a:b];locs={}
for loc,node in re.findall(r'\b(R\d+C\d+(?:\[[^\]]+\])+)\s+(\S+)',t):
    n=node if node in g.cells else node.rsplit('/',1)[0]
    if n in g.cells:locs.setdefault(n,set()).add(loc)
assert len(locs)==109 and all(len(x)==1 for x in locs.values())
assert all(re.fullmatch(r'LUT[1-5]|DFFRE|DFFCE',g.cells[n]['type']) for n in locs)
locations={n:next(iter(x)) for n,x in sorted(locs.items())};old=dict(locations)
regions={'acc_time/output_az_3_s0':'R[33:35]C[23:25]','mtf/metric/vy_x100_28_s0':'R[49:51]C[55:57]','previous_pose_valid_s0':'R[35:37]C[77:79]'}
assert all(n in g.regs for n in regions);locations.update(regions)
floorplan={'scope':'All109 mapped cells on the raw top25 setup representatives; preserve106 old locations and give3 source FFs small regions near their old first LUT. Not an enumeration of every violated endpoint and not a timing proof.',
    'locations':locations,'baseline_locations':old,'three_changed_to_regions':regions,'types':{n:g.cells[n]['type'] for n in locations},
    'raw_TR_sha256':sha(TR),'raw_VG_sha256':sha(VG),'graph_reader_sha256':sha(reader),'location_syntax_manual':'SUG1541-1.0E PDF17-19',
    'reason':'Moving3 FFs with all other cells unconstrained failed PR0004/unrouted0/noTR/noFS. Preserve the already-known critical logic clusters and let regional FF constraints choose legal free sites instead of hard-binding a possibly incompatible LUT/FF pair.'}
(O/'FLOORPLAN_FROM_RAW.json').write_text(json.dumps(floorplan,indent=2)+'\n');(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p3r0_partial_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_mf60_01',label)
    if name=='run_physical.py':
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23' else ",'').replace("('route_maxfan','60')","('route_maxfan','23')").replace("'route_maxfan':60","'route_maxfan':23").replace('Maxfan60','partial critical floorplan')
        marker="    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    floorplan=json.loads((O/'FLOORPLAN_FROM_RAW.json').read_text());locations=floorplan['locations'];assert len(locations)==109\n    assert floorplan['raw_VG_sha256']==VG_SHA\n    constraints=SOURCE/'physical_constraints.cst';original_cst=(SOURCE/'acg720_ano_port.cst').read_bytes()\n    extra_cst='\\n// Raw critical-path physical-only floorplan; immutable IO prefix retained.\\n'+''.join('INS_LOC '+json.dumps(n)+' '+loc+';\\n' for n,loc in locations.items())\n    constraints.write_bytes(original_cst+extra_cst.encode('ascii'))\n    write('placement_constraint_binding.json',{'original_cst_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_cst_sha256':sha(constraints),'locations':locations,'floorplan_from_raw_sha256':sha(O/'FLOORPLAN_FROM_RAW.json'),'added_commands':'INS_LOC only109; original SDC and18pins unchanged'})\n")
        t=t.replace("('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
        t=t.replace("'period_ns':20,'usercode':'0000B0B4'","'period_ns':20,'usercode':'0000B0B4','combined_cst_sha256':sha(constraints),'floorplan_from_raw_sha256':sha(O/'FLOORPLAN_FROM_RAW.json')")
    if name=='seal_terminal.py':
        t=t.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()","paths += [V/'placement_constraint_binding.json',ATTEMPT/'source/physical_constraints.cst',O/'FLOORPLAN_FROM_RAW.json']\npaths=[p for p in paths if p.is_file()];copies.mkdir()")
    ast.parse(t);(O/name).write_text(t)
t=(O.parent/'compact_aw_v4_loc3_followup/independent_raw_review.py').read_text().replace('physical_p3r0_inc_loc3_01',label)
t='\n'.join(line for line in t.splitlines() if not line.startswith("checks['same_VG_seed_unchanged']"))+'\n'
t=t.replace("checks['only_three_INS_LOC_added']","checks['only_declared_INS_LOC_added']")
marker="checks['combined_CST_used']=";i=t.index(marker)
t=t[:i]+"checks['declared109_locations']=len(binding['locations'])==109 and binding['locations']==read(O/'FLOORPLAN_FROM_RAW.json')['locations']\n"+t[i:]
ast.parse(t);(O/'independent_raw_review.py').write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':floorplan['scope'],'period_ns':20,'only_effective_change':'Additional109 INS_LOC outside immutable55; no RTL/SYN/SDC/IO changes, ordinary P3/R0/maxfan23.',
    'floorplan_sha256':sha(O/'FLOORPLAN_FROM_RAW.json'),'PNR_started':False,'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Prepared109 raw-bound placement constraints; not launched.')
