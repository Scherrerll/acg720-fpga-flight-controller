"""Prepare only: dedicate physical routing to three late data/ready nets, never FF clocks."""
from pathlib import Path
import ast,hashlib,importlib.util,json
O=Path(__file__).resolve().parent/'compact_aw_v4_data_routing_followup';D=O.parent/'compact_aw_v4_p3mf60_followup';R=O.parents[3]
assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
VG=R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'
reader=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026/tools/read_cones.py');sp=importlib.util.spec_from_file_location('data_route_graph',reader);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);g=m.Graph(VG)
drivers={'previous_pose_valid_s0':'Q','core/fallback_control/height_fallback_active_s':'F','native_navigation/nav_xy_ready_s':'F'}
nets=[g.cells[n]['pins'][port][0] for n,port in drivers.items()]
assert len(set(nets))==3 and all(g.find(n)!=g.find('clk50_d') for n in nets)
assert nets==['previous_pose_valid','core/fallback_control/height_fallback_active','native_navigation/nav_xy_ready']
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
declaration={'scope':'Physical routing only; three data/ready nets use vendor BUFG routing with signal_type LOGIC only. No CLK constraint, no FF clock connection change, no SDC/falsepath/pin/RTL change.',
    'nets':nets,'drivers':drivers,'VG_sha256':sha(VG),'graph_reader_sha256':sha(reader),
    'reason':'Original v4 raw path8 previous_pose_valid firstnet6.920ns; path1 fallback-active output fanout115 and1.569ns next hop; path3 nav_xy_ready output2.470ns next hop. Original PNR uses all8 PRIMARY and8LW, all true FF clocks stillclk50. Test explicit priority for these late data nets; actual full route/STA remains mandatory.',
    'official_manual':'SUG1541-1.0E PDF28-29, CLOCK_LOC with signal_type LOGIC supports a non-CLK/CE/SR net on global routing. BUFS is not used (not documented for this AroraV).',
    'source_clock_audit_reused':'Same exact mapped VG, strict all-FF CLK50 audit; raw TR must still have exactly clk50 Base20ns and all five timing gates.'}
(O/'DATA_ROUTE_DECLARATION.json').write_text(json.dumps(declaration,indent=2)+'\n')
label='physical_p3r0_data_route_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_mf60_01',label)
    if name=='run_physical.py':
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23' else ",'').replace("('route_maxfan','60')","('route_maxfan','23')").replace("'route_maxfan':60","'route_maxfan':23").replace('Maxfan60','three LOGIC data-net routing priorities')
        marker="    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    declaration=json.loads((O/'DATA_ROUTE_DECLARATION.json').read_text());nets=declaration['nets'];assert len(nets)==3 and declaration['VG_sha256']==VG_SHA\n    constraints=SOURCE/'physical_constraints.cst';original_cst=(SOURCE/'acg720_ano_port.cst').read_bytes()\n    extra_cst='\\n// Physical data-net routing priority only; no new clocks or timing exceptions.\\n'+''.join('CLOCK_LOC '+json.dumps(n)+' BUFG = LOGIC;\\n' for n in nets)\n    constraints.write_bytes(original_cst+extra_cst.encode('ascii'))\n    write('data_routing_binding.json',{'original_cst_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_cst_sha256':sha(constraints),'nets':nets,'declaration_sha256':sha(O/'DATA_ROUTE_DECLARATION.json'),'added_commands':'Three CLOCK_LOC BUFG=LOGIC only, no CLK/CE/SR or SDC changes'})\n")
        t=t.replace("('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
        t=t.replace("'period_ns':20,'usercode':'0000B0B4'","'period_ns':20,'usercode':'0000B0B4','combined_cst_sha256':sha(constraints),'data_routing_declaration_sha256':sha(O/'DATA_ROUTE_DECLARATION.json')")
    if name=='seal_terminal.py':
        t=t.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()","paths += [V/'data_routing_binding.json',ATTEMPT/'source/physical_constraints.cst',O/'DATA_ROUTE_DECLARATION.json']\npaths=[p for p in paths if p.is_file()];copies.mkdir()")
    if name=='independent_raw_review.py':
        marker="out=report/'INDEPENDENT_RAW_REVIEW.json';assert not out.exists()";assert t.count(marker)==1
        extra="""binding=read(V/'data_routing_binding.json');combined=S/'physical_constraints.cst'
checks['combined_CST_bound']=sha(combined)==binding['combined_cst_sha256']
prefix=(S/'acg720_ano_port.cst').read_bytes();suffix=combined.read_bytes()[len(prefix):].decode('ascii')
checks['combined_CST_original_prefix']=combined.read_bytes().startswith(prefix)
checks['only_three_declared_LOGIC_routes']=re.findall(r'^CLOCK_LOC "([^"]+)" BUFG = LOGIC;$',suffix,re.M)==binding['nets']==read(O/'DATA_ROUTE_DECLARATION.json')['nets'] and len(binding['nets'])==3 and all(line.startswith('//') or line.startswith('CLOCK_LOC ') for line in suffix.splitlines() if line.strip())
checks['combined_CST_used']='physical_constraints.cst' in (S/'physical.gprj').read_text()
files[str(combined.relative_to(R))]=sha(combined)
"""
        t=t.replace(marker,extra+marker)
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':declaration['scope'],'period_ns':20,'only_effective_change':'Three physical CLOCK_LOC BUFG=LOGIC priorities, same P3/R0/maxfan23 and exact VG/source55.',
    'declaration_sha256':sha(O/'DATA_ROUTE_DECLARATION.json'),'PNR_started':False,'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Prepared only three data routing priorities, no new clocks/SDC; not launched.')
