"""Fresh P2/R0 using exact old v4 SYN; no change to frozen v4 evidence."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V4=O.parent/'compact_aw_v4';V8=O.parent/'compact_aw_v8'
freeze=V4/'source_freeze.json';assert sha(freeze)=='933482eff5ff7ab4e9dffa69b06d358c61dc422ef92977ac0e51bd5e4d7ae7d7'
assert not (O/'source_freeze.json').exists();(O/'source_freeze.json').write_bytes(freeze.read_bytes())
donor=V4/'run_physical_p3r0.py';text=donor.read_text()
text=text.replace('physical_p3r0_01','physical_p2r0_01').replace('P3/R0','P2/R0').replace('P3/R0','P2/R0')
text=text.replace("('place_option','3')","('place_option','2')").replace("'place':3","'place':2")
needle="    tcl='\\n'.join('run pnr' if line=='run all' else 'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else line for line in lines if line.strip()!='exit')"
assert text.count(needle)==1
text=text.replace(needle,"    tcl='\\n'.join('run pnr' if line=='run all' else 'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else 'set_option -place_option 2' if line=='set_option -place_option 3' else line for line in lines if line.strip()!='exit')")
text=text.replace('O=Path(__file__)', 'import sys\nsys.dont_write_bytecode=True\nO=Path(__file__)',1)
marker="    spec=importlib.util.spec_from_file_location('v4_exact_original_physical_gate',HELPER);";assert text.count(marker)==1
text=text.replace(marker,"    evidence=[DONOR/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']]\n    evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']\n    bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}\n"+marker)
marker="    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n";assert text.count(marker)==1
text=text.replace(marker,marker+"    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')\n    write('donor_evidence_binding.json',{'passed':True,'artifacts':bound,'source55':expected,'vg_sha256':VG_SHA})\n")
marker="    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)\n";assert text.count(marker)==1
text=text.replace(marker,marker+"    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}==bound\n")
ast.parse(text);(O/'run_physical.py').write_text(text)
sup=(O.parent/'compact_aw_v9/launch_incremental_hidden.py').read_text().replace('physical_p3r0_inc_v4_01','physical_p2r0_01').replace('run_incremental.py','run_physical.py')
ast.parse(sup);(O/'launch_physical_hidden.py').write_text(sup)
vg='e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f'
for name in ['seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    text=(V8/name).read_text().replace('compact_aw_v8','compact_aw_v4')
    text=text.replace('5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e',vg)
    if name=='seal_terminal.py':
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'";assert text.count(old)==1
        text=text.replace(old,"assert len(sys.argv)==1;label='physical_p2r0_01'")
    elif name=='independent_raw_review.py':
        old="assert len(sys.argv)==2 and sys.argv[1] in ['2','3']\nlabel=f'physical_p{sys.argv[1]}r0_01'";assert text.count(old)==1
        text=text.replace(old,"assert len(sys.argv)==1\nlabel='physical_p2r0_01'")
    else:text=text.replace('for place in [3,2]:','for place in [2]:')
    ast.parse(text);(O/name).write_text(text)
expected=json.loads((O/'source_freeze.json').read_text())['source55']
proof=R/'analysis/20261026_z_aw_fix/build/compact_aw_v9/proofs_retry02/results.json'
new=json.loads(proof.read_text());assert new['passed']
dependencies=['position/mtf_xyz_hold_control.v','nav_math_service.v','position/position_math.v','position/ano_xy_stick.v','position/ano_xy_divide36.v','position/ano_z_stick.v']
assert all(new['source55'][p]==expected[p] for p in dependencies)
(O/'PREPARATION.json').write_text(json.dumps({'scope':'One new v4 exact-VG P2R0. Existing source and SYN/audits unchanged; no hardware. No new PNR started by preparation.',
    'reason':'v4 P3 routed at49.456MHz/−0.220ns; P2 changes placement only. Incremental eligibility failed2.75%, leaving one physical slot.',
    'source55':expected,'VG_sha256':vg,'original_runner_sha256':sha(donor),'new_runner_sha256':sha(O/'run_physical.py'),
    'frozen_v4_source_freeze_sha256':sha(freeze),'reused_control_proofs_sha256':sha(proof),'identical_control_dependencies':dependencies,
    'generated_scripts':{p.name:sha(p) for p in O.glob('*.py')}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared exact v4 VG P2R0; no synthesis rerun or frozen file mutation.')
