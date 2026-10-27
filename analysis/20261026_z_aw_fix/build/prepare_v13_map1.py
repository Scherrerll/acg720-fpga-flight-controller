"""Prepare a SYN-only mapping comparison on identical proven v13 source55."""
from pathlib import Path
import ast, datetime, hashlib, json, shutil
O=Path(__file__).resolve().parent;R=O.parents[2];P=O/'compact_aw_v13';M=O/'compact_aw_v13_map1'
OLD=R/'out/z_aw_fix_20261026/compact_aw_v13/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v13_map1/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not M.exists() and not NEW.exists()
proof=read(P/'PROOF_BINDING.json');expected=proof['source55']
assert proof['passed'] and proof['actual_proof_runner_wait']==0
assert {n:sha(OLD/n) for n in expected}==expected
for name,item in proof['artifacts'].items():
    path=R/name;assert path.resolve().is_relative_to(R) and path.name.lower()!='deployment.env' and '.env' not in path.suffixes
    assert sha(path)==item['sha256']
M.mkdir();shutil.copytree(OLD,NEW)
review=M/'source_review.md'
review.write_text('''# v13 同源 map1 综合对照

55份源码逐字节等于已经通过行为证明的v13，canonical build.tcl仍按源清单保持map2。只在实际执行的独立SYN Tcl中将map_option由2改为1，其余area、replicate0、50MHz/20ns、唯一原radio输入falsepath和UserCode不改。官方本地SUG1220-2.1E PDF第37页将1列为默认映射，2为不增加LUT数量的LUT5导向映射；本轮没有宣称1更省面积或更快，须查看实际资源和网表审计。

依据是既有实际完整路由报告的CLS89%/Logic77%占用与多次map2布线拥塞。默认映射可能改变LUT尺寸分布和打包取舍；该假设只授权一次SYN资源对照，不授予物理或下载资格。v13两条物理运行不被更改，不增加当前物理任务数。功能证明由同一55源和v13实际7阶段/root0及其父证明哈希复用；不复制或重新标注旧测试退出记录。新网表仍须新clock/radio/gain/18ports审计和真实正常退出。当前不启动PNR。
''',encoding='utf8')
freeze={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source55':expected,
        'baseline_source55':expected,'changed_files':[],'source_review_sha256':sha(review),
        'parent_v13_proof_binding_sha256':sha(P/'PROOF_BINDING.json'),
        'effective_SYN_option_override':{'map_option':{'source_baseline':2,'executed_SYN':1}},
        'scope':'Identical RTL55, SYN mapping experiment only; actual Tcl is separate from immutable source build.tcl.'}
(M/'source_freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
(M/'PROOF_BINDING.json').write_text(json.dumps({'passed':True,'source55':expected,'actual_proof_runner_wait':0,
    'scope':'Exact same source55 reuses actual v13 proofs; no new simulation claim.',
    'parent_proof':str(P/'PROOF_BINDING.json'),'parent_proof_sha256':sha(P/'PROOF_BINDING.json'),
    'parent_artifacts_rechecked':len(proof['artifacts'])},indent=2)+'\n')
text=(P/'run_synthesis.py').read_text()
text=text.replace('v13','__CURRENT__').replace('v12','v13').replace('__CURRENT__','v13_map1')
needle="O=Path(__file__).resolve().parent;R=O.parents[3];ROOT="
assert text.count(needle)==1
text=text.replace(needle,"O=Path(__file__).resolve().parent;R=O.parents[3];PROOF_DIR=O.parent/'compact_aw_v13/proofs';ROOT=")
for name in ['results.json','runner_exit.json']:
    text=text.replace("O/'proofs/"+name+"'","PROOF_DIR/'"+name+"'")
needle="'synthesis_options':{'map_option':2,'replicate_resources':0}"
assert text.count(needle)==1;text=text.replace(needle,"'synthesis_options':{'map_option':1,'replicate_resources':0}")
needle="'run syn' if line=='run all' else line"
assert text.count(needle)==1
text=text.replace(needle,"'run syn' if line=='run all' else 'set_option -map_option 1' if line=='set_option -map_option 2' else line")
needle="tcl,re.M)==['2']";assert text.count(needle)==1;text=text.replace(needle,"tcl,re.M)==['1']")
text=text.replace('candidate_v13_map1_map2','candidate_v13_map1_map1')
text=text.replace('Actual map2 vs map2 resources only','Actual map1 vs map2 resources on identical RTL55 only')
text=text.replace('v13_map1 map2 full-top','v13_map1 map1 full-top').replace('v13_map1 fulltop/map2','v13_map1 fulltop/map1')
ast.parse(text);(M/'run_synthesis.py').write_text(text,encoding='utf8')
(M/'launch_synthesis_hidden.py').write_bytes((P/'launch_synthesis_hidden.py').read_bytes())
(M/'PREPARATION.json').write_text(json.dumps({'prepared_only':True,'source_files':55,
    'parent_SYN_runner_sha256':sha(P/'run_synthesis.py'),'new_SYN_runner_sha256':sha(M/'run_synthesis.py'),
    'source_freeze_sha256':sha(M/'source_freeze.json'),'proof_binding_sha256':sha(M/'PROOF_BINDING.json')},indent=2)+'\n')
print('Prepared exact-v13-source map1 SYN-only comparison; no vendor launched.')
