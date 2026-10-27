"""v4 plus combinational distribution of landing comparison across collective mux."""
from pathlib import Path
import ast, datetime, difflib, hashlib, json, shutil
O=Path(__file__).resolve().parent;R=O.parents[2];M=O/'compact_aw_v15'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v15/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
before=read(O/'v4_release_proofs/RESULT.json')['source55']
assert len(before)==55 and all(sha(OLD/n)==h for n,h in before.items())
assert not M.exists() and not NEW.exists();M.mkdir();shutil.copytree(OLD,NEW)
changes={
 'core/ano_flight_state.v':[
 ('module ano_flight_state #(parameter integer TICKS_PER_MS=50000)(', 'module ano_flight_state #(parameter integer TICKS_PER_MS=50000,\n parameter integer PRECHECKED_COLLECTIVE=0)('),
 (' input wire [15:0] ch3,collective_us,',' input wire [15:0] ch3,collective_us,\n input wire collective_below_landing,'),
 (' wire positive_stick=ch3>=1594;', ' wire positive_stick=ch3>=1594;\n wire landing_collective_low=PRECHECKED_COLLECTIVE ?collective_below_landing:(collective_us<1250);'),
 ('ch3<=1150 && collective_us<1250','ch3<=1150 && landing_collective_low')],
 'core/flight_core.v':[
 ('ano_flight_state #(.TICKS_PER_MS(FLIGHT_STATE_TICKS_PER_MS)) flight_state', 'ano_flight_state #(.TICKS_PER_MS(FLIGHT_STATE_TICKS_PER_MS),.PRECHECKED_COLLECTIVE(1)) flight_state'),
 ('.ch3(ch3),.collective_us(selected_throttle),.motor_prepared(motor_prepared),', '.ch3(ch3),.collective_us(selected_throttle),.collective_below_landing(selected_collective_below_landing),.motor_prepared(motor_prepared),'),
 ('    wire [15:0] fallback_collective,fallback_unmasked_collective;', '    wire [15:0] fallback_collective,fallback_unmasked_collective;\n    // Compare each numeric branch before the late live availability selection.\n    // No state or cycle is added; active implies public fallback equals unmasked.\n    (* syn_keep = 1 *) wire fallback_collective_below_landing=fallback_unmasked_collective<1250;\n    (* syn_keep = 1 *) wire auto_collective_below_landing=hold_collective_us<1250;\n    wire selected_collective_below_landing=height_fallback_active ?fallback_collective_below_landing:auto_collective_below_landing;')]
}
diff='';transforms={};normalised=[]
for n,edits in changes.items():
    raw=(OLD/n).read_text(encoding='utf8');s=raw
    for a,b in edits:assert s.count(a)==1;(None);s=s.replace(a,b)
    rev=s
    for a,b in reversed(edits):assert rev.count(b)==1;rev=rev.replace(b,a)
    assert rev==raw
    if (OLD/n).read_bytes()!=raw.encode():normalised.append(n)
    (NEW/n).write_text(s,encoding='utf8',newline='\n')
    transforms[n]=dict(edits=edits,baseline_sha256=sha(OLD/n),candidate_sha256=sha(NEW/n),reverse_exact_normalized_text=True)
    diff+=''.join(difflib.unified_diff(raw.splitlines(True),s.splitlines(True),fromfile='v4/'+n,tofile='v15/'+n))
after={n:sha(NEW/n) for n in before}
assert sorted(n for n in before if before[n]!=after[n])==sorted(changes)
review='''# v15：着陆阈值比较分配到油门选择器之前

依据 v4 实际最差路径 output_az_3 到 flight_state/flying_ms_3：垂直可用性经过 fallback active，再选择16位 collective，随后比较 collective<1250，最后着陆状态分支可清零 flying_ms。这里仅把同一比较分配到两个数值分支，再选择1位结果，不添加寄存器、周期或保护延迟。

严格等价依据：active 为1时 fallback_collective 等于 fallback_unmasked_collective；active 为0时 selected_throttle 等于 hold_collective_us。因此对硬件二值输入，(active ? (active ? unmasked : 1000) : automatic)<1250 等于 active ? (unmasked<1250) : (automatic<1250)。阈值与所有着陆条件/优先级保持。两个纯组合分支比较使用 syn_keep 防止工具把阈值重新吸收到宽选择器之后；实际映射效果必须看新网表与 STA。

ano_flight_state 新增默认0参数 PRECHECKED_COLLECTIVE 和一位输入；默认仍逐字使用原 collective_us<1250，core 显式启用并传入同拍谓词。各 always 块内仅替换该条件名字；所有状态、更新式、复位、初值与输出不变。新增接口不用于其他调用者。对于无效 X 输入的仿真四态传播不作通用代数等价声明；自然初始化和二值功能输入须严格逐拍对比。

只改 core/flight_core.v 与 core/ano_flight_state.v；53文件字节不变，包括 v4 反积分控制器、XY1000/350默认、时基/时钟/约束。修改文件的 CRLF→LF 若存在会单独记录。候选先跑阈值全值覆盖、旧新完整飞行状态逐拍比较和原 top13，再绑定原六依赖五场景/FRAC/争用与43地面输入。新综合/物理资格另验；不得从这个数学依据宣称已通过时序或安装。
'''
(M/'source_review.md').write_text(review,encoding='utf8')
(M/'source_changes.diff').write_text(diff,encoding='utf8')
(M/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps(dict(scope='Binary combinational distributivity only; actual simulations and physical gates separate',transformations=transforms,unchanged_files=53,line_endings_normalized=normalised,threshold=1250,no_new_state_or_cycle=True),indent=2)+'\n',encoding='utf8')
(M/'source_freeze.json').write_text(json.dumps(dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=after,baseline_source55=before,changed_files=list(changes),source_review_sha256=sha(M/'source_review.md'),source_equivalence_basis_sha256=sha(M/'SOURCE_EQUIVALENCE_BASIS.json')),indent=2)+'\n',encoding='utf8')
D=M/'proofs';D.mkdir()
parent=O/'compact_aw_v14/proofs/run_top13.py'
runner=parent.read_text(encoding='utf8').replace('compact_aw_v14','compact_aw_v15')
ast.parse(runner);(D/'run_top13.py').write_text(runner,encoding='utf8')
(M/'TOP13_RUNNER_DERIVATION.json').write_text(json.dumps(dict(parent=str(parent),parent_runner_sha256=sha(parent),new_runner_sha256=sha(D/'run_top13.py'),change='Only canonical source directory v14 to v15; testbench stimulus unchanged'),indent=2)+'\n',encoding='utf8')
for n in ['verify_reused_bindings.py','run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py']:
    s=(O/'compact_aw_v14'/n).read_text(encoding='utf8').replace('compact_aw_v14','compact_aw_v15').replace('new_v14_proof','new_v15_proof').replace('v14','v15')
    ast.parse(s);(M/n).write_text(s,encoding='utf8')
(M/'SYNTHESIS_PREPARATION.json').write_text(json.dumps(dict(scope='v14 SYN-only runner/auditor adapted to v15 paths and proof key; actual original gates retained, B3-relative5 source files',parent_sha256={n:sha(O/'compact_aw_v14'/n) for n in ['run_synthesis.py','audit_synthesis_only.py']},source55=after),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,source55=len(after),changed_files=list(changes),new_state=False,new_cycles=0)))
