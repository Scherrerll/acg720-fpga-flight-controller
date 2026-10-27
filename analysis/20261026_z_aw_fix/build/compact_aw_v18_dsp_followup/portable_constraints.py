"""Strict read-only official DSP/BSRAM constraint binding; no vendor execution."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v18'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v18';CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01'
E=O.parent/'native_v4_DSP_export';OFFICIAL=E/'vendor_dsp_bsram.cst';VALIDATION=E/'EXPORT_VALIDATION.json';PORTABLE=E/'portable_v18_dsp_bsram.cst'
GRAPH=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
TARGET=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg'
DONOR_V4=R/'out/z_aw_fix_20261026/native_v4_DSP_export_snapshot/source/impl/gwsynthesis/acg720_ano_port.vg'
VG_SHA='64e76270fe35298e698bfe5b14b9d9e267469f746d3c2382a8a15284c5942d4f'
HELPER=R/'firmware/B0B4/build_candidate.py';HELPER_SHA='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))

def semantic(name):
    return '/'.join(part[1:] if part.startswith('\\') else part for part in name.split('/'))

def rows(path):
    out=[];seen=set();pattern=r'INS_LOC "([^"\r\n]+)" ((?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?(?:,(?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?)*);'
    for n,line in enumerate(path.read_text(encoding='utf8').splitlines(),1):
        s=line.strip()
        if not s or s.startswith('//'):continue
        m=re.fullmatch(pattern,s);assert m,(path,n,'unexpected directive or syntax',s)
        name,locations=m.groups();assert name==semantic(name) and name not in seen,(path,n,'duplicate/nonsemantic instance',name)
        seen.add(name);locs=locations.split(',');assert len(locs)==len(set(locs))
        kinds={loc.split('_R')[0] for loc in locs};assert len(kinds)==1
        out.append({'instance':name,'locations':locs,'line':s,'resource_kind':next(iter(kinds))})
    return out

def semantic_cells(graph):
    out={}
    for name,cell in graph.cells.items():
        normalized=semantic(name)
        assert normalized not in out,('normalization collision',normalized,out.get(normalized),name)
        out[normalized]={'raw':name,'type':cell['type']}
    return out

def combined_bytes():
    original=(CANON/'acg720_ano_port.cst').read_bytes()
    assert original.endswith(b'\n'),'Original IO CST must already terminate with newline; never alter prefix'
    return original+PORTABLE.read_bytes()

def validate(check_binding=True):
    freeze=read(P/'source_freeze.json');expected=freeze['source55']
    assert len(expected)==55 and {n:sha(CANON/n) for n in expected}==expected
    assert {n:sha(DONOR/'source'/n) for n in expected}==expected
    if (O/'source_freeze.json').exists():assert (O/'source_freeze.json').read_bytes()==(P/'source_freeze.json').read_bytes()
    proof=read(P/'PROOF_BINDING.json');vy=read(P/'VY_BINDING.json');syn=read(P/'SYNTHESIS_RESULT.json')
    assert proof['passed'] and proof['source55']==expected and proof['actual_proof_runner_wait']==0
    assert vy['passed'] and vy['source55']==expected and vy['actual_successful_root_wait']==0
    assert proof['vy_binding_sha256']==sha(P/'VY_BINDING.json')
    assert syn['passed_SYN_only'] and syn['source55']==expected
    assert syn['vendor_actual_wait']==syn['runner_actual_wait']==syn['audit_actual_wait']==0
    assert sha(TARGET)==syn['netlist_sha256']==VG_SHA and sha(HELPER)==HELPER_SHA
    ev=read(VALIDATION);target=ev['portable']['v18']
    assert sha(OFFICIAL)==ev['export_sha256'] and sha(DONOR_V4)==ev['donor_VG_sha256']
    assert sha(GRAPH)==ev['graph_reader_sha256'] and sha(PORTABLE)==target['constraint_sha256']
    assert target['VG_sha256']==VG_SHA and ev['exported_rows']==52 and target['kept']==46
    assert len(target['dropped'])==6 and target['DSP']==44 and target['BSRAM']==2
    official=rows(OFFICIAL);portable=rows(PORTABLE);assert len(official)==52 and len(portable)==46
    assert [r['line'] for r in official]==[r['line'] for r in ev['rows']]
    spec=importlib.util.spec_from_file_location('official_fixed_graph_reader',GRAPH);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    donor=semantic_cells(module.Graph(DONOR_V4));current=semantic_cells(module.Graph(TARGET))
    kept=[];dropped=[]
    for row,documented in zip(official,ev['rows']):
        name=row['instance'];d=donor.get(name);assert d and d['type']==documented['donor_primitive']
        kind='BSRAM' if d['type'] in ['pROM','SP','DP','SDP','ROM'] else 'DSP' if d['type'] in ['MULT12X12','MULT27X36','MULTALU27X18'] else None
        assert kind==row['resource_kind']==documented['resource_kind'],('resource/primitive type mismatch',name)
        c=current.get(name)
        if c and c['type']==d['type']:
            kept.append({**row,'donor_graph_identifier':d['raw'],'target_graph_identifier':c['raw'],'primitive':c['type']})
        else:dropped.append(name)
    assert [x['line'] for x in kept]==[x['line'] for x in portable]==[x['line'] for x in target['kept_rows']]
    assert dropped==[x['instance'] for x in target['dropped']]
    assert sum(x['resource_kind']=='DSP' for x in kept)==44 and sum(x['resource_kind']=='BSRAM' for x in kept)==2
    original=(CANON/'acg720_ano_port.cst').read_bytes();combined=combined_bytes()
    assert combined[:len(original)]==original and combined[len(original):]==PORTABLE.read_bytes()
    baseline_clocks=[]
    for line in original.decode('utf8').splitlines():
        s=line.strip()
        if s=='CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;':baseline_clocks.append(s);continue
        assert not s or s.startswith('//') or re.fullmatch(r'IO_(?:LOC|PORT)\s+"[^"\r\n]+"\s+[^;\r\n]+;',s),('frozen baseline CST has unexpected directive',s)
    assert baseline_clocks==['CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;']
    result={'passed':True,'source55':expected,'VG_sha256':VG_SHA,'official_rows':52,'kept':46,'DSP':44,'BSRAM':2,'dropped':dropped,'rows':kept,
        'original_IO_CST_sha256':sha(CANON/'acg720_ano_port.cst'),'portable_CST_sha256':sha(PORTABLE),'combined_CST_sha256':hashlib.sha256(combined).hexdigest(),
        'combined_CST_bytes':len(combined),'original_IO_prefix_bytes':len(original),'original_CLOCK_LOC_statements_preserved':baseline_clocks,'normalization':'Strip exactly one leading Verilog lexical escape per hierarchy segment; reject collisions; no generated-number renames'}
    if check_binding:
        binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json');assert binding['validation']==result
        assert binding['checker_sha256']==sha(Path(__file__))
        for p,h in binding['bound_inputs'].items():assert sha(Path(p))==h,p
        preparation=read(O/'PHYSICAL_PREPARATION.json')
        assert preparation['portable_constraint_binding_sha256']==sha(O/'PORTABLE_CONSTRAINT_BINDING.json')
        for name,h in preparation['new_scripts_sha256'].items():assert sha(O/name)==h,name
    return result

def verify_attempt(source):
    result=validate();expected=result['source55']
    assert {n:sha(source/n) for n in expected}==expected
    assert (source/'physical_constraints.cst').read_bytes()==combined_bytes()
    assert (source/'acg720_ano_port.cst').read_bytes()==(CANON/'acg720_ano_port.cst').read_bytes()
    entries=[(f.attrib['path'],f.attrib['type'],f.attrib.get('enable')) for f in ET.parse(source/'physical.gprj').findall('.//File')]
    assert entries==[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist','1'),('physical_constraints.cst','file.cst','1'),('acg720_ano_port.sdc','file.sdc','1')]
    return result
