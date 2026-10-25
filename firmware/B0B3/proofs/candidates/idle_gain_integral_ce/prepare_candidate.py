"""Freeze one saved-I enable refactor from the accepted idle-gain candidate."""
from pathlib import Path
import difflib,hashlib,json,shutil
C=Path(__file__).resolve().parent;R=C.parents[1];B=R/'candidates/idle_gain_ce';S=C/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'freeze_manifest.json')=='d8948b1ae15d32dd65f54886826611495436ac57806a6062305866a37305ea00'
freeze=json.loads((B/'freeze_manifest.json').read_text());frozen=freeze['candidate_source_sha256']
assert (C/'SOURCE_PROOF.md').exists() and len(frozen)==55 and not S.exists()
for rel,digest in frozen.items():
 assert sha(B/'source'/rel)==digest,rel
 p=S/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/'source'/rel,p)
p=S/'position/mtf_xyz_hold_control.v';before=p.read_bytes();capture=b'saved_ix<=ix_store;saved_iy<=iy_store;'
idle=b'  work_p<=xy_p_value;work_i<=xy_i_value;\n'
assert before.count(capture)==1 and before.count(idle)==1 and before.count(b'      '+capture)==1
after=before.replace(idle,idle+b'  '+capture+b'\n').replace(b'      '+capture,b'      ')
assert after.count(capture)==1 and b'\r'not in after
assert after.replace(idle+b'  '+capture+b'\n',idle).replace(b'      saved_afx<=afx_store;',b'      '+capture+b'saved_afx<=afx_store;')==before
p.write_bytes(after);current={rel:sha(S/rel)for rel in frozen};changed=[rel for rel in frozen if current[rel]!=frozen[rel]]
assert changed==['position/mtf_xyz_hold_control.v']
(C/'verification/tmp').mkdir(parents=True)
(C/'candidate.diff').write_text(''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='idle_gain_ce/source/position/mtf_xyz_hold_control.v',tofile='idle_gain_integral_ce/source/position/mtf_xyz_hold_control.v')))
record=dict(status='isolated_not_selected',baseline=str(B/'source'),baseline_freeze_sha256=sha(B/'freeze_manifest.json'),baseline_source_sha256=frozen,candidate_source_sha256=current,changed_files=changed,byte_identical_files=54,baseline_controller_sha256=frozen[changed[0]],candidate_controller_sha256=sha(p),additional_equivalence_reference=str(R/'candidates/response_compact/source'),scope='Move only saved_ix/saved_iy signed27-bit captures into existing state0 sampler; saved AFX/AFY, all math/state/reset and other54source files unchanged')
(C/'change.json').write_text(json.dumps(record,indent=2))
adaptations={}
def adapt(name,transforms,source=None):
 old=(B/(source or name)).read_text();new=old
 for a,b in transforms:
  assert a in new,(name,a);new=new.replace(a,b)
 q=C/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(new)
 adaptations[name]=dict(baseline=str(B/(source or name)),baseline_sha256=sha(B/(source or name)),candidate_sha256=sha(q))
 (C/'verification'/(name.replace('/','_')+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(B/(source or name)),tofile=str(q))))
adapt('verification/regressions/run_regressions.py',[("candidates/idle_gain_ce","candidates/idle_gain_integral_ce"),('9bb8eae57f9491d8e187ac4d5e5868666714920cb91f17e6423daae95618bad9',sha(p))])
adapt('verification/regressions/publish_results.py',[("candidates/idle_gain_ce","candidates/idle_gain_integral_ce")])
adapt('audit_synthesis.py',[
 ("new_snapshot=only_ce(new,'saved_ix')","new_snapshot=only_ce(new,'saved_afx')"),
 ("['CE_FF_pins']==215","['CE_FF_pins']==183"),
 ("assert only_ce(old,'work_p')==only_ce(old,'work_i')==old_snapshot","assert only_ce(old,'work_p')==only_ce(old,'work_i')!=old_snapshot"),
 ("['CE_FF_pins']==183,purpose","['CE_FF_pins']==129,purpose"),
 ("['CE_FF_pins']==32,purpose","['CE_FF_pins']==86,purpose"),
 ("=={'work_p':16,'work_i':16},purpose","=={'work_p':16,'work_i':16,'saved_ix':27,'saved_iy':27},purpose"),
 ("for name in ['saved_iy','saved_afx','saved_afy']:assert only_ce(new,name)==new_snapshot","for name in ['saved_afx','saved_afy']:assert only_ce(new,name)==new_snapshot\nfor name in ['saved_ix','saved_iy']:assert only_ce(new,name)==new_work")])
adapt('audit_idle_decode.py',[("ce=next(iter(nets));cone={};leaves=set()","ce=next(iter(nets));saved=[c for c in cells.values()if c['type'].startswith('DFF')and c['pins'].get('Q','').startswith(('saved_ix[','saved_iy['))];assert len(saved)==54 and all(c['pins']['CE']==ce for c in saved);cone={};leaves=set()"),("work_gain_FF=32,actual_mapped_boolean","work_gain_FF=32,saved_integral_FF=54,idle_CE_FF=86,actual_mapped_boolean")])
adapt('run_synthesis.py',[
 ("tcl=tcl.replace(b'run all',b'run syn');assert b'run pnr'not in tcl and b'run all'not in tcl", "tcl=tcl.replace(b'run all',b'run syn');assert tcl.endswith(b'exit\\n');tcl=tcl[:-len(b'exit\\n')]+b'puts SYNTHESIS_COMMAND_RETURNED_EOF\\nflush stdout\\n';assert b'run pnr'not in tcl and b'run all'not in tcl and not any(line.strip()==b'exit'for line in tcl.splitlines())")])
(C/'verification/helper_adaptation.json').write_text(json.dumps(adaptations,indent=2))
assert all(sha(B/'source'/rel)==digest for rel,digest in frozen.items())
print(json.dumps({k:record[k]for k in ['changed_files','byte_identical_files','baseline_controller_sha256','candidate_controller_sha256']},indent=2))
