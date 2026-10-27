"""v15 landing compare plus one local synthesis-only fanout hint at actual187-load data net."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v15';M=O/'compact_aw_v16'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v15/canonical/source';C=R/'out/z_aw_fix_20261026/compact_aw_v16/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
pf=read(P/'source_freeze.json');expected=pf['source55'];assert read(P/'PROOF_BINDING.json')['passed']
assert all(sha(OLD/n)==h for n,h in expected.items()) and not M.exists() and not C.exists()
mapped=read(P/'MAPPED_LANDING_COMPARISON.json');assert any(x['cell']=='core/fallback_control/height_fallback_active_s' and x['loads']==187 for x in mapped['results']['v15']['selected_cells'])
M.mkdir();shutil.copytree(OLD,C)
n='core/height_loss_fallback.v';before=' assign active=rst_n && healthy && armed && (latched || enter);'
after=' // Identity wire, with a local synthesis-only fanout limit on this data driver.\n wire active_fanout_limited /* synthesis syn_maxfan = 50 */;\n assign active_fanout_limited=rst_n && healthy && armed && (latched || enter);\n assign active=active_fanout_limited;'
s=(OLD/n).read_text(encoding='utf8');assert s.count(before)==1
t=s.replace(before,after);assert t.replace(after,before)==s;(C/n).write_text(t,encoding='utf8',newline='\n')
new={x:sha(C/x) for x in expected};assert [x for x in expected if expected[x]!=new[x]]==[n]
basis=read(P/'SOURCE_EQUIVALENCE_BASIS.json');basis['transformations'][n]=dict(edits=[[before,after]],baseline_sha256=pf['baseline_source55'][n],candidate_sha256=new[n],reverse_exact_normalized_text=True)
basis['unchanged_files']=52
if (OLD/n).read_bytes()!=s.encode():basis['line_endings_normalized'].append(n)
basis['scope']='v15 binary combinational threshold distribution plus one plain identity wire and synthesis-only local hint. No new state/cycles/clock; actual proofs and STA separate.'
(M/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps(basis,indent=2)+'\n',encoding='utf8')
review=(P/'source_review.md').read_text(encoding='utf8')+'''\n\n# v16：只给实际187负载的fallback组合数据驱动施加局部syn_maxfan50\n\nv15实际SYN/严格时钟和增益审计已通过，AZ→flying_ms组合锥体19→14级，但fallback active实际合并到187负载。此候选在准确v15源上仅对原active表达式经同值普通wire施加局部syn_maxfan50，不给previous_pose_valid加属性，不全局改SYN fanout，不新加状态、周期或时钟。原厂SUG550支持内部wire/reg综合扇出约束；先前v14此属性确实拆分驱动，但v14物理未布通，不是v16成功依据。v16必须新测完整原/新/default FSM、实际fallback关系和原top13，新综合/物理另验。相对v4共3文件变化、52文件字节相同，B3相对6文件。上方v15叙述仅说明父候选；本候选不宣称只改2文件。\n'''
(M/'source_review.md').write_text(review,encoding='utf8')
diff=(P/'source_changes.diff').read_text(encoding='utf8')+''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='v15/'+n,tofile='v16/'+n))
(M/'source_changes.diff').write_text(diff,encoding='utf8')
freeze=dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=new,baseline_source55=pf['baseline_source55'],changed_files=list(basis['transformations']),source_review_sha256=sha(M/'source_review.md'),source_equivalence_basis_sha256=sha(M/'SOURCE_EQUIVALENCE_BASIS.json'),parent_v15_source55=expected)
(M/'source_freeze.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
D=M/'proofs';D.mkdir()
top=(P/'proofs_retry02/run_top13.py').read_text(encoding='utf8').replace('compact_aw_v15','compact_aw_v16');(D/'run_top13.py').write_text(top,encoding='utf8')
proof=(P/'run_proofs_retry02.py').read_text(encoding='utf8').replace('compact_aw_v15','compact_aw_v16').replace("D=O/'proofs_retry02'","D=O/'proofs'").replace('v15','v16')
ast.parse(proof);(M/'run_proofs.py').write_text(proof,encoding='utf8')
names=['verify_reused_bindings.py','run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']
for name in names:
    text=(P/name).read_text(encoding='utf8').replace('compact_aw_v15','compact_aw_v16').replace('v15','v16').replace('len(h.EXPECTED_CHANGES)==5','len(h.EXPECTED_CHANGES)==6').replace('len(helper.EXPECTED_CHANGES)==5','len(helper.EXPECTED_CHANGES)==6')
    ast.parse(text);(M/name).write_text(text,encoding='utf8')
(M/'SYNTHESIS_PREPARATION.json').write_text(json.dumps(dict(scope='v15 original SYN-only gates, exactly6 B3-relative files expected. Only actual candidate paths/proof key/source-count changed.',source55=new,parent_scripts_sha256={name:sha(P/name) for name in names}),indent=2)+'\n',encoding='utf8')
(M/'PREPARATION.json').write_text(json.dumps(dict(scope='v15 plus one data-driver syn_maxfan50; new exact-source miter and top13 required before SYN; no new state or cycle',parent_proof_sha256=sha(P/'PROOF_BINDING.json'),mapped_basis_sha256=sha(P/'MAPPED_LANDING_COMPARISON.json'),source55=new,parent_source55=expected,parent_proof_runner_sha256=sha(P/'run_proofs_retry02.py'),new_proof_runner_sha256=sha(M/'run_proofs.py'),stimulus_changes='Only v15 to v16 text/path labels; no vector, timing or assertion changes',vendor_started=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,source55=55,changed_from_v15=[n],hardware=False)))
