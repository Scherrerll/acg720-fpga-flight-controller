"""Prepare bound physical recipes only after actual successful v15 SYN and audit waits."""
from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[2];M=O/'compact_aw_v16';P=O/'compact_aw_v14'
A=R/'out/z_aw_fix_20261026/compact_aw_v16/build_attempt_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
syn=read(M/'SYNTHESIS_RESULT.json');assert syn['passed_SYN_only']
for path in [M/'runner_exit.json',A/'verification/synthesis_exit.json',A/'verification/audit_exit.json']:
    receipt=read(path);assert receipt['normal_wait_return'] and receipt['actual_p_wait']==0
VG=syn['netlist_sha256'];assert sha(A/'source/impl/gwsynthesis/acg720_ano_port.vg')==VG
names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']
for n in names:
    target=M/n;assert not target.exists()
    text=(P/n).read_text(encoding='utf8').replace('compact_aw_v14','compact_aw_v16').replace('v14','v16').replace('29b02a42dfe5d8899d5774213964235ef39f720d6ff0c6d05446cbd7315f7f48',VG)
    ast.parse(text);target.write_text(text,encoding='utf8')
for place in ['2','3']:(M/f'physical_p{place}r0_01').mkdir()
(M/'PHYSICAL_PREPARATION.json').write_text(json.dumps(dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='v16 landing predicate and one data-driver fanout hint, exact actual audited SYN VG. Original helper and all real20ns/50MHz timing/exit/pin/B4 gates retained. One physical job maximum in this chat.',source55=read(M/'source_freeze.json')['source55'],actual_SYN_vendor_wait=0,actual_SYN_runner_wait=0,actual_audit_wait=0,VG_sha256=VG,parent_scripts_sha256={n:sha(P/n) for n in names},new_scripts_sha256={n:sha(M/n) for n in names}),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(physical_prepared=True,VG_sha256=VG,source_files=55,vendor_started=False)))
