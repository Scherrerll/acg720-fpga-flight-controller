"""v16 plus a synthesis-only previous_pose_valid fanout hint from another real v4 late path."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v16';M=O/'compact_aw_v17'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v16/canonical/source';C=R/'out/z_aw_fix_20261026/compact_aw_v17/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
pf=read(P/'source_freeze.json');expected=pf['source55'];assert read(P/'PROOF_BINDING.json')['passed'] and read(P/'SYNTHESIS_RESULT.json')['passed_SYN_only']
assert all(sha(OLD/n)==h for n,h in expected.items()) and not M.exists() and not C.exists()
M.mkdir();shutil.copytree(OLD,C)
n='acg720_ano_port.v';a=' reg previous_pose_valid=0;';b=' reg previous_pose_valid /* synthesis syn_maxfan = 10 */ =0;'
s=(OLD/n).read_text(encoding='utf8');assert s.count(a)==1;t=s.replace(a,b);assert t.replace(b,a)==s;(C/n).write_text(t,encoding='utf8',newline='\n')
new={x:sha(C/x) for x in expected};assert [x for x in expected if expected[x]!=new[x]]==[n]
basis=read(P/'SOURCE_EQUIVALENCE_BASIS.json');basis['transformations'][n]=dict(edits=[[a,b]],baseline_sha256=pf['baseline_source55'][n],candidate_sha256=new[n],reverse_exact_normalized_text=True)
basis['unchanged_files']=51;basis['scope']='v16 plus one synthesis-only reg comment; no RTL state, equation, cycle or clock changes from v16. Full proofs and physical qualification separate.'
if (OLD/n).read_bytes()!=s.encode():basis['line_endings_normalized'].append(n)
(M/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps(basis,indent=2)+'\n',encoding='utf8')
review=(P/'source_review.md').read_text(encoding='utf8')+'''\n\n# v17：previous_pose_valid 数据寄存器的局部 syn_maxfan10\n\n从实际已证明/综合通过的v16只新增一个综合注释，RTL时钟、FF定义/状态与表达式不变。依据旧v4原始TR，previous_pose_valid→共享乘法 held_a38/42 为setup−0.140ns，首网布线6.920ns；v16实际映射仍有19个引脚负载。此前v14同属性真实产生9/8负载副本，但v14原19级主路径未布通，因此不能作为v17物理成功依据。此候选保留v16已缩至12级的主路径与active扇出50，只对第二条旧关键数据网请求局部复制；不约束clock/CE/reset，不新增状态或周期，不改全局扇出。必须以新SYN实测是否复制并保留严格50MHz物理门。相对v4共4文件变化，B3相对7文件。上方各段分别为父候选沿革，本段给出最终新增范围。\n'''
(M/'source_review.md').write_text(review,encoding='utf8')
(M/'source_changes.diff').write_text((P/'source_changes.diff').read_text(encoding='utf8')+''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='v16/'+n,tofile='v17/'+n)),encoding='utf8')
(M/'source_freeze.json').write_text(json.dumps(dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=new,baseline_source55=pf['baseline_source55'],changed_files=list(basis['transformations']),source_review_sha256=sha(M/'source_review.md'),source_equivalence_basis_sha256=sha(M/'SOURCE_EQUIVALENCE_BASIS.json'),parent_v16_source55=expected),indent=2)+'\n',encoding='utf8')
D=M/'proofs';D.mkdir()
for old,name in [(P/'proofs/run_top13.py','proofs/run_top13.py'),(P/'run_proofs.py','run_proofs.py'),*[(P/name,name) for name in ['verify_reused_bindings.py','run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']]]:
    text=old.read_text(encoding='utf8').replace('compact_aw_v16','compact_aw_v17').replace('v16','v17').replace('len(h.EXPECTED_CHANGES)==6','len(h.EXPECTED_CHANGES)==7').replace('len(helper.EXPECTED_CHANGES)==6','len(helper.EXPECTED_CHANGES)==7')
    ast.parse(text);(M/name).write_text(text,encoding='utf8')
(M/'SYNTHESIS_PREPARATION.json').write_text(json.dumps(dict(scope='v16 SYN-only gates retained with7 expected B3-relative files; paths and source-count adapted',source55=new,parent_v16_actual_SYN_result_sha256=sha(P/'SYNTHESIS_RESULT.json')),indent=2)+'\n',encoding='utf8')
(M/'PREPARATION.json').write_text(json.dumps(dict(scope='v16 plus previous_pose_valid syn_maxfan10 data-reg hint; full new exact-source miter/top13 and actual SYN required; one physical slot only after prior run ends',parent_proof_sha256=sha(P/'PROOF_BINDING.json'),mapped_basis_sha256=sha(P/'MAPPED_LANDING_COMPARISON.json'),source55=new,parent_source55=expected,parent_proof_runner_sha256=sha(P/'run_proofs.py'),new_proof_runner_sha256=sha(M/'run_proofs.py'),stimulus_changes='Only v16 to v17 path/text labels; same vectors/timing/assertions',vendor_started=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,source55=55,changed_from_v16=[n],hardware=False)))
