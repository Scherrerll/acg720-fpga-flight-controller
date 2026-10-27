"""Prepare native-flow auditors while preserving original physical gates byte-for-byte."""
from pathlib import Path
import ast, hashlib, json
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
helper=R/'firmware/B0B4/build_candidate.py'
assert sha(helper)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
text=helper.read_text(encoding='utf8')
function=text[text.index('def physical_audit('):text.index('\ndef main():')]
original=function
needle="    base=SOURCE/'impl/pnr/acg720_ano_port'"
assert function.count(needle)==1
function=function.replace(needle,"""    syn=json.loads((VERIFY/'native_synthesis_audit.json').read_text(encoding='utf8'))
    assert syn['passed'] and syn['source55']==expected and syn['netlist_sha256']==vg_sha
    assert sha(SOURCE/'acg720_ano_port.gprj')==syn['project_sha256']
    for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
        data=json.loads((VERIFY/name).read_text(encoding='utf8'))
        assert data['passed'] and sha(VERIFY/name)==syn[name.replace('.json','_sha256')]
    clock_audit=json.loads((VERIFY/'strict_ff_clock_audit.json').read_text(encoding='utf8'))
    assert clock_audit['all_FF_CLK50'] and not clock_audit['bad']
    project_files=[f.attrib for f in ET.parse(SOURCE/'acg720_ano_port.gprj').findall('.//File')]
    native_project=any(f.get('type')=='file.verilog' and f.get('enable')=='1' for f in project_files) and not any(f.get('type')=='file.netlist' for f in project_files)
"""+needle)
needle="        skip_synthesis='Skip synthesis, because there is only one netlist file' in log,"
assert function.count(needle)==1
function=function.replace(needle,"""        native_RTL_project=native_project,
        native_synthesis_audited=all(marker in log for marker in ['GowinSynthesis finish','SYNTHESIS_COMMAND_RETURNED_EOF','SYNTHESIS_AUDIT_RETURNED_EOF']) and 'Skip synthesis, because there is only one netlist file' not in log,
        constrained_frequency_50=float(fmax[1])==50,
""")
function=function.replace("SOURCE/'physical.gprj'","SOURCE/'acg720_ano_port.gprj'")
needle="    write('physical_audit.json',out)";assert function.count(needle)==1
function=function.replace(needle,"    out.update(workflow='native_RTL_project_SYN_audit_PNR_one_vendor_process',native_synthesis_audit_sha256=sha(VERIFY/'native_synthesis_audit.json'))\n"+needle)
prefix="""from pathlib import Path
import hashlib,json,math,re,xml.etree.ElementTree as ET
SOURCE=VERIFY=ATTEMPT=None
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\\n',encoding='utf8')
"""
generated=prefix+function
ast.parse(generated);target=O/'native_physical_audit.py';assert not target.exists();target.write_text(generated,encoding='utf8')

# Keep a separately implemented raw-table parser independent of the physical auditor.
parent=O.parent/'compact_aw_v13/independent_raw_review.py'
raw=parent.read_text(encoding='utf8').replace('compact_aw_v13','compact_aw_v13_native')
raw=raw.replace('import datetime, hashlib, json, math, re, sys','import datetime, hashlib, json, math, re, sys, xml.etree.ElementTree as ET')
needle="checks={'vendor_wait0'";assert raw.count(needle)==1
raw=raw.replace(needle,"syn=read(V/'native_synthesis_audit.json') if (V/'native_synthesis_audit.json').is_file() else {}\n"+needle)
needle="sha(S/'impl/gwsynthesis/acg720_ano_port.vg')=='001eca6c8a3e4f21e7d7fe84e33601bef9692d5fba739bff9fccb3b4c6ca639a'"
assert raw.count(needle)==1
raw=raw.replace(needle,"(S/'impl/gwsynthesis/acg720_ano_port.vg').is_file() and sha(S/'impl/gwsynthesis/acg720_ano_port.vg')==syn.get('netlist_sha256')")
needle="checks['netlist_only']='Skip synthesis, because there is only one netlist file' in log"
assert raw.count(needle)==1
raw=raw.replace(needle,"""project=S/'acg720_ano_port.gprj'
project_files=[f.attrib for f in ET.parse(project).findall('.//File')]
checks['native_RTL_project']=any(f.get('type')=='file.verilog' and f.get('enable')=='1' for f in project_files) and not any(f.get('type')=='file.netlist' for f in project_files)
checks['native_SYN_and_hook_eof']=all(marker in log for marker in ['GowinSynthesis finish','SYNTHESIS_COMMAND_RETURNED_EOF','SYNTHESIS_AUDIT_RETURNED_EOF']) and 'Skip synthesis, because there is only one netlist file' not in log
checks['native_SYN_source_binding']=bool(syn.get('passed') and syn.get('source55')==expected and syn.get('project_sha256')==sha(project))
files[str(project.relative_to(R))]=sha(project)
mapped_ok=True
for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
    path=V/name
    mapped_ok=mapped_ok and path.is_file() and read(path).get('passed') is True and sha(path)==syn.get(name.replace('.json','_sha256'))
    if path.is_file():files[str(path.relative_to(R))]=sha(path)
checks['native_mapped_audits']=bool(mapped_ok)
clock_audit=read(V/'strict_ff_clock_audit.json') if (V/'strict_ff_clock_audit.json').is_file() else {}
checks['all_mapped_FF_clk50']=clock_audit.get('all_FF_CLK50') is True and clock_audit.get('bad')==[]
if (V/'native_synthesis_audit.json').is_file():files[str((V/'native_synthesis_audit.json').relative_to(R))]=sha(V/'native_synthesis_audit.json')""")
ast.parse(raw);review=O/'independent_raw_review.py';assert not review.exists();review.write_text(raw,encoding='utf8')
adaptation={'scope':'Only flow-identity gates adapt from VG-import to actual native RTL SYN+hook+PNR. All genuine timing, endpoints, pin, UserCode, source and actual process acceptance gates remain.',
    'original_helper_sha256':sha(helper),'original_function_sha256':hashlib.sha256(original.encode()).hexdigest(),
    'new_physical_auditor_sha256':sha(target),'parent_independent_parser_sha256':sha(parent),'new_independent_parser_sha256':sha(review),
    'old_flow_identity':'skip_synthesis because one imported netlist file',
    'new_flow_identity':['unchanged original RTL project with no netlist FileList','actual SYN finish and SYN EOF','successful actual audit-hook exec EOF','source/project/VG/mapped audits binding'],
    'extra_gate':'Raw frequency constraint explicitly50MHz in addition to period20ns.'}
(O/'GATE_ADAPTATION.json').write_text(json.dumps(adaptation,indent=2)+'\n',encoding='utf8')
print('Prepared two native-flow auditors; original helper unchanged; no build/audit executed.')
