from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,time,xml.etree.ElementTree as ET,random
R=Path(__file__).resolve().parent;F=R/'fixture';TOP='acg720_ano_port'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());inputs=q['sources_sha256'];assert all(sha(F/n)==h for n,h in inputs.items())
D=R/'synthesis'/('target_storage_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));D.mkdir(parents=True)
for n in inputs:
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(F/n,p)
p=D/'position/mtf_xyz_hold_control.v';s=p.read_text()
replacements={
 'reg signed [49-1:0] target_z_q16_store=0;':'reg signed [31-1:0] target_z_q16_store=0;',
 'reg signed [48-1:0] height_feedback_old_store=0;':'reg signed [30-1:0] height_feedback_old_store=0;',
 '{{15{target_z_q16_store[48]}},target_z_q16_store}':'{{33{target_z_q16_store[30]}},target_z_q16_store}',
 '{{16{height_feedback_old_store[47]}},height_feedback_old_store}':'{{34{height_feedback_old_store[29]}},height_feedback_old_store}',
 'reg signed [63:0] target_sum_q=0,target_lo_q=0,target_hi_q=0;':
 'reg signed [63:0] target_sum_q=0;\n reg signed [30:0] target_lo_store=0,target_hi_store=0;\n wire signed [63:0] target_lo_q={{33{target_lo_store[30]}},target_lo_store};\n wire signed [63:0] target_hi_q={{33{target_hi_store[30]}},target_hi_store};',
 'target_lo_q<=':'target_lo_store<=', 'target_hi_q<=':'target_hi_store<='
}
for old,new in replacements.items():assert s.count(old)==1,old;s=s.replace(old,new)
p.write_text(s,encoding='utf8')
# Induction: reset/cancel=0; seed=bounded feedback; subsequent target is
# clipped to old feedback +/-2000mm in Q16. Keep the 64-bit add/compare,
# including overflow behavior, and change only the proven stored words.
radius=131072000;low=-radius;high=5000*65536+radius
assert -(1<<30)<=low<=high<(1<<30)
assert -(1<<29)<=0<=5000*65536<(1<<29)
rng=random.Random(0xB0AE);vectors=0
for h in range(5001):
 fb=(h//10)*10*65536;lo=fb-radius;hi=fb+radius
 for raw in [-(1<<63),(1<<63)-1,lo-1,lo,lo+1,hi-1,hi,hi+1,0,rng.randrange(-(1<<63),1<<63)]:
  value=min(hi,max(lo,raw));stored=((value+(1<<30))%(1<<31))-(1<<30)
  assert stored==value and -(1<<30)<=lo<=hi<(1<<30);vectors+=1
lemma=dict(passed=True,feedback_domain_mm=[0,5000],feedback_q16=[0,327680000],
 target_q16=[low,high],tests=vectors,kept_sum_and_comparison_bits=64,changed_fraction_bits=False,
 experimental_source_sha256=sha(p),parent_source_sha256=inputs['position/mtf_xyz_hold_control.v'])
(D/'range_lemma.json').write_text(json.dumps(lemma,indent=2))
script=(D/'build.tcl').read_text();assert script.splitlines().count('run all')==1
(D/'study.tcl').write_text(script.replace('run all','run syn'),encoding='utf8')
log=D/'console.txt'
with log.open('w',encoding='utf8') as stream:
 process=subprocess.Popen(['C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe','study.tcl'],cwd=D,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 start=time.monotonic();done=None
 while process.poll() is None:
  if 'GowinSynthesis finish' in log.read_text(encoding='utf8',errors='replace'):
   if done is None:done=time.monotonic()
   if time.monotonic()-done>10:process.terminate();process.wait(timeout=10);break
  if time.monotonic()-start>600:process.terminate();process.wait(timeout=10);raise RuntimeError('study timeout')
  time.sleep(1)
assert 'GowinSynthesis finish' in log.read_text(encoding='utf8',errors='replace')
assert all(sha(F/n)==h for n,h in inputs.items()),'Main source changed during isolated study'
node=ET.parse(D/'impl/gwsynthesis'/(TOP+'_syn_rsc.xml')).getroot()
result=dict(offline_synthesis_only=True,pnr_run=False,hardware_accessed=False,
 experiment='bounded target/feedback storage, same Q16, all operations remain signed64',
 parent_sources_sha256=inputs,resources=node.attrib,range_lemma=lemma,folder=str(D))
(D/'study.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(resources=node.attrib,range_lemma=lemma,folder=str(D)),indent=2),flush=True)
