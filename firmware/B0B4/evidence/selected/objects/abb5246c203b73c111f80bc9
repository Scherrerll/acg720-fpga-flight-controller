"""Build an immutable B0B4 copy; no serial, programmer, service, or Git operations."""
from pathlib import Path
import collections
import datetime
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
CANON = REPO / 'firmware/B0B4/source'
ATTEMPT = REPO / 'out/z_aw_fix_20261026/build_attempt_01'
SOURCE = ATTEMPT / 'source'
VERIFY = ATTEMPT / 'verification'
GOWIN = Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')
IVERILOG = REPO.parents[1] / '.tools/iverilog/app/bin/iverilog.exe'
PRIMITIVES = GOWIN.parents[1] / 'simlib/gw5a/prim_sim.v'
RUNTIME = REPO.parents[1] / 'runtime_xy_pi_20261026'
GRAPH_READER = RUNTIME / 'tools/read_cones.py'
EXPECTED_CHANGES = {
    'position/mtf_xyz_hold_control.v': '5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c',
    'xy_pi_parameters.v': 'c7333f8d629a8eed60f0d0a1c042536ffb92eab753d23daee03bcfbdef306392',
    'build.tcl': 'ae4e19024a4869bb0665311dd56589014f1ca0aff123c9cc5c02e441200e17a4',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, data):
    (VERIFY / name).write_text(json.dumps(data, indent=2), encoding='utf8')


def check_sources(expected):
    for rel, digest in expected.items():
        assert sha(CANON / rel) == digest, ('canonical changed; obsolete build', rel)
        assert sha(SOURCE / rel) == digest, ('build input changed', rel)


def run_phase(name, command, cwd, expected):
    check_sources(expected)
    log = VERIFY / f'{name}.log'
    receipt = dict(stage=name, command=command, cwd=str(cwd), started_utc=utc(),
                   stdin='DEVNULL', create_no_window=True, log=str(log), runner_sha256=sha(Path(__file__)))
    with log.open('wb') as output:
        proc = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=output,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
        receipt.update(parent_pid=os.getpid(), pid=proc.pid)
        write(f'{name}_process.json', receipt)
        print(f'{name} PID {proc.pid}; log {log}', flush=True)
        code = proc.wait()
    receipt.update(ended_utc=utc(), actual_p_wait=code, normal_wait_return=True, log_sha256=sha(log))
    write(f'{name}_exit.json', receipt)
    print(f'{name} actual p.wait()={code}', flush=True)
    assert code == 0, (name, 'nonzero real process exit', code, str(log))
    check_sources(expected)
    return receipt


def mapped_audit(vg, expected):
    spec = importlib.util.spec_from_file_location('b4_build_graph', GRAPH_READER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    graph = module.Graph(vg)
    same = lambda a,b: graph.find(a) == graph.find(b)
    clk = [(n,c) for n,c in graph.cells.items() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
    assert len(clk)==1
    clocknet=clk[0][1]['pins']['O'][0]
    grounds={graph.find(net) for c in graph.cells.values() if c['type']=='GND' for net in c['pins']['G']}
    clocks=[(n,pin,net) for n,c in graph.cells.items() for pin,nets in c['pins'].items()
            if pin in ('CLK','CLKA','CLKB','WCLK','RCLK') for net in nets]
    bad=[x for x in clocks if not same(x[2],clocknet) and graph.find(x[2]) not in grounds]
    assert not bad, ('non-clk50 clock pins',bad[:10])
    loads=collections.defaultdict(list)
    for n,c in graph.cells.items():
        for pin,nets in c['pins'].items():
            if pin not in ('Q','F','O','G','V','SUM','COUT'):
                for net in nets: loads[graph.find(net)].append((n,pin,c['type']))
    rx=[(n,c) for n,c in graph.cells.items() if c['type']=='IBUF' and c['pins'].get('I')==['radio_rx']]
    assert len(rx)==1
    padloads=loads[graph.find(rx[0][1]['pins']['O'][0])]
    assert {n for n,p,t in padloads}=={'parameter_uart/rx_meta_s0','parameter_uart/rx_meta_s1'}
    assert all(p=='D' and t.startswith('DFF') for n,p,t in padloads)
    meta=graph.cells['parameter_uart/rx_meta_s1']; sync=graph.cells['parameter_uart/rx_sync_s1']
    assert same(meta['pins']['Q'][0],sync['pins']['D'][0])
    metaloads=loads[graph.find(meta['pins']['Q'][0])]
    assert {n for n,p,t in metaloads}=={'parameter_uart/rx_sync_s0','parameter_uart/rx_sync_s1'}
    assert all(p=='D' for n,p,t in metaloads)
    sdc=(SOURCE/'acg720_ano_port.sdc').read_text()
    assert re.findall(r'^create_clock.*$',sdc,re.M)==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]']
    assert re.findall(r'^set_false_path.*$',sdc,re.M)==['set_false_path -from [get_ports {radio_rx}]']
    xml=SOURCE/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    def resources(p):
        result={}
        def walk(node,prefix=''):
            name=prefix+node.attrib['name']; result[name]={k:int(re.match(r'\d+',v)[0]) for k,v in node.attrib.items() if k.startswith('T_')}
            for child in node:walk(child,name+'/')
        walk(ET.parse(p).getroot()); return result
    baseline=RUNTIME/'candidates/idle_gain_integral_ce/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    reference=resources(baseline); current=resources(xml)
    selected=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    comparison={n:dict(baseline=reference[n],candidate=current[n],delta={k:current[n].get(k,0)-reference[n].get(k,0) for k in reference[n].keys()|current[n].keys()}) for n in selected}
    out=dict(passed=True,source_sha256=expected,netlist_sha256=sha(vg),resource_xml_sha256=sha(xml),
        graph_reader_sha256=sha(GRAPH_READER),reference_resources_sha256=sha(baseline),resources=comparison,
        clock_pin_count=len(clocks),mapped_ff_count=len(graph.regs),non_clk50_non_ground=[],
        radio_pad_loads=padloads,radio_meta_q_loads=metaloads,only_false_path='radio_rx pad -> first synchronizer D; Q paths stay timed')
    write('mapped_audit.json',out)
    print(json.dumps(dict(mapped_audit_pass=True,resources=comparison),indent=2),flush=True)


def physical_audit(vg_sha, expected):
    base=SOURCE/'impl/pnr/acg720_ano_port'
    tr=base.with_suffix('.tr'); rpt=base.with_suffix('.rpt.txt'); fs=base.with_suffix('.fs')
    pr=base.with_suffix('.pr'); cfg=base.parent/'device.cfg'
    for p in (tr,rpt,fs,pr,cfg):assert p.is_file(),('missing physical artifact',str(p))
    text=tr.read_text(errors='replace'); report=rpt.read_text(errors='replace'); log=(VERIFY/'physical.log').read_text(errors='replace')
    def section(start,end):
        m=re.search(r'^'+re.escape(start)+r'\s*$(.*?)^'+re.escape(end),text,re.S|re.M); assert m,('missing raw timing table',start); return m[1]
    checks={}
    for name,start,end in [('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table'),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table'),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table')]:
        rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',section(start,end),re.M)
        assert rows,('empty timing table',name)
        checks[name]=dict(worst_slack_ns=min(float(r[1])for r in rows),reported_paths=len(rows),worst_path=rows[0])
    rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+?)\s+(clk50)\s+(\S+)\s*$',section('3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type'),re.M)
    assert rows
    checks['minimum_pulse_width']=dict(worst_slack_ns=min(float(r[1])for r in rows),reported_paths=len(rows),worst_path=rows[0])
    clock=re.search(r'^\s+1\s+clk50\s+Base\s+(\d+\.\d+)\s+',text,re.M)
    fmax=re.search(r'^\s+1\s+clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',text,re.M)
    assert clock and fmax
    setup=int(re.search(r'<Numbers of Setup Violated Endpoints>:(\d+)',text)[1]); hold=int(re.search(r'<Numbers of Hold Violated Endpoints>:(\d+)',text)[1])
    expected_pins=dict(re.findall(r'IO_LOC\s+"([^"]+)"\s+(\w+)\s*;',(SOURCE/'acg720_ano_port.cst').read_text()))
    pins={m[1]:(m[2],m[3])for m in re.finditer(r'^\s*(\w+)\s*\|[^|]*\|\s*(\w+)/\d+\s*\|\s*Y\s*\|\s*(in|out)\s*\|',report,re.M)}
    header=fs.open('rb').read(4096).decode('ascii',errors='replace')
    unrouted=[int(x)for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log+report,re.I)]
    criteria=dict(actual_period_20ns=float(clock[1])==20, fmax_at_least_50=math.isfinite(float(fmax[2])) and float(fmax[2])>=50,
        setup_hold_endpoints_zero=setup==hold==0,all_five_nonnegative=all(math.isfinite(c['worst_slack_ns'])and c['worst_slack_ns']>=0 for c in checks.values()),
        full_route='Placement and routing completed' in log and 'Bitstream generation completed' in log and not any(unrouted),
        physical_command_returned='PHYSICAL_COMMAND_RETURNED_EOF' in log,only_new_vg=sha(SOURCE/'impl/gwsynthesis/acg720_ano_port.vg')==vg_sha,
        skip_synthesis='Skip synthesis, because there is only one netlist file' in log,
        pins18=len(expected_pins)==len(pins)==18 and {n:x[0]for n,x in pins.items()}==expected_pins and pins.get('radio_rx')==('B16','in')and pins.get('radio_tx')==('B15','out'),
        fs_usercode_b4=bool(re.search(r'UserCode:\s*0x0000b0b4\b',header,re.I)),
        cfg_usercode_b4=bool(re.search(r'set user_code = 0x0000B0B4\b',cfg.read_text(),re.I)))
    evidence=[tr,rpt,fs,pr,cfg,SOURCE/'acg720_ano_port.sdc',SOURCE/'acg720_ano_port.cst',SOURCE/'physical.gprj',SOURCE/'impl/gwsynthesis/acg720_ano_port.vg',VERIFY/'physical.log',VERIFY/'physical_exit.json',ATTEMPT/'physical.tcl']
    out=dict(passed=all(criteria.values()),criteria=criteria,period_ns=float(clock[1]),fmax_mhz=float(fmax[2]),checks=checks,
        setup_violated_endpoints=setup,hold_violated_endpoints=hold,unrouted_reports=unrouted,pins=pins,
        source_sha256=expected,evidence_sha256={str(p.relative_to(ATTEMPT)):sha(p)for p in evidence})
    write('physical_audit.json',out)
    assert out['passed'],('physical qualification failed',criteria,str(VERIFY/'physical_audit.json'))
    return out


def main():
    assert not ATTEMPT.exists(), 'Use a new attempt; never overwrite build evidence'
    baseline=json.loads((REPO/'firmware/B0B3/qualification.json').read_text())['source_sha256']
    expected={p.relative_to(CANON).as_posix():sha(p)for p in CANON.rglob('*')if p.is_file()}
    assert len(expected)==55 and expected.keys()==baseline.keys()
    assert {n:expected[n]for n in expected if expected[n]!=baseline[n]}==EXPECTED_CHANGES
    SOURCE.parent.mkdir(parents=True); shutil.copytree(CANON,SOURCE); VERIFY.mkdir()
    tmp=VERIFY/'tmp';tmp.mkdir(); os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    assert IVERILOG.is_file() and PRIMITIVES.is_file()
    write('build_input.json',dict(started_utc=utc(),canonical_source=str(CANON),source_directory=str(SOURCE),source_sha256=expected,
        baseline_B3_source_sha256=baseline,changed_source_sha256=EXPECTED_CHANGES,runner_sha256=sha(Path(__file__)),
        tools={str(p):sha(p)for p in (GOWIN,IVERILOG,PRIMITIVES,GRAPH_READER)},
        physical_options=dict(place=3,route=0,map_option=2,replicate_resources=0),usercode='0000B0B4',a591_feature='0000B0B4'))
    check_sources(expected)
    project=ET.parse(SOURCE/'acg720_ano_port.gprj')
    files=[f.attrib['path']for f in project.findall('.//File')if f.attrib.get('type')=='file.verilog'and f.attrib.get('enable')=='1']
    run_phase('elaboration',[str(IVERILOG),'-g2012','-s','acg720_ano_port','-I',str(SOURCE),'-o',str(VERIFY/'top.vvp')]+files+[str(PRIMITIVES)],SOURCE,expected)
    tcl=(SOURCE/'build.tcl').read_text(); assert tcl.count('run all')==1
    tcl='\n'.join(line for line in tcl.splitlines()if line.strip()!='exit')+'\n'
    tcl=tcl.replace('run all','run syn')+'puts SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    st=ATTEMPT/'synth_only.tcl';st.write_text(tcl,encoding='utf8')
    write('synthesis_input.json',dict(tcl_sha256=sha(st),source_sha256=expected,tool_sha256=sha(GOWIN)))
    run_phase('synthesis',[str(GOWIN),str(st)],SOURCE,expected)
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (VERIFY/'synthesis.log').read_text(errors='replace')
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg'; assert vg.is_file(); vg_sha=sha(vg)
    mapped_audit(vg,expected)
    root=project.getroot(); files=root.find('FileList');files.clear()
    for path,kind in [('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]:
        ET.SubElement(files,'File',dict(path=path,type=kind,enable='1'))
    (SOURCE/'physical.gprj').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf-8'))
    pt=ATTEMPT/'physical.tcl'; pt.write_text(tcl.replace('open_project acg720_ano_port.gprj','open_project physical.gprj').replace('run syn','run pnr').replace('SYNTHESIS_COMMAND_RETURNED_EOF','PHYSICAL_COMMAND_RETURNED_EOF'),encoding='utf8')
    write('physical_input.json',dict(source_sha256=expected,donor_netlist_sha256=vg_sha,project_sha256=sha(SOURCE/'physical.gprj'),tcl_sha256=sha(pt)))
    run_phase('physical',[str(GOWIN),str(pt)],SOURCE,expected)
    result=physical_audit(vg_sha,expected); check_sources(expected)
    write('build_result.json',dict(passed=True,scope='Physical artifact qualification only; functional qualification and hardware acceptance are separate',
        completed_utc=utc(),source_inputs_unchanged=True,source_sha256=expected,physical_audit_sha256=sha(VERIFY/'physical_audit.json'),
        netlist_sha256=vg_sha,bitstream_sha256=sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),checks=result['checks'],fmax_mhz=result['fmax_mhz']))
    print('B0B4 exact-VG P3R0 physical qualification PASS',flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if VERIFY.exists():write('build_failure.json',dict(passed=False,utc=utc(),exception=repr(exc),traceback=traceback.format_exc()))
        raise
