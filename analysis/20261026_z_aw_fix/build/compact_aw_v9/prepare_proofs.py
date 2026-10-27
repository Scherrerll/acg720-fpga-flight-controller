"""Adapt substantive frozen fixtures by source/output identity only."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs';assert not D.exists();D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
items={};hold='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
for kind,source_name in [('five','aw_storage_regression/run_regression.py'),('boundary','aw_storage_boundary/verify_boundary.py'),('top','aw_storage_integration/verify_top_safety.py'),('contention','aw_storage_integration/verify_contention.py')]:
    source=R/'analysis/20261026_z_aw_fix'/source_name
    folder=D/kind;folder.mkdir();text=source.read_text()
    text=text.replace('compact_aw_v7/canonical','compact_aw_v9/canonical')
    if kind=='five':
        text=text.replace('R=O.parents[2]',f'R=Path({str(R)!r})').replace('2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad',hold)
        for name in ['aw_tb.v','b4_v1_reference.v']:(folder/name).write_bytes((source.parent/name).read_bytes())
    elif kind=='boundary':text=text.replace('R = O.parents[2]',f'R = Path({str(R)!r})')
    elif kind=='top':text=text.replace('REPO=Path(__file__).resolve().parents[3]',f'REPO=Path({str(R)!r})')
    else:text=text.replace('REPO=Path(__file__).resolve().parents[3]',f'REPO=Path({str(R)!r})')
    ast.parse(text);dest=folder/'run.py';dest.write_text(text)
    items[kind]={'source':str(source),'source_sha256':sha(source),'driver_sha256':sha(dest)}
(O/'proof_derivation.json').write_text(json.dumps({'scope':'Fixture assertions unchanged. Source/output path identity and expected hold digest only.', 'items':items},indent=2)+'\n')
print('Prepared four substantive v9 proof suites.')
