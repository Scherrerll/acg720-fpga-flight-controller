"""Bind a full-build mapped netlist to the reviewed physical/Boolean proof."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(p):
 s=p.read_text();s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 lex=re.compile(r'\\\S+|"(?:\\.|[^"\\])*"|[A-Za-z_$][A-Za-z0-9_$]*|\s+|.',re.S)
 return hashlib.sha256(json.dumps([x for x in lex.findall(s)if not x.isspace()],separators=(',',':')).encode()).hexdigest()
def verify(netlist,sources):
 review=json.loads((ROOT/'hardware/mapped_init_review.json').read_text())
 assert review['passed'] is True and review['sources_sha256']==sources
 assert (review.get('logical_bits_verified'),review.get('nav_logical_bits'),review.get('mtf_logical_bits'))==(1696,720,976)
 assert review.get('nav_passed') is True and review.get('mtf_passed') is True
 assert canonical(netlist)==review['canonical_netlist_sha256'],'Actual full-build mapped logic differs from reviewed INIT/720-bit/CE proof; rerun mapped audit before release'
 for path,value in review['evidence_sha256'].items():assert sha(Path(path))==value,('Mapped proof binding changed',path)
 result=dict(passed=True,actual_netlist=str(netlist),actual_netlist_sha256=sha(netlist),canonical_netlist_sha256=review['canonical_netlist_sha256'],review_sha256=sha(ROOT/'hardware/mapped_init_review.json'),method='Exact complete mapped token identity after comments/whitespace removal; inherits verified INIT, Boolean output mapping and CE proof.')
 (ROOT/'hardware/full_build_mapped_init_review.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
