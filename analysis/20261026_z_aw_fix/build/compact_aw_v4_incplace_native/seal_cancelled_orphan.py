"""Seal actual root1 plus separately observed native OS cancellation; no vendor p.wait claim."""
from pathlib import Path
import datetime,gzip,hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];A=R/'out/z_aw_fix_20261026/compact_aw_v4_incplace_native/physical_p3r0_01';V=A/'verification';D=O/'physical_p3r0_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
expected=read(O/'source_freeze.json')['source55']
assert all(sha(A/'source'/n)==h for n,h in expected.items())
root=read(D/'runner_exit.json');close=read(V/'controlled_cancellation_closed.json')
assert root['actual_p_wait']==1 and root['normal_wait_return']
assert close['actual_vendor_p_wait'] is None and close['observed_native_OS_exit_code']==-1
assert sha(V/'physical.log')==close['log_sha256_after_close']
log=(V/'physical.log').read_text(encoding='utf8',errors='replace')
assert 'matching(2.82)' in log and 'default placement flow will be run' in log
assert 'SYNTHESIS_AUDIT_RETURNED_EOF' in log and not (V/'physical_exit.json').exists()
old=R/'out/z_aw_fix_20261026/compact_aw_v4_native/physical_p3r0_01/source/impl/gwsynthesis/acg720_ano_port.vg'
new=A/'source/impl/gwsynthesis/acg720_ano_port.vg'
# Whole file hashes differ because generated comments contain time/absolute source paths.
# Compare only exact noncomment bytes as a diagnostic, never use this normalization for artifact hashes.
strip=lambda p:'\n'.join(line for line in p.read_text(encoding='utf8').splitlines() if not line.lstrip().startswith('//'))
old_text,new_text=strip(old),strip(new)
equivalence=dict(scope='Diagnostic textual comparison after removing only full-line comments; not a functional or physical qualification',old_raw_sha256=sha(old),new_raw_sha256=sha(new),noncomment_text_equal=old_text==new_text,old_noncomment_sha256=hashlib.sha256(old_text.encode()).hexdigest(),new_noncomment_sha256=hashlib.sha256(new_text.encode()).hexdigest(),monitor_error='Compared whole generated VG hashes, so timestamp/source-index comments caused the assertion before proc.wait; own orphan later identified and closed')
(O/'NATIVE_INCREMENTAL_OBSERVATION.json').write_text(json.dumps(equivalence,indent=2)+'\n',encoding='utf8')
paths=[D/n for n in ['runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log']]
paths += [V/n for n in ['physical_process.json','physical.log','build_input.json','physical_input.json','build_failure.json','controlled_cancellation.json','controlled_cancellation_closed.json','native_synthesis_audit.json','mapped_audit.json','strict_ff_clock_audit.json','gain_port_audit.json']]
paths += [A/'physical.tcl',O/'run_physical.py',O/'PREPARATION.json',O/'NATIVE_INCREMENTAL_OBSERVATION.json']
out=D/'TERMINAL_MANIFEST.json';copies=D/'terminal_receipts';assert not out.exists() and not copies.exists();copies.mkdir()
items={}
for p in paths:
    dest=copies/p.name;assert not dest.exists();data=p.read_bytes()
    if p.suffix=='.log':
        dest=dest.with_suffix(dest.suffix+'.gz')
        with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as z:z.write(data)
    else:dest.write_bytes(data)
    items[p.relative_to(R).as_posix()]=dict(sha256=sha(p),bytes=len(data),preserved=dest.relative_to(R).as_posix(),preserved_sha256=sha(dest))
result=dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),profile='physical_p3r0_01',classification='cancelled_orphan_after_runner_assertion',passed=False,vendor_actual_p_wait=None,runner_actual_p_wait=1,observed_native_OS_exit_code=-1,source55=expected,source55_unchanged=True,vg_sha256=sha(new),unrouted_reports=[],criteria=None,artifacts=items,scope='No completed PNR/STA. Native incremental reuse again rejected2.82percent. Original runner1 and distinct external handle close preserved without fabricating vendor wait.')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(sealed=True,classification=result['classification'],noncomment_vg_equal=equivalence['noncomment_text_equal'],vendor_p_wait=None,root_p_wait=1)))
