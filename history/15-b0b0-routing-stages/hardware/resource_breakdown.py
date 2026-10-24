"""Read-only synthesis area inventory. Inclusive child totals are not additive."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'variants/p2_r2_rep1/fixture/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'

def number(node, key):
    return int(node.get(key, '0').split('(')[0])

def inventory(node, parent=''):
    path = '/'.join(filter(None, (parent, node.get('name'))))
    row = {'path': path}
    for name in ('Lut', 'Alu', 'Register'):
        row[name.lower() + '_own'] = number(node, name)
        row[name.lower() + '_inclusive'] = number(node, 'T_' + name)
    yield row
    for child in node:
        yield from inventory(child, path)

def main():
    data = SOURCE.read_bytes()
    rows = list(inventory(ET.fromstring(data)))
    lookup = {row['path']: row for row in rows}
    total = lookup['acg720_ano_port']['lut_inclusive']
    receiver_state = sum(lookup['acg720_ano_port/core/' + name]['lut_inclusive']
                         for name in ('receiver', 'flight_state'))
    report = {
        'source': str(SOURCE), 'source_sha256': hashlib.sha256(data).hexdigest(),
        'stage': 'Synthesis before placement and high-fanout replication',
        'inclusive_counts_must_not_be_added_across_nested_rows': True,
        'receiver_and_flight_state_lut': receiver_state,
        'receiver_and_flight_state_fraction_of_total_lut': receiver_state / total,
        'note': 'This is not all pilot-input processing. Filters, normalization, and manual attitude control are separate rows. Routing feasibility cannot be inferred from LUT counts alone.',
        'modules': rows,
    }
    destination = BASE / 'hardware/resource_breakdown.json'
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'source_sha256': report['source_sha256'],
                      'total_lut': total, 'receiver_and_flight_state_lut': receiver_state,
                      'fraction': receiver_state / total, 'output': str(destination)}))

if __name__ == '__main__':
    main()
