from pathlib import Path
import re,json,hashlib,collections,importlib.util
C=Path(__file__).resolve().parents[1];R=C.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
S=Path(json.loads((C/'synthesis_study.json').read_text())['folder']);V=S/'impl/gwsynthesis/acg720_ano_port.vg';O=R/'variants/p2_r2_rep1/fixture/impl/gwsynthesis/acg720_ano_port.vg';lib=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
new=json.loads((C/'hardware/mapped_720_candidate_bdd.json').read_text());old=json.loads((C/'hardware/mapped_720_reference_bdd.json').read_text())
assert len(new['mapping_msb_first'])==len(old['mapping_msb_first'])==720
for index,e in enumerate(new['mapping_msb_first']):
 bit=719-index
 if isinstance(e,list):assert 112<=bit<=143 and len(e)==3 and e[0]=='q085' and e[1]==0 and re.fullmatch(r'q\d{3}',e[2])
 else:assert e in [0,1] or isinstance(e,str) and re.fullmatch(r'q\d{3}',e) and 0<=int(e[1:])<720
assert new['netlist_sha256']==sha(V) and old['netlist_sha256']==sha(O)
parts=[(8,5),(8,128),(8,1),(8,0),(64,0),(32,0),(32,0xffffffff),(32,0),(32,0x001d0080)]+[(32,0)]*11+[(16,0)]*3+[(16,0x40),(8,0),(8,0),(16,0),(16,1),(32,0)]
assert sum(w for w,x in parts)==720
expected=0
for w,x in parts:expected=(expected<<w)|x
expected=f'{expected:0180x}';assert old['init_hex']==new['init_hex']==expected
# Exact Boolean mappings differ only by a proved bank-register merge.
def alias(x):
 if isinstance(x,list):return list(map(alias,x))
 return 'q111' if x in ['q106','q107','q108','q109','q110']else 'q504' if x=='q505' else x
assert list(map(alias,old['mapping_msb_first']))==new['mapping_msb_first']
assert new['capture_condition']==old['capture_with_boot'],'Mapped CE must be exact startup release AND original snapshot-not-held condition'
nav=lambda p:re.search(r'module mtf_xyz_navigation_control \(.*?endmodule',p.read_text(),re.S).group()
a=nav(O);b=nav(V)
def cells(s):
 out={}
 for m in re.finditer(r'(?m)^  (DFF\w+) (diagnostic_q_(\d+)_\w+)\s*\((.*?)\);\s*defparam.*?INIT=(.*?);',s,re.S):
  typ,name,n,body,init=m.groups();pins={x:re.sub(r'\s+','',y)for x,y in re.findall(r'\.([^\s(]+)\((.*?)\)',body,re.S)};out[int(n)]=dict(type=typ,name=name,pins=pins,init=int(init[-1]))
 return out
A=cells(a);B=cells(b);assert len(A)==588 and len(B)==583 and set(A)-set(B)==set(range(106,111))|{505} and set(B)-set(A)=={504}
for n,c in B.items():assert c['init']==A[505 if n==504 else n]['init']==((int(expected,16)>>n)&1)
assert A[505]['pins']['D']==B[504]['pins']['D']=='VCC' and A[505]['init']==B[504]['init']==0
assert sum(c['init']for c in A.values())==sum(c['init']for c in B.values())==38
for n in range(106,112):
 assert re.search(r'LUT2 nav_z_throttle_'+str(n-96)+r'_s\s*\(\s*\.F\(nav_z_throttle\['+str(n-96)+r'\]\),\s*\.I0\(controller_delta\[15\]\),\s*\.I1\(nav_z_active\)\s*\);\s*defparam[^;]+INIT=4\x27h8;',a)
 assert A[n]['init']==0 and A[n]['pins']['RESET']=='n13_16'
 assert A[n]['pins']['CE']==A[111]['pins']['CE']
# All candidate bank clocks and enables must be identical.
assert {c['pins']['CLK']for c in B.values()}=={'clk50_d'}
assert {c['pins']['CE']for c in B.values()}=={'diagnostic_q_32_20'}
required=[('diagnostic_q_32_s13','diagnostic_q_32_20',['n13_13','n13_14',r'\staged_telemetry.core_q_453_16'],0x80,3),('position_x_q8_31_s2','position_x_q8_31_6',['have_epoch','live_velocity','position_ready_5','diagnostic_q_32_20'],0x7f00,4),('z_throttle_delta_15_s2','z_throttle_delta_15_5',['nav_z_active','n13_13','n13_14',r'\staged_telemetry.core_q_453_16'],0x4000,4),('xy_reason_11_s2','xy_reason_11_5',['observer_reset','n13_13','n13_14',r'\staged_telemetry.core_q_453_16'],0x8000,4)]
for inst,out,ins,init,width in required:
 m=re.search(r'LUT'+str(width)+' '+inst+r'\s*\((.*?)\);\s*defparam[^;]+INIT=\d+\x27h([0-9A-F]+);',b,re.S);assert m,inst
 pins={x:re.sub(r'\s+','',y)for x,y in re.findall(r'\.([^\s(]+)\((.*?)\)',m[1],re.S)}
 assert pins==dict(F=out,**{'I'+str(i):v for i,v in enumerate(ins)})and int(m[2],16)==init
# Gated data-zero RESET truth tables never change bank state when capture CE=0.
for value in range(16):
 i=[(value>>k)&1 for k in range(4)]
 assert ((0x7f00>>value)&1)==(i[3]and not(i[0]and i[1]and i[2]))
 assert ((0x4000>>value)&1)==((not i[0])and i[1]and i[2]and i[3])
 assert ((0x8000>>value)&1)==(i[0]and i[1]and i[2]and i[3])
controls=collections.defaultdict(list)
for n,c in B.items():controls[c['pins'].get('RESET',c['pins'].get('SET'))].append(n)
assert set(controls)=={'GND','xy_reason_11_5','position_x_q8_31_6','z_throttle_delta_15_5'}
assert set(controls['xy_reason_11_5'])=={33,35,38,39,40,41,517,518,522,523,524,525} # excludes source reason bit10=1 on origin.
assert all(144<=n<=207 for n in controls['position_x_q8_31_6'])
assert all(n in set(range(32))|set(range(48,64))|set(range(96,112))for n in controls['z_throttle_delta_15_5'])
for n,c in B.items():
 if c['init']:assert c['type']=='DFFSE' and c['pins']['SET']=='GND'
# Independent actual vendor-primitive simulation must agree with BDDs for all720bits in all14 phases.
log=(C/'hardware/mapped_probe/sim.log').read_text();assert '$finish called' in log
banks={}
for phase,bank,h in re.findall(r'BANK (\d+) (\d+) ([0-9a-f]{16})',log):banks.setdefault(int(phase),{})[int(bank)]=h
assert set(banks)==set(range(14))
def value(e,phase):
 if isinstance(e,int):return e
 if isinstance(e,list):return value(e[2]if value(e[0],phase)else e[1],phase)
 assert re.fullmatch(r'q\d{3}',e),e
 bit=int(e[1:])
 if bit==85:return 0 if phase==13 else 1
 return 1 if phase in [2,13]else ((bit+1)>>(phase-3))&1 if 3<=phase<=12 else 0
for phase,data in banks.items():
 assert set(data)==set(range(12));actual=''.join(data[i]for i in range(12))[8:188]
 predicted=expected if phase==0 else f'{int("".join(str(value(e,phase))for e in new["mapping_msb_first"]),2):0180x}'
 assert actual==predicted,(phase,actual,predicted)
# Bind exact final builder/source contract and primitive semantics; full-build gate compares entire mapped token stream.
spec=importlib.util.spec_from_file_location('bind',C/'verify_mapped_binding.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
spec=importlib.util.spec_from_file_location('build',C/'fixture/build_project.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
paths=[V,O,lib,C/'hardware/mapped_structure.py',Path(__file__),C/'verify_mapped_binding.py',C/'fixture/build_project.py',C/'source_contract.json',C/'hardware/mapped_720_candidate_bdd.json',C/'hardware/mapped_720_reference_bdd.json',C/'hardware/mapped_probe.py',C/'hardware/review_synthesis_freshness.py',C/'hardware/synthesis_freshness_review.json']+list((C/'hardware/mapped_probe').glob('*'))
report=dict(passed=True,sources_sha256=build.source_hashes(),netlist=str(V),netlist_sha256=sha(V),canonical_netlist_sha256=mod.canonical(V),evidence_sha256={str(p):sha(p)for p in paths if p.is_file()},expected_reset_hex=expected,logical_bits_verified=720,original_bank_ff=588,candidate_bank_ff=583,former_set_bits_verified=38,old_ones_all_preserved=True,merged_bits=list(range(106,111)),merged_to=111,renamed_alias_representative={'old_q505':'new_q504','logical_bits':[504,505],'D':'VCC','INIT':0},control_groups={k:sorted(v)for k,v in controls.items()},ce='boot==255 && !diagnostic_hold',data_resets='CE && !position_ready; CE && !z_active; CE && origin_reset on zero reason bits only',boolean_mapping='Exact reduced BDD of all720 serializer payload bits: only constants, retained bank Qs, and unchanged q85 AND target masks; reference comparison exact after proved five-register merge and representative rename q505->q504.',primitive_simulation='Actual complete mapped netlist with vendor GW5A library, no clocks; NAV/index probes reconstruct every720bit startup and13 label/mask patterns. Payload Q forced only after initial unforced startup phase.',limitations=['This is not whole-design sequential netlist equivalence. Nonbank mapped cells were reoptimized. Source-bound changes comprise the startup-only diagnostic option and the separately reviewed two-file published-anchor repair; focused current-source RTL proofs and the independent control review cover that repair.','Final full-build mapped logic must match this complete canonical token stream or release verification fails and mapped audit must be rerun.'],programming_authorized=False,pnr_run=False)
(C/'hardware/mapped_init_review.json').write_text(json.dumps(report,indent=2)+'\n');print('Mapped INIT/720-bit Boolean/primitive simulation audit PASS')
