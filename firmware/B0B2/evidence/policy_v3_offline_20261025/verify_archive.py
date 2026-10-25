from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text())
for n,v in m['files'].items():
 p=(root/n).resolve();assert p.is_relative_to(root),n
 assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],n
assert not list(root.rglob('*.fs'))
assert m['physical_qualification_passed']is False
assert (root/'best/fixture/acg720_ano_port.sdc').read_text().strip()=='create_clock -name clk50 -period 19.500 [get_ports {clk50}]'
assert hashlib.sha256((root/'best/fixture/impl/gwsynthesis/acg720_ano_port.vg').read_bytes()).hexdigest()==m['netlist_sha256']
print('PASS archive integrity; required physical timing NOT qualified; no hardware action')
