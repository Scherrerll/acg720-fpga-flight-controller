"""Independent pure status checks and read-only revision/hash validation."""
from pathlib import Path
import ast, datetime, hashlib, itertools, json

R = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
M = R / 'analysis/20261026_z_aw_fix/build/compact_aw_v20_dsp_followup'
S = M.parent / 'compact_aw_v20'
runtime = R / 'out/z_aw_fix_20261026/compact_aw_v20'
def safe(path):
    path = Path(path)
    for part in path.parts:
        name = part.casefold().rstrip(' .')
        assert not name.startswith('.env') and not name.endswith('.env') and '.env' not in [x.casefold() for x in Path(name).suffixes]
    for p in [path, *path.parents]:
        assert not p.is_symlink() and not (hasattr(p, 'is_junction') and p.is_junction())
    return path
sha = lambda p: hashlib.sha256(safe(p).read_bytes()).hexdigest()
read = lambda p: json.loads(safe(p).read_text())
prep = read(M / 'PHYSICAL_PREPARATION.json')
binding = read(M / 'PORTABLE_CONSTRAINT_BINDING.json')
assert prep['prepared_revision'] == '02'
assert prep['portable_constraint_binding_sha256'] == sha(M / 'PORTABLE_CONSTRAINT_BINDING.json')
for name, digest in prep['new_scripts_sha256'].items(): assert sha(M / name) == digest
for name, digest in prep['parent_scripts_sha256'].items(): assert sha(S / name) == digest
for path, digest in binding['bound_inputs'].items(): assert sha(path) == digest
revision_counts = {}
for revision in ['revision_01', 'revision_02']:
    folder = M / 'prepared_revisions' / revision
    manifest = read(folder / 'REVISION_MANIFEST.json')
    for name, item in manifest['immutable_saved_files'].items():
        assert sha(folder / name) == item['sha256'] and (folder / name).stat().st_size == item['bytes']
    revision_counts[revision] = len(manifest['immutable_saved_files'])
assert sha(M / 'prepared_revisions/revision_01/REVISION_MANIFEST.json') == prep['prior_prepared_revision_manifest_sha256']
initial = read(D / 'INITIAL_REVIEW.json')
for name in ['seal_terminal.py', 'physical_snapshot.py']:
    assert sha(M / 'prepared_revisions/revision_01' / name) == initial['input_sha256'][str(M / name)]
for name in ['run_physical.py', 'portable_constraints.py', 'independent_raw_review.py', 'preflight_physical_recipe.py', 'launch_physical_hidden.py']:
    assert sha(M / name) == initial['input_sha256'][str(M / name)]
tree = ast.parse((M / 'terminal_diagnostics.py').read_text())
assert all(isinstance(n, (ast.FunctionDef, ast.Expr)) for n in tree.body)
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
namespace = {}
exec(compile(ast.Module(body=functions, type_ignores=[]), 'reviewed-pure-diagnostics', 'exec'), namespace)
expressions = []
for name in ['seal_terminal.py', 'physical_snapshot.py']:
    parsed = ast.parse((M / name).read_text())
    calls = [n.value for n in ast.walk(parsed) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
             and isinstance(n.value.func, ast.Name) and n.value.func.id == 'terminal_status']
    assert len(calls) == 1
    expressions.append(compile(ast.Expression(calls[0]), name, 'eval'))
    outputs = [n for n in ast.walk(parsed) if isinstance(n, ast.keyword) and n.arg == ('passed' if name.startswith('seal') else 'full_gate_pass')]
    assert outputs and all(isinstance(n.value, ast.Name) and n.value.id == 'passed' for n in outputs)
receipts = [None, {}, {'actual_p_wait': 0}, {'normal_wait_return': True}, {'normal_wait_return': True, 'actual_p_wait': None},
            {'normal_wait_return': True, 'actual_p_wait': 1}, {'normal_wait_return': False, 'actual_p_wait': 0},
            {'normal_wait_return': None, 'actual_p_wait': 0}, {'normal_wait_return': 1, 'actual_p_wait': 0},
            {'normal_wait_return': True, 'actual_p_wait': False}, {'normal_wait_return': True, 'actual_p_wait': 0.0},
            {'normal_wait_return': True, 'actual_p_wait': '0'}, {'normal_wait_return': True, 'actual_p_wait': 0}]
results = [None, {}, {'passed': False}, {'passed': None}, {'passed': 1}, {'passed': 'true'}, {'passed': True}]
valid = lambda x: isinstance(x, dict) and x.get('normal_wait_return') is True and type(x.get('actual_p_wait')) is int and x['actual_p_wait'] == 0
checks = 0
for result, vendor, runner in itertools.product(results, receipts, receipts):
    expected = isinstance(result, dict) and result.get('passed') is True and valid(vendor) and valid(runner)
    for expression in expressions:
        actual, classification = eval(expression, {'terminal_status': namespace['terminal_status']},
            dict(result=result, build_result=result, vendor=vendor, runner=runner, audit={'passed': True}, unrouted=[], physical_log='', text=''))
        assert actual is expected
        if valid(vendor) and runner is not None and not valid(runner): assert classification == 'runner_failed_after_physical_gate_pass'
        checks += 1
for receipt_name, stdout_name, stderr_name in [('DIAGNOSTIC_TRUTH_EXIT.json', 'diagnostic_truth.stdout.log', 'diagnostic_truth.stderr.log'),
                                              ('INSPECTION_REVISION02_FINAL_EXIT.json', 'inspection_revision02_final.stdout.log', 'inspection_revision02_final.stderr.log')]:
    receipt = read(M / receipt_name)
    assert receipt['normal_wait_return'] is True and receipt['actual_p_wait'] == 0
    assert sha(M / stdout_name) == receipt['stdout_sha256'] and sha(M / stderr_name) == receipt['stderr_sha256']
assert sha(M / 'PHYSICAL_PREPARATION.json') == read(M / 'PREPARATION_REVISION_02.json')['PHYSICAL_PREPARATION_sha256']
assert not (runtime / 'physical_p3r0_dsploc_01').exists() and not list((M / 'physical_p3r0_dsploc_01').iterdir())
record = dict(reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), reviewer='/root/review_50mhz',
    approved_preparation=True, findings=[], initial_finding_resolved=True, prepared_revision='02', actual_pure_expression_checks=checks,
    actual_distinct_truth_vectors=checks // 2, archived_revision_file_counts=revision_counts, thin_bound_inputs_rehashed=len(binding['bound_inputs']),
    original_helper_and_raw_physical_gates_unchanged=True, physical_runtime_created=False, vendor_executed=False, hardware_accessed=False,
    standard_attempt_running_at_initial_review=True, thin_runtime_absent=True, thin_receipt_directory_empty=True,
    initial_review_sha256=sha(D / 'INITIAL_REVIEW.json'), preparation_sha256=sha(M / 'PHYSICAL_PREPARATION.json'),
    constraint_binding_sha256=sha(M / 'PORTABLE_CONSTRAINT_BINDING.json'), revision_note_sha256=sha(M / 'PREPARATION_REVISION_02.json'),
    reviewed_script_hashes=prep['new_scripts_sha256'], checker_sha256=sha(Path(__file__)),
    scope='Prepared physical-only standard-v20 DSP41 recipe review. Independent macro/source/constraint inspection is recorded in INITIAL_REVIEW. Pure revision02 truth checks execute only audited function definitions and AST-selected call expressions; no bound script top-level, vendor or runtime action. No physical qualification.')
(D / 'REVIEW.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(dict(passed=True, expressions=checks, revision_counts=revision_counts, review_sha256=sha(D / 'REVIEW.json'))))
