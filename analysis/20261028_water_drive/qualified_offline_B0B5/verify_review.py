"""Verify the bounded offline review package. No device access."""
from pathlib import Path
import argparse, gzip, hashlib, importlib.util, json, re
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);args=parser.parse_args()
    root=args.package.resolve();manifest=json.loads((root/'manifest.json').read_text())
    for rel,h in manifest.items():
        p=(root/rel).resolve()
        assert p.is_relative_to(root) and p.name.lower() not in ('.env','deployment.env','proof.zip')
        assert sha(p)==h,rel
    q=json.loads((root/'qualification.json').read_text())
    assert q['passed'] is True and q['hardware_qualified'] is q['installed'] is q['hardware_actions'] is False
    assert q['physical_vendor_exit']==q['synthesis_vendor_exit']==0
    assert q['period_ns']==20 and q['fmax_mhz']>=50 and min(q['timing'].values())>=0
    assert len(q['source_sha256'])==q['source_count']==57
    for n,h in q['source_sha256'].items():assert sha(root/'source'/n)==h,n
    assert sha(root/'DO_NOT_PROGRAM/acg720_ano_port.fs')==q['bitstream_sha256']
    if q.get('incremental_checkpoint'):
        assert sha(root/'physical_checkpoint/B0B4.pr')==q['incremental_checkpoint']['checkpoint_sha256']
    net=gzip.decompress((root/'evidence/acg720_ano_port.vg.gz').read_bytes())
    assert hashlib.sha256(net).hexdigest()==q['netlist_sha256']
    original=json.loads((root/'BASELINE.json').read_text())['source_sha256']
    baseline_map=json.loads((root/'evidence/baseline_changed_input_map.json').read_text())
    for name,digest in original.items():
        p=root/baseline_map[name]['packaged_path'] if name in baseline_map else root/'source'/name
        assert p.resolve().is_relative_to(root) and sha(p)==digest,('baseline source55',name)
    resources=json.loads((root/'evidence/mapped_resource_comparison.json').read_text())
    assert resources['revisions'][q['rtl_revision']]['netlist_sha256']==q['netlist_sha256']
    assert sha(root/'source/acg720_ano_port.sdc')==original['acg720_ano_port.sdc']
    assert (root/'source/build.tcl').read_text().count('set_option -user_code 0000B0B5')==1
    assert len(re.findall(r'^IO_LOC ',(root/'source/acg720_ano_port.cst').read_text(),re.M))==20
    for phase in ('physical','synthesis'):
        name='physical_exit.json' if phase=='physical' else 'synthesis_synthesis_exit.json'
        receipt=json.loads((root/'evidence'/name).read_text())
        assert receipt['actual_p_wait']==0 and receipt['normal_wait_return'] is True
        assert hashlib.sha256(gzip.decompress((root/'evidence'/(phase+'.log.gz')).read_bytes())).hexdigest()==receipt['log_sha256']
    results=json.loads((root/'evidence/functional_results.json').read_text())
    assert results['passed'] and len(results['results'])==q['functional_tests'] and q['functional_tests'] in (8,10,11,12,13)
    if q.get('rtl_revision') in ('v4','v5','v6','v7','v8'):assert all(any(x['name']==n and x['passed'] for x in results['results']) for n in ('mode_gate_invariant','water_end_to_end'))
    if q.get('rtl_revision') in ('v7','v8'):assert any(x['name']=='quantized_timer_bounds' and x['passed'] for x in results['results'])
    if q.get('rtl_revision') in ('v7','v8'):
        timing=q['water_timer_contract'];assert timing['divider_clocks']==50000 and timing['clock_hz']==50000000
        assert timing['freshness_max_cycles']<=5000000 and timing['low_min_cycles']>=25000000 and timing['high_min_cycles']>=25000000 and timing['mode_min_cycles']>=1250000
        assert timing['fault_checks_every_clock']
    if q.get('rtl_revision')=='v8':
        assert any(x['name']=='navigation_equivalence' and x['passed'] for x in results['results'])
        height=json.loads((root/'evidence/height_cofactor_audit.json').read_text())
        assert height['passed'] and height['after']['netlist_sha256']==q['netlist_sha256'] and height['after']['reachable_pin_pairs']==0
        assert hashlib.sha256(gzip.decompress((root/'evidence/cofactor_before_v7.vg.gz').read_bytes())).hexdigest()==height['before']['netlist_sha256']
        audit=json.loads((root/'evidence/source_audit.json').read_text());assert audit['bounded_height_reference_cofactor'] and audit['height_fusion_restoration_to_B0B4_exact']
    if q.get('rtl_revision') in ('v5','v6','v7','v8'):
        assert any(x['name']=='mtf_equivalence' and x['passed'] for x in results['results'])
        cache=json.loads((root/'evidence/mtf_cache_audit.json').read_text())
        assert cache['passed'] and cache['clock_reset_enable_identical'] and cache['netlist_sha256']==q['netlist_sha256']
        if q.get('rtl_revision') in ('v6','v7','v8'):assert cache['flow_cache']['clock_reset_enable_identical']
    assert all(r['passed'] for r in results['results'])
    inputs=json.loads((root/'evidence/functional_input_map.json').read_text())
    for name,record in inputs.items():
        if record['packaged_path'] is not None:
            p=(root/record['packaged_path']).resolve();assert p.is_relative_to(root)
            assert sha(p)==record['sha256'],name
        else:assert record['external_dependency'] and Path(name).name=='prim_sim.v'
    for result in results['results']:
        for name,digest in result['inputs'].items():assert inputs[name]['sha256']==digest
    response=re.search(r'RESPONSE=([0-9a-fA-F]{48})',(root/'evidence/parameter_identity.log').read_text())[1]
    spec=importlib.util.spec_from_file_location('verified_offline_b5_codec',root/'xy_pi_cli.py')
    codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    decoded=codec.decode_response(bytes.fromhex(response))
    assert (decoded['build'],decoded['p_wire'],decoded['i_wire'],decoded['generation'])==('0000B0B5',1000,350,0)
    mapped=json.loads((root/'evidence/mapped_audit.json').read_text())
    assert mapped['passed'] and set(mapped['registered_water_output_drivers'])=={'water_left_pwm','water_right_pwm'}
    assert not mapped['non_clk50_non_ground']
    print('PASS offline review package:',len(manifest),'bound files; exact source57/VG/FS, vendor exits, true 50MHz and',q['functional_tests'],'functional checks. HARDWARE NOT QUALIFIED.')

if __name__=='__main__':main()
