"""Fail-closed source-bound context substitution proof for the unchanged diagnostic bank."""
from pathlib import Path
import re,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(s):return re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
def compact(s):return re.sub(r'\s+','',clean(s))
def build_report():
 from verify_diagnostic_proof import verify_original
 assert verify_original()['passed']
 from verify_published_anchor import verify as verify_anchor
 assert verify_anchor()['passed']
 F=ROOT/'fixture';D=ROOT/'hardware/diagnostic_reset_proof'
 delta=json.loads((ROOT/'published_anchor_delta.json').read_text());parent=Path(delta['reference'])
 unchanged=['acg720_ano_port.v','mtf_xyz_navigation_control.v','telemetry_tx.v','core/spi_uart_modules.v']
 for n in unchanged:assert sha(F/n)==sha(parent/'fixture'/n),('Diagnostic context interface changed',n)
 for n,proposal in [('acg720_ano_port.v','acg720_ano_port.proposed.v'),('mtf_xyz_navigation_control.v','mtf_xyz_navigation_control.proposed.v')]:assert sha(F/n)==sha(D/proposal)
 top=compact((F/'acg720_ano_port.v').read_text());nav=compact((F/'mtf_xyz_navigation_control.v').read_text())
 boot="reg[7:0]boot=0;always@(posedgeclk50)if(boot!=255)boot<=boot+1'b1;wirerst_n=boot==255;"
 assert boot in top and len(re.findall(r'\bboot\b',clean((F/'acg720_ano_port.v').read_text())))==5
 assert len(re.findall(r'\bboot\s*(?:<=|=(?!=))',clean((F/'acg720_ano_port.v').read_text())))==2
 # Exact sole driver: initialized bank, startup-only branch, unchanged runtime-reset default branch.
 bank="reg[719:0]diagnostic_q=RESET_DIAGNOSTIC;always@(posedgeclk)beginif(STARTUP_ONLY_DIAGNOSTIC_RESET)beginif(rst_n&&!diagnostic_hold)diagnostic_q<=diagnostic_next;endelsebeginif(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;elseif(!diagnostic_hold)diagnostic_q<=diagnostic_next;endend"
 assert len(re.findall(r'\brst_n\s*(?:<=|=(?!=))',clean((F/'acg720_ano_port.v').read_text())))==1
 assert bank in nav and nav.count('diagnostic_q<=')==3
 original_bank_proof=json.loads((D/'proof.json').read_text())
 oldnav_path=next(Path(n)for n in original_bank_proof['source_sha256']if Path(n).name=='mtf_xyz_navigation_control.v')
 oldtop_path=next(Path(n)for n in original_bank_proof['source_sha256']if Path(n).name=='acg720_ano_port.v')
 oldnav=compact(oldnav_path.read_text());oldtop=compact(oldtop_path.read_text())
 oldbank="reg[719:0]diagnostic_q=RESET_DIAGNOSTIC;always@(posedgeclk)beginif(!rst_n)diagnostic_q<=RESET_DIAGNOSTIC;elseif(!diagnostic_hold)diagnostic_q<=diagnostic_next;end"
 assert oldbank in oldnav and oldnav.count('diagnostic_q<=')==2 and boot in oldtop
 reset_pattern=r'localparam\[719:0\]RESET_DIAGNOSTIC=(.*?);'
 assert re.search(reset_pattern,nav).group()==re.search(reset_pattern,oldnav).group()
 assert 'STARTUP_ONLY_DIAGNOSTIC_RESET=0' in nav and '.STARTUP_ONLY_DIAGNOSTIC_RESET(1)' in top
 mask="assigndiagnostic_body={diagnostic_q[719:144],diagnostic_q[85]?diagnostic_q[143:128]:16'd0,diagnostic_q[85]?diagnostic_q[127:112]:16'd0,diagnostic_q[111:0]};"
 assert mask in nav
 remainder=nav.replace(bank,'').replace(mask,'');assert 'diagnostic_q' not in remainder
 assert len(re.findall(r'\bdiagnostic_body\b',clean((F/'mtf_xyz_navigation_control.v').read_text())))==2
 assert len(re.findall(r'\bnavigation_body\b',clean((F/'acg720_ano_port.v').read_text())))==3
 assert '.diagnostic_body(navigation_body)' in top and '.nav_body(navigation_body)' in top
 assert '.NAV_CALLER_SNAPSHOT(1)' in top and '.EXTERNAL_SNAPSHOT(1)' in top
 assert remainder.count('diagnostic_hold')==1 # input declaration only; hold affects no controller/history state.
 # All original proof dependency differences are exactly the two reviewed common-context core files.
 original=json.loads((D/'proof_bundle.json').read_text());changes=[]
 for path,h in original['original_dependencies_sha256'].items():
  source=Path(path);rel=source.relative_to(ROOT.parents[1]/'fixture');now=F/rel
  if str(rel).replace('\\','/')in ['acg720_ano_port.v','mtf_xyz_navigation_control.v']:continue
  if sha(now)!=h:changes.append(str(rel).replace('\\','/'))
 assert set(changes)=={'core/flight_core.v','core/height_loss_fallback.v'}
 proof_names=['fallback_component','fallback_core','published_anchor','nominal_core_equivalence','top','legacy_telemetry_wire','fallback_telemetry_wire']
 paths=[ROOT/'diagnostic_context_bridge.py',ROOT/'verify_diagnostic_proof.py',ROOT/'verify_published_anchor.py',ROOT/'published_anchor_delta.json',ROOT/'hardware/published_anchor.patch',D/'proof_bundle.json',ROOT/'hardware/independent_control_review.json',ROOT/'hardware/mapped_init_review.json',ROOT/'hardware/synthesis_freshness_review.json',ROOT/'tests/host_tests.proof.json',ROOT/'tests/host_tests.log',ROOT/'hardware/partial_current_full_top/status.json']
 for name in proof_names:
  p=ROOT/'tests'/f'{name}.proof.json';proof=json.loads(p.read_text());assert proof['passed']is True
  for n,h in proof['source_sha256'].items():
   src=Path(n);assert sha(src if src.is_absolute()else ROOT/src)==h,('Current proof stale',name,n)
  paths.append(p)
 host=json.loads((ROOT/'tests/host_tests.proof.json').read_text());assert host['passed']is True and host['tests']==24
 for n,h in host['source_sha256'].items():assert sha(ROOT/n)==h
 assert host['log_sha256']==sha(ROOT/'tests/host_tests.log')
 partial=json.loads((ROOT/'hardware/partial_current_full_top/status.json').read_text());assert partial['passed']is False and partial['completed']is False
 mapped=json.loads((ROOT/'hardware/mapped_init_review.json').read_text());fresh=json.loads((ROOT/'hardware/synthesis_freshness_review.json').read_text());assert mapped['passed']is True and fresh['passed']is True and mapped['netlist_sha256']==fresh['netlist_sha256']
 for n,h in mapped['evidence_sha256'].items():assert sha(Path(n))==h
 control=json.loads((ROOT/'hardware/independent_control_review.json').read_text());assert control['findings']==[]
 for n,h in control['sha256'].items():assert sha(ROOT/n)==h
 spec=importlib.util.spec_from_file_location('bridge_builder',F/'build_project.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 sources=b.source_hashes();assert mapped['sources_sha256']==sources
 return dict(passed=True,proof_kind='Source-bound compositional substitution with algebraic reset induction; not a formal-tool proof',current_full_top_simulation_passed=False,original_actual_full_top_simulation_passed=True,original_bundle_sha256=sha(D/'proof_bundle.json'),current_sources_sha256=sources,unchanged_interfaces_sha256={n:sha(F/n)for n in unchanged},changed_common_context_sources=changes,evidence_sha256={str(p.relative_to(ROOT)):sha(p)for p in paths},induction=['boot is initialized0, increments only while unequal255, and holds255 forever; rst_n is exactly boot==255 and has no other driver.','Before boot release, old bank repeatedly writes RESET_DIAGNOSTIC; new bank holds the identical initialized value. Both bank/output values are equal.','At and after the sole release, both banks capture identical arbitrary720-bit diagnostic_next exactly when !diagnostic_hold, otherwise hold. The unchanged output mask preserves equality.','Diagnostic bank/body feed telemetry only and do not affect control/history state. Substituting equal bank outputs into identical current surrounding RTL preserves the complete context trace by induction. Both compared contexts use the exact same two reviewed patched core modules.'],requirements=['Original50000cycle bank test and source-bound original4935299cycle/1136byte actual dual-top UART evidence remain immutable original-source evidence.','Current published-anchor component/core/nominal/top/UART/24host proofs, independent control review, actual mapped720bit INIT/CE/Boolean output proof and freshness-to-PWM review all pass and are hash-bound.'],limitations=['The cancelled redundant current-core full-top run is incomplete and is not counted as passed.','The arbitrary-input claim follows the explicit algebraic induction and exact source/driver/interface checks, not finite simulation coverage alone.','This bridge proves applicability of the unchanged diagnostic optimization to the reviewed current context. It is not whole-design sequential mapped-netlist equivalence, routing acceptance, or hardware acceptance.'])
def freeze():
 report=build_report();(ROOT/'hardware/diagnostic_context_bridge.json').write_text(json.dumps(report,indent=2)+'\n');return report
def verify():
 report=json.loads((ROOT/'hardware/diagnostic_context_bridge.json').read_text());assert report==build_report(),'Diagnostic compositional bridge is stale or incomplete'
 return dict(passed=True,proof_kind=report['proof_kind'],current_full_top_simulation_passed=False)
if __name__=='__main__':print(json.dumps(verify()))
