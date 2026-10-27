"""One-time offline tightening of dormant thin diagnostics; no runtime/vendor."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json
O=Path(__file__).resolve().parent;P=O.parent/'prepare_v20_dsp_followup.py';S=O.parent/'compact_aw_v20'
OLD=O/'prepared_revisions/revision_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8',newline='\n')
assert read(OLD/'REVISION_MANIFEST.json')['runtime_attempt_absent']
for n,x in read(OLD/'REVISION_MANIFEST.json')['immutable_saved_files'].items():assert sha(OLD/n)==x['sha256']
assert P.read_bytes()==(OLD/P.name).read_bytes()
def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def tighten_terminal(text,kind):
    if kind=='seal':
        text=one(text,'"""Preserve actual terminal evidence once; no gate changes, process controls or rebuild."""','"""Preserve terminal evidence once; diagnostic PASS requires actual successful waits."""')
        text=one(text,"read=lambda p:json.loads(p.read_text())\nrunner=read(REPORT/'runner_exit.json');assert runner['normal_wait_return'] is True\nvendor=read(V/'physical_exit.json');assert vendor['normal_wait_return'] is True", "read=lambda p:json.loads(p.read_text()) if p.is_file() else None\nfrom terminal_diagnostics import terminal_status\nassert (REPORT/'runner_exit.json').is_file() and (V/'physical_exit.json').is_file(), 'Both terminal receipt files must exist before sealing'\nrunner=read(REPORT/'runner_exit.json')\nvendor=read(V/'physical_exit.json')")
        text=one(text,"passed=(V/'build_result.json').is_file() and read(V/'build_result.json')['passed'] is True","build_result=read(V/'build_result.json')")
        text=one(text,"classification='full_gate_pass' if passed else 'completed_full_route_timing_failure' if audit and audit['criteria']['full_route'] and vendor['actual_p_wait']==0 else 'route_failure' if vendor['actual_p_wait']!=0 and (any(unrouted) or 'DesRoute failed.' in physical_log) else 'vendor_nonzero_unclassified' if vendor['actual_p_wait']!=0 else 'physical_gate_or_artifact_failure'","passed,classification=terminal_status(build_result,vendor,runner,audit,unrouted,physical_log)")
        text=one(text,"    vendor_actual_p_wait=vendor['actual_p_wait'],runner_actual_p_wait=runner['actual_p_wait'],passed=passed,", "    vendor_actual_p_wait=vendor.get('actual_p_wait') if isinstance(vendor,dict) else None,\n    runner_actual_p_wait=runner.get('actual_p_wait') if isinstance(runner,dict) else None,passed=passed,\n    vendor_normal_wait_return=vendor.get('normal_wait_return') if isinstance(vendor,dict) else None,\n    runner_normal_wait_return=runner.get('normal_wait_return') if isinstance(runner,dict) else None,")
    elif kind=='snapshot':
        text=one(text,"def read(p):return json.loads(p.read_text()) if p.is_file() else None","def read(p):return json.loads(p.read_text()) if p.is_file() else None\nfrom terminal_diagnostics import terminal_status")
        anchor="    vendor=read(v/'physical_exit.json');runner=read(a/'runner_exit.json');audit=read(v/'physical_audit.json');result=read(v/'build_result.json');failure=read(v/'build_failure.json')"
        text=one(text,anchor,anchor+"\n    unrouted=[int(x) for x in re.findall(r'total\\s+(\\d+)\\s+unrouted nets',text,re.I)]\n    passed,classification=terminal_status(result,vendor,runner,audit,unrouted,text)")
        text=one(text,"        vendor_actual_p_wait=vendor['actual_p_wait'] if vendor else None,\n        runner_actual_p_wait=runner['actual_p_wait'] if runner else None,\n        full_gate_pass=bool(result and result.get('passed')),\n        terminal=bool(runner),unrouted=[int(x) for x in re.findall(r'total\\s+(\\d+)\\s+unrouted nets',text,re.I)])", "        vendor_actual_p_wait=vendor.get('actual_p_wait') if isinstance(vendor,dict) else None,\n        runner_actual_p_wait=runner.get('actual_p_wait') if isinstance(runner,dict) else None,\n        full_gate_pass=passed,\n        terminal=bool(runner),unrouted=unrouted)")
        text=one(text,"        if vendor and vendor['actual_p_wait']!=0:row['failure_class']='vendor_nonzero_route_failure' if any(row['unrouted']) else 'vendor_nonzero_unclassified'\n        elif audit:row['failure_class']='completed_vendor_physical_gate_failure'\n        elif vendor:row['failure_class']='completed_vendor_missing_or_unparseable_artifact'\n        else:row['failure_class']='runner_ended_without_vendor_exit_receipt'", "        row['failure_class']=classification")
    else:raise AssertionError(kind)
    return text

for name,kind in [('seal_terminal.py','seal'),('physical_snapshot.py','snapshot')]:
    assert tighten_terminal((OLD/name).read_text(),kind)==(O/name).read_text(),name
text=(OLD/P.name).read_text()
tree=ast.parse(Path(__file__).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tighten_terminal')
helper_source=(O/'terminal_diagnostics.py').read_text()
insert='\nDIAGNOSTICS_SOURCE='+repr(helper_source)+'\n'+ast.get_source_segment(Path(__file__).read_text(),node)+"\n(O/'terminal_diagnostics.py').write_text(DIAGNOSTICS_SOURCE,encoding='utf8',newline='\\n')\n\n"
text=one(text,"text=add_standard((P/'run_physical.py').read_text(encoding='utf8'))",insert+"text=add_standard((P/'run_physical.py').read_text(encoding='utf8'))")
text=one(text,"(O/'seal_terminal.py').write_text(text,encoding='utf8',newline='\\n')","text=tighten_terminal(text,'seal')\n(O/'seal_terminal.py').write_text(text,encoding='utf8',newline='\\n')")
text=one(text,"(O/'physical_snapshot.py').write_text(text,encoding='utf8',newline='\\n')","text=tighten_terminal(text,'snapshot')\n(O/'physical_snapshot.py').write_text(text,encoding='utf8',newline='\\n')")
text=text.replace("names+['portable_constraints.py']","names+['portable_constraints.py','terminal_diagnostics.py']")
text=one(text,"(O/'SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\\n')","diff+=''.join(difflib.unified_diff([],DIAGNOSTICS_SOURCE.splitlines(True),fromfile='/dev/null',tofile='v20_dsp_followup/terminal_diagnostics.py'))\n(O/'SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\\n')")
text=one(text,"'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})","'diagnostic_PASS_requires':\"build_result.passed is True AND actual vendor/root receipt normal_wait_return is True and exact int actual_p_wait==0\",'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})")
ast.parse(text);P.write_text(text,encoding='utf8',newline='\n')
names=list(read(O/'PHYSICAL_PREPARATION.json')['parent_scripts_sha256'])
diff=''
for n in names:diff+=''.join(difflib.unified_diff((S/n).read_text().splitlines(True),(O/n).read_text().splitlines(True),fromfile='standard_v20/'+n,tofile='v20_dsp_followup/'+n))
diff+=''.join(difflib.unified_diff([],helper_source.splitlines(True),fromfile='/dev/null',tofile='v20_dsp_followup/terminal_diagnostics.py'))
(O/'SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json')
binding['preparation_diagnostic_correction']={'revision':'02','prior_revision_manifest':str(OLD/'REVISION_MANIFEST.json'),'prior_revision_manifest_sha256':sha(OLD/'REVISION_MANIFEST.json'),'scope':'Only dormant thin diagnostic PASS/seal/snapshot truth gates strengthened; standardv20 physical gates, source55,VG,CST/SDC and portable41 rows unchanged.'}
binding['bound_inputs'][str(OLD/'REVISION_MANIFEST.json')]=sha(OLD/'REVISION_MANIFEST.json')
write(O/'PORTABLE_CONSTRAINT_BINDING.json',binding)
print(json.dumps({'updated_preparer_sha256':sha(P),'saved_revision_manifest_sha256':sha(OLD/'REVISION_MANIFEST.json'),'binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'runtime_created':False,'vendor_started':False}))
