"""Create only new v22 source55 and fixtures. No synthesis tools are invoked."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
P=O.parent/'compact_aw_v20';OLD=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(p,j):p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
f=read(P/'source_freeze.json');expected=f['source55'];assert len(expected)==55
assert read(P/'SYNTHESIS_RESULT.json')['passed_SYN_only']
assert read(P/'SYNTHESIS_RESULT.json')['source55']==expected
assert {n:sha(OLD/n) for n in expected}==expected
assert sorted(p.relative_to(OLD).as_posix() for p in OLD.rglob('*') if p.is_file())==sorted(expected)
assert not NEW.exists();NEW.parent.mkdir(parents=True);shutil.copytree(OLD,NEW)
n='position/mtf_xyz_hold_control.v';old=(OLD/n).read_bytes()
anchor=b' end endfunction\n function [9:0] auto_takeoff_mmps;'
insert=b' end endfunction\n wire signed [31:0] quantized_climb_logic_q16 /* synthesis syn_dspstyle="logic" */;\n assign quantized_climb_logic_q16=quantized_climb_q16(speed_z_tick_store);\n function [9:0] auto_takeoff_mmps;'
oldcall=b'alt_speed<=taking_off ?quantized_climb_q16(speed_z_tick_store)+next_auto_speed*32\'sd65536:0;'
newcall=b'alt_speed<=taking_off ?quantized_climb_logic_q16+next_auto_speed*32\'sd65536:0;'
assert old.count(anchor)==old.count(oldcall)==1
new=old.replace(anchor,insert).replace(oldcall,newcall)
assert new.replace(insert,anchor).replace(newcall,oldcall)==old
(NEW/n).write_bytes(new)
current={n:sha(NEW/n) for n in expected};changes=[n for n in expected if current[n]!=expected[n]]
assert changes==['position/mtf_xyz_hold_control.v']
b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];delta={n:h for n,h in current.items() if h!=b3[n]};assert len(delta)==12
doc=R.parents[1]/'routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG550-2.4E_GowinSynthesis User Guide.txt'
edits=[{'old_hex':anchor.hex(),'new_hex':insert.hex()},{'old_hex':oldcall.hex(),'new_hex':newcall.hex()}]
diff=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='v20/'+n,tofile='v22/'+n))
(O/'source_changes.diff').write_text(diff,encoding='utf8',newline='\n')
review='''v22 is an isolated source55 fork of the actually sealed v20. Only position/mtf_xyz_hold_control.v changes: add a signed32 continuous wire carrying the unchanged signed32 function result, attach local syn_dspstyle="logic", and replace one same-width function call with that wire. Reverse exact byte replacements reconstruct the complete parent controller. Other54 files are byte-identical. No state, clock, latency, arithmetic, precision, SDC, CST, gain or build option changes.\n\nThe actual function remains byte-identical: signed29 input; signed14 whole_mm implements truncation toward zero; signed10 cm divides by signed14 decimal10; signed32 result is cm*32'sd655360. Both addition operands at alt_speed remain signed32. Continuous-wire simulation settles after source-store NBA and long before state61 publication; speed_z_tick_store writes occur only on capture, not state61. No shift/add rewrite changes X/Z propagation.\n\nOfficial SUG550-2.4E pages45-47 allows object /* synthesis syn_dspstyle="logic" */; page31 priority example has signed16 wire mult with local logic hint. Whether Gowin propagates the hint through this function output remains an actual SYN question. No timing improvement is claimed.\n\nNew controller bytes invalidate byte-identity reuse of the old six-controller dependency set. Fresh five cases, FRAC0/16 whole-controller miter, four-client contention and source-bound original top13 are required, plus actual-function alias miter. Unchanged guard/FSM/ground evidence is rebound to its exact dependencies only.\n'''
(O/'source_review.md').write_text(review,encoding='utf8')
write(O/'SOURCE_CHANGES.json',{'passed':True,'parent':'v20 actual sealed SYN_ONLY source55','parent_source_root':str(OLD),'source_root':str(NEW),'parent_source55':expected,'source55':current,'changed_files':changes,'other54_byte_exact':True,'exact_reversible_edits':edits,'new_state_bits':0,'new_clock_edges':0,'legacy_public_output_cycle_change':0,'function_unchanged':True,'local_hint_scope':'one signed32 function-result wire only','official_document':str(doc),'official_document_sha256':sha(doc),'official_lines':[1879,2322,2355,2428],'diff_sha256':sha(O/'source_changes.diff'),'pending_actual_synthesis_hint_effect':True})
write(O/'source_freeze.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_root':str(NEW),'source55':current,'baseline_source55':f['baseline_source55'],'B3_relative_changes':delta,'parent_source_freeze_sha256':sha(P/'source_freeze.json'),'parent_SYNTHESIS_RESULT_sha256':sha(P/'SYNTHESIS_RESULT.json'),'source_changes_sha256':sha(O/'SOURCE_CHANGES.json'),'source_review_sha256':sha(O/'source_review.md'),'source_diff_sha256':sha(O/'source_changes.diff')})
# Keep old runners verbatim except source selection/hash and output-local instrumentation.
D=O/'proofs_attempt01';D.mkdir();legacy=O.parent/'compact_aw_v9/proofs_retry02'
for stage in ['five','boundary','contention']:
 d=D/stage;d.mkdir();src=legacy/stage/'run.py';s=src.read_text(encoding='utf8')
 s=s.replace('compact_aw_v9/canonical','compact_aw_v22/canonical')
 if stage=='five':
  s=s.replace(expected[n],current[n]);shutil.copy2(legacy/stage/'aw_tb.v',d/'aw_tb.v');shutil.copy2(legacy/stage/'b4_v1_reference.v',d/'b4_v1_reference.v')
 if stage=='boundary':
  s=s.replace('compact_aw_v5/canonical/source','compact_aw_v20/canonical/source')
  s=s.replace('04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873',expected[n])
 (d/'run.py').write_text(s,encoding='utf8',newline='\n')
top=D/'top13';top.mkdir();src=P/'proofs/top13/run_top13.py'
(top/'run_top13.py').write_bytes(src.read_bytes().replace(b'compact_aw_v20/canonical',b'compact_aw_v22/canonical'))
write(O/'FIXTURE_ADAPTATIONS.json',{'source55':current,'parent_runner_paths':{stage:str(legacy/stage/'run.py') for stage in ['five','boundary','contention']},'parent_runner_sha256':{stage:sha(legacy/stage/'run.py') for stage in ['five','boundary','contention']},'source_changes_only':['five: v9 source root -> v22, expected controller hash -> v22','boundary: v5 old source -> v20 with actual old hash; v9 new source -> v22; stimuli and assertions unchanged','contention: v9 source root -> v22; original legacy adaptation remains unchanged','top13: v20 source root -> v22; generated TB must equal frozen original byte-for-byte'],'fixture_bytes':{str(p):sha(p) for p in [legacy/'five/aw_tb.v',legacy/'five/b4_v1_reference.v',P/'proofs/top13/top_safety_tb.v',R/'firmware/B0B3/proofs/review/contention/contention_tb.v']},'old_controller_hash_not_claimed_for_new_source':True})
print(json.dumps({'source55':len(current),'changed_files':changes,'new_controller_sha256':current[n],'source_freeze_sha256':sha(O/'source_freeze.json')}))
