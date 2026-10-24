"""Prepared only. Pure source algebra/projection; root authorization required after50clean winner."""
from pathlib import Path
import hashlib,json,re,importlib.util,textwrap,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;P=D.parent;H=P.parent
B=H/'control_ready_factoring_plan/synthesis_only/20261024T013341_913278Z';N=P/'synthesis_only/20261024T015539_307340Z'
PARENT=H/'control_ready_factoring_plan/post_route_pending/prove_factoring.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prepared=json.loads((D/'prepared_inputs.json').read_text());assert all(sha(p)==h for p,h in prepared['bindings'].items())
 names=['sensor/mtf_shared_geometry.v','position/mtf_shared_height_fusion.v','mtf_xyz_navigation_control.v'];olds={n:(B/n).read_text() for n in names};news={n:(N/n).read_text() for n in names}
 assert olds[names[0]]==news[names[0]]
 # Exact inverse projections, not loose regex deletion of state or producer statements.
 fusion=news[names[1]];fusion=fusion.replace(' output wire estimate_ready_state_numeric_tail,\n output wire vz_q16_range_raw\n',' output wire estimate_ready_state_numeric_tail\n').replace('\n assign vz_q16_range_raw=v_q16_range;','');assert fusion==olds[names[1]]
 assert ' reg publish_v_q16_range=0,v_q16_range=0;' in news[names[1]]
 assert ' assign vz_q16_range_raw=v_q16_range;' in news[names[1]]
 assert news[names[1]].index('reg publish_v_q16_range=0,v_q16_range=0;')<news[names[1]].index('assign vz_q16_range_raw=')
 assert ' assign vz_q16_valid=estimate_ready && v_q16_range;' in news[names[1]]
 nav=news[names[2]];original=olds[names[2]]
 expected=original.replace(' wire fused_vz_q16_valid;wire [15:0] height_reason;',' wire fused_vz_q16_valid;wire [15:0] height_reason;\n wire height_vz_q16_range_raw;').replace('.vz_q16_valid(fused_vz_q16_valid),','.vz_q16_valid(fused_vz_q16_valid),.vz_q16_range_raw(height_vz_q16_range_raw),').replace('wire observation_bad=!height_ready || !fused_vz_q16_valid;','wire observation_bad=!height_ready || !height_vz_q16_range_raw;').replace('observation_bad || !height_ready || !fused_vz_q16_valid || !position_internal_ready','observation_bad || !position_internal_ready').replace('height_ready && fused_vz_q16_valid','height_ready && height_vz_q16_range_raw')
 assert expected==nav
 assert len([x for x in original.splitlines() if 'fused_vz_q16_valid' in x])==6
 assert len([x for x in nav.splitlines() if 'fused_vz_q16_valid' in x])==2
 # Reuse original parser/AND-normalizer definitions WITHOUT calling parent's main or changing its file.
 spec=importlib.util.spec_from_file_location('parent_source_algebra_only',PARENT);parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
 assert parent.expression(original,'height_ready')==parent.expression(nav,'height_ready')
 _,pins=parent.instance(nav,'mtf_shared_height_fusion','height_fusion');assert pins['vz_q16_range_raw']=='height_vz_q16_range_raw'
 # Reuse exact parent normalization block. Both new/old inputs are now factored, so enable its
 # existing tail aliases/static named-parameter checks for BOTH, and also retain E atoms.
 source=PARENT.read_text();start=source.index(' outputs=[]\n');end=source.index(" assert outputs[0]['atoms']==outputs[1]['atoms']",start);block=textwrap.dedent(source[start:end]);assert block.count("if label=='new':")==2;block=block.replace("if label=='new':","if True:")
 atom_fragment="atoms=sorted(expand('N',expression(nav,'height_ready')))";assert block.count(atom_fragment)==1;block=block.replace(atom_fragment,atom_fragment+",estimate_atoms=sorted(expand('F',expression(f,'estimate_ready')))")
 ns=dict(parent.__dict__);ns.update(olds=olds,news=news,names=names);exec(compile(block,'parent_normalization_block_metadata','exec'),ns);normalized=ns['outputs'];assert len(normalized)==2
 assert normalized[0]['atoms']==normalized[1]['atoms']
 for item in normalized:assert set(item['estimate_atoms'])<=set(item['atoms']),item
 # All six two-state valuations allowed by H=>E; no invalid-state don't-care beyond that proven lemma.
 truth=[]
 for h in [False,True]:
  for e in [False,True]:
   if h and not e:continue
   for r in [False,True]:
    v=e and r;old_bad=(not h) or (not v);new_bad=(not h) or (not r)
    assert (h and v)==(h and r)
    assert old_bad==new_bad
    assert (old_bad or (not h) or (not v))==new_bad
    truth.append(dict(H=h,E=e,R=r,old_bad=old_bad,new_bad=new_bad))
 assert len(truth)==6
 assert all(sha(p)==h for p,h in prepared['bindings'].items())
 report=dict(status='PASS executed two-file exact source projection and H=>E source-atom implication',bindings=prepared['bindings'],normalization=normalized,truth_cases=truth,H_unchanged=True,fusion_original_producer_projection_exact=True,rawR_source_direct_existing_Q=True,parent_proof_inheritance=prepared['parent_proof_inheritance'],limits=['Source Boolean algebra only, no mapped FF-transition/consumer equivalence or timing acceptance','OR range-age guard retained indivisible same-source atom; numeric predicates not dropped','Original publicV remains E&&R; rawR never standalone validity','No functional compile/sim/fullFSM/core/parser/host matrix'],functional_compile_run=False,synthesis_run=False,pnr_run=False)
 report['evidence_hashes']={p.name:sha(p) for p in [D/'prove_fine_velocity.py',D/'prepared_inputs.json']};(D/'fine_velocity_proof.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
