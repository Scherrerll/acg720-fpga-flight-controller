"""Bind both independently checked diagnostic banks to one actual SYN output."""
from pathlib import Path
import hashlib, importlib.util, json, sys
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))

def main():
 spec=importlib.util.spec_from_file_location('builder',ROOT/'fixture/build_project.py')
 b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 b.static_contract();sources=b.source_hashes()
 study=load(ROOT/'synthesis_study.json');assert study['passed'] is True and study['sources_sha256']==sources
 folder=Path(study['folder']);vg=folder/'impl/gwsynthesis/acg720_ano_port.vg'
 for n,h in sources.items():assert sha(folder/n)==h,('SYN snapshot changed',n)
 if len(sys.argv)>1:
  vg=Path(sys.argv[1]).resolve()
  assert vg==(ROOT/'fixture/impl/gwsynthesis/acg720_ano_port.vg').resolve(),'Only this actual full build may replace preliminary SYN'
  assert load(ROOT/'fixture/build_manifest.json')['sources_sha256']==sources,'Actual build input freeze changed'
  assert 'GowinSynthesis finish' in (ROOT/'fixture/build_console.txt').read_text(),'Actual SYN incomplete'
 from verify_info_binding import verify as verify_info
 info=verify_info(vg,sources)
 nav=load(ROOT/'hardware/mapped_nav_review.json');mtf=load(ROOT/'hardware/mapped_mtf_review.json')
 fresh=load(ROOT/'hardware/synthesis_freshness_review.json')
 assert nav['passed'] is True and nav['logical_bits_verified']==720 and nav['sources_sha256']==sources
 assert nav['netlist_sha256']==mtf['candidate_vg_sha256']==fresh['netlist_sha256']==sha(vg)
 assert mtf['passed'] is True and mtf['logical_bits']==976 and mtf['physical_bank_ffs']==827
 assert len(mtf['logical_mapping_msb_first'])==976 and len(mtf['physical_mapping'])==827
 assert all(mtf[k] is True for k in ['all_logical_init_zero','all_bank_init_zero','d_payload_boolean_equal','boot_init_zero_and_saturating'])
 assert fresh['passed'] is True and fresh['forbidden_warnings']==0
 contract=load(ROOT/'source_contract.json')
 reference=Path(contract['independent_mtf_reference'])
 assert sha(reference)==contract['independent_mtf_reference_sha256']==mtf['reference_vg_sha256']
 for name,h in nav['evidence_sha256'].items():assert sha(Path(name))==h,('NAV evidence changed',name)
 spec=importlib.util.spec_from_file_location('binding',ROOT/'verify_mapped_binding.py')
 binding=importlib.util.module_from_spec(spec);spec.loader.exec_module(binding)
 paths=[ROOT/'freeze_mapped_review.py',ROOT/'verify_mapped_binding.py',ROOT/'fixture/build_project.py',ROOT/'source_contract.json',ROOT/'synthesis_study.json',vg,
        ROOT/'hardware/mapped_nav_review.json',ROOT/'hardware/mapped_mtf_review.json',ROOT/'hardware/mapped_mtf_audit.py',ROOT/'hardware/synthesis_freshness_review.json',ROOT/'hardware/review_synthesis_freshness.py']
 evidence=dict(nav['evidence_sha256']);evidence.update(info['evidence_sha256']);evidence.update({str(p):sha(p)for p in [ROOT/'verify_info_binding.py',ROOT/'hardware/info_mapped_review.json',ROOT/'hardware/info_mapped_binding.json']});evidence.update({str(p):sha(p)for p in paths})
 report=dict(passed=True,sources_sha256=sources,netlist=str(vg),netlist_sha256=sha(vg),canonical_netlist_sha256=binding.canonical(vg),
   logical_bits_verified=1968,diagnostic_logical_bits=1696,nav_logical_bits=720,mtf_logical_bits=976,info_logical_bits=272,nav_passed=True,mtf_passed=True,info_passed=True,evidence_sha256=evidence,
   nav_review_sha256=sha(ROOT/'hardware/mapped_nav_review.json'),mtf_review_sha256=sha(ROOT/'hardware/mapped_mtf_review.json'),
   scope='Current aa2deVG NAV720 exact BDD/vendor primitive INIT/output, MTF976 exact BDD INIT/payload/CE/boot, independent INFO272 mapped proof with source/evidence binding. Original N34/C128 control evidence retained at original paths plus reviewed INFO caller substitution. No new current full-top dynamic simulation, whole-design sequential equivalence, PNR or hardware acceptance.',programming_authorized=False,pnr_run=False,hardware_accessed=False)
 (ROOT/'hardware/mapped_init_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS aggregate1968 logical bits (NAV720 + MTF976 + INFO272), original actual SYN/current source/evidence bound')
if __name__=='__main__':main()
