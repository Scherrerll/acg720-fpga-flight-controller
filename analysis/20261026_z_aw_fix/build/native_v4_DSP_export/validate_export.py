"""Validate official backannotation and filter actual target primitive identities only."""
from pathlib import Path
import hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent;R=O.parents[3];p=O/'vendor_dsp_bsram.cst'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reader=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
assert sha(reader)=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
spec=importlib.util.spec_from_file_location('official_cst_primitive_portability',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def names(graph):
    result={}
    for name,cell in graph.cells.items():
        # The escape prefix is Verilog lexical syntax, not part of its identifier.
        normalized='/'.join(part[1:] if part.startswith(chr(92)) else part for part in name.split('/'))
        assert normalized not in result,('Ambiguous semantic primitive name',normalized)
        result[normalized]=(name,cell['type'])
    return result
rows=[]
for line in p.read_text(encoding='utf8').splitlines():
    line=line.strip()
    if not line or line.startswith('//'):continue
    match=re.fullmatch(r'INS_LOC "([^"]+)"\s+([^;]+);',line);assert match,line
    name,locations=match.groups();slots=locations.split(',')
    assert all(re.fullmatch(r'DSP_R\d+\[\d+\]\[[AB]\]|BSRAM_R\d+\[\d+\](?:\[[AB]\])?',slot) for slot in slots),slots
    rows.append(dict(instance=name,locations=slots,line=line))
assert len({x['instance'] for x in rows})==len(rows)
donor=R/'out/z_aw_fix_20261026/native_v4_DSP_export_snapshot/source/impl/gwsynthesis/acg720_ano_port.vg';old=names(module.Graph(donor))
for row in rows:
    assert row['instance'] in old,row
    row['donor_graph_identifier'],row['donor_primitive']=old[row['instance']]
    assert row['donor_primitive'].startswith(('MULT','pROM'))
    row['resource_kind']='BSRAM' if row['locations'][0].startswith('BSRAM') else 'DSP'
portable={}
for label in ['v17','v18']:
    vg=R/('out/z_aw_fix_20261026/compact_aw_'+label+'/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg');current=names(module.Graph(vg));kept=[];dropped=[]
    for row in rows:
        actual=current.get(row['instance'])
        if actual and actual[1]==row['donor_primitive']:kept.append(dict(**row,target_graph_identifier=actual[0]))
        else:dropped.append(dict(**row,target_primitive=actual[1] if actual else None,reason='Absent or changed primitive type; no inferred rename'))
    dest=O/('portable_'+label+'_dsp_bsram.cst');assert not dest.exists()
    dest.write_text('// Official v4 complete-route (timing-failed) DSP/BSRAM positions, exact semantic-name/type filter. Unqualified physical-only option.\n'+'\n'.join(x['line'] for x in kept)+'\n',encoding='utf8')
    portable[label]=dict(VG_sha256=sha(vg),kept=len(kept),dropped=dropped,kept_rows=kept,constraint_path=dest.relative_to(R).as_posix(),constraint_sha256=sha(dest),BSRAM=sum(x['resource_kind']=='BSRAM' for x in kept),DSP=sum(x['resource_kind']=='DSP' for x in kept))
result=dict(scope='Official GUI backannotation from exact copied native fullroute but timing-failed v4. Only INS_LOC DSP/BSRAM rows, no ports/clocks/timing exceptions. Name/type filter is not device-legality/routability/STA acceptance.',export_sha256=sha(p),donor_VG_sha256=sha(donor),graph_reader_sha256=sha(reader),escaped_identifier_normalization='Remove one leading Verilog lexical escape prefix per hierarchy segment; require no semantic name collisions. Never change CST lines or infer numerical instance renames.',exported_rows=len(rows),rows=rows,portable=portable)
dest=O/'EXPORT_VALIDATION.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(exported=len(rows),portable={k:{a:v[a] for a in ['kept','BSRAM','DSP']} for k,v in portable.items()}),indent=2))
