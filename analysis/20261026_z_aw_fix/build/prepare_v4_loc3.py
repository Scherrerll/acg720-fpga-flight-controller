"""Prepare an exact-VG copied-seed physical experiment based on three raw late paths."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent/'compact_aw_v4_loc3_followup';D=O.parent/'compact_aw_v4_p3mf60_followup'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'source_freeze.json').write_bytes((D/'source_freeze.json').read_bytes())
label='physical_p3r0_inc_loc3_01'
for name in ['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py']:
    t=(D/name).read_text().replace('physical_p3r0_mf60_01',label)
    if name=='run_physical.py':
        t=t.replace("'set_option -route_maxfan 60' if line=='set_option -route_maxfan 23' else ",'')
        t=t.replace("('route_maxfan','60')","('route_maxfan','23')").replace("'route_maxfan':60","'route_maxfan':23")
        extra="""
SEED_ORIGINAL=ROOT/'physical_p3r0_01/source/impl/pnr/acg720_ano_port.pr'
SEED_SHA='ba20959930d4ddac2f4841d3ce4962d4ee1c84c2b65feaf004b9def3a6f76a1e'
SEED=ATTEMPT/'donor/v4_P3R0.pr'
LOCATIONS={'acc_time/output_az_3_s0':'R34C24[0][A]',
 'mtf/metric/vy_x100_28_s0':'R50C56[3][B]',
 'previous_pose_valid_s0':'R36C78[0][B]'}
"""
        t=t.replace('def main():\n',extra+'\ndef main():\n')
        marker="    evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    assert sha(SEED_ORIGINAL)==SEED_SHA\n    evidence += [SEED_ORIGINAL]\n")
        marker="    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()\n";assert t.count(marker)==1
        t=t.replace(marker,marker+"    SEED.parent.mkdir();shutil.copy2(SEED_ORIGINAL,SEED);assert sha(SEED)==SEED_SHA\n    constraints=SOURCE/'physical_constraints.cst'\n    original_cst=(SOURCE/'acg720_ano_port.cst').read_bytes()\n    extra_cst='\\n// Three placement-only source FF constraints; original 18 IO constraints unchanged.\\n'+''.join('INS_LOC '+json.dumps(n)+' '+loc+';\\n' for n,loc in LOCATIONS.items())\n    constraints.write_bytes(original_cst+extra_cst.encode('ascii'))\n    assert constraints.read_bytes().startswith(original_cst) and extra_cst.count('INS_LOC ')==3\n    write('placement_constraint_binding.json',{'original_cst_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_cst_sha256':sha(constraints),'locations':LOCATIONS,'copied_seed_sha256':sha(SEED),'original_seed_sha256':sha(SEED_ORIGINAL),'only_added_commands':'INS_LOC, three source DFFs from old raw late paths1/3/8; no SDC changes'})\n")
        t=t.replace("('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
        marker="    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')\n";assert t.count(marker)==1
        t=t.replace(marker,"    assert not any(c in SEED.as_posix() for c in '{}[]$;')\n    tcl=tcl.replace('run pnr\\n','set_option -inc_pnr {'+SEED.as_posix()+'}\\nrun pnr\\n')\n    assert tcl.count('set_option -inc_pnr ')==1\n"+marker)
        t=t.replace("'period_ns':20,'usercode':'0000B0B4'","'period_ns':20,'usercode':'0000B0B4','incremental_seed_sha256':SEED_SHA,'combined_cst_sha256':sha(constraints),'locations':LOCATIONS")
        t=t.replace("'project_sha256':sha(physical_project)","'combined_cst_sha256':sha(constraints),'incremental_seed_sha256':SEED_SHA,'project_sha256':sha(physical_project)")
        t=t.replace("    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)","    assert sha(SEED_ORIGINAL)==sha(SEED)==SEED_SHA\n    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)")
        t=t.replace('Maxfan60','three-source LOC/copied same-VG seed')
    if name=='seal_terminal.py':
        t=t.replace("paths=[p for p in paths if p.is_file()];copies.mkdir()","paths += [V/'placement_constraint_binding.json',ATTEMPT/'source/physical_constraints.cst']\npaths=[p for p in paths if p.is_file()];copies.mkdir()")
    if name=='independent_raw_review.py':
        marker="out=report/'INDEPENDENT_RAW_REVIEW.json';assert not out.exists()"
        extra="""binding=read(V/'placement_constraint_binding.json')
combined=S/'physical_constraints.cst'
checks['combined_CST_bound']=sha(combined)==binding['combined_cst_sha256']
suffix=combined.read_bytes()[len((S/'acg720_ano_port.cst').read_bytes()):].decode('ascii')
checks['only_three_INS_LOC_added']=re.findall(r'^INS_LOC \\"([^\\"]+)\\" (R[^;]+);$',suffix,re.M)==list(binding['locations'].items()) and all(line.startswith('//') or line.startswith('INS_LOC ') for line in suffix.splitlines() if line.strip())
checks['combined_CST_prefix']=combined.read_bytes().startswith((S/'acg720_ano_port.cst').read_bytes())
checks['same_VG_seed_unchanged']=sha(A/'donor/v4_P3R0.pr')==binding['copied_seed_sha256']==binding['original_seed_sha256']==sha(R/'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.pr')
checks['combined_CST_used']='physical_constraints.cst' in (S/'physical.gprj').read_text()
files[str(combined.relative_to(R))]=sha(combined)
"""
        assert t.count(marker)==1;t=t.replace(marker,extra+marker)
    ast.parse(t);(O/name).write_text(t)
(O/label).mkdir()
(O/'PREPARATION.json').write_text(json.dumps({'scope':'Exact v4 source55 and mapped VG. Copy its own old P3 PR; add only three INS_LOC physical constraints outside immutable55. No changes to clocks/falsepaths/RTL/pins.',
    'reason':'Old complete-route setup table has three launch FF groups. Source AZ path first hop0.517ns; vy path first hop1.315ns; previous_pose path first hop6.920ns. Place each launch FF near its existing first LUT, then require fresh full-route independent50MHz gates.',
    'baseline_full_route_setup_ns':-.220,'period_ns':20,'route_maxfan':23,
    'official_manual':'C:/Gowin/Gowin_V1.9.12.04_x64/IDE/doc/EN/SUG1541-1.0E_Gowin Software Physical Constraints User Guide.pdf','manual_pdf_pages':[17,18,19],
    'seed_is_timing_failed_reference_only':True,'incremental_effect_requires_actual_log_review':True,
    'fallback_policy':'Do not cancel a distinct LOC run solely for incremental fallback; preserve actual flow and fresh result.',
    'scripts':{p.name:sha(p) for p in O.glob('*.py')}},indent=2)+'\n')
print('Three-source physical-only LOC experiment prepared.')
