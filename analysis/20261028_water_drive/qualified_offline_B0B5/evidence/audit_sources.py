"""Bounded source/constraint review. Never reads unrelated evidence or secrets."""
from pathlib import Path
import argparse, gzip, hashlib, json, re, sys, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
SRC=ROOT/'candidate/source'
BASE=REPO/'firmware/B0B4/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def audit(source=None):
    SRC=Path(source).resolve() if source else ROOT/'candidate/source'
    baseline=json.loads((ROOT/'candidate/BASELINE.json').read_text())['source_sha256']
    assert len(baseline)==55
    for name,h in baseline.items():assert sha(BASE/name)==h,('frozen source changed',name)
    current={p.relative_to(SRC).as_posix():sha(p) for p in SRC.rglob('*') if p.is_file()}
    changes=sorted(n for n in baseline if baseline[n]!=current[n])
    additions=sorted(set(current)-set(baseline))
    assert additions==['water_drive_control.v','water_pwm_pair.v']
    expected_changes=['acg720_ano_port.cst','acg720_ano_port.gprj','acg720_ano_port.v','build.tcl','core/flight_core.v','xy_pi_parameters.v']
    mtf_cached='sensor/mtf01p_reader.v' in changes
    mtf_flow_cached=False
    height_bounded_cofactor='mtf_xyz_navigation_control.v' in changes or 'position/mtf_shared_height_fusion.v' in changes
    if height_bounded_cofactor:expected_changes.extend(['mtf_xyz_navigation_control.v','position/mtf_shared_height_fusion.v'])
    if mtf_cached:expected_changes.append('sensor/mtf01p_reader.v')
    assert changes==sorted(expected_changes),changes
    if mtf_cached:
        mtf=(SRC/'sensor/mtf01p_reader.v').read_text()
        mtf_flow_cached='payload_flow_ok_q' in mtf
        if mtf_flow_cached:
            flow_replacements=[
                ('output wire payload_range_ok,payload_flow_ok,','output wire payload_range_ok,'),
                ('assign payload_range_ok=payload_range_ok_q;\n (* syn_preserve=1 *) reg payload_flow_ok_q=0;\n assign payload_flow_ok=payload_flow_ok_q;','assign payload_range_ok=payload_range_ok_q;'),
                ("wire next_payload_range_ok=next_raw_frame[87:80]==8'd1 && next_distance_mm>=32'd10 && next_distance_mm<=32'd12000;\n wire next_payload_flow_ok=next_payload_range_ok && next_distance_mm>=32'd80 && next_raw_frame[31:24]==8'd1 && next_raw_frame[39:32]!=8'd0;","wire next_payload_range_ok=next_raw_frame[87:80]==8'd1 && next_distance_mm>=32'd10 && next_distance_mm<=32'd12000;"),
                ('raw_frame<=0;payload_range_ok_q<=0;payload_flow_ok_q<=0;','raw_frame<=0;payload_range_ok_q<=0;'),
                ('raw_frame<=next_raw_frame;payload_range_ok_q<=next_payload_range_ok;payload_flow_ok_q<=next_payload_flow_ok;','raw_frame<=next_raw_frame;payload_range_ok_q<=next_payload_range_ok;'),
                ('module mtf_metric_observer #(parameter integer PRECHECKED_RANGE=0,PRECHECKED_FLOW=0)(','module mtf_metric_observer #(parameter integer PRECHECKED_RANGE=0)('),
                ('input wire payload_range_ok,payload_flow_ok,','input wire payload_range_ok,'),
                ('assign flow_numeric_ok=PRECHECKED_FLOW ? (link_fresh && payload_flow_ok) :\n  (range_numeric_ok && distance_mm>=80 && flow_status==1 && quality!=0);','assign flow_numeric_ok=range_numeric_ok && distance_mm>=80 && flow_status==1 && quality!=0;'),
                ('wire sample_valid,payload_range_ok,payload_flow_ok;','wire sample_valid,payload_range_ok;'),
                ('.raw_frame(raw_frame),.payload_range_ok(payload_range_ok),.payload_flow_ok(payload_flow_ok),.time_ms(time_ms)','.raw_frame(raw_frame),.payload_range_ok(payload_range_ok),.time_ms(time_ms)'),
                ('mtf_metric_observer #(.PRECHECKED_RANGE(1),.PRECHECKED_FLOW(1)) metric','mtf_metric_observer #(.PRECHECKED_RANGE(1)) metric'),
                ('.payload_range_ok(payload_range_ok),.payload_flow_ok(payload_flow_ok),\n  .time_ms(time_ms)','.payload_range_ok(payload_range_ok),\n  .time_ms(time_ms)'),
            ]
            for candidate,original in flow_replacements:
                assert mtf.count(candidate)==1,candidate;mtf=mtf.replace(candidate,original)
        replacements=[
            ('output reg sample_valid=0,output reg [215:0] raw_frame=0,\n output wire payload_range_ok,','output reg sample_valid=0,output reg [215:0] raw_frame=0,'),
            ('''reg [215:0] shift=0;
 (* syn_preserve=1 *) reg payload_range_ok_q=0;
 assign payload_range_ok=payload_range_ok_q;
 // Cache the exact existing range predicate on the SAME accepted-frame edge.
 // Data, predicate, reset and hold ownership all remain in this parser.
 wire [215:0] next_raw_frame={shift[207:0],byte_data};
 wire [31:0] next_distance_mm={next_raw_frame[111:104],next_raw_frame[119:112],next_raw_frame[127:120],next_raw_frame[135:128]};
 wire next_payload_range_ok=next_raw_frame[87:80]==8'd1 && next_distance_mm>=32'd10 && next_distance_mm<=32'd12000;''','reg [215:0] shift=0;'),
            ('raw_frame<=0;payload_range_ok_q<=0;','raw_frame<=0;'),
            ("samples<=samples+1'b1;sample_valid<=1;raw_frame<=next_raw_frame;payload_range_ok_q<=next_payload_range_ok;","samples<=samples+1'b1;sample_valid<=1;raw_frame<={shift[207:0],byte_data};"),
            ('module mtf_metric_observer #(parameter integer PRECHECKED_RANGE=0)(','module mtf_metric_observer('),
            ('input wire clk,rst_n,sample_valid,link_fresh,\n input wire payload_range_ok,','input wire clk,rst_n,sample_valid,link_fresh,'),
            ('assign range_numeric_ok=link_fresh && (PRECHECKED_RANGE ? payload_range_ok :\n  (tof_status==1 && distance_mm>=10 && distance_mm<=12000));','assign range_numeric_ok=link_fresh && tof_status==1 && distance_mm>=10 && distance_mm<=12000;'),
            ('wire sample_valid,payload_range_ok;wire [215:0] raw_frame;','wire sample_valid;wire [215:0] raw_frame;'),
            ('.sample_valid(sample_valid),.raw_frame(raw_frame),.payload_range_ok(payload_range_ok),.time_ms(time_ms)','.sample_valid(sample_valid),.raw_frame(raw_frame),.time_ms(time_ms)'),
            ('mtf_metric_observer #(.PRECHECKED_RANGE(1)) metric(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh || sample_valid),\n  .payload_range_ok(payload_range_ok),','mtf_metric_observer metric(.clk(clk),.rst_n(rst_n),.sample_valid(sample_valid),.link_fresh(link_fresh || sample_valid),')]
        for candidate,original in replacements:
            assert mtf.count(candidate)==1,candidate;mtf=mtf.replace(candidate,original)
        assert mtf==(BASE/'sensor/mtf01p_reader.v').read_text(),'unexpected MTF arithmetic/protocol/threshold/publication change'
    if height_bounded_cofactor:
        navigation=(SRC/'mtf_xyz_navigation_control.v').read_text()
        specialized='.RANGE_AGE_PRECHECKED(1),.PRECHECKED_AZ_RANGE(PRECHECKED_AZ_RANGE),.REF_HEIGHT_BOUNDED(1)) height_fusion('
        original='.RANGE_AGE_PRECHECKED(1),.PRECHECKED_AZ_RANGE(PRECHECKED_AZ_RANGE)) height_fusion('
        assert navigation.count(specialized)==1
        assert navigation.replace(specialized,original)==(BASE/'mtf_xyz_navigation_control.v').read_text()
        fusion=(SRC/'position/mtf_shared_height_fusion.v').read_text()
        marker='parameter integer RANGE_AGE_PRECHECKED=0,PRECHECKED_AZ_RANGE=0,REF_HEIGHT_BOUNDED=0'
        assert fusion.count(marker)==1;fusion=fusion.replace(marker,'parameter integer RANGE_AGE_PRECHECKED=0,PRECHECKED_AZ_RANGE=0')
        cached=" // Opt-in caller guarantees geometry publication is always 0..5000,\n // including initial/reset/hold states. Other callers retain both live bounds.\n wire ref_height_numeric_ok=REF_HEIGHT_BOUNDED ? 1'b1:(ref_height_mm>=0 && ref_height_mm<=5000);\n"
        assert fusion.count(cached)==1;fusion=fusion.replace(cached,'')
        assert fusion.count('ref_height_numeric_ok')==2
        fusion=fusion.replace('ref_height_numeric_ok','ref_height_mm>=0 && ref_height_mm<=5000')
        assert fusion==(BASE/'position/mtf_shared_height_fusion.v').read_text(),'unexpected fusion arithmetic/FSM/ROM/publication change'
        producer=(SRC/'sensor/mtf_shared_geometry.v').read_text()
        assert sha(SRC/'sensor/mtf_shared_geometry.v')==baseline['sensor/mtf_shared_geometry.v']
        assert re.findall(r'\bheight_mm<=([^;]+);',producer)==['0','pending_height[31:0]']
        assert 'output reg signed [31:0] height_mm=0' in producer
        assert 'pending_height<0 || pending_height>5000' in producer
    tcl=(BASE/'build.tcl').read_text().replace('0000B0B4','0000B0B5')
    current_tcl=(SRC/'build.tcl').read_text()
    place=int(re.search(r'^set_option -place_option (\d+)$',current_tcl,re.M)[1])
    route=int(re.search(r'^set_option -route_option (\d+)$',current_tcl,re.M)[1])
    assert (place,route) in ((3,0),(2,0),(3,1),(1,0),(4,0))
    checkpoint_line='set_option -inc_pnr ../physical_checkpoint/B0B4.pr\n'
    incremental=checkpoint_line in current_tcl
    if incremental:
        assert current_tcl.count(checkpoint_line)==1
        checkpoint=ROOT/'candidate/physical_checkpoint/B0B4.pr'
        expected_checkpoint=gzip.decompress((REPO/'firmware/B0B4/evidence/selected/acg720_ano_port.pr.gz').read_bytes())
        assert checkpoint.read_bytes()==expected_checkpoint
    assert current_tcl.replace(checkpoint_line,'').replace(f'set_option -place_option {place}','set_option -place_option 3').replace(f'set_option -route_option {route}','set_option -route_option 0')==tcl
    params=(BASE/'xy_pi_parameters.v').read_text().replace("32'h0000b0b4","32'h0000b0b5")
    assert (SRC/'xy_pi_parameters.v').read_text()==params
    gprj=(BASE/'acg720_ano_port.gprj').read_text().replace('<File path="core/control_gate.v"','<File path="water_drive_control.v" type="file.verilog" enable="1"/>\n<File path="water_pwm_pair.v" type="file.verilog" enable="1"/>\n<File path="core/control_gate.v"')
    assert (SRC/'acg720_ano_port.gprj').read_text()==gprj
    assert sha(SRC/'acg720_ano_port.sdc')==baseline['acg720_ano_port.sdc']
    old=(BASE/'acg720_ano_port.cst').read_text();new=(SRC/'acg720_ano_port.cst').read_text()
    assert new.startswith(old)
    oldpins=dict(re.findall(r'IO_LOC "([^"]+)" (\w+);',old))
    pins=dict(re.findall(r'IO_LOC "([^"]+)" (\w+);',new))
    assert len(oldpins)==18 and len(pins)==20 and len(set(pins.values()))==20
    assert {n:pins[n] for n in oldpins}==oldpins
    core=(SRC/'core/flight_core.v').read_text()
    # Reverse exactly the allowed adapter edits. The entire remaining core
    # must match frozen B0B4, including all control, gain, protection and PWM code.
    restored=core.replace('    output wire water_left_pwm,water_right_pwm,\n','')
    start=restored.index('    wire flight_permitted,water_mode,water_enabled,water_neutral,water_rc_fresh;')
    end=restored.index('    rc_ppm receiver',start)
    restored=restored[:start]+restored[end:]
    restored=restored.replace(' && !land_lock && flight_permitted)',' && !land_lock)')
    restored=restored.replace('wire live_armed_conditions=flight_permitted && installation_verified','wire live_armed_conditions=installation_verified')
    restored=restored.replace('    // Mode inhibition enters the qualified gate. The arbiter can inhibit only\n    // while CH5 is low and armed_raw=0; gate cannot arm while inhibited.\n    // Thus !flight_permitted implies !armed_raw on every reachable edge.\n','')
    restored=restored.replace('assign parameter_write_safe=water_neutral && !water_enabled && !parameter_arm_intent','assign parameter_write_safe=!parameter_arm_intent')
    assert restored==(BASE/'core/flight_core.v').read_text(),'unexpected flight core change'
    top=(SRC/'acg720_ano_port.v').read_text()
    top=top.replace('output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm,\n output wire water_left_pwm,water_right_pwm\n','output wire motor1_pwm,motor2_pwm,motor3_pwm,motor4_pwm\n')
    top=top.replace('  .water_left_pwm(water_left_pwm),.water_right_pwm(water_right_pwm),\n','')
    assert top==(BASE/'acg720_ano_port.v').read_text(),'unexpected top change'
    project=ET.parse(SRC/'acg720_ano_port.gprj')
    assert project.find('Device').attrib['pn']=='GW5AT-LV60PG484AC1/I0'
    for f in project.findall('.//File'):assert (SRC/f.attrib['path']).is_file()
    divider=re.search(r'parameter integer TIMER_DIVISOR=(\d+)',(SRC/'water_drive_control.v').read_text())
    timer_contract=None
    if divider:
        assert int(divider[1])==50000
        timer_contract=dict(clock_hz=50000000,divider_clocks=50000,freshness_min_cycles=4950001,freshness_max_cycles=5000000,
            low_min_cycles=25000000,low_max_cycles=25050000,high_min_cycles=25000000,high_max_cycles=25050000,
            mode_min_cycles=1250000,mode_max_cycles=1300001,fault_checks_every_clock=True,
            scope='Timer bounds from control-domain sampling/eligibility; mode upper bound includes one request observation clock; upstream RC decode latency is separate.')
    return dict(passed=True,frozen_source55_unchanged=True,unchanged_baseline_file_count=55-len(changes),
        changed_files=changes,new_files=additions,source_sha256=current,original18_io_preserved=True,
        original_sdc_byte_identical=True,no_new_timing_exceptions=True,physical_options=dict(place=place,route=route,incremental=incremental),
        core_restoration_to_B0B4_exact=True,top_restoration_to_B0B4_exact=True,mtf_same_cycle_predicate_cache=mtf_cached,mtf_same_cycle_flow_cache=mtf_flow_cached,mtf_restoration_to_B0B4_exact=True,
        bounded_height_reference_cofactor=height_bounded_cofactor,navigation_restoration_to_B0B4_exact=True,height_fusion_restoration_to_B0B4_exact=True,
        water_timer_contract=timer_contract,
        retained='All baseline numerical computations, gains, gate/flight FSMs, motor PWM and arithmetic publication cycles; predicate caches/cofactor only under explicit producer contracts',
        changed_behavior='Water mode selection/interlock and parameter write permission during water pulses; B0B5 identity',
        hardware_qualified=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',nargs='?',type=Path);parser.add_argument('--source',type=Path)
    args=parser.parse_args();result=audit(args.source)
    if args.output:args.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
