"""Create one source-enable candidate from the immutable response snapshot."""
from pathlib import Path
import difflib,hashlib,json,shutil
C=Path(__file__).resolve().parent;R=C.parents[1];B=R/'candidates/response_compact';S=C/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads((B/'change.json').read_text())['candidate_source_sha256']
assert len(frozen)==55 and not S.exists()
for rel,digest in frozen.items():
 p=B/'source'/rel
 assert sha(p)==digest,(rel,sha(p),digest)
 q=S/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
p=S/'position/mtf_xyz_hold_control.v';before=p.read_bytes()
declaration=b' reg [15:0] work_p=500,work_i=0;\n'
capture=b'work_p<=xy_p_value;work_i<=xy_i_value;'
assert before.count(declaration)==1 and before.count(capture)==1
after=before.replace(declaration,declaration+b' always @(posedge clk) if(state==0)begin\n  '+capture+b'\n end\n').replace(b'position_due<=0;work_xy<=1;'+capture,b'position_due<=0;work_xy<=1;')
assert after.count(capture)==1 and b'\r' not in after
assert after.replace(declaration+b' always @(posedge clk) if(state==0)begin\n  '+capture+b'\n end\n',declaration).replace(b'position_due<=0;work_xy<=1;',b'position_due<=0;work_xy<=1;'+capture)==before
p.write_bytes(after)
current={rel:sha(S/rel) for rel in frozen}
changed=[rel for rel in frozen if current[rel]!=frozen[rel]]
assert changed==['position/mtf_xyz_hold_control.v']
assert all(sha(B/'source'/rel)==digest for rel,digest in frozen.items())
(C/'verification/tmp').mkdir(parents=True)
(C/'candidate.diff').write_bytes(''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='response_compact/source/position/mtf_xyz_hold_control.v',tofile='idle_gain_ce/source/position/mtf_xyz_hold_control.v')).encode())
record=dict(status='isolated_not_selected',baseline=str(B/'source'),baseline_source_sha256=frozen,candidate_source_sha256=current,changed_files=changed,byte_identical_files=54,baseline_controller_sha256=sha(B/'source'/changed[0]),candidate_controller_sha256=sha(p),scope='Move both16-bit gain captures to independent state==0 clock enable; no other source bytes changed; no canonical baseline read')
(C/'change.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:record[k] for k in ['status','changed_files','byte_identical_files','baseline_controller_sha256','candidate_controller_sha256']},indent=2))
