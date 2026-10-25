from pathlib import Path
import json,hashlib,difflib,random,math
from read_numbered import ROOT,P2,RTL,BASE,text
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def truncdiv(n,d):return (abs(n)//d)*(-1 if n<0 else 1)
def clip(x,lo,hi):return min(max(x,lo),hi)
def equation_pair(p,i,steps):
    """P2 OF (of_df_ok branch) formulas vs frozen RTL Q16 equations.
    This is an equation audit, NOT execution of C or RTL.
    """
    af=0.;inte=0.;afq=0;iq=0;outs=[]
    for s,v,a,off in steps:
        dt=.02; alpha=31.4*dt/(1+31.4*dt)
        af+=alpha*(a-af); fix=s-v; err=fix-.03*af
        inte=clip(inte+10*i*clip(fix,-500,500)*dt,-1000 if off else 0,1000 if off else 0)
        u=10*p*err+inte+.2*s
        aq=truncdiv(20000*314*65536,10000000+20000*314)
        afq+=truncdiv((a*65536-afq)*aq,65536)
        fixq=(s-v)*65536;errq=fixq-truncdiv(afq*3,100)
        if i==0:iq=0
        else:
            # Original I=.10 makes its mm->cdeg coefficient exactly1.
            assert i==.1
            iq=clip(iq+truncdiv(clip(fixq,-32768000,32768000)*20000,1000000),-65536000,65536000)if off else 0
        pq=truncdiv(errq,2)if p==.05 else truncdiv(errq*15,10)
        uq=pq+iq+truncdiv(s*65536,5)
        outs.append(dict(target_mmps=s,velocity_mmps=v,accel_mmps2=a,taking_off=off,c_u_cdeg=u,rtl_formula_u_cdeg=uq/65536,rtl_integer_u_cdeg=truncdiv(uq,65536),c_i_cdeg=inte,rtl_i_cdeg=iq/65536,lp_c_mmps2=af,lp_rtl_mmps2=afq/65536))
    return {'max_formula_error_cdeg':max(abs(x['c_u_cdeg']-x['rtl_formula_u_cdeg'])for x in outs),'max_integer_output_error_cdeg':max(abs(x['c_u_cdeg']-x['rtl_integer_u_cdeg'])for x in outs),'steps':outs}
def run():
    package=ROOT.parent;idx=json.loads((package/'ano_reference_index.json').read_text(encoding='utf8'))
    refroot=ROOT/idx['snapshot_relative_root']
    bad=[k for k,v in idx['files'].items()if sha(refroot/k)!=v['sha256']]
    orig=BASE/'source';same=[];diff=[]
    for q in RTL.rglob('*'):
        if not q.is_file():continue
        rel=q.relative_to(RTL);p=orig/rel
        if not p.exists():continue
        (same if sha(p)==sha(q) else diff).append(str(rel))
    d=''.join(difflib.unified_diff(text(orig/'position/mtf_xyz_hold_control.v').splitlines(True),text(RTL/'position/mtf_xyz_hold_control.v').splitlines(True),fromfile='original V15',tofile='P005 I0'))
    (OUT/'original_to_p005i0.diff').write_text(d,encoding='utf8')
    src={'p2_index_sha256':sha(package/'ano_reference_index.json'),'p2_files_checked':len(idx['files']),'p2_hash_mismatches':bad,'rtl_compared_files':len(same)+len(diff),'rtl_same_files':len(same),'rtl_different_files':diff,'frozen_current_hold_sha256':sha(RTL/'position/mtf_xyz_hold_control.v'),'original_v15_hold_sha256':sha(orig/'position/mtf_xyz_hold_control.v'),'authority':'P2 identity from explicit user confirmation. Hash verification only; no provenance/version investigation.'}
    (OUT/'source_audit.json').write_text(json.dumps(src,ensure_ascii=False,indent=2),encoding='utf8')
    steps=[(100,0,0,True),(100,0,1000,True),(0,100,0,True),(-100,0,-1000,True),(0,0,0,False)]
    rng=random.Random(720)
    rand=[(rng.randint(-1500,1500),rng.randint(-3000,3000),rng.randint(-5000,5000),True)for _ in range(2000)]
    tests={}
    for p,i in [(.05,0),(.15,.1)]:
        k=f'P{p}_I{i}'
        tests[k]={'samples':equation_pair(p,i,steps),'random2000':equation_pair(p,i,rand)}
        tests[k]['random2000'].pop('steps')
    (OUT/'equation_audit.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(src,ensure_ascii=False,indent=2));print(json.dumps(tests,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
