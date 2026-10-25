from pathlib import Path
import sys
ROOT = Path(r'C:\Users\ScherrerL\Desktop\apple\handoff_xy_pi_runtime_20261026\workspace_snapshot')
P2 = ROOT/'reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1'
RTL = ROOT/'timing_closure_20261025/v15_xy_p005_i0_review_20261025/source'
BASE = ROOT/'github_publish/acg720-fpga-flight-controller/firmware/B0B2'
def text(p):
    b=p.read_bytes()
    try: return b.decode('utf-8-sig')
    except UnicodeDecodeError: return b.decode('gb18030',errors='replace')
if __name__=='__main__':
    root={'p2':P2,'rtl':RTL,'base':BASE,'snapshot':ROOT}[sys.argv[1]]
    p=root/sys.argv[2]
    lines=text(p).splitlines()
    lo=int(sys.argv[3]) if len(sys.argv)>3 else 1
    hi=int(sys.argv[4]) if len(sys.argv)>4 else len(lines)
    print(str(p))
    for i,l in enumerate(lines,1):
        if lo<=i<=hi: print(f'{i:4}: {l}')
