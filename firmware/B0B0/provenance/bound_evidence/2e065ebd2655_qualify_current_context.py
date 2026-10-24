"""Freeze scoped current-context evidence; never relabel parent simulations."""
from pathlib import Path
import datetime,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))

def main():
 from inherited_context_bridge import verify as inherited
 bridge=inherited();assert bridge['passed'] is True
 info=load(ROOT/'hardware/info_mapped_review.json');assert info['passed'] is True
 info_binding=load(ROOT/'hardware/info_mapped_binding.json');assert info_binding['passed'] is True
 assert info_binding['report_sha256']==sha(ROOT/'hardware/info_mapped_review.json')
 spec=importlib.util.spec_from_file_location('builder',ROOT/'fixture/build_project.py')
 b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 b.static_contract();sources=b.source_hashes();study=load(ROOT/'synthesis_study.json')
 from verify_info_binding import verify as verify_info
 verify_info(Path(study['folder'])/'impl/gwsynthesis/acg720_ano_port.vg',sources)
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
 result=dict(candidate='B0B0 INFO caller snapshot contingency',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),offline_tests_passed=True,
   sources_sha256=sources,evidence_sha256=evidence,programming_authorized=False,hardware_programmed=False,flight_ready=False,pnr_verified=False,
   current_full_top_simulation_passed=False,parent_simulations_retained_at_original_paths=True,
   requalified_after_full_synthesis=archive.is_dir(),actual_reviewed_netlist=str(vg),
   qualification_execution='Original N34 and C128 proofs at original paths; exact reviewed INFO caller/top substitution, real-UART/default/source boundary evidence, current X top elaboration and actual INFO272/NAV720/MTF976/freshness audits on reused immutable aa2deVG. No new synthesis execution.',
   scope='Control RTL unchanged from N and published-anchor C. New structural change only reviewed INFO duplicate snapshot removal plus opt-in top. No full X top dynamic simulation, PNR or hardware acceptance claimed.')
 (ROOT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(offline_tests_passed=True,evidence_files=len(evidence),pnr_verified=False,hardware_accessed=False)))
if __name__=='__main__':main()
