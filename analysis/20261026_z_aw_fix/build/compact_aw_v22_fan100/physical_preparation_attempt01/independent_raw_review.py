"""Independent raw report review. Does not import build_candidate or its audit."""
from pathlib import Path
import datetime, hashlib, json, math, re, sys

O=Path(__file__).resolve().parent; R=O.parents[3]
STANDARD=O.parent/'compact_aw_v22'
assert len(sys.argv)==2 and sys.argv[1] in ['3']
label='physical_p3r0_01'; A=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100'/label
S=A/'source'; V=A/'verification'; report=O/label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
expected=read(O/'source_freeze.json')['source55']
vendor=read(V/'physical_exit.json'); runner=read(report/'runner_exit.json')
assert vendor['normal_wait_return'] and runner['normal_wait_return']
checks={'vendor_wait0':vendor['actual_p_wait']==0,'runner_wait0':runner['actual_p_wait']==0,
    'source55':len(expected)==55 and {p:sha(S/p) for p in expected}==expected,
    'canonical_source55':{p:sha(R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'/p) for p in expected}==expected,
    'VG':sha(S/'impl/gwsynthesis/acg720_ano_port.vg')==read(O/'SYNTHESIS_RESULT.json')['netlist_sha256']}
proof=read(STANDARD/'PROOF_BINDING.json');binding=read(O/'PHYSICAL_INPUT_BINDING.json')
F=Path(proof['fresh_proof_directory']);D=Path(proof['proof_directory']);B=Path(proof['alias_retry_directory'])
old=read(F/'functional_runner_exit.json');failed=read(F/'alias_compile_exit.json');alias=read(B/'runner_exit.json');completion=read(D/'functional_runner_exit.json');top=read(F/'top13_exit.json')
checks['v22_original_TEMP_compile1_root1_alias_retry0_completion0']=proof['passed'] and proof['source55']==expected and old['normal_wait_return'] and old['actual_p_wait']==1 and failed['normal_wait_return'] and failed['actual_p_wait']==1 and alias['normal_wait_return'] and alias['actual_p_wait']==0 and completion['normal_wait_return'] and completion['actual_p_wait']==0 and top['normal_wait_return'] and top['actual_p_wait']==0
checks['v22_new_controller_fresh_five_fraction_four_top']=proof['fresh_five_cases']==5 and proof['fresh_fraction_cases']==[0,16] and proof['fresh_four_client'] and proof['fresh_top13']['cases']==13 and not proof['old_six_controller_byte_identity_reuse_claimed'] and proof['fresh_controller_six_dependencies']['position/mtf_xyz_hold_control.v']==expected['position/mtf_xyz_hold_control.v']
checks['v22_22_actual_successful_receipts']=len(proof['fresh_actual_exit_receipts'])==22 and all(sha(Path(x['path']))==x['sha256'] and read(Path(x['path']))[x['normal_field']] and read(Path(x['path']))[x['actual_wait_field']]==0 for x in proof['fresh_actual_exit_receipts'])
checks['v22_components_and_no_new_cycle']=proof['guard_binding_sha256']==sha(STANDARD/'COMPONENT_REUSE_BINDING.json') and proof['new_state_bits']==0 and proof['legacy_public_output_cycle_change']==0
checks['unchanged_bound_inputs']=all(sha(Path(p))==h for p,h in binding['validation']['bound_inputs'].items())
checks['actual_local_hint_effect_bound']=sha(R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01/verification/local_hint_effect_audit.json')==read(O/'PHYSICAL_PREPARATION.json')['local_hint_effect_audit_sha256']
checks['fan100_sealed_donor']=read(O/'SYNTHESIS_RESULT.json')['passed_SYN_only'] and read(O/'SYNTHESIS_RESULT.json')['netlist_sha256']=='bf2c2de81c82f16bd3c0badd8790aa0a4c216ad9bf8273bbcd1e79a3f997508e'
checks['actual_exact_int_vendor_runner0']=all(j.get('normal_wait_return') is True and type(j.get('actual_p_wait')) is int and j['actual_p_wait']==0 for j in [vendor,runner])
tcl=(A/'physical.tcl').read_text()
checks['fan100_effective_recipe']=re.findall(r'^set_option -max_fanout\s+(\S+)\s*$',tcl,re.M)==['100'] and re.findall(r'^set_option -global_freq\s+(\S+)\s*$',tcl,re.M)==['50'] and 'run syn' not in tcl and tcl.count('run pnr\n')==1
log=(V/'physical.log').read_text(errors='replace'); files={str(p.relative_to(R)):sha(p) for p in [V/'physical.log',V/'physical_exit.json',report/'runner_exit.json']}
checks['raw_log_hash']=sha(V/'physical.log')==vendor['log_sha256']
checks['normal_eof']='PHYSICAL_COMMAND_RETURNED_EOF' in log
checks['fullroute_and_bitstream']='Placement and routing completed' in log and 'Bitstream generation completed' in log
checks['no_unrouted_nets']=not any(int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log,re.I))
checks['netlist_only']='Skip synthesis, because there is only one netlist file' in log
base=S/'impl/pnr/acg720_ano_port'
slacks={}; endpoints={}; clock=None; fmax=None; worst_setup=None
if base.with_suffix('.tr').is_file():
    tr=base.with_suffix('.tr'); text=tr.read_text(errors='replace')
    core=text[text.index('Note:Core Timing Report'):]
    headings=['3.1.1 Setup Paths Table','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type']
    for i,name in enumerate(['setup','hold','recovery','removal','minimum_pulse_width']):
        section=core.split(headings[i],1)[1].split(headings[i+1],1)[0]
        rows=[line.split() for line in section.splitlines() if re.match(r'^\s*\d+\s+-?\d+\.\d+\s+',line)]
        assert rows,(name,'empty raw table')
        values=[float(row[1]) for row in rows]
        slacks[name]=min(values)
        if name=='setup':worst_setup=min(rows,key=lambda x:float(x[1]))
    for kind in ['Setup','Hold']:
        endpoints[kind.lower()]=int(core.split(f'<Numbers of {kind} Violated Endpoints>:',1)[1].splitlines()[0])
    clockrows=[line.split() for line in core.split('2.2 Clock Summary',1)[1].split('2.3 Max Frequency Summary',1)[0].splitlines() if line.strip().startswith('1 ')]
    assert len(clockrows)==1 and clockrows[0][1:3]==['clk50','Base']
    clock=float(clockrows[0][3]); checks['period20']=clock==20.0
    frequencyrows=[line.split() for line in core.split('2.3 Max Frequency Summary',1)[1].split('2.4 Total Negative Slack Summary',1)[0].splitlines() if line.strip().startswith('1 ')]
    assert len(frequencyrows)==1 and frequencyrows[0][1]=='clk50'
    constraint=float(frequencyrows[0][2].replace('(MHz)','')); fmax=float(frequencyrows[0][3].replace('(MHz)',''))
    checks['constraint50_and_fmax50']=constraint==50.0 and math.isfinite(fmax) and fmax>=50.0
    checks['five_slacks_nonnegative']=all(math.isfinite(v) and v>=0 for v in slacks.values())
    checks['setup_hold_zero']=endpoints=={'setup':0,'hold':0}
    files[str(tr.relative_to(R))]=sha(tr)
else:checks['raw_TR_exists']=False

needed=[base.with_suffix(ext) for ext in ['.rpt.txt','.fs','.pr']]+[base.parent/'device.cfg']
checks['physical_artifacts']=all(p.is_file() for p in needed)
pins={}
if checks['physical_artifacts']:
    for line in needed[0].read_text(errors='replace').splitlines():
        fields=[x.strip() for x in line.split('|')]
        if len(fields)>5 and fields[3]=='Y' and fields[4] in ['in','out']:
            pins[fields[0]]=[fields[2].split('/')[0],fields[4]]
    expected_pins={m[0]:m[1] for m in re.findall(r'IO_LOC\s+"([^"]+)"\s+([A-Z]\d+)\s*;', (S/'acg720_ano_port.cst').read_text())}
    inputs={'clk50','imu_miso','rc_ppm_in','range_rx','radio_rx'}
    checks['pins18_all_directions']=len(pins)==len(expected_pins)==18 and pins=={n:[p,'in' if n in inputs else 'out'] for n,p in expected_pins.items()}
    header=needed[1].open('rb').read(4096).decode('ascii',errors='replace')
    checks['FS_B4']='usercode: 0x0000b0b4' in header.lower()
    checks['cfg_B4']='set user_code = 0x0000b0b4' in needed[3].read_text().lower()
    for p in needed:files[str(p.relative_to(R))]=sha(p)
sdc=(S/'acg720_ano_port.sdc').read_text()
commands=[line.strip() for line in sdc.splitlines() if line.strip() and not line.lstrip().startswith('#')]
checks['unchanged_constraints']=commands==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]','set_false_path -from [get_ports {radio_rx}]']
out=report/'INDEPENDENT_RAW_REVIEW.json';assert not out.exists()
out.write_text(json.dumps({'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Direct independent parsing of raw reports, actual exits, source and bitstream. No imported gate parser.',
    'passed':all(checks.values()),'checks':checks,'period_ns':clock,'fmax_mhz':fmax,'slacks_ns':slacks,
    'violated_endpoints':endpoints,'worst_setup_row':worst_setup,'pins':pins,'raw_sha256':files,
    'review_script_sha256':sha(Path(__file__))},indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':all(checks.values()),'failed':[k for k,v in checks.items() if not v],
    'fmax_mhz':fmax,'slacks_ns':slacks,'violated_endpoints':endpoints,'worst_setup':worst_setup},indent=2))
