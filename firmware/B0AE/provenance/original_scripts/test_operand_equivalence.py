from pathlib import Path
import hashlib,json,random
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'reference/operand_before_hold.v';new=R/'fixture/position/mtf_xyz_hold_control.v'
meta=json.loads((R/'reference/operand_parent.json').read_text());assert sha(old)==meta['source_sha256']
s=old.read_text()
changes={
 'reg signed [63:0] ma=0;':'reg signed [49:0] ma_store=0;\n wire signed [63:0] ma={{14{ma_store[49]}},ma_store};',
 'reg signed [63:0] mb=0;':'reg signed [33:0] mb_store=0;\n wire signed [63:0] mb={{30{mb_store[33]}},mb_store};',
 'reg signed [63:0] value=0;':'reg signed [47:0] value_store=0;\n wire signed [63:0] value={{16{value_store[47]}},value_store};',
 'begin ma<=a;mb<=b;':'begin ma_store<=a;mb_store<=b;',
 'value<=quotient;state<=return_state;':'value_store<=quotient;state<=return_state;'
}
for a,b in changes.items():assert s.count(a)==1;s=s.replace(a,b)
assert s==new.read_text(),'Unexpected change beyond stored operand/result widths and signed64 aliases'
# Induction for the only variable denominator: pdt starts at20000 and can
# only be captured in the1000..100000 branch. dt is written only from pdt.
assert s.count('pdt<=')==1 and s.count('dt<=pdt;')==1
assert 'position_dt_us<1000 || position_dt_us>100000' in s
assert 'else begin position_due<=1;position_stick_captured<=0;px<=' in s
assert 'pdt<=position_dt_us;' in s and 'pyaw=0;reg [31:0] pdt=20000;' in s
assert 'reg [31:0] dt=20000,base=1000;' in s
assert s.count('inner_alt_speed<=')==1 and 'inner_alt_speed<=alt_speed;' in s
def signed(n):return (-(1<<(n-1)),(1<<(n-1))-1)
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def neg(a):return (-a[1],-a[0])
def sub(a,b):return add(a,neg(b))
def mul(a,b):
 v=[x*y for x in a for y in b];return min(v),max(v)
def c(a):return (a,a)
def rounded(n,d):return ((abs(n)+d//2)//d)*(1 if n>=0 else -1)
dt=(1000,100000);hs=(32768000,98304000)
iv={
 '$signed(pending_az)*65536-afz':sub(mul(signed(32),c(65536)),signed(32)),
 '$signed(pending_nx)':signed(18),'$signed(pending_ny)':signed(18),
 '$signed({1\'b0,dt})*314':mul(dt,c(314)),
 'hy-afy':sub(signed(33),signed(33)),
 'hx-afx':sub(signed(33),signed(33)),
 'afx':signed(33),'afy':signed(33),
 'clip(fixx,-32768000,32768000)':(-32768000,32768000),
 'clip(fixy,-32768000,32768000)':(-32768000,32768000),
 'ex':signed(32),'ey':signed(32),'sx':signed(29),'sy':signed(29),
 '-sample_vx':neg(signed(31)),
 'world_sy':signed(28),'world_sx':signed(28),
 'world_sx-sample_vx':sub(signed(28),signed(31)),
 'world_sy-sample_vy':sub(signed(28),signed(31)),
 'world_ax':signed(32),'world_ay':signed(32),
 'afz+value':add(signed(32),signed(48)),
 'inner_alt_speed':signed(32),
 'clip(exz+value,-65536000,65536000)':(-65536000,65536000),
 '22937600-bias':sub(c(22937600),signed(33)),
 'exz':signed(31),'alt_speed':signed(32),
 'horizontal_speed_limit_q16':hs,'alpha':signed(17),'cs':signed(18),'sn':signed(18),
 '$signed({1\'b0,dt})':dt,
 '10000000+dt*314':add(c(10000000),mul(dt,c(314)))
}
def interval(expr):return iv[expr] if expr in iv else c(int(expr))
calls=[];pos=0
while True:
 i=s.find('calc(',pos)
 if i<0:break
 depth=1;j=i+5
 while depth:
  if s[j]=='(':depth+=1
  elif s[j]==')':depth-=1
  j+=1
 text=s[i+5:j-1];parts=[];start=0;depth=0
 for k,ch in enumerate(text):
  if ch in '({':depth+=1
  elif ch in ')}':depth-=1
  elif ch==',' and depth==0:parts.append(text[start:k]);start=k+1
 parts.append(text[start:]);assert len(parts)==4
 calls.append(parts);pos=j
assert len(calls)==32,'Every calc call must have a bound'
rng=random.Random(0xB0AE50);cases=0;bounds=[]
for a,b,d,dest in calls:
 aa,bb,dd=interval(a),interval(b),interval(d)
 assert signed(50)[0]<=aa[0]<=aa[1]<=signed(50)[1]
 assert signed(34)[0]<=bb[0]<=bb[1]<=signed(34)[1]
 assert 1<=dd[0]<=dd[1]<2**32
 product=mul(aa,bb);assert signed(64)[0]<product[0]<=product[1]<=signed(64)[1]
 quot=(min(0,rounded(product[0],dd[0])),max(0,rounded(product[1],dd[0])))
 assert signed(48)[0]<=quot[0]<=quot[1]<=signed(48)[1],(a,b,d,quot)
 for _ in range(1000):
  x=rng.randint(*aa);y=rng.randint(*bb);den=rng.randint(*dd)
  def store(v,n):return (v+(1<<(n-1)))%(1<<n)-(1<<(n-1))
  assert store(x,50)==x and store(y,34)==y
  z=rounded(x*y,den);assert store(z,48)==z;cases+=1
 bounds.append(dict(a=a,b=b,denominator=d,ma=aa,mb=bb,quotient=quot))
# Original fixed-point traces also must remain exactly byte-for-byte equal.
traces={}
for name,h in meta['trace_sha256'].items():
 a=R/'reference'/('operand_before_'+name);b=R/'tests'/name
 assert sha(a)==h and a.read_bytes()==b.read_bytes(),('RTL trace changed',name)
 traces[name]=sha(b)
report=dict(passed=True,calls=len(calls),cases=cases,intervals=bounds,
 rtl_traces_bit_identical=traces,operations_signed_bits=64,
 fraction_bits_unchanged=True,multiplier_divider_and_latency_unchanged=True)
(R/'tests/operand_equivalence.json').write_text(json.dumps(report,indent=2))
paths=[old,new,R/'reference/operand_parent.json',R/'test_operand_equivalence.py']
paths +=[R/'reference'/('operand_before_'+name)for name in traces]
paths +=[R/'tests'/name for name in traces]
(R/'tests/operand_equivalence.proof.json').write_text(json.dumps(dict(passed=True,
 source_sha256={str(p.relative_to(R)).replace('\\','/'):sha(p)for p in paths},
 method='Inductive operand/result intervals for all32 calc sites; exact old/new RTL trace equality'),indent=2))
print('OPERAND_EQUIVALENCE_PASS all32 calc bounds,32000 cases; same64-bit math and RTL traces')
