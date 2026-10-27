"""Independent source/manual-only v22 review. No candidate edits, tests or vendor calls."""
from pathlib import Path
import datetime,hashlib,json,re
R=Path('C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller')
O=Path(__file__).resolve().parent;M=R/'analysis/20261026_z_aw_fix/build/compact_aw_v22';P=R/'analysis/20261026_z_aw_fix/build/compact_aw_v20'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
f=read(M/'source_freeze.json');old_f=read(P/'source_freeze.json');C=Path(f['source_root']);OLD=Path(old_f['source_root'])
expected=f['source55'];before=old_f['source55']
assert len(expected)==len(before)==55 and {n:sha(C/n) for n in expected}==expected and {n:sha(OLD/n) for n in before}==before
assert read(P/'SYNTHESIS_RESULT.json')['passed_SYN_only'] and read(P/'SYNTHESIS_RESULT.json')['source55']==before
changed=[n for n in expected if expected[n]!=before[n]];assert changed==['position/mtf_xyz_hold_control.v']
n=changed[0];a=(OLD/n).read_bytes();b=(C/n).read_bytes()
anchor=b' end endfunction\n function [9:0] auto_takeoff_mmps;'
insert=b' end endfunction\n wire signed [31:0] quantized_climb_logic_q16 /* synthesis syn_dspstyle="logic" */;\n assign quantized_climb_logic_q16=quantized_climb_q16(speed_z_tick_store);\n function [9:0] auto_takeoff_mmps;'
oldcall=b'alt_speed<=taking_off ?quantized_climb_q16(speed_z_tick_store)+next_auto_speed*32\'sd65536:0;'
newcall=b'alt_speed<=taking_off ?quantized_climb_logic_q16+next_auto_speed*32\'sd65536:0;'
assert a.count(anchor)==a.count(oldcall)==1
assert b==a.replace(anchor,insert,1).replace(oldcall,newcall,1)
assert b.replace(insert,anchor,1).replace(newcall,oldcall,1)==a
text=b.decode('utf8');oldtext=a.decode('utf8')
pattern=r' function signed \[31:0\] quantized_climb_q16;.*? end endfunction'
fun=re.search(pattern,text,re.S).group();assert fun==re.search(pattern,oldtext,re.S).group()
assert 'input signed [28:0] v;' in fun and 'reg signed [13:0] whole_mm;' in fun and 'reg signed [9:0] cm;' in fun
assert "cm=whole_mm/14'sd10;quantized_climb_q16=cm*32'sd655360;" in fun
writes=[m.start() for m in re.finditer(r'\bspeed_z_tick_store\s*<=',text)];assert len(writes)==1
assert text.rfind('0:if(height_due && height_stick_captured)',0,writes[0])>=0
assert writes[0]<text.index('61:begin')<text.index(newcall.decode())
assert 'reg signed [29-1:0] speed_z_tick_store=0;' in text
manual=Path('C:/Users/ScherrerL/Desktop/apple/routing_rescue_20261015/mtf01p_b0ae_ano_control/tools_notes/SUG550-2.4E_GowinSynthesis User Guide.txt')
guide=manual.read_text(encoding='utf8');assert 'module/entity, wire/reg/signal' in guide and 'object /* synthesis syn_dspstyle = "value" */;' in guide
assert 'wire signed [15:0]mult/*synthesis syn_dspstyle="logic"*/;' in guide and 'wire [15:0] temp/*synthesis syn_dspstyle = "logic" */;' in guide
record={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'dsp_export_scout','stage':'source + primary local manual applicability only',
    'source_review_passed':True,'actionable_source_findings':[],'full_proof_SYN_review_complete':False,'SYN_approval':False,
    'source_freeze_sha256':sha(M/'source_freeze.json'),'source_changes_sha256':sha(M/'SOURCE_CHANGES.json'),'source_diff_sha256':sha(M/'source_changes.diff'),
    'source55':expected,'parent_v20_source_freeze_sha256':sha(P/'source_freeze.json'),'parent_v20_sealed_SYN_result_sha256':sha(P/'SYNTHESIS_RESULT.json'),
    'changed_files':changed,'other54_byte_exact':True,'exact_expected_two_edits_and_inverse_byte_match':True,'function_body_byte_exact':True,
    'parent_controller_sha256':before[n],'new_controller_sha256':expected[n],'old_six_controller_hash_reuse_allowed':False,
    'semantic_findings':{'function_return_and_alias':'Both signed32; signed29 input, signed14 whole_mm and signed10 cm unchanged; no shift/add arithmetic rewrite',
        'alt_speed_expression':'Original signed32 function result replaced by signed32 wire; same signed32 next_auto_speed multiplication, ternary and destination',
        'state_and_cycles':'No new state/clock edge. speed_z_tick_store has one nonblocking assignment at accepted state0 capture; state61 reads after prior-cycle combinational settling.',
        'X_Z_scope':'Same function and signed widths preserve four-state expression at stable sampled input. No broad claim about arbitrary forced same-delta private-state races.',
        'inherited_source':'Both AZ/VY guards and all clocks/SDC/CST/ports/gains remain among the54 exact parent files'},
    'official_manual':{'path':str(manual),'sha256':sha(manual),'version':'SUG550-2.4E','text_lines':[1843,1855,1879,2322,2334,2344,2355,2428],'pages':[34,45,47],
        'applicability':'Wire/reg/signal is an expressly supported object; logic selects logic implementation, with a local attributed wire example and local-attribute priority.',
        'unresolved_mapping_question':'Manual examples directly assign multiplication to a wire; actual propagation through this unchanged function return still requires a real new SYN/mapped inspection. No timing improvement is established.'},
    'documentation_notes':[{'severity':'citation only','path':str(M/'source_review.md'),'note':'The local priority wire example is printed manual page34, not31; text1879 is the correct line. Section45/47 applicability is unaffected. Erratum retained here without mutating bound candidate docs.'}],
    'STA_motivation_scope':'Parent supplied recent raw DSP constant-multiply observation; this source-only review does not independently reparse that raw path or grant timing qualification.',
    'pending_full_review':['Fresh five controller cases with new controller digest','Fresh FRAC0/FRAC16 whole-controller boundary miter','Fresh four-client contention','Fresh exact original top13','Actual-function alias proof and fixture-retry provenance','Successful real proof root/source/log/input bindings','Prospective original proof-root self-output hash failure must be classified only from actual terminal receipts; completion must recheck every immutable input and all actual successful stages without hiding any other failure or source change','Dormant SYN scripts/helper hashes/guard inheritance/CLK50/default gains/18pin gates']}
dest=O/'SOURCE_REVIEW.json';assert not dest.exists();dest.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
(O/'SOURCE_REVIEW.md').write_text('''Source-only review: no actionable source issue found. This is not SYN approval; fresh proof and SYN preparation review remains pending.

The complete new controller equals the frozen v20 controller plus exactly the attributed signed32 wire/continuous assignment and the single same-width alt_speed call replacement. Inverting those edits restores the parent bytes. All other54 files match the parent. The function body, signed29 input, signed14 truncation, signed10 division and signed32 constant multiply remain exact. The only speed_z_tick_store write is a nonblocking accepted state0 capture; state61 consumes the settled alias. No new state, clock or output cycle appears in source.

Primary local SUG550-2.4E supports wire/reg/signal syn_dspstyle and the logic value (text2334/2344/2355, manual45), with attributed wire examples (text1879 and2428, manual34/47). The bound candidate review says31 for the priority example; that citation-only erratum is recorded here. Actual synthesis must show whether the hint reaches the multiply inside the function; documentation and source equivalence do not prove mapping or STA improvement.

The controller digest changed, so the prior exact-six controller result cannot be reused as new-controller proof. Fresh five cases, FRAC0/16, contention, exact top13 and actual-function alias evidence must be audited before approval. Unchanged guard/FSM/ground reuse must retain its parent source identities and exact dependencies.
''',encoding='utf8',newline='\n')
print(json.dumps({'source_review_passed':True,'changed_files':1,'other54_byte_exact':True,'manual_signal_hint_supported':True,'mapping_effect_pending':True,'full_proof_review_pending':True,'SYN_approval':False,'review_sha256':sha(dest),'new_controller_sha256':expected[n]}))
