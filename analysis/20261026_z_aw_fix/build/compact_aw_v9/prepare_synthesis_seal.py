"""Use completed v8 archive format for exact v9 SYN, with truthful current phase."""
from pathlib import Path
import ast,json
O=Path(__file__).resolve().parent;R=O.parents[3]
summary=json.loads((R/'out/z_aw_fix_20261026/compact_aw_v9/build_attempt_01/verification/synthesis_summary.json').read_text())
assert summary['passed']
text=(O.parent/'compact_aw_v8/seal_synthesis.py').read_text().replace('v8','v9').replace('proofs_completion02','proofs_retry02')
text=text.replace('5f3637446527bd5b1c83b20c5493027ca7101d664b845630104d9a51b035a33e',summary['netlist_sha256'])
text=text.replace('SYN passed, PNR not started, not qualified for installation','SYN passed; physical trials started; not qualified for installation')
text=text.replace("'PNR_started':False","'PNR_started':True")
ast.parse(text);p=O/'seal_synthesis.py';assert not p.exists();p.write_text(text)
