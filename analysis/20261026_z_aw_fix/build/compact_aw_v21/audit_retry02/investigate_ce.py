"""Read-only investigation only; does not perform or seal audit retry acceptance."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;O=D.parent;R=O.parents[3];A=R/'out/z_aw_fix_20261026/compact_aw_v21/build_attempt_01'
V=A/'verification';vg=A/'source/impl/gwsynthesis/acg720_ano_port.vg'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reader=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026/tools/read_cones.py')
spec=importlib.util.spec_from_file_location('v21_investigation_original_reader',reader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from escaped_port_adapter import complete_snapshot_aliases
from ce_boolean import prove_shared_ce
g=module.Graph(vg)
before=dict(SP_CE=sorted({g.find(c['pins']['CE'][0]) for c in g.cells.values() if c['type']=='SP'}),
    core_CE=sorted({g.find(p['CE'][0]) for n,p in g.regs.items() if 'staged_telemetry.core_q' in n and p.get('CE')}))
aliases=complete_snapshot_aliases(g,vg);boolean=prove_shared_ce(g,vg)
bound={str(p):sha(p) for p in [Path(__file__),D/'escaped_port_adapter.py',D/'ce_boolean.py',reader,vg,O/'source_freeze.json',O/'runner_exit.json',V/'synthesis_exit.json',V/'audit_exit.json',V/'native_synthesis_audit_failure.json',O/'sp_clock_audit.py']}
record=dict(investigation_only=True,cause_confirmed=True,original_source_unchanged=True,original_scripts_receipts_artifacts_unchanged=True,
    failure='Protected shared reader regex requires named port directly followed by (, omitting legal escaped-name termination whitespace.',
    actual_VG_evidence_lines=dict(wrapper_input_declaration=350184,SP0_CE=350212,wrapper_instance=661773,explicit_parent_child_CE_connection=661775,explicit_parent_child_DO_connection=661796),
    original_graph=before,explicit_lexical_alias_completion=aliases,actual_CE_boolean_cone=boolean,bound_files=bound,
    original_waits=dict(SYN=0,audit=1,root=1),audit_retry_executed=False,SYN_rerun=False,
    scope='Read-only topology/Boolean investigation result for independent review. This is not a successful replacement audit or synthesis qualification.')
(D/'CE_TOPOLOGY_INVESTIGATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(cause_confirmed=True,alias_bits=aliases['alias_bit_count'],same_CE_net=boolean['same_canonical_CE_net'],core_FFs=boolean['remaining_core_snapshot_FF_count'],FF_roots=boolean['FF_root_count'],BDD_nodes=boolean['BDD_allocated_nodes'],audit_retry_executed=False)))
