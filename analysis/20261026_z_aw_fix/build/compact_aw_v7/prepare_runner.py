"""Freeze a v5-derived SYN_ONLY runner in the new v7 evidence folder."""
from pathlib import Path
import hashlib, json

O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=O.parent/'compact_aw_v5/run_synthesis.py'
assert sha(prior)=='87f36cb27859f379c0bf2eb2909665f729015d33c21ef191410bc47514113904'
assert not (O/'run_synthesis.py').exists()
assert not (O/'launch_synthesis_hidden.py').exists()
freeze=json.loads((O/'source_freeze.json').read_text())
hold=freeze['source55']['position/mtf_xyz_hold_control.v']
text=prior.read_text().replace('v5','v7').replace('v4','v5')
text=text.replace("HOLD_SHA='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'", "HOLD_SHA='"+hold+"'")
text=text.replace("prior['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'", "prior['position/mtf_xyz_hold_control.v']=='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'")
text=text.replace('import hashlib,importlib.util,json,os,re,shutil,traceback,xml.etree.ElementTree as ET', 'import hashlib,importlib.util,json,os,re,shutil,sys,traceback,xml.etree.ElementTree as ET\nsys.dont_write_bytecode=True')
text=text.replace("    assert hash55(CANON,expected)==expected", "    assert prior==freeze['baseline_source55']\n    assert sha(O/'source_review.md')==freeze['source_review_sha256']\n    assert sha(O.parent/'sign_step_bound.md')==freeze['proof_sha256']\n    assert hash55(CANON,expected)==expected", 1)
text=text.replace("    tmp=VERIFY/'tmp';tmp.mkdir();", "    shutil.copy2(Path(__file__),VERIFY/'executed_run_synthesis.py')\n    tmp=VERIFY/'tmp';tmp.mkdir();", 1)
text=text.replace("    helper.check_sources(expected);assert hash55(PRIOR/'canonical/source',expected)==prior", "    assert not (SOURCE/'impl/pnr').exists(),'SYN_ONLY must not produce PNR artifacts'\n    helper.check_sources(expected);assert hash55(PRIOR/'canonical/source',expected)==prior", 1)
text=text.replace("    print(json.dumps({'synthesis_only_pass':True", "    manifest={'scope':'v7 SYN_ONLY raw artifact freeze; excludes itself; no PNR qualification', 'source_sha256':expected, 'source_freeze_sha256':sha(O/'source_freeze.json'), 'runner_sha256':sha(Path(__file__)), 'PNR_started':False, 'artifacts':{p.relative_to(ATTEMPT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(ATTEMPT.rglob('*')) if p.is_file()}}\n    (ATTEMPT/'synthesis_freeze_manifest_final.json').write_text(json.dumps(manifest,indent=2)+'\\n',encoding='utf8')\n    print(json.dumps({'synthesis_only_pass':True", 1)
compile(text,str(O/'run_synthesis.py'),'exec')
(O/'run_synthesis.py').write_text(text,encoding='utf8',newline='\n')
supervisor=(O.parent/'compact_aw_v6/launch_synthesis_hidden.py').read_text()
compile(supervisor,str(O/'launch_synthesis_hidden.py'),'exec')
(O/'launch_synthesis_hidden.py').write_text(supervisor,encoding='utf8',newline='\n')
receipt=dict(baseline_runner=str(prior),baseline_runner_sha256=sha(prior),source_freeze_sha256=sha(O/'source_freeze.json'),runner_sha256=sha(O/'run_synthesis.py'),supervisor_sha256=sha(O/'launch_synthesis_hidden.py'),changes='Paths/labels v5->v7 and baseline v4->v5; hold freeze update; frozen proof/note checks; copied executed runner; no-PNR artifact assertion; final artifact manifest. Original helper and extended gates unchanged.')
(O/'runner_derivation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,indent=2))
