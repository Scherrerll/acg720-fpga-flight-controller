"""Prepare a read-only actual-netlist fanout comparison; never run synthesis."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;D=O/'compact_aw_v4_fan100_native/inspect_mapped_fanout.py';M=O/'compact_aw_v14'
t=D.read_text(encoding='utf8')
old="new=R/'out/z_aw_fix_20261026/compact_aw_v4_fan100_native/physical_p3r0_01'";assert t.count(old)==1
t=t.replace(old,"new=R/'out/z_aw_fix_20261026/compact_aw_v14/build_attempt_01'\nassert read(O/'runner_exit.json')['actual_p_wait']==0")
t=t.replace("'new_max100'","'new_local_hints'")
t=t.replace("families=['core/fallback_control/height_fallback_active_s'","families=['core/fallback_control/active_fanout_limited', 'core/fallback_control/height_fallback_active_s'")
t=t.replace('after the new SYN audit','after actual new SYN wait0 and strict audit')
ast.parse(t);dest=M/'inspect_mapped_fanout.py';assert not dest.exists();dest.write_text(t,encoding='utf8')
(M/'MAPPED_INSPECTION_DERIVATION.json').write_text(json.dumps({'parent_script_sha256':hashlib.sha256(D.read_bytes()).hexdigest(),
    'new_script_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'scope':'Read-only mapped topology/fanout; paths select actual SYN-only build and additionally inspect the local alias driver. Not executed by this preparation.'},indent=2)+'\n',encoding='utf8')
print('Prepared read-only v14 mapped inspection; no compiler, PNR or hardware action.')
