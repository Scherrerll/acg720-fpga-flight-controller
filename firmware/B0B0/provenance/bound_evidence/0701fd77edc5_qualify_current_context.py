"""Freeze scoped current-context evidence; never relabel parent simulations."""
from pathlib import Path
import datetime,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))

def main():
 from inherited_context_bridge import verify as inherited
 bridge=inherited();assert bridge['passed'] is True
 spec=importlib.util.spec_from_file_location('builder',ROOT/'fixture/build_project.py')
 b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 b.static_contract();sources=b.source_hashes();study=load(ROOT/'synthesis_study.json')
 assert study['passed'] is True and study['sources_sha256']==sources
 top=load(ROOT/'tests/top_elaboration.proof.json');assert top['passed'] is True
 assert top['sources_sha256']==sources,'Elaboration inputs changed'
 assert sha(ROOT/'tests/top_elaboration.log')==top['log_sha256']
 from verify_mapped_binding import verify as mapped
 vg=Path(load(ROOT/'hardware/mapped_init_review.json')['netlist']);mapped(vg,sources)
 archive=ROOT/'preliminary_mapped_archive'
 if archive.is_dir():
  prior=load(archive/'qualification.json');assert prior['sources_sha256']==sources,'Compiled inputs changed since original qualification'
  for n,h in prior['evidence_sha256'].items():assert sha(archive/n)==h,('Archived preliminary proof changed',n)
 files=list(ROOT.glob('*.py'))+[ROOT/'source_contract.json',ROOT/'OPERATOR_NOTES.txt',ROOT/'DO_NOT_PROGRAM',ROOT/'synthesis_study.json',ROOT/'fixture/build_project.py']
 files+=list((ROOT/'tests').glob('*.json'))+list((ROOT/'tests').glob('*.log'))
 if archive.is_dir():files+=[archive/'qualification.json',archive/'archive_index.json']
 files+=[p for p in (ROOT/'hardware').rglob('*')if p.is_file() and '__pycache__'not in p.parts and not p.name.startswith('full_build_')]
 evidence={str(p.relative_to(ROOT)):sha(p)for p in files}
 result=dict(candidate='B0B0 MTF diagnostic startup reset',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),offline_tests_passed=True,
   sources_sha256=sources,evidence_sha256=evidence,programming_authorized=False,hardware_programmed=False,flight_ready=False,pnr_verified=False,
   current_full_top_simulation_passed=False,parent_simulations_retained_at_original_paths=True,
   requalified_after_full_synthesis=archive.is_dir(),actual_reviewed_netlist=str(vg),
   qualification_execution='Original C control/core/nominal/UART/host proofs checked at original paths; exact two-file MTF substitution with 50000-cycle boundary proof and algebraic boot argument; current N top elaboration and actual new mapped NAV720/MTF976/freshness audits.',
   scope='Control RTL unchanged from published-anchor C. New structural change only in MTF diagnostic bank and opt-in caller. No full N top dynamic simulation, PNR or hardware acceptance claimed.')
 (ROOT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(offline_tests_passed=True,evidence_files=len(evidence),pnr_verified=False,hardware_accessed=False)))
if __name__=='__main__':main()
