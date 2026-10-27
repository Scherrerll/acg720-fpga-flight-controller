"""Prepare only: same existing clk50 on another documented physical global line."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_clockbuf1_followup';D=O.parent/'compact_aw_v4_p3mf60_followup'
assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p3r0_clkbuf1_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_mf60_01',label)
    if name=='run_physical.py':
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23' else ",'').replace("('route_maxfan','60')","('route_maxfan','23')").replace("'route_maxfan':60","'route_maxfan':23").replace('Maxfan60','existing clk50 physical global line1')
        marker="    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    constraints=SOURCE/'physical_constraints.cst';original_cst=(SOURCE/'acg720_ano_port.cst').read_bytes()\n    extra_cst='\\n// Same existing50MHz net, physical global line only; no new clock/phase/period.\\nCLOCK_LOC \\\"clk50_d\\\" BUFG[1] = CLK;\\n'\n    constraints.write_bytes(original_cst+extra_cst.encode('ascii'))\n    write('clock_route_binding.json',{'original_cst_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_cst_sha256':sha(constraints),'existing_clock_net':'clk50_d','requested_global_line':1,'frequency_mhz':50,'period_ns':20,'scope':'Only physical line assignment for the same original IBuf clock net. All FF clock connectivity unchanged in exact VG; no generated clock, frequency, phase, SDC or exception change.'})\n")
        t=t.replace("('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
        t=t.replace("'period_ns':20,'usercode':'0000B0B4'","'period_ns':20,'usercode':'0000B0B4','combined_cst_sha256':sha(constraints),'existing_clock_physical_line':1")
    if name=='seal_terminal.py':
        t=t.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()","paths += [V/'clock_route_binding.json',ATTEMPT/'source/physical_constraints.cst']\npaths=[p for p in paths if p.is_file()];copies.mkdir()")
    if name=='independent_raw_review.py':
        marker="out=report/'INDEPENDENT_RAW_REVIEW.json';assert not out.exists()";assert t.count(marker)==1
        extra="""binding=read(V/'clock_route_binding.json');combined=S/'physical_constraints.cst'
checks['combined_CST_bound']=sha(combined)==binding['combined_cst_sha256']
prefix=(S/'acg720_ano_port.cst').read_bytes();suffix=combined.read_bytes()[len(prefix):].decode('ascii')
checks['combined_CST_original_prefix']=combined.read_bytes().startswith(prefix)
checks['only_existing_clock_physical_line']=binding['existing_clock_net']=='clk50_d' and binding['requested_global_line']==1 and [line for line in suffix.splitlines() if line.strip() and not line.startswith('//')]==['CLOCK_LOC "clk50_d" BUFG[1] = CLK;']
checks['combined_CST_used']='physical_constraints.cst' in (S/'physical.gprj').read_text()
files[str(combined.relative_to(R))]=sha(combined)
"""
        t=t.replace(marker,extra+marker)
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':'Same exact v4 VG/source55, source clock and20ns constraints. Assign existing clk50_d to physical BUFG[1] only; no new clock/phase/period or falsepath.',
    'basis':'Closest complete-route v4 Fmax49.456/setup−0.220ns; raw detailed worst path has launch-clock3.623ns/capture-clock3.186ns, skew−0.437ns. Test a different physical global line, keeping full five-table and setup/hold0 acceptance mandatory.',
    'manual':'SUG1541-1.0E PDF29-30 documents CLOCK_LOC net BUFG[n]=CLK. Native parser/device must accept it; no success inferred.',
    'period_ns':20,'physical_options':{'place':3,'route':0,'route_maxfan':23,'existing_clk50_global_line':1},'PNR_started':False,
    'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Prepared existing50MHz physical global-line1 experiment only; not launched.')
