"""Re-run diagnostic-only dual-top comparison with the selected core dependencies.

The reference top and navigation wrapper retain their original runtime reset;
both sides use the new candidate's identical core, including fallback repairs.
No hardware access or FPGA programming.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, shutil, subprocess, sys

ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'variants/diagnostic_reset_p2_r2_rep1/hardware/diagnostic_reset_proof'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path)
    args=p.parse_args();candidate=args.candidate.resolve();fixture=candidate/'fixture'
    assert candidate.is_relative_to(ROOT/'variants')
    folder=candidate/'hardware/diagnostic_reset_proof';folder.mkdir(parents=True,exist_ok=True)
    old_bundle=json.loads((OLD/'proof_bundle.json').read_text())
    # Preserve the completed, independent bank-level equivalence experiment.
    for name in old_bundle['study_artifacts_sha256']:
        if name.startswith('full_') or name=='README.md': continue
        source=OLD/name
        assert sha(source)==old_bundle['study_artifacts_sha256'][name]
        shutil.copy2(source,folder/name)
    for name in ('acg720_ano_port.v','mtf_xyz_navigation_control.v'):
        assert sha(fixture/name)==sha(folder/(Path(name).stem+'.proposed.v'))
    original=ROOT/'fixture'
    script=(OLD/'full_top.py').read_text()
    before="sources=[F/n for n in re.findall(r'<File path=\"([^\"]+\\.v)\"',(F/'acg720_ano_port.gprj').read_text())]"
    after=before+"\nORIGINAL=Path("+repr(str(original))+ ")\n"+"sources=[ORIGINAL/p.name if p.name in ('acg720_ano_port.v','mtf_xyz_navigation_control.v') else p for p in sources]"
    assert script.count(before)==1
    script=script.replace(before,after)
    # full_top.py resolves D/../.. to this variant, so all other sources are current.
    (folder/'full_top.py').write_text(script)
    for name in ('full_top.py','check_packets.py'):
        subprocess.run([sys.executable,str(folder/name)],cwd=folder,check=True)
    full=json.loads((folder/'full_top.proof.json').read_text())
    assert full['passed'] and full['accepted_bytes']==1136 and full['checksums_verified']
    artifact_names=list(old_bundle['study_artifacts_sha256'])
    (folder/'README.md').write_text(
        'Diagnostic equivalence requalified against published-anchor core dependencies.\n'
        'Reference top/navigation: original runtime reset. Candidate: startup-only diagnostic reset.\n'
        'Both use the exact same updated flight_core and fallback. Only packet period is accelerated; '
        'diagnostic payload/origin events are injected identically. This does not replace control '
        'regressions, mapped INIT review, routing or hardware acceptance.\n')
    bundle=dict(schema_version=1,passed=True,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        study_artifacts_sha256={n:sha(folder/n) for n in artifact_names},
        original_dependencies_sha256=full['source_sha256'],
        scope='Bank proof reused unchanged; actual dual-top comparison rerun with current core dependencies.',
        requalification_driver_sha256=sha(Path(__file__)))
    (folder/'proof_bundle.json').write_text(json.dumps(bundle,indent=2)+'\n')
    subprocess.run([sys.executable,str(candidate/'verify_diagnostic_proof.py')],cwd=candidate,check=True)
    print('PASS refreshed source-bound diagnostic bundle',flush=True)

if __name__=='__main__':main()
