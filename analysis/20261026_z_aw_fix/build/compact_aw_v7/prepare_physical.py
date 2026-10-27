"""Derive v7 physical-only runners from the frozen v6 gate implementation."""
from pathlib import Path
import ast, datetime, hashlib, json

O = Path(__file__).resolve().parent
R = O.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
items = {}
for name in ['run_physical.py', 'launch_physical_hidden.py', 'seal_terminal.py', 'physical_snapshot.py']:
    donor = O.parent / 'compact_aw_v6' / name
    text = donor.read_text(encoding='utf8').replace('v6', 'v7')
    if name == 'run_physical.py':
        text = text.replace("'04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'", "'2109595a24c6f15a553ea8a0958b8313c3f19d56b4371c827cd428976489daad'")
        text = text.replace("    assert expected['mtf_xyz_navigation_control.v']=='f826345ebd2c2fa97477042b0eaea8aa888683911c95cb3907314ebcfc508fea'\n", '')
        text = text.replace("    assert expected['position/mtf_shared_height_fusion.v']=='69b386c20fc04ce24904ad871d8e36168d4ea8e813f3eccb3b48b8cea90b2dc0'\n", '')
        marker = "    assert hash55(CANON,expected)==expected and hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior\n"
        assert text.count(marker) == 1
        text = text.replace(marker, marker + "    assert prior==freeze['baseline_source55'] and [p for p in expected if expected[p]!=prior[p]]==['position/mtf_xyz_hold_control.v']\n")
        text = text.replace('    tmp=VERIFY/', "    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')\n    tmp=VERIFY/")
    if name in ['run_physical.py', 'seal_terminal.py']:
        text = text.replace('6b169818d5029c45e0a778d74d8d3e90e129caa430e93eb3778661f18fa7cb99', 'dc20d15cec4471df8679960fb05660349caaa19dfaee40604b419ca6450cf0e0')
    if name == 'physical_snapshot.py':
        text = text.replace('for place in [3,2,1]:', 'for place in [3,2]:')
    if name == 'seal_terminal.py':
        text = text.replace("['1','2','3']", "['2','3']")
    if name == 'run_physical.py':
        text = text.replace('O=Path', 'sys.dont_write_bytecode=True\nO=Path', 1)
    ast.parse(text)
    destination = O / name
    assert not destination.exists(), destination
    destination.write_text(text, encoding='utf8')
    items[name] = {'donor':str(donor), 'donor_sha256':sha(donor), 'derived_sha256':sha(destination)}
out = O / 'physical_runner_derivation.json'
assert not out.exists()
out.write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Reuse exact frozen physical gates, change only variant identity, source binding and provenance copy. No gate relaxation.',
    'profiles':{'P3R0':'v4 nearest full-route 49.456MHz reference; v7 storage reduction changes mapped topology',
                'P2R0':'v6 P2R0 routed and outperformed P1; alternative placement for unchanged v7 netlist'},
    'items':items}, indent=2)+'\n', encoding='utf8')
print(json.dumps(items, indent=2))
