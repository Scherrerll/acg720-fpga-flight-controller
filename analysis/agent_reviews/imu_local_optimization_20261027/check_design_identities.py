"""Offline binary identities and original-source assignment inventory only.

This does not execute RTL, synthesis, timing, or a firmware qualification gate.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'out/z_aw_fix_20261026/compact_aw_v22/canonical/source/core/ano_attitude_estimator.v'
assert all(not (p.lower().startswith('.env') or p.lower() == 'deployment.env') for p in SOURCE.parts)
assert not SOURCE.is_symlink()
source = SOURCE.read_bytes()
assert hashlib.sha256(source).hexdigest() == '72c7e1fe56eca1a723f1f59bc0d38e081b9e3315eb0750c41dd3f038dea3ea0a'
text = source.decode('utf-8-sig')
assignments = []
for match in re.finditer(r'\bindex\s*<=\s*([^;]+);', text):
    assignments.append({'line': text.count('\n', 0, match.start()) + 1, 'rhs': match.group(1)})
zeros = [x['line'] for x in assignments if x['rhs'] == '0']
increments = [x['line'] for x in assignments if x['rhs'] == "index+1'b1"]
assert zeros == [413, 419, 458, 463, 471, 476, 478, 493, 571, 614]
assert increments == [443, 474, 478, 486, 499, 630]
assert len(assignments) == 16

def prev_bit1(index):
    return 1 ^ ((index >> 1) & 1) ^ (index & 1)

bit_checks = address_checks = cache_checks = onehot_checks = 0
for index in range(32):
    raw_previous = (index - 1) & 0xffffffff
    narrow_previous = (index - 1) & 31
    assert prev_bit1(index) == ((raw_previous >> 1) & 1)
    assert prev_bit1((index + 1) & 31) == ((index >> 1) & 1)
    bit_checks += 2
    original_slot = raw_previous if raw_previous < 24 else None
    new_slot = narrow_previous if narrow_previous < 24 else None
    assert original_slot == new_slot
    address_checks += 1
    for action in ('hold', 'zero', 'increment'):
        next_index = index if action == 'hold' else 0 if action == 'zero' else (index + 1) & 31
        cache = prev_bit1(index) if action == 'hold' else 1 if action == 'zero' else (index >> 1) & 1
        assert cache == prev_bit1(next_index)
        cache_checks += 1
        selector = 1 << index
        next_selector = selector if action == 'hold' else 1 if action == 'zero' else ((selector << 1) | (selector >> 31)) & 0xffffffff
        assert next_selector == 1 << next_index
        onehot_checks += 1

print(json.dumps({
    'passed_binary_design_checks': True,
    'scope': 'Algebra over all 32 known-binary index values and abstract hold/zero/increment actions; source assignment inventory. No X/Z, RTL, protocol, mapped, physical or qualification proof.',
    'source_sha256': hashlib.sha256(source).hexdigest(),
    'assignment_inventory': assignments,
    'zero_count': len(zeros),
    'increment_count': len(increments),
    'binary_identity_checks': bit_checks,
    'out_of_range_slot_equivalence_checks': address_checks,
    'cache_action_checks': cache_checks,
    'onehot_action_checks': onehot_checks,
}, ensure_ascii=False, indent=2))
