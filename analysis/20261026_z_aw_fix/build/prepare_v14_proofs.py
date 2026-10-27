"""Prepare exact original top13 stimulus at v14; only capture actual new process receipts."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;M=O/'compact_aw_v14';D=M/'proofs';P=O/'v4_release_proofs'
assert not D.exists();D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=(P/'run_top13.py').read_text(encoding='utf8')
assert text.count('compact_aw_v4/canonical')==1
text=text.replace('compact_aw_v4/canonical','compact_aw_v14/canonical')
for kind,marker in [('compile',"(O/'top_safety.compile.log').write_text"),('vvp',"(O/'top_safety.log').write_text")]:
    assert text.count(marker)==1
    receipt="(O/'"+kind+"_exit.json').write_text(json.dumps({'actual_completedprocess_returncode':c.returncode,'normal_return':True,'command':c.args},indent=2))\n"
    text=text.replace(marker,receipt+marker)
ast.parse(text);(D/'run_top13.py').write_text(text,encoding='utf8')
(M/'TOP13_RUNNER_DERIVATION.json').write_text(json.dumps({'parent_runner_sha256':sha(P/'run_top13.py'),
    'new_runner_sha256':sha(D/'run_top13.py'),'stimulus_text_unchanged':True,
    'changes':'Only canonical source root v4 to v14 and actual compile/vvp CompletedProcess return-code receipts. Existing testbench text, expectations and 13 gate stimuli unchanged.'},indent=2)+'\n',encoding='utf8')
print('Prepared original top13 stimulus for exact v14 source; not executed.')
