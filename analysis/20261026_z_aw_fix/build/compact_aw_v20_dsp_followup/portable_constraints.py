"""Thin physical-only v20 official resource placement filter; standard proof origin only."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v20'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v20';CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01'
E=O.parent/'native_v4_DSP_export';OFFICIAL=E/'vendor_dsp_bsram.cst';OLD_VALIDATION=E/'EXPORT_VALIDATION.json'
DONOR_V4=R/'out/z_aw_fix_20261026/native_v4_DSP_export_snapshot/source/impl/gwsynthesis/acg720_ano_port.vg'
TARGET=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg';GRAPH=R.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
PORTABLE=O/'portable_v20_dsp_bsram.cst';PROFILE='physical_p3r0_dsploc_01'
HEADER=b'// Official v4 complete-route but timing-failed DSP/BSRAM positions; exact semantic-name/type subset of sealed standard v20. Physical-only, unqualified.\n'
def safe(path):
    p=Path(path)
    for part in p.parts:
        n=part.lower().rstrip(' .');assert not n.startswith('.env') and not n.endswith('.env') and '.env' not in [s.lower() for s in Path(n).suffixes],str(p)
    for ancestor in [p,*p.parents]:assert not ancestor.is_symlink() and not (hasattr(ancestor,'is_junction') and ancestor.is_junction()),str(p)
    return p
def sha(p):return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def read(p):return json.loads(safe(p).read_text(encoding='utf8'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def semantic(name):return '/'.join(s[1:] if s.startswith('\\') else s for s in name.split('/'))
def rows(path):
    out=[];seen=set()
    pattern=r'INS_LOC "([^"\r\n]+)" ((?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?(?:,(?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?)*);'
    for line_number,raw in enumerate(safe(path).read_bytes().splitlines(),1):
        text=raw.decode('utf8');s=text.strip()
        if not s or s.startswith('//'):continue
        m=re.fullmatch(pattern,s);assert m,(str(path),line_number,'Unexpected appended/export directive or syntax',s)
        name,locations=m.groups();assert name==semantic(name) and name not in seen,(name,'duplicate or nonsemantic instance')
        seen.add(name);locs=locations.split(',');assert len(locs)==len(set(locs))
        kinds={x.split('_R')[0] for x in locs};assert len(kinds)==1
        out.append({'instance':name,'locations':locs,'resource_kind':next(iter(kinds)),'statement':s,'original_line':text,'original_line_sha256':hashlib.sha256(raw).hexdigest(),'line_number':line_number})
    return out
def semantic_cells(g):
    out={}
    for name,cell in g.cells.items():
        s=semantic(name);assert s not in out,('Verilog lexical normalization collision',s)
        out[s]={'raw':name,'type':cell['type']}
    return out
def portable_bytes(report):return HEADER+b'\n'.join(x['original_line'].encode('utf8') for x in report['kept_rows'])+b'\n'
def combined_bytes():
    prefix=(CANON/'acg720_ano_port.cst').read_bytes();assert prefix.endswith(b'\n')
    return prefix+PORTABLE.read_bytes()

def measure():
    # This is the existing standard-v20 contract, not a new thin-family proof.
    base=load('standard_v20_sealed_physical_contract',STANDARD/'physical_input_contract.py').validate20(require_preparation=True)
    assert base['passed'] and base['B3_relative_change_count']==12 and sha(TARGET)==base['VG_sha256']
    old=read(OLD_VALIDATION);assert old['exported_rows']==52 and sha(OFFICIAL)==old['export_sha256'] and sha(DONOR_V4)==old['donor_VG_sha256']
    assert sha(GRAPH)==old['graph_reader_sha256']=='a7d8faf9b8bd5c51b7bacf1ce54906c102df745b0d1c9913c2431ced9f5d09cc'
    exported=rows(OFFICIAL);assert len(exported)==52 and [x['statement'] for x in exported]==[x['line'] for x in old['rows']]
    graph=load('unchanged_official_portability_graph',GRAPH)
    donor=semantic_cells(graph.Graph(DONOR_V4));target=semantic_cells(graph.Graph(TARGET));kept=[];dropped=[]
    for row,e in zip(exported,old['rows']):
        name=row['instance'];d=donor.get(name);assert d and d['type']==e['donor_primitive']
        kind='BSRAM' if d['type'] in ['pROM','SP','DP','SDP','ROM'] else 'DSP' if d['type'] in ['MULT12X12','MULT27X36','MULTALU27X18'] else None
        assert kind==row['resource_kind']==e['resource_kind'],('Donor resource type mismatch',name)
        t=target.get(name)
        if t and t['type']==d['type']:kept.append({**row,'donor_graph_identifier':d['raw'],'target_graph_identifier':t['raw'],'primitive':d['type']})
        else:dropped.append({**row,'donor_primitive':d['type'],'target_primitive':t['type'] if t else None,'reason':'Absent exact semantic name or changed exact primitive type; no inferred generated-number rename'})
    assert kept and len(kept)+len(dropped)==52
    prefix=(CANON/'acg720_ano_port.cst').read_bytes();assert sha(CANON/'acg720_ano_port.cst')==base['source55']['acg720_ano_port.cst'] and prefix.endswith(b'\n')
    clocks=[x.strip() for x in prefix.decode('utf8').splitlines() if x.strip().startswith('CLOCK_LOC')]
    assert clocks==['CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;']
    report={'passed':True,'official_export_rows':52,'kept':len(kept),'excluded':len(dropped),'DSP':sum(x['resource_kind']=='DSP' for x in kept),'BSRAM':sum(x['resource_kind']=='BSRAM' for x in kept),
        'VG_sha256':base['VG_sha256'],'donor_V4_VG_sha256':sha(DONOR_V4),'official_export_sha256':sha(OFFICIAL),'original_validation_sha256':sha(OLD_VALIDATION),'graph_reader_sha256':sha(GRAPH),
        'kept_rows':kept,'dropped_rows':dropped,'original_baseline_CST_sha256':sha(CANON/'acg720_ano_port.cst'),'original_baseline_prefix_bytes':len(prefix),'original_CLOCK_LOC_preserved':clocks,
        'normalization':'Strip exactly one leading Verilog lexical escape from each hierarchy segment; reject collisions; no numerical generated-instance rename or manufacturer statement rewrite',
        'source_proof_origin':'Exact existing standard compact_aw_v20 source55, dual-guard/component proof/retry/top13 and actual sealed SYN contract. Thin family adds no source or functional proof.'}
    suffix=portable_bytes(report);report['portable_CST_sha256']=hashlib.sha256(suffix).hexdigest();report['combined_CST_sha256']=hashlib.sha256(prefix+suffix).hexdigest();report['combined_CST_bytes']=len(prefix+suffix)
    return report,base

def validate(check_preparation=True):
    report,base=measure()
    assert (O/'source_freeze.json').read_bytes()==(STANDARD/'source_freeze.json').read_bytes()
    assert PORTABLE.read_bytes()==portable_bytes(report)
    portable=rows(PORTABLE);assert [x['original_line'] for x in portable]==[x['original_line'] for x in report['kept_rows']]
    frozen=read(O/'PORTABLE_FILTER_VALIDATION.json');assert frozen['report']==report
    binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json');assert binding['filter_validation_sha256']==sha(O/'PORTABLE_FILTER_VALIDATION.json') and binding['checker_sha256']==sha(Path(__file__))
    assert binding['standard_source_proof_origin']==str(STANDARD) and binding['source55']==base['source55']
    for p,h in binding['bound_inputs'].items():assert sha(Path(p))==h,p
    assert hashlib.sha256(combined_bytes()).hexdigest()==report['combined_CST_sha256']
    if check_preparation:
        prep=read(O/'PHYSICAL_PREPARATION.json');assert prep['portable_constraint_binding_sha256']==sha(O/'PORTABLE_CONSTRAINT_BINDING.json') and prep['VG_sha256']==base['VG_sha256']
        for n,h in prep['new_scripts_sha256'].items():assert sha(O/n)==h,n
    return {'passed':True,'filter':report,'standard_contract':base}

def verify_attempt(source):
    check=validate();expected=check['standard_contract']['source55']
    assert {n:sha(source/n) for n in expected}==expected
    assert (source/'acg720_ano_port.cst').read_bytes()==(CANON/'acg720_ano_port.cst').read_bytes()
    assert (source/'physical_constraints.cst').read_bytes()==combined_bytes()
    entries=[(f.attrib['path'],f.attrib['type'],f.attrib.get('enable')) for f in ET.parse(source/'physical.gprj').findall('.//File')]
    assert entries==[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist','1'),('physical_constraints.cst','file.cst','1'),('acg720_ano_port.sdc','file.sdc','1')]
    return check
