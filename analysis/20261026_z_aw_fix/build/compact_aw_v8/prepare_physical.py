"""Prepare exact-v8-VG physical runners; this script launches no PNR."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((O/'SYNTHESIS_RESULT.json').read_text())
assert summary['vendor_actual_wait']==summary['runner_actual_wait']==0 and summary['clock_radio_gain_18ports_passed']
proof=json.loads((O/'proofs_completion02/results.json').read_text())
assert proof['passed'] and proof['source55']['v8']==summary['source55']
oldvg='dc20d15cec4471df8679960fb05660349caaa19dfaee40604b419ca6450cf0e0'
newvg='5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e'
items={}
for name in ['run_physical.py','launch_physical_hidden.py','physical_snapshot.py','seal_terminal.py','independent_raw_review.py']:
    donor=O.parent/'compact_aw_v7'/name
    text=donor.read_text().replace('v7','v8').replace('v5','v7').replace(oldvg,newvg)
    if name=='run_physical.py':
        old="assert prior==freeze['baseline_source55'] and [p for p in expected if expected[p]!=prior[p]]==['position/mtf_xyz_hold_control.v']"
        assert text.count(old)==1
        text=text.replace(old,"assert prior==freeze['baseline_source55'] and sorted(p for p in expected if expected[p]!=prior[p])==sorted(freeze['changed_files'])")
        marker="    evidence += [O/'source_freeze.json',O/'runner_exit.json',donor_vg]\n"
        assert text.count(marker)==1
        text=text.replace(marker,marker+"    proof=json.loads((O/'proofs_completion02/results.json').read_text());px=json.loads((O/'proofs_completion02/runner_exit.json').read_text())\n    assert proof['passed'] and proof['source55']['v8']==expected and px['actual_p_wait']==0 and px['normal_wait_return']\n    evidence += [O/'proofs_completion02/results.json',O/'proofs_completion02/runner_exit.json']\n")
        # Both synthesis runner and proof runner have runner_exit.json basenames.
        # Preserve each under a path-derived unique name; binding keeps absolute originals.
        text=text.replace("shutil.copy2(p,provenance/p.name)","shutil.copy2(p,provenance/(p.parent.name+'__'+p.name))")
    ast.parse(text)
    destination=O/name;assert not destination.exists();destination.write_text(text)
    items[name]={'donor':str(donor),'donor_sha256':sha(donor),'derived_sha256':sha(destination)}
(O/'physical_runner_derivation.json').write_text(json.dumps({'scope':'Exact unchanged physical gates; v8 source/VG and focused proof binding only. No physical run started by preparation.',
    'VG_sha256':newvg,'items':items,'planned_profiles':[3,2]},indent=2)+'\n')
print('Prepared exact v8 physical scripts; no PNR launched.')
