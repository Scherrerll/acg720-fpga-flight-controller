"""Derive unchanged original physical gates for an actual successfully sealed v14 VG."""
from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent;M=O/'compact_aw_v14';P=O/'compact_aw_v4_p1_followup';R=O.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sx=read(M/'SYNTHESIS_RESULT.json');assert sx['passed_SYN_only'] and sx['vendor_actual_wait']==sx['runner_actual_wait']==sx['audit_actual_wait']==0
vg=sx['netlist_sha256'];assert not (M/'PHYSICAL_PREPARATION.json').exists()
names=['run_physical.py','seal_terminal.py','independent_raw_review.py']
for name in names:
    t=(P/name).read_text(encoding='utf8').replace("compact_aw_v4'","compact_aw_v14'")
    t=t.replace('e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f',vg)
    if name=='run_physical.py':
        assert t.count('import sys\n')==1
        t=t.replace('import sys\n',"import sys\nassert len(sys.argv)==2 and sys.argv[1] in ['2','3'];PLACE=int(sys.argv[1])\n")
        t=t.replace("ATTEMPT=ROOT/'physical_p1r0_01'","ATTEMPT=ROOT/f'physical_p{PLACE}r0_01'")
        t=t.replace("PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v3/canonical/source'","PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'")
        t=t.replace("prior=din['baseline_v3_map2_source55']","prior=freeze['baseline_source55']")
        t=t.replace("din['synthesis_options']=={'map_option':2,'replicate_resources':0}","din['synthesis_options']=={'map_option':2,'replicate_resources':0,'max_fanout':200,'opt_goal':'area'}")
        t=t.replace("'set_option -place_option 1' if line=='set_option -place_option 3'","f'set_option -place_option {PLACE}' if line=='set_option -place_option 3'")
        t=t.replace("('place_option','1')","('place_option',str(PLACE))").replace("'place':1","'place':PLACE")
        t=t.replace('v3_source55','v4_source55').replace('P1/R0 routability-priority','v14 P2-or-P3/R0 original full physical gates')
        t=t.replace('Root-authorized fresh v4 map2','Root-authorized fresh v14 map2')
        assert "prior=freeze['baseline_source55']" in t and "ATTEMPT=ROOT/f'physical_p{PLACE}r0_01'" in t
    else:
        if name=='seal_terminal.py':
            old="assert len(sys.argv)==1;label='physical_p1r0_01'";assert t.count(old)==1
            t=t.replace(old,"assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];label=f'physical_p{sys.argv[1]}r0_01'")
        else:
            t=t.replace('compact_aw_v4/canonical/source','compact_aw_v14/canonical/source')
            old="assert len(sys.argv)==1";assert t.count(old)==1;t=t.replace(old,"assert len(sys.argv)==2 and sys.argv[1] in ['2','3']")
            old="label='physical_p1r0_01'";assert t.count(old)==1;t=t.replace(old,"label=f'physical_p{sys.argv[1]}r0_01'")
    ast.parse(t);assert not (M/name).exists();(M/name).write_text(t,encoding='utf8')
for name in ['launch_physical_hidden.py','physical_snapshot.py']:
    t=(O/'compact_aw_v13'/name).read_text(encoding='utf8').replace('compact_aw_v13','compact_aw_v14')
    ast.parse(t);assert not (M/name).exists();(M/name).write_text(t,encoding='utf8');names.append(name) if name not in names else None
for place in [2,3]:
    d=M/f'physical_p{place}r0_01';assert not d.exists();d.mkdir()
(M/'PHYSICAL_PREPARATION.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact newly audited v14 SYN VG, original source55/CST/SDC and unchanged original physical gate. No seed or external LOC/clock/falsepath changes.',
    'source55':sx['source55'],'VG_sha256':vg,'synthesis_result_sha256':sha(M/'SYNTHESIS_RESULT.json'),
    'scripts_sha256':{n:sha(M/n) for n in names},'PNR_started':False},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_only':True,'VG':vg,'PNR_started':False,'physical_profiles':[2,3]}))
