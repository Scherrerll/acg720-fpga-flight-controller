from pathlib import Path
import hashlib,json,random
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((R/'reference/storage_parent.json').read_text())
old=R/'reference/storage_before_hold.v';new=R/'reference/operand_before_hold.v'
assert sha(old)==meta['source_sha256']
s=old.read_text()
changes={
 'reg signed [49-1:0] target_z_q16_store=0;':'reg signed [31-1:0] target_z_q16_store=0;',
 'reg signed [48-1:0] height_feedback_old_store=0;':'reg signed [30-1:0] height_feedback_old_store=0;',
 '{{15{target_z_q16_store[48]}},target_z_q16_store}':'{{33{target_z_q16_store[30]}},target_z_q16_store}',
 '{{16{height_feedback_old_store[47]}},height_feedback_old_store}':'{{34{height_feedback_old_store[29]}},height_feedback_old_store}',
 'reg signed [63:0] target_sum_q=0,target_lo_q=0,target_hi_q=0;':
 'reg signed [63:0] target_sum_q=0;\n reg signed [30:0] target_lo_store=0,target_hi_store=0;\n wire signed [63:0] target_lo_q={{33{target_lo_store[30]}},target_lo_store};\n wire signed [63:0] target_hi_q={{33{target_hi_store[30]}},target_hi_store};',
 'target_lo_q<=':'target_lo_store<=', 'target_hi_q<=':'target_hi_store<='
}
for a,b in changes.items():assert s.count(a)==1;s=s.replace(a,b)
assert s==new.read_text(),'Unexpected executable change beyond bounded storage and signed64 aliases'
assert 'target_sum_q<=target_z_q16+value;' in s
assert 'target_lo_store<=height_feedback_old-64\'sd131072000;' in s
assert 'target_hi_store<=height_feedback_old+64\'sd131072000;' in s
traces={}
for name,h in meta['trace_sha256'].items():
 a=R/'reference'/('storage_before_'+name);b=R/'tests'/name
 assert sha(a)==h and a.read_bytes()==b.read_bytes(),('RTL trace changed',name)
 traces[name]=sha(b)
rng=random.Random(0xB0AE);cases=0
for h in range(5001):
 fb=(h//10)*10*65536;lo=fb-131072000;hi=fb+131072000
 assert 0<=fb<=327680000 and fb<(1<<29)
 assert -(1<<30)<=lo<=hi<(1<<30)
 for raw in [-(1<<63),(1<<63)-1,lo-1,lo,lo+1,hi-1,hi,hi+1,0,rng.randrange(-(1<<63),1<<63)]:
  clipped=min(hi,max(lo,raw));stored=((clipped+(1<<30))%(1<<31))-(1<<30)
  assert stored==clipped;cases+=1
report=dict(passed=True,cases=cases,rtl_traces_bit_identical=traces,fraction_bits_unchanged=16,
 operations_signed_bits=64,physical_hardware_accessed=False)
(R/'tests/storage_equivalence.json').write_text(json.dumps(report,indent=2))
paths=[old,new,R/'reference/storage_parent.json',R/'test_storage_equivalence.py']
paths +=[R/'reference'/('storage_before_'+name) for name in traces]
paths +=[R/'tests'/name for name in traces]
proof=dict(passed=True,source_sha256={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in paths},
 method='Inductive clipping/storage bounds and exact previous-qualified RTL traces; no fractional precision or arithmetic changed')
(R/'tests/storage_equivalence.proof.json').write_text(json.dumps(proof,indent=2))
print('STORAGE_EQUIVALENCE_PASS signed64 math, same Q16; height/XY/manual traces bit-identical')
