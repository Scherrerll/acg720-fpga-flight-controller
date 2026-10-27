"""Independently parse only VG module/instance declarations and official52 rows."""
from pathlib import Path
import collections,hashlib,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2]
E=R/'analysis/20261026_z_aw_fix/build/native_v4_DSP_export'
donor=R/'out/z_aw_fix_20261026/native_v4_DSP_export_snapshot/source/impl/gwsynthesis/acg720_ano_port.vg'
target=R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'
official=E/'vendor_dsp_bsram.cst';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((E/'EXPORT_VALIDATION.json').read_text())
assert sha(official)==old['export_sha256']=='a9d20d20d9495e6d351003e2b7f214c5673ce4dea55791b6d2270743b5ec8258'
assert sha(donor)==old['donor_VG_sha256']=='f91ca98e3252020035fa9e012b2c6ad95649bc0fec8cf0f551ed4ef001601727'
assert sha(target)=='e84a81f4a5abb4c15c9e599cc4c2d2e77397a328c9372d0a94c8949fbbf7f4f8'
def semantic(s):return '/'.join(p[1:] if p.startswith('\\') else p for p in s.split('/'))
def instances(path):
    modules={}
    for m in re.finditer(r'^module\s+(\S+)\s*\(.*?\)\s*;(.*?)^endmodule',path.read_text(),re.S|re.M):
        name,body=m.groups();assert name not in modules
        modules[name]=[(x[0],x[1]) for x in re.findall(r'^[ \t]+(\S+)[ \t]+(\S+)[ \t]*\(.*?\)[ \t]*;',body,re.S|re.M)]
    leaves={};raw={}
    def walk(typ,prefix,ancestors):
        assert typ not in ancestors
        for child,name in modules[typ]:
            full=prefix+name
            if child in modules:walk(child,full+'/',ancestors|{typ})
            else:
                normalized=semantic(full);assert normalized not in leaves,(path,normalized)
                leaves[normalized]=child;raw[normalized]=full
    walk('acg720_ano_port','',set())
    return leaves,raw,len(modules)
d,dr,dm=instances(donor);t,tr,tm=instances(target)
rows=[];names=set()
for number,raw in enumerate(official.read_bytes().splitlines(),1):
    line=raw.decode();s=line.strip()
    if not s or s.startswith('//'):continue
    m=re.fullmatch(r'INS_LOC "([^"\r\n]+)" ((?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?(?:,(?:DSP|BSRAM)_R\d+\[\d+\](?:\[[AB]\])?)*);',s);assert m
    name,locations=m.groups();assert name==semantic(name) and name not in names;names.add(name)
    kind=locations.split('_R')[0];assert all(x.startswith(kind+'_R') for x in locations.split(','))
    primitive=d[name];assert (kind=='DSP' and primitive in ['MULT12X12','MULT27X36','MULTALU27X18']) or (kind=='BSRAM' and primitive in ['pROM','SP','DP','SDP','ROM'])
    rows.append({'instance':name,'primitive':primitive,'target_primitive':t.get(name),'resource_kind':kind,'kept':t.get(name)==primitive,'original_line':line,'line_number':number,'locations':locations.split(','),'donor_raw':dr[name],'target_raw':tr.get(name)})
assert len(rows)==52 and [x['original_line'].strip() for x in rows]==[x['line'] for x in old['rows']]
assert [x['primitive'] for x in rows]==[x['donor_primitive'] for x in old['rows']]
kept=[x for x in rows if x['kept']];dropped=[x for x in rows if not x['kept']]
assert len(kept)==33 and len(dropped)==19
assert collections.Counter(x['resource_kind'] for x in kept)=={'DSP':31,'BSRAM':2}
out={'passed':True,'independent_parser':'Only module/instance declaration hierarchy, not shared Graph or candidate portable_constraints parser; exact primitive type and literal semantic-name match; no renumbering.','official_sha256':sha(official),'donor_sha256':sha(donor),'target_sha256':sha(target),'module_counts':{'donor':dm,'target':tm},'leaf_counts':{'donor':len(d),'target':len(t)},'official52':52,'kept':33,'dropped':19,'DSP':31,'BSRAM':2,'rows':rows,'script_sha256':sha(Path(__file__))}
dest=O/'REFERENCE_MAPPING.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
