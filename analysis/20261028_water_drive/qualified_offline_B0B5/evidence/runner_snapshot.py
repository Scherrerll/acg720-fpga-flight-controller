"""Fresh candidate synthesis, then independent full PNR for three P7 pin pairs.

Offline only: never opens a serial port or invokes a programmer. New directories
are mandatory. All PNR variants use the exact same newly synthesized netlist.
"""
from pathlib import Path
import argparse, collections, concurrent.futures, datetime, hashlib, importlib.util
import gzip, json, math, os, re, shutil, subprocess, time, traceback
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
CANON=ROOT/'candidate/source'
GOWIN=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')
GRAPH_READER=REPO.parents[1]/'runtime_xy_pi_20261026/tools/read_cones.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
INPUT_NAMES=sorted(list(json.loads((ROOT/'candidate/BASELINE.json').read_text())['source_sha256'])+['water_drive_control.v','water_pwm_pair.v'])
def sources(p):return {n:sha(p/n) for n in INPUT_NAMES}

def run_phase(name,cmd,cwd,out):
    out.mkdir(exist_ok=True)
    temporary=out/'tmp';temporary.mkdir(exist_ok=True)
    env=dict(os.environ,TMP=str(temporary),TEMP=str(temporary),TMPDIR=str(temporary))
    log=out/(name+'.log')
    receipt=dict(command=cmd,cwd=str(cwd),started_utc=utc(),stdin='DEVNULL',create_no_window=True)
    start=time.monotonic()
    with log.open('wb') as stream:
        proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
        receipt['pid']=proc.pid;write(out/(name+'_process.json'),receipt)
        print(name,'PID',proc.pid,'log',log,flush=True)
        code=proc.wait()
    receipt.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),elapsed_s=time.monotonic()-start,log_sha256=sha(log))
    write(out/(name+'_exit.json'),receipt)
    print(name,'actual p.wait()',code,flush=True)
    assert code==0,(name,'vendor nonzero exit',code)
    return receipt

def mapped_audit(src,out):
    vg=src/'impl/gwsynthesis/acg720_ano_port.vg'
    spec=importlib.util.spec_from_file_location('water_graph',GRAPH_READER)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    graph=mod.Graph(vg)
    clock=[c for c in graph.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
    assert len(clock)==1
    net=graph.find(clock[0]['pins']['O'][0])
    grounds={graph.find(n) for c in graph.cells.values() if c['type']=='GND' for n in c['pins']['G']}
    clocks=[(n,p,x) for n,c in graph.cells.items() for p,xs in c['pins'].items() if p in ('CLK','CLKA','CLKB','WCLK','RCLK') for x in xs]
    bad=[x for x in clocks if graph.find(x[2])!=net and graph.find(x[2]) not in grounds]
    assert not bad,('unexpected clock pins',bad[:10])
    loads=collections.defaultdict(list)
    for n,c in graph.cells.items():
        for pin,ns in c['pins'].items():
            if pin not in ('Q','F','O','G','V','SUM','COUT'):
                for x in ns:loads[graph.find(x)].append((n,pin,c['type']))
    rx=[c for c in graph.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['radio_rx']]
    assert len(rx)==1
    padloads=loads[graph.find(rx[0]['pins']['O'][0])]
    assert padloads and all('parameter_uart/rx_meta' in n and p=='D' and t.startswith('DFF') for n,p,t in padloads),padloads
    follow={n:loads[graph.find(graph.cells[n]['pins']['Q'][0])] for n,p,t in padloads}
    assert any(follow.values()) and all(all('parameter_uart/rx_sync' in n and p=='D' for n,p,t in ls) for ls in follow.values()),follow
    output_drivers={}
    for port in ('water_left_pwm','water_right_pwm'):
        buffers=[c for c in graph.cells.values() if c['type']=='OBUF' and c['pins'].get('O')==[port]]
        assert len(buffers)==1,(port,'expected one output buffer')
        data=graph.find(buffers[0]['pins']['I'][0])
        drivers=[(n,c['type']) for n,c in graph.cells.items() if c['type'].startswith('DFF') and any(graph.find(q)==data for q in c['pins'].get('Q',[]))]
        assert len(drivers)==1,(port,'not directly driven by one FF',drivers)
        output_drivers[port]=drivers
    write(out/'mapped_audit.json',dict(passed=True,netlist_sha256=sha(vg),clock_pin_count=len(clocks),non_clk50_non_ground=[],radio_pad_loads=padloads,radio_meta_q_loads=follow,registered_water_output_drivers=output_drivers,graph_reader_sha256=sha(GRAPH_READER)))

def physical_audit(src,out,vg_sha):
    base=src/'impl/pnr/acg720_ano_port'
    tr=base.with_suffix('.tr');rpt=base.with_suffix('.rpt.txt');fs=base.with_suffix('.fs');cfg=base.parent/'device.cfg'
    for p in (tr,rpt,fs,cfg,base.with_suffix('.pr')):assert p.is_file(),str(p)
    text=tr.read_text(errors='replace');report=rpt.read_text(errors='replace');log=(out/'physical.log').read_text(errors='replace')
    def section(start,end):
        m=re.search(r'^'+re.escape(start)+r'\s*$(.*?)^'+re.escape(end),text,re.S|re.M)
        assert m,('missing timing table',start)
        return m[1]
    checks={}
    for name,start,end in [('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table'),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table'),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table')]:
        rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',section(start,end),re.M)
        assert rows,('empty timing table',name)
        checks[name]=dict(worst_slack_ns=min(float(r[1]) for r in rows),reported_paths=len(rows),worst_path=rows[0])
    rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+?)\s+(clk50)\s+(\S+)\s*$',section('3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type'),re.M)
    assert rows
    checks['minimum_pulse_width']=dict(worst_slack_ns=min(float(r[1]) for r in rows),reported_paths=len(rows),worst_path=rows[0])
    clock=re.search(r'^\s+1\s+clk50\s+Base\s+(\d+\.\d+)\s+',text,re.M)
    fmax=re.search(r'^\s+1\s+clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',text,re.M)
    assert clock and fmax
    setup=int(re.search(r'<Numbers of Setup Violated Endpoints>:(\d+)',text)[1]);hold=int(re.search(r'<Numbers of Hold Violated Endpoints>:(\d+)',text)[1])
    expected_pins=dict(re.findall(r'IO_LOC\s+"([^"]+)"\s+(\w+)\s*;',(src/'acg720_ano_port.cst').read_text()))
    pins={m[1]:(m[2],m[3]) for m in re.finditer(r'^\s*(\w+)\s*\|[^|]*\|\s*(\w+)/\d+\s*\|\s*Y\s*\|\s*(in|out)\s*\|',report,re.M)}
    with fs.open('rb') as stream:header=stream.read(4096).decode('ascii',errors='replace')
    unrouted=[int(x) for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log+report,re.I)]
    exit_receipt=json.loads((out/'physical_exit.json').read_text())
    criteria=dict(actual_period_20ns=float(clock[1])==20,fmax_at_least_50=math.isfinite(float(fmax[2])) and float(fmax[2])>=50,
        setup_hold_endpoints_zero=setup==hold==0,all_five_nonnegative=all(math.isfinite(c['worst_slack_ns']) and c['worst_slack_ns']>=0 for c in checks.values()),
        full_route='Placement and routing completed' in log+report and 'Bitstream generation completed' in log+report and not any(unrouted),
        physical_command_returned='PHYSICAL_COMMAND_RETURNED_EOF' in log,only_new_vg=sha(src/'impl/gwsynthesis/acg720_ano_port.vg')==vg_sha,
        skip_synthesis='Skip synthesis, because there is only one netlist file' in log,
        all20pins=len(expected_pins)==len(pins)==20 and {n:x[0] for n,x in pins.items()}==expected_pins and pins['water_left_pwm'][1]==pins['water_right_pwm'][1]=='out',
        fs_usercode_b5=bool(re.search(r'UserCode:\s*0x0000b0b5\b',header,re.I)),cfg_usercode_b5=bool(re.search(r'set user_code = 0x0000B0B5\b',cfg.read_text(),re.I)),
        actual_vendor_exit_zero=exit_receipt['normal_wait_return'] is True and exit_receipt['actual_p_wait']==0)
    pressure_lines=[x for x in (log+report).splitlines() if re.search(r'congest|overflow|wire.?length|unrouted|Total Routing|Routing Phase|^\s*Logic\s+\||Logic Register as FF',x,re.I)]
    result=dict(passed=all(criteria.values()),criteria=criteria,period_ns=float(clock[1]),fmax_mhz=float(fmax[2]),checks=checks,
        setup_violated_endpoints=setup,hold_violated_endpoints=hold,unrouted_reports=unrouted,pins=pins,pressure_report_lines=pressure_lines,
        congestion_metric='No numerical congestion metric assumed; report availability recorded verbatim',
        bitstream_sha256=sha(fs),netlist_sha256=vg_sha,evidence_sha256={str(p.relative_to(src.parent)):sha(p) for p in (tr,rpt,fs,cfg,base.with_suffix('.pr'),out/'physical.log',out/'physical_exit.json')})
    write(out/'physical_audit.json',result)
    return result

def main():
    global CANON
    parser=argparse.ArgumentParser();parser.add_argument('--name',required=True)
    parser.add_argument('--source',type=Path,default=CANON)
    parser.add_argument('--synthesis-donor',type=Path)
    parser.add_argument('--synthesis-only',action='store_true')
    parser.add_argument('--place',type=int,choices=(1,2,3,4),default=3)
    parser.add_argument('--route',type=int,choices=(0,1),default=0)
    parser.add_argument('--incremental-pr',action='store_true',help='Copy manifest-bound frozen B0B4 checkpoint; requalify the complete new implementation')
    parser.add_argument('--pins',nargs=2,metavar=('LEFT','RIGHT'),help='One additional table-verified pin pair instead of the initial three pairs')
    args=parser.parse_args();assert re.fullmatch(r'[a-z0-9_]+',args.name)
    CANON=args.source.resolve();assert CANON.is_relative_to(ROOT)
    run=REPO/'out/water_drive_20261028'/args.name
    assert not run.exists(),'fresh directory required'
    run.mkdir(parents=True)
    shutil.copy2(Path(__file__),run/'runner_snapshot.py')
    frozen=json.loads((ROOT/'candidate/BASELINE.json').read_text())['source_sha256']
    immutable={str(REPO/'firmware/B0B4/source'/rel):h for rel,h in frozen.items()}
    for rel in ('release/acg720_ano_port.fs','release_manifest.json','release_manifest.sha256','qualification.json'):
        p=REPO/'firmware/B0B4'/rel
        if p.is_file():immutable[str(p)]=sha(p)
    def check_frozen():
        for n,h in immutable.items():assert sha(Path(n))==h,('frozen B0B4 changed',n)
    check_frozen();write(run/'baseline_frozen.json',immutable)
    checkpoint=None
    if args.incremental_pr:
        archive=REPO/'firmware/B0B4/evidence/selected/acg720_ano_port.pr.gz'
        manifest=json.loads((REPO/'firmware/B0B4/release_manifest.json').read_text())
        record=next(x for x in manifest['files'] if x['path']=='firmware/B0B4/evidence/selected/acg720_ano_port.pr.gz')
        assert record['sha256']==sha(archive)
        checkpoint=gzip.decompress(archive.read_bytes())
        checkpoint_info=dict(archive_relative=record['path'],archive_sha256=sha(archive),checkpoint_sha256=hashlib.sha256(checkpoint).hexdigest(),scope='Physical checkpoint input only; no inherited timing or bitstream qualification')
        write(run/'incremental_checkpoint_input.json',checkpoint_info)
        immutable[str(archive)]=sha(archive);write(run/'baseline_frozen.json',immutable)
    expected=sources(CANON);assert len(expected)==57
    assert expected['acg720_ano_port.sdc']==frozen['acg720_ano_port.sdc']
    original_cst=(REPO/'firmware/B0B4/source/acg720_ano_port.cst').read_text()
    assert (CANON/'acg720_ano_port.cst').read_text().startswith(original_cst)
    donor=run/'synthesis';src=donor/'source';shutil.copytree(CANON,src);out=donor/'verification';out.mkdir()
    write(out/'build_input.json',dict(source_sha256=expected,tool_sha256=sha(GOWIN),runner_sha256=sha(Path(__file__)),created_utc=utc()))
    tcl=(src/'build.tcl').read_text();assert tcl.count('run all')==1
    tcl='\n'.join(x for x in tcl.splitlines() if x.strip()!='exit')+'\n'
    st=donor/'synthesis.tcl';st.write_text(tcl.replace('run all','run syn')+'puts SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n')
    if args.synthesis_donor:
        previous=args.synthesis_donor.resolve()
        assert previous.is_relative_to(REPO/'out/water_drive_20261028')
        original=json.loads((previous/'verification/build_input.json').read_text())
        exited=json.loads((previous/'verification/synthesis_exit.json').read_text())
        assert original['source_sha256']==expected==sources(previous/'source')
        assert exited['actual_p_wait']==0 and exited['normal_wait_return'] is True
        assert exited['log_sha256']==sha(previous/'verification/synthesis.log')
        assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (previous/'verification/synthesis.log').read_text(errors='replace')
        shutil.copytree(previous/'source/impl/gwsynthesis',src/'impl/gwsynthesis')
        provenance=out/'donor_provenance';provenance.mkdir()
        for name in ('build_input.json','synthesis_exit.json','synthesis_process.json','synthesis.log'):
            shutil.copy2(previous/'verification'/name,provenance/name)
        write(out/'synthesis_donor.json',dict(path=str(previous),source_sha256=expected,netlist_sha256=sha(src/'impl/gwsynthesis/acg720_ano_port.vg'),actual_vendor_exit=0,
            reason='Reuse the same revision freshly synthesized netlist only after all 57 declared source hashes and the original successful vendor exit/log match'))
    else:
        run_phase('synthesis',[str(GOWIN),str(st)],src,out)
        assert sources(src)==expected and sources(CANON)==expected
        assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (out/'synthesis.log').read_text(errors='replace')
    mapped_audit(src,out);check_frozen()
    vg=src/'impl/gwsynthesis/acg720_ano_port.vg';vg_sha=sha(vg)
    if args.synthesis_only:
        write(run/'synthesis_only.json',dict(passed=True,source_sha256=expected,netlist_sha256=vg_sha,scope='Fresh mapped synthesis only; no routing/timing qualification',hardware_actions=False))
        print('SYNTHESIS ONLY',run,flush=True)
        return
    variants=[('b18_c18',('B18','C18')),('b18_c19',('B18','C19')),('f18_f19',('F18','F19'))]
    if args.pins:
        assert all(re.fullmatch(r'[A-Z]{1,2}\d{1,2}',x) for x in args.pins)
        occupied=set(re.findall(r'IO_LOC "[^"]+" (\w+);',original_cst))
        assert len(set(args.pins))==2 and not occupied.intersection(args.pins)
        variants=[('_'.join(x.lower() for x in args.pins),tuple(args.pins))]
    def physical(variant):
        name,pair=variant;attempt=run/name;work=attempt/'source';proof=attempt/'verification'
        try:
            shutil.copytree(CANON,work);proof.mkdir()
            cst=work/'acg720_ano_port.cst';text=cst.read_text()
            text=re.sub(r'IO_LOC "water_left_pwm" \w+;',f'IO_LOC "water_left_pwm" {pair[0]};',text)
            text=re.sub(r'IO_LOC "water_right_pwm" \w+;',f'IO_LOC "water_right_pwm" {pair[1]};',text);cst.write_text(text)
            build_tcl=work/'build.tcl'
            profile_tcl=build_tcl.read_text().replace('set_option -place_option 3',f'set_option -place_option {args.place}').replace('set_option -route_option 0',f'set_option -route_option {args.route}')
            if checkpoint is not None:
                dependency=attempt/'physical_checkpoint';dependency.mkdir()
                (dependency/'B0B4.pr').write_bytes(checkpoint)
                profile_tcl=profile_tcl.replace('run all','set_option -inc_pnr ../physical_checkpoint/B0B4.pr\nrun all')
            build_tcl.write_text(profile_tcl)
            inputs=sources(work)
            copied_vg=work/'impl/gwsynthesis/acg720_ano_port.vg';copied_vg.parent.mkdir(parents=True);shutil.copy2(vg,copied_vg)
            project=ET.parse(work/'acg720_ano_port.gprj');files=project.getroot().find('FileList');files.clear()
            for path,kind in [('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]:ET.SubElement(files,'File',dict(path=path,type=kind,enable='1'))
            (work/'physical.gprj').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(project.getroot(),encoding='utf-8',xml_declaration=False))
            # Derived project is a build artifact, outside the declared source57.
            inputs=sources(work)
            physical_tcl='\n'.join(x for x in profile_tcl.splitlines() if x.strip()!='exit')+'\n'
            pt=attempt/'physical.tcl';pt.write_text(physical_tcl.replace('open_project acg720_ano_port.gprj','open_project physical.gprj').replace('run all','run pnr')+'puts PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n')
            write(proof/'build_input.json',dict(source_sha256=inputs,netlist_sha256=vg_sha,pins=pair,physical_options=dict(place=args.place,route=args.route,incremental=args.incremental_pr),incremental_checkpoint=checkpoint_info if checkpoint is not None else None,tool_sha256=sha(GOWIN),runner_sha256=sha(Path(__file__)),tcl_sha256=sha(pt)))
            run_phase('physical',[str(GOWIN),str(pt)],work,proof)
            assert sources(work)==inputs and sources(CANON)==expected
            result=physical_audit(work,proof,vg_sha);check_frozen()
            print(name,'qualified',result['passed'],'setup',result['checks']['setup']['worst_slack_ns'],flush=True)
            return dict(name=name,pins=pair,passed=result['passed'],audit=str(proof/'physical_audit.json'))
        except BaseException as exc:
            proof.mkdir(exist_ok=True,parents=True)
            failure=dict(name=name,pins=pair,passed=False,exception=repr(exc),traceback=traceback.format_exc());write(proof/'failure.json',failure)
            print(name,'FAILED',repr(exc),flush=True);return failure
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(physical,variants))
    check_frozen()
    write(run/'comparison.json',dict(completed_utc=utc(),source_sha256=expected,netlist_sha256=vg_sha,physical_options=dict(place=args.place,route=args.route,incremental=args.incremental_pr),baseline_unchanged=True,variants=results,hardware_actions=False))
    print('COMPARISON',run/'comparison.json',flush=True)
    if not any(r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':main()
