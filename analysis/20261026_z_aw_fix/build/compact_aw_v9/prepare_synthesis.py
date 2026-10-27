"""Prepare a proof-gated SYN-only runner for v4-based v9; no execution here."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
donor=O.parent/'compact_aw_v8/run_synthesis.py'
text=donor.read_text().replace('v8','v9').replace('v7','v4')
text=text.replace('2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad','ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642')
text=text.replace('proofs_completion02','proofs_retry02')
assert text.count("proof['source55']['v9']")==1
text=text.replace("proof['source55']['v9']","proof['source55']")
ast.parse(text)
assert "compact_aw_v4'" in text and "compact_aw_v9'" in text
dest=O/'run_synthesis.py';assert not dest.exists();dest.write_text(text)
supervisor=O.parent/'compact_aw_v8/launch_synthesis_hidden.py'
dest=O/'launch_synthesis_hidden.py';assert not dest.exists();dest.write_bytes(supervisor.read_bytes())
(O/'synthesis_runner_derivation.json').write_text(json.dumps({'scope':'v4 map2 donor; v9 guard change; proof_retry02 required before execution. No synthesis launched by preparation.',
    'donor_runner_sha256':sha(donor),'derived_runner_sha256':sha(O/'run_synthesis.py'),
    'supervisor_sha256':sha(O/'launch_synthesis_hidden.py')},indent=2)+'\n')
print('Prepared v9 SYN-only runner gated by completed proof retry02.')
