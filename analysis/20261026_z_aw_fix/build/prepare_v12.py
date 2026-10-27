"""One-expression rewrite of the v11 next-age predicate; all counter bits preserved."""
from pathlib import Path
import ast,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent/'compact_aw_v12';R=O.parents[3];D=O.parent/'compact_aw_v11'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v11/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v12/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists() and not NEW.exists();O.mkdir()
before=json.loads((D/'source_freeze.json').read_text())['source55'];assert {p:sha(OLD/p) for p in before}==before
shutil.copytree(OLD,NEW);rel='position/mtf_shared_height_fusion.v';p=NEW/rel;t=p.read_text()
a="publication_fresh<=((publication_age+32'd1)<AGE_LIMIT)";b="publication_fresh<=((AGE_LIMIT!=0)&&(publication_age<(AGE_LIMIT-32'd1)))"
assert t.count(a)==1;t=t.replace(a,b);p.write_text(t,encoding='utf8',newline='')
after={p:sha(NEW/p) for p in before};assert [p for p in before if before[p]!=after[p]]==[rel]
review='''# v12：下一年龄谓词的等价比较

仅将v11普通自增分支的f(age+32d1)改为AGE_LIMIT!=0 && age<(AGE_LIMIT-32d1)。分支原有age!=FFFFFFFF保证32位无符号加一不溢出；对L=0，两式对已初始化的已知年龄均为0；对非零32位L，A+1<L等价A<L-1。减数32d1令结果保持32位无符号，保留原integer参数参与比较时的无符号转换，含高位为1的参数。饱和保持、初始化/cleanup与发布覆盖不动，原32位年龄及同拍新鲜性不变量保持。

不声称任意强制破坏内部年龄或不变量后的X状态等价。原源输入可以四态，但年龄只从已知初始化/复位值、常数0及已知年龄加一产生；这些分支优先级不改。将用从两份实际源提取的表达式检查九种integer阈值的随机32位及边界值，并重做完整融合差分/同拍超时及top13。控制器、生产者、所有算术服务和54个其他文件完全不变。

动机是v11 age10到新位D的映射组合拓扑10级，局部高度融合+1FF/+45LUT；全顶层+789LUT中大部分来自跨模块重排，不能称作此加法器直接成本。去除比较前加一有明确逻辑取舍，但最终资源/延迟仍以新综合与完整物理报告判断。当前无综合、布线或下载资格。
'''
(O/'source_review.md').write_text(review,encoding='utf8');(O/'source_changes.diff').write_text(''.join(difflib.unified_diff((OLD/rel).read_text().splitlines(True),t.splitlines(True),fromfile='v11/'+rel,tofile='v12/'+rel)),encoding='utf8')
(O/'source_freeze.json').write_text(json.dumps({'scope':'v11 plus one equivalent next-age comparison expression; no counter-width/math/latency/clock changes.','source_root':str(NEW),'source55':after,'baseline_source55':before,'changed_files':[rel],'source_review_sha256':sha(O/'source_review.md'),'synthesis_started':False,'physical_started':False},indent=2)+'\n')
t=(D/'run_proofs.py').read_text()
old="OLD=R/'out/z_aw_fix_20261026/compact_aw_v9/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v11/canonical/source'";assert t.count(old)==1
t=t.replace(old,"OLD=R/'out/z_aw_fix_20261026/compact_aw_v11/canonical/source';NEW=R/'out/z_aw_fix_20261026/compact_aw_v12/canonical/source'")
old="before={'v9':read(O.parent/'compact_aw_v9/source_freeze.json')['source55'],'v11':read(O/'source_freeze.json')['source55']}";assert t.count(old)==1
t=t.replace(old,"before={'old':read(O.parent/'compact_aw_v11/source_freeze.json')['source55'],'new':read(O/'source_freeze.json')['source55']}")
t=t.replace("[('v9',OLD),('v11',NEW)]","[('old',OLD),('new',NEW)]").replace("before['v11']","before['new']").replace("before['v9']","before['old']")
t=t.replace(".replace('compact_aw_v4/canonical','compact_aw_v11/canonical')",".replace('compact_aw_v4/canonical','compact_aw_v12/canonical')")
t=t.replace("'fixtures':{str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file()}","'fixtures':{p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and (p.suffix=='.v' or p==D/'top/run.py')}")
marker="(D/'inputs.json').write_text(";assert t.count(marker)==1
extra=r'''
# Exact source expressions, tested with the original integer parameter type.
limits=[0,1,31,65536,5000000,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
oldtext=(OLD/'position/mtf_shared_height_fusion.v').read_text();newtext=(NEW/'position/mtf_shared_height_fusion.v').read_text()
oldexpr="((publication_age+32'd1)<AGE_LIMIT)";newexpr="((AGE_LIMIT!=0)&&(publication_age<(AGE_LIMIT-32'd1)))"
assert oldtext.count('publication_fresh<='+oldexpr)==1 and newtext.count('publication_fresh<='+newexpr)==1
model='module pred #(parameter integer AGE_LIMIT=5000000)(input wire [31:0] publication_age,output wire same);\nwire a='+oldexpr+';wire b='+newexpr+';assign same=(publication_age==32\'hffffffff)||(a===b);endmodule\n'
pred='`timescale 1ns/1ps\n`default_nettype none\n'+model+'module predicate_tb;reg[31:0]publication_age=0;wire[8:0]same;integer checks=0,n;reg[31:0]rng=32\'h9c137ac5;\n'
for i,lim in enumerate(limits):pred+=f"pred #(.AGE_LIMIT(32'h{lim:08x})) p{i}(.publication_age(publication_age),.same(same[{i}]));\n"
pred+="task check;input[31:0]x;begin publication_age=x;#1;if(same!==9'h1ff)$fatal(1,\"unsigned rewrite mismatch A=%h same=%h\",x,same);checks=checks+1;end endtask\ninitial begin\n"
values=[0,1,0xfffffffe,0xffffffff]+[((lim+k)&0xffffffff) for lim in limits for k in [-2,-1,0,1]]
for value in values:pred+=f"check(32'h{value:08x});\n"
pred+="for(n=0;n<200000;n=n+1)begin rng=(rng*32'd1664525)+32'd1013904223;check(rng);end\n$display(\"PASS predicate vectors=%0d integer_limits=9 eligible_increment_age_excludes_MAX=1\",checks);$finish;end\nendmodule\n`default_nettype wire\n"
(D/'predicate_tb.v').write_text(pred)
'''
t=t.replace(marker,extra+'\n'+marker)
marker='records=[]\n';assert t.count(marker)==1
t=t.replace(marker,"run('predicate_compile',[str(IV),'-g2012','-Wall','-s','predicate_tb','-o',str(D/'predicate.vvp'),str(D/'predicate_tb.v')])\npredicate_log=run('predicate_simulation',[str(VVP),str(D/'predicate.vvp')]);assert 'PASS predicate vectors=200040 integer_limits=9' in predicate_log\n"+marker)
t=t.replace('PASS v11 full fusion','PASS v12 predicate/full fusion')
ast.parse(t);(O/'run_proofs.py').write_text(t)
t=(D/'launch_proofs_hidden.py').read_text();ast.parse(t);(O/'launch_proofs_hidden.py').write_text(t)
(O/'PROOF_PREPARATION.json').write_text(json.dumps({'scope':'Same original eight full-fusion/expiry cases andtop13, plus exact-expression unsigned32 rewrite check over9 integer limits/200040vectors. No DUT-state force; source module arithmetic unchanged.',
    'template_runner_sha256':sha(D/'run_proofs.py'),'derived_runner_sha256':sha(O/'run_proofs.py'),'expected_immutable_stimuli':6,'new_flag_expression':b,'proof_started':False},indent=2)+'\n')
print('Prepared v12 one-expression source and complete proof runner; no tests/SYN/PNR started.')
