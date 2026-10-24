"""Inspect the repaired freshness path in an actual emitted Gowin netlist."""
from pathlib import Path
import argparse, datetime, hashlib, json, random, re

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / 'variants/diagnostic_reset_p2_r2_rep1/synthesis/20261023T102524_797062Z/impl/gwsynthesis/acg720_ano_port.vg'
CANDIDATE = Path(__file__).resolve().parents[1]
DEFAULT = CANDIDATE / 'synthesis/20261023T105648_315816Z/impl/gwsynthesis/acg720_ano_port.vg'

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

def exact_age_proof(tree):
    """Canonical ordered BDD equality over all 2**32 command_age values."""
    nodes = {0: (99, 0, 0), 1: (99, 1, 1)}
    unique, cache = {}, {}
    def node(rank, low, high):
        if low == high: return low
        key = (rank, low, high)
        if key not in unique:
            unique[key] = len(nodes); nodes[unique[key]] = key
        return unique[key]
    def ite(c, t, f):
        if c == 1: return t
        if c == 0: return f
        if t == f: return t
        key = (c,t,f)
        if key not in cache:
            rank = min(nodes[x][0] for x in key)
            def branch(x, side): return nodes[x][side] if nodes[x][0] == rank else x
            cache[key] = node(rank, ite(*(branch(x,1) for x in key)), ite(*(branch(x,2) for x in key)))
        return cache[key]
    variables = [node(31-i,0,1) for i in range(32)]
    def convert(value):
        if isinstance(value,str):
            if value in ('GND','VCC'): return int(value == 'VCC')
            assert re.fullmatch(r'command_age\[\d+\]',value), value
            return variables[int(re.search(r'\d+',value)[0])]
        init, children = value
        args = [convert(x) for x in children]
        def lut(table, count):
            if count == 0: return table & 1
            half = 1 << (count-1)
            return ite(args[count-1], lut(table >> half,count-1), lut(table & ((1 << half)-1),count-1))
        return lut(init,len(args))
    expected = 1
    for bit in range(32):
        expected = ite(variables[bit], expected if (3000000 >> bit)&1 else 1,
                       0 if (3000000 >> bit)&1 else expected)
    assert convert(tree) == expected, 'Exact age comparator BDD mismatch'
    return len(nodes)

def arbitrary_cone(graph, net):
    if net not in graph: return net
    init, inputs = graph[net]
    return init, tuple(arbitrary_cone(graph,n) for n in inputs)

def instance(body, kind, name):
    found = re.findall(r'\b'+kind+r' '+name+r'\s*\((.*?)\);',body,re.S)
    assert len(found) == 1, (kind,name,len(found))
    return dict((k,v.strip()) for k,v in re.findall(r'\.(\w+)\((.*?)\)',found[0]))

def review(path):
    text, old = path.read_text(), REFERENCE.read_text()
    body, prior = module(text, 'flight_core'), module(old, 'flight_core')
    graph, old_graph = lut_graph(body), lut_graph(prior)
    assert graph['core_body_0_4'] == (0x4000, ('n3434_132', 'command_seen', 'core_body_861', 'controller_run'))
    age_cone = cone(graph, 'n3434_132')
    assert age_cone == cone(old_graph, 'n3434_132'), 'Age comparator changed'
    assert graph['core_body_0'][0] == 0xFF70
    assert graph['core_body_0'][1] == ('flight_state_flags_0_2', 'flight_state_flags_16[1]', 'core_body_860', 'core_body_0_4')
    assert graph['core_body_861'] == old_graph['core_body_861'] == (0xA800, ('core_body_860','height_fallback_active','z_handoff_active','flight_state_flags_0_2'))
    for address in range(16):
        expired, seen, enabled, running = [(address >> i) & 1 for i in range(4)]
        assert ((0x4000 >> address) & 1) == (not expired and seen and enabled and running)
        prepared, taking_off, armed, fresh = [(address >> i) & 1 for i in range(4)]
        assert ((0xFF70 >> address) & 1) == (fresh or (armed and not (prepared and taking_off)))
        armed, fallback, altitude, taking_off = [(address >> i) & 1 for i in range(4)]
        assert ((0xA800 >> address) & 1) == (armed and taking_off and (fallback or altitude))
    rng = random.Random(0xB0B0)
    ages = {0, 1, 2999999, 3000000, 3000001, 0xffffffff}
    ages.update(range(3000000-128, 3000000+129))
    ages.update(1 << i for i in range(32))
    ages.update(rng.getrandbits(32) for _ in range(2048))
    assert all(evaluate(age_cone, age) == (age >= 3000000) for age in ages)
    bdd_nodes = exact_age_proof(age_cone)
    pwm = module(text, 'motor_pwm')
    old_pwm = module(old, 'motor_pwm')
    declarations = lambda b: re.findall(r'^(input|output)\s+(\[[^\]]+\]\s*)?(\w+)\s*;',b,re.M)
    old_ports, new_ports = declarations(old_pwm), declarations(pwm)
    assert [(d,w) for d,w,n in old_ports] == [(d,w) for d,w,n in new_ports]
    assert len({n for d,w,n in new_ports}) == len(new_ports)
    rename = {a[2]:b[2] for a,b in zip(old_ports,new_ports) if a[2] != b[2]}
    assert len(set(rename.values())) == len(rename)
    translated = re.sub(r'\b\w+\b',lambda m: rename.get(m[0],m[0]),old_pwm)
    assert translated == pwm, 'PWM module differs beyond declared port/net alpha-renaming'
    output_instance = re.search(r'\bmotor_pwm outputs\s*\(.*?\);', body, re.S).group()
    prior_instance = re.search(r'\bmotor_pwm outputs\s*\(.*?\);', prior, re.S).group()
    bindings = dict(re.findall(r'\.(\w+)\((.*?)\)', output_instance))
    prior_bindings = dict(re.findall(r'\.(\w+)\((.*?)\)', prior_instance))
    inputs = re.findall(r'^input\s+(?:\[[^\]]+\]\s*)?(\w+)\s*;', pwm, re.M)
    assert len(inputs) == 34
    cone_equivalent_inputs = []
    for direction, width, old_name in old_ports:
        name = rename.get(old_name,old_name)
        if direction == 'input' and bindings[name] != prior_bindings[old_name]:
            assert arbitrary_cone(graph,bindings[name]) == arbitrary_cone(old_graph,prior_bindings[old_name]), name
            cone_equivalent_inputs.append(name)
        elif direction == 'input' or name.startswith('motor'):
            assert bindings[name] == prior_bindings[old_name], name
    top = module(text, 'acg720_ano_port')
    core_instance = re.search(r'\bflight_core core\s*\(.*?\);', top, re.S).group()
    assert '.core_body_0(core_body[0])' in core_instance
    core_bindings = instance(top,'flight_core','core')
    physical_connections = {}
    for i in range(1,5):
        name = 'motor'+str(i)+'_pwm'
        assert core_bindings[name+'_d'] == name+'_d'
        ports = instance(top,'OBUF',name+'_obuf')
        assert ports == {'O':name,'I':name+'_d'}
        physical_connections[name] = ports
    primary = re.search(r'DFFRE \\staged_telemetry\.core_q_862_\w+\s*\(.*?defparam[^;]+;', top, re.S).group()
    assert '.D(core_body[0])' in primary and '.RESET(GND)' in primary
    assert '.Q(\\staged_telemetry.core_q [862])' in primary
    log = path.with_suffix('.log')
    warnings = re.findall(r'Undeclared symbol|EX3638|EX1998|ERROR\s*\(', log.read_text())
    assert not warnings
    source_names = ('core/flight_core.v','core/height_loss_fallback.v')
    for name in source_names:
        assert sha(path.parents[2]/name) == sha(CANDIDATE/'fixture'/name), 'Synthesis snapshot differs from reviewed current RTL: '+name
    return dict(passed=True, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                netlist=str(path), netlist_sha256=sha(path), reference_netlist=str(REFERENCE), reference_sha256=sha(REFERENCE),
                log_sha256=sha(log), reviewer_sha256=sha(Path(__file__)), forbidden_warnings=0,
                age_cone_structurally_identical=True, age_boundary_and_sample_checks=len(ages),
                age_comparator_exact_all_32bit_values=True, age_bdd_node_count=bdd_nodes,
                freshness_gate_truth_tables_exhaustive=True, pwm_module_exactly_unchanged=True,
                pwm_unchanged_definition='Exact complete module text equality after bijective declared port/net alpha-renaming; INIT/cells/all connections retained.',
                pwm_port_alpha_renaming=rename, pwm_renamed_input_cones_proven=cone_equivalent_inputs,
                pwm_all_34_input_and_four_motor_output_bindings_unchanged=True,
                pwm_binding_definition='Bindings exact or identical LUT cones to the same committed motor bits for renamed inputs.',
                physical_motor_obuf_connections=physical_connections,
                source_sha256={name:sha(path.parents[2]/name) for name in source_names},
                synthesized_two_file_snapshot_matches_current_fixture=True,
                limitations=['Only targeted mapped freshness/motor PWM/primary snapshot paths are checked; not whole-design equivalence.',
                             'Bindings/cones are compared at committed motor-bit and named interface boundaries, not the changed upstream mixer/controller arithmetic.',
                             'Primary bit862 is checked through snapshot D/Q connectivity; UART serialization is covered by separate proofs.',
                             'No timing/routing/board/flight acceptance is implied.'],
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
