"""Prepare exact map1 VG physical recipes; no vendor process is started."""
from pathlib import Path
import ast, hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v13'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(O/'SYNTHESIS_RESULT.json')
assert result['passed_SYN_only'] and result['vendor_actual_wait']==result['runner_actual_wait']==0
vg=result['netlist_sha256'];assert vg=='f71a16a54abdb1f7cf13b3b943996cd7c4005d4d342de9306fb2566648a79272'
assert read(O/'PROOF_BINDING.json')['source55']==read(P/'PROOF_BINDING.json')['source55']==result['source55']
assert read(O/'PROOF_BINDING.json')['parent_proof_sha256']==sha(P/'PROOF_BINDING.json')
receipt=O/'PHYSICAL_PREPARATION.json';assert not receipt.exists()
files=['run_physical.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','launch_physical_hidden.py']
for name in files:
    target=O/name;assert not target.exists()
    text=(P/name).read_text()
    text=text.replace('v13','__CURRENT__').replace('v12','v13').replace('__CURRENT__','v13_map1')
    oldvg='001eca6c8a3e4f21e7d7fe84e33601bef9692d5fba739bff9fccb3b4c6ca639a'
    if name in ['run_physical.py','seal_terminal.py','independent_raw_review.py']:
        assert text.count(oldvg)==1;text=text.replace(oldvg,vg)
    if name=='run_physical.py':
        needle="O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=";assert text.count(needle)==1
        text=text.replace(needle,"O=Path(__file__).resolve().parent;R=O.parents[3];PROOF_DIR=O.parent/'compact_aw_v13/proofs';ROOT=")
        for filename in ['results.json','runner_exit.json']:
            text=text.replace("O/'proofs/"+filename+"'","PROOF_DIR/'"+filename+"'")
        needle="din['synthesis_options']=={'map_option':2,'replicate_resources':0}"
        assert text.count(needle)==1;text=text.replace(needle,"din['synthesis_options']=={'map_option':1,'replicate_resources':0}")
        needle="'set_option -place_option 3':f'set_option -place_option {PLACE}'"
        assert text.count(needle)==1
        text=text.replace(needle,needle+",'set_option -map_option 2':'set_option -map_option 1'")
        needle="('map_option','2')";assert text.count(needle)==1;text=text.replace(needle,"('map_option','1')")
        needle="'physical_options':{'place':PLACE,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1}"
        assert text.count(needle)==1
        text=text.replace(needle,"'physical_options':{'place':PLACE,'route':0,'map_option':1,'replicate_resources':0,'timing_driven':1}")
        needle="evidence += [O/'PROOF_BINDING.json']";assert text.count(needle)==1
        text=text.replace(needle,"assert binding['parent_proof_sha256']==sha(O.parent/'compact_aw_v13/PROOF_BINDING.json')\n    evidence += [O/'PROOF_BINDING.json',O.parent/'compact_aw_v13/PROOF_BINDING.json']")
    ast.parse(text);target.write_text(text,encoding='utf8')
receipt.write_text(json.dumps({'prepared_not_started':True,'netlist_sha256':vg,'map_option':1,
    'proof_origin':str(P/'PROOF_BINDING.json'),'proof_origin_sha256':sha(P/'PROOF_BINDING.json'),
    'scripts':{name:sha(O/name) for name in files},
    'scope':'Only prepare exact audited map1 VG P3/R0 or P2/R0. At most two owned PNR jobs; launch only after inspecting a current terminal result.'},indent=2)+'\n',encoding='utf8')
print('Prepared exact map1 VG physical scripts; no vendor started.')
