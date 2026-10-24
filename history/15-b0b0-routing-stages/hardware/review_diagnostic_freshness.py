"""Inspect the repaired freshness path in an actual emitted Gowin netlist."""
from pathlib import Path
import argparse, datetime, hashlib, json, random, re

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / 'variants/p2_r2_rep1/fixture/impl/gwsynthesis/acg720_ano_port.vg'
CANDIDATE = ROOT / 'variants/diagnostic_reset_p2_r2_rep1'
DEFAULT = CANDIDATE / 'synthesis/20261023T102524_797062Z/impl/gwsynthesis/acg720_ano_port.vg'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def module(text, name):
    return re.search(r'^module ' + name + r'\s*\(.*?^endmodule', text, re.M | re.S).group()

def lut_graph(body):
    graph = {}
    for m in re.finditer(r'\bLUT([1-6])\s+(\w+)\s*\((.*?)\);\s*defparam\s+\2\.INIT=(\d+)\x27h([0-9A-Fa-f]+);', body, re.S):
        ports = {k: v.strip() for k,v in re.findall(r'\.(\w+)\((.*?)\)', m[3])}
        count = int(m[1])
        graph[ports['F']] = (int(m[5], 16), tuple(ports['I'+str(i)] for i in range(count)))
    return graph

def cone(graph, net):
    if net not in graph:
        assert net in ('GND', 'VCC') or re.fullmatch(r'command_age\[\d+\]', net), net
        return net
    init, inputs = graph[net]
    return (init, tuple(cone(graph, value) for value in inputs))

def evaluate(tree, age):
    if isinstance(tree, str):
        if tree == 'GND': return 0
        if tree == 'VCC': return 1
        return (age >> int(re.search(r'\d+', tree)[0])) & 1
    init, children = tree
    address = sum(evaluate(child, age) << i for i, child in enumerate(children))
    return (init >> address) & 1

def review(path):
    text, old = path.read_text(), REFERENCE.read_text()
    body, prior = module(text, 'flight_core'), module(old, 'flight_core')
    graph, old_graph = lut_graph(body), lut_graph(prior)
    assert graph['core_body_0_4'] == (0x4000, ('n3434_132', 'command_seen', 'core_body_861', 'controller_run'))
    age_cone = cone(graph, 'n3434_132')
    assert age_cone == cone(old_graph, 'n3434_132'), 'Age comparator changed'
    assert graph['core_body_0'][0] == 0xFF70
    assert graph['core_body_0'][1] == ('flight_state_flags_0_2', 'flight_state_flags_14[1]', 'core_body_860', 'core_body_0_4')
    for address in range(16):
        expired, seen, enabled, running = [(address >> i) & 1 for i in range(4)]
        assert ((0x4000 >> address) & 1) == (not expired and seen and enabled and running)
        prepared, taking_off, armed, fresh = [(address >> i) & 1 for i in range(4)]
        assert ((0xFF70 >> address) & 1) == (fresh or (armed and not (prepared and taking_off)))
    rng = random.Random(0xB0B0)
    ages = {0, 1, 2999999, 3000000, 3000001, 0xffffffff}
    ages.update(range(3000000-128, 3000000+129))
    ages.update(1 << i for i in range(32))
    ages.update(rng.getrandbits(32) for _ in range(2048))
    assert all(evaluate(age_cone, age) == (age >= 3000000) for age in ages)
    pwm = module(text, 'motor_pwm')
    assert pwm == module(old, 'motor_pwm'), 'PWM implementation changed'
    output_instance = re.search(r'\bmotor_pwm outputs\s*\(.*?\);', body, re.S).group()
    prior_instance = re.search(r'\bmotor_pwm outputs\s*\(.*?\);', prior, re.S).group()
    bindings = dict(re.findall(r'\.(\w+)\((.*?)\)', output_instance))
    prior_bindings = dict(re.findall(r'\.(\w+)\((.*?)\)', prior_instance))
    inputs = re.findall(r'^input\s+(?:\[[^\]]+\]\s*)?(\w+)\s*;', pwm, re.M)
    assert len(inputs) == 34
    for name in inputs + ['motor'+str(i)+'_pwm_d' for i in range(1,5)]:
        assert bindings[name] == prior_bindings[name], name
    top = module(text, 'acg720_ano_port')
    core_instance = re.search(r'\bflight_core core\s*\(.*?\);', top, re.S).group()
    assert '.core_body_0(core_body[0])' in core_instance
    primary = re.search(r'DFFRE \\staged_telemetry\.core_q_862_\w+\s*\(.*?defparam[^;]+;', top, re.S).group()
    assert '.D(core_body[0])' in primary and '.RESET(GND)' in primary
    log = path.with_suffix('.log')
    warnings = re.findall(r'Undeclared symbol|EX3638|EX1998|ERROR\s*\(', log.read_text())
    assert not warnings
    return dict(passed=True, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                netlist=str(path), netlist_sha256=sha(path), reference_sha256=sha(REFERENCE),
                log_sha256=sha(log), reviewer_sha256=sha(Path(__file__)), forbidden_warnings=0,
                age_cone_structurally_identical=True, age_boundary_and_sample_checks=len(ages),
                freshness_gate_truth_tables_exhaustive=True, pwm_module_exactly_unchanged=True,
                pwm_all_34_input_and_four_motor_output_bindings_unchanged=True,
                primary_862_reads_combined_freshness=True, primary_cell=primary,
                hardware_accessed=False,
                scope='Targeted synthesized age/seen/enabled/run freshness-to-PWM and telemetry connectivity. Not a whole-netlist equivalence proof or routing acceptance.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--netlist', type=Path, default=DEFAULT)
    parser.add_argument('--output', type=Path, default=CANDIDATE/'hardware/synthesis_freshness_review.json')
    args=parser.parse_args()
    result=review(args.netlist)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('passed','netlist_sha256','age_boundary_and_sample_checks','scope')}))
