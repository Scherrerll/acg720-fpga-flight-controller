from pathlib import Path
import difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
BASE=R/'firmware/B0B4/source';ROOT=R/'out/z_aw_fix_20261026/compact_aw_v1';DEST=ROOT/'canonical/source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not ROOT.exists(),'Never overwrite an existing variant/evidence tree'
assert sha(BASE/'position/mtf_xyz_hold_control.v')=='5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c'
files=[p for p in sorted(BASE.rglob('*')) if p.is_file()]
assert len(files)==55
before={p.relative_to(BASE).as_posix():sha(p) for p in files}
for p in files:
    q=DEST/p.relative_to(BASE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
p=DEST/'position/mtf_xyz_hold_control.v';old=p.read_text();new=old
decl=' reg signed [32:0] candidate_iz_store=0,p_bias_store=0;\n reg signed [32:0] candidate_collective_store=0,current_collective_store=0;'
replacement=''' // Lifetime aliases: each value is written before its qualified use.
 // state22 consumes the old lower rail before reusing it for candidate I.
 wire signed [32:0] candidate_iz_store=iz_lower_q[32:0];
 wire signed [32:0] p_bias_store={{2{exz_store[30]}},exz_store};
 wire signed [32:0] candidate_collective_store=inner_alt_speed[32:0];
 wire signed [32:0] current_collective_store={{2{sample_vx_store[30]}},sample_vx_store};'''
assert new.count(decl)==1;new=new.replace(decl,replacement)
clear='candidate_iz_store<=0;p_bias_store<=0;candidate_collective_store<=0;current_collective_store<=0;'
assert new.count(clear)==2;new=new.replace(clear,'')
changes={
 'candidate_iz_store<=keep64(taking_off ?clip(iz+value,iz_lower_q,iz_upper_q):0);':'iz_lower_q<=keep64(taking_off ?clip(iz+value,iz_lower_q,iz_upper_q):0);',
 '24:begin p_bias_store<=keep64(value+bias);state<=66;end':'24:begin exz_store<=keep64(value+bias);state<=66;end',
 'candidate_collective_store<=keep64(p_bias+candidate_iz);':'inner_alt_speed<={{33{compact_candidate_sum31[30]}},compact_candidate_sum31};',
 'current_collective_store<=keep64(p_bias+iz);':'sample_vx_store<=keep64(p_bias+iz);',
}
for a,b in changes.items():assert new.count(a)==1;(new:=new.replace(a,b))
anchor=' wire signed [63:0] current_collective={{31{current_collective_store[32]}},current_collective_store};'
assert new.count(anchor)==1
new=new.replace(anchor,anchor+'''
 // Both sums fit signed31 Q16 by the source-level bound; keep the 64-bit
 // expression semantics, then explicitly retain/sign-extend those bits.
 wire signed [63:0] compact_candidate_sum=p_bias+candidate_iz;
 wire signed [30:0] compact_candidate_sum31=compact_candidate_sum[30:0];''')
p.write_text(new,encoding='utf8',newline='\n')
after={n:sha(DEST/n) for n in before}
assert [n for n in before if before[n]!=after[n]]==['position/mtf_xyz_hold_control.v']
O.mkdir(exist_ok=True)
(O/'candidate.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='B4-v1/position/mtf_xyz_hold_control.v',tofile='compact-aw-v1/position/mtf_xyz_hold_control.v')))
receipt={'scope':'Independent same-B4-algorithm storage-lifetime variant; only hold changes; original canonical and active attempts untouched.',
 'base_source':str(BASE),'variant_source':str(DEST),'base_source55':before,'variant_source55':after,
 'changed':['position/mtf_xyz_hold_control.v'],'prepare_script_sha256':sha(Path(__file__)),'diff_sha256':sha(O/'candidate.diff')}
(O/'source_freeze.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert before=={p.relative_to(BASE).as_posix():sha(p) for p in files}
print(json.dumps({'variant_source':str(DEST),'hold_sha256':after['position/mtf_xyz_hold_control.v'],'source_freeze_sha256':sha(O/'source_freeze.json'),'files':len(after)},indent=2))
