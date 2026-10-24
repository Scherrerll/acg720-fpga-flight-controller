"""Offline full-control resource candidate. No hardware or programming command."""
import argparse
import hashlib
import json
import re
import subprocess
import time
import datetime
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP = 'acg720_ano_port'
GW_SH = 'C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe'
PINS = {'clk50': 'Y18', 'imu_sck': 'E17', 'imu_mosi': 'C20', 'imu_miso': 'D19', 'imu_cs_n': 'E18', 'imu_gyro_cs_n': 'F20', 'rc_ppm_in': 'B17', 'uart_tx': 'M15', 'led2': 'L21', 'led3': 'K21', 'motor1_pwm': 'D17', 'motor2_pwm': 'C17', 'motor3_pwm': 'E16', 'motor4_pwm': 'D16', 'range_rx': 'C14', 'range_tx': 'C15', 'radio_tx': 'B15'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    project = HERE / (TOP + '.gprj')
    paths = re.findall(r'<File path="([^"]+)"', project.read_text(encoding='utf-8'))
    paths += [project.name, 'build.tcl']
    return {name: digest(HERE / name) for name in paths}


def static_contract():
    import sys
    sys.path.insert(0,str(HERE.parent))
    from control_contract import verify
    return verify()


def reject_connectivity_warnings(folder):
    paths=list((folder/'impl/gwsynthesis').glob('*.log'))
    if not paths:raise ValueError('Missing synthesis diagnostic log')
    for path in paths:
        text=path.read_text(encoding='utf8',errors='replace')
        if re.search(r'Undeclared symbol|EX3638|EX1998',text):
            raise ValueError('Unsafe synthesis connectivity diagnostics: '+str(path))


def synthesize_only():
    static_contract();verify_parent_synthesis_inputs();inputs=source_hashes()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=HERE.parent/'synthesis'/stamp;folder.mkdir(parents=True,exist_ok=False)
    for name in inputs:
        dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,dest)
    script=(folder/'build.tcl').read_text(encoding='utf-8')
    if script.splitlines().count('run all')!=1:raise ValueError('Expected one full-build entry')
    (folder/'synthesis_only.tcl').write_text(script.replace('run all','run syn'),encoding='utf-8')
    path=folder/'console.txt';finished=None;workaround=False
    with path.open('w',encoding='utf-8')as log:
        process=subprocess.Popen([GW_SH,'synthesis_only.tcl'],cwd=folder,stdout=log,
            stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        start=time.monotonic()
        while process.poll()is None:
            report=folder/'impl/gwsynthesis'/(TOP+'_syn_rsc.xml')
            if report.is_file()and 'GowinSynthesis finish'in path.read_text(encoding='utf-8',errors='replace'):
                if finished is None:finished=time.monotonic()
                if time.monotonic()-finished>=10:
                    ET.parse(report);process.terminate();process.wait(timeout=10);workaround=True;break
            if time.monotonic()-start>600:
                process.terminate();process.wait(timeout=10);raise RuntimeError('Synthesis-only timeout')
            time.sleep(1)
    if process.returncode and not workaround:raise RuntimeError('Synthesis failed: '+str(path))
    reject_connectivity_warnings(folder)
    if source_hashes()!=inputs:raise ValueError('Main source changed during resource study')
    if any((folder/name).is_file()and digest(folder/name)!=value for name,value in inputs.items()):
        raise ValueError('Study source changed')
    if (folder/'impl/pnr').exists():raise ValueError('Resource study must not run PNR')
    report=folder/'impl/gwsynthesis'/(TOP+'_syn_rsc.xml');prj=folder/'impl/gwsynthesis'/(TOP+'.prj')
    options={e.attrib.get('type'):e.attrib.get('value')for e in ET.parse(prj).findall('.//Option')}
    if any(options.get(k)!=v for k,v in {'map_option':'2','max_fanout':'200','opt_goal':'area'}.items())or float(options.get('global_freq','0'))!=50:
        raise ValueError('Unexpected actual synthesis options')
    node=ET.parse(report).getroot()
    counts={k:int(node.attrib.get(k,'0').split('(')[0])for k in ('T_Lut','T_Alu','T_Register','T_Bsram')}
    study=dict(passed=True,sources_sha256=inputs,folder=str(folder),resources=counts,
        logic=counts['T_Lut']+counts['T_Alu'],options=options,report_sha256=digest(report),
        options_sha256=digest(prj),script_sha256=digest(folder/'synthesis_only.tcl'),
        driver_sha256=digest(Path(__file__)),pnr_run=False,hardware_accessed=False,
        programming_authorized=False,flight_ready=False)
    (folder/'study.json').write_text(json.dumps(study,indent=2)+'\n',encoding='utf-8')
    (HERE.parent/'synthesis_study.json').write_text(json.dumps(study,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(study=str(folder/'study.json'),resources=counts,logic=study['logic']),indent=2))


def verify_parent_synthesis_inputs():
    static_contract()
    import sys
    sys.path.insert(0,str(HERE.parent))
    from inherited_context_bridge import verify
    verify()


def verify(inputs):
    import sys
    sys.path.insert(0,str(HERE.parent))
    from inherited_context_bridge import verify as verify_inherited
    verify_inherited()
    from verify_mapped_binding import verify as verify_mapped
    mapped_review=verify_mapped(HERE/'impl/gwsynthesis'/(TOP+'.vg'),inputs)
    sys.path.insert(0,str(HERE.parent/'hardware'))
    from review_synthesis_freshness import review as review_freshness
    fresh_review=review_freshness(HERE/'impl/gwsynthesis'/(TOP+'.vg'))
    (HERE.parent/'hardware/full_build_synthesis_freshness_review.json').write_text(json.dumps(fresh_review,indent=2)+'\n')
    reject_connectivity_warnings(HERE)
    if source_hashes() != inputs:
        raise ValueError('Source changed during or after the build')
    static_contract()
    tcl=(HERE/'build.tcl').read_text(encoding='utf-8')
    settings=dict(re.findall(r'^\s*set_option\s+-(\w+)\s+(\S+)\s*$',tcl,re.M))
    for key,value in {'global_freq':'50','opt_goal':'area','map_option':'2',
                      'max_fanout':'200','place_option':'2','route_option':'2','timing_driven':'1','replicate_resources':'1'}.items():
        if settings.get(key)!=value:raise ValueError('Unexpected build option: '+key)
    pnr_command_path=HERE/'impl/pnr/cmd.do'
    pnr_command=pnr_command_path.read_text(encoding='utf-8')
    actual_pnr=dict(re.findall(r'^-(\w+)\s+(\S+)\s*$',pnr_command,re.M))
    if actual_pnr.get('place_option')!='2' or actual_pnr.get('route_maxfan')!='23' or actual_pnr.get('route_option')!='2' or \
       float(actual_pnr.get('global_freq','0'))!=50 or not re.search(r'^-timing\s*$',pnr_command,re.M) or not re.search(r'^-replicate\s*$',pnr_command,re.M):
        raise ValueError('Actual PNR settings differ from frozen50MHz candidate')
    syn_options_path=HERE/'impl/gwsynthesis'/(TOP+'.prj')
    syn_resources_path=HERE/'impl/gwsynthesis'/(TOP+'_syn_rsc.xml')
    options={e.attrib.get('type'):e.attrib.get('value') for e in ET.parse(syn_options_path).findall('.//Option')}
    if options.get('map_option')!='2' or options.get('max_fanout')!='200' or \
       float(options.get('global_freq','0'))!=50 or options.get('opt_goal')!='area':
        raise ValueError('Actual synthesis settings differ from frozen50MHz candidate')
    syn=ET.parse(syn_resources_path).getroot()
    synthesis_resources={k:int(syn.attrib.get(k,'0').split('(')[0]) for k in ('T_Lut','T_Alu','T_Register','T_Bsram')}
    timing_path = HERE / 'impl/pnr' / (TOP + '.tr')
    resources_path = HERE / 'impl/pnr' / (TOP + '.rpt.txt')
    timing = timing_path.read_text(encoding='utf-8', errors='replace')
    resources = resources_path.read_text(encoding='utf-8', errors='replace')
    if re.search(r'ERROR\s*\(',resources) or re.search(r'\b[1-9][0-9]*\s+unrouted nets\b',resources):
        raise ValueError('PNR reports errors or unrouted nets')
    console=(HERE/'build_console.txt').read_text(encoding='utf-8',errors='replace')
    if re.search(r'ERROR\s*\(',console) or not all(marker in console for marker in (
        'Placement and routing completed','Bitstream generation completed')):
        raise ValueError('Compiler did not confirm complete error-free routing and bitstream')
    fmax = re.search(r'clk50\s+50\.000\(MHz\)\s+([0-9.]+)\(MHz\)', timing)
    io = re.search(r'^\s*I/O Port\s+\|\s*([0-9]+)/([0-9]+)', resources, flags=re.MULTILINE)
    if not fmax or not io or float(fmax.group(1)) < 50 or int(io.group(1)) != 17:
        raise ValueError('Timing or I/O count fails the control bench requirement')
    slack = {}
    for kind in ['setup', 'hold']:
        match = re.search(r'clk50\s+' + kind + r'\s+(-?[0-9.]+)\s+([0-9]+)', timing)
        if not match or float(match.group(1)) != 0 or int(match.group(2)) != 0:
            raise ValueError(f'{kind} timing violations or missing summary')
        slack[kind] = {'tns_ns': float(match.group(1)), 'violated_endpoints': int(match.group(2))}
    pins = dict(re.findall(r'^(\w+)\s+\|\s+-\s+\|\s+(\w+)/\d+\s+\|', resources, flags=re.MULTILINE))
    if pins != PINS:
        raise ValueError(f'Placed pins differ: {pins}')
    fs = HERE / 'impl/pnr' / (TOP + '.fs')
    with fs.open(encoding='ascii', errors='replace') as stream:
        header = ''.join(next(stream, '') for _ in range(15))
    code = re.search(r'UserCode:\s*(0x[0-9A-Fa-f]+)', header)
    if not code:
        raise ValueError('Missing bitstream UserCode')
    if int(code.group(1),16)!=0xB0B0:
        raise ValueError('Bitstream UserCode does not identify this ANO candidate')
    cls=re.search(r'^\s*CLS\s+\|\s*([0-9]+)/([0-9]+)',resources,flags=re.MULTILINE)
    if not cls:raise ValueError('Missing placed CLS resource summary')
    return {'verified': True, 'resource_timing_verified': True, 'profile': 'bmi088_mtf_ano_control_b0b0', 'physical_sensor_verified': False, 'motor_lock': False, 'flight_ready': False, 'programming_authorized':False, 'control_input': True, 'top': TOP, 'fmax_mhz': float(fmax.group(1)), 'io_count': 17,
            'motor_ports': [f'motor{i}_pwm' for i in range(1,5)], 'pins': pins, 'slack': slack, 'sources_sha256': inputs,
            'cls_used':int(cls.group(1)),'cls_total':int(cls.group(2)),'unrouted_nets':0,
            'synthesis_options':options,'synthesis_resources':synthesis_resources,'mapped_init_review':mapped_review,'synthesis_freshness_review':fresh_review,
            'artifact_sha256':{str(p.relative_to(HERE)).replace('\\','/'):digest(p) for p in
                (syn_options_path,syn_resources_path,pnr_command_path,timing_path,resources_path,HERE/'build_console.txt')},
            'bitstream': {'path': str(fs), 'sha256': digest(fs), 'user_code': code.group(1)},
            'timing_report': str(timing_path), 'resource_report': str(resources_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-existing', action='store_true')
    parser.add_argument('--synthesis-only',action='store_true')
    args = parser.parse_args()
    if args.synthesis_only:
        if args.verify_existing:parser.error('Choose only one action')
        synthesize_only();return
    manifest_path = HERE / 'build_manifest.json'
    if args.verify_existing:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if not manifest.get('verified'):
            raise ValueError('Build is not verified')
        result = verify(manifest['sources_sha256'])
        if result['bitstream'] != manifest['bitstream']:
            raise ValueError('Bitstream changed after build verification')
        if result['artifact_sha256'] != manifest.get('artifact_sha256'):
            raise ValueError('Build reports changed after verification')
    else:
        static_contract()
        inputs = source_hashes()
        init_review=json.loads((HERE.parent/'hardware/mapped_init_review.json').read_text())
        if init_review.get('passed') is not True or init_review.get('sources_sha256')!=inputs:
            raise ValueError('Current-source mapped INIT reviews required before PNR')
        q=json.loads((HERE.parent/'qualification.json').read_text(encoding='utf-8'))
        if not q.get('offline_tests_passed')or q.get('sources_sha256')!=inputs or q.get('programming_authorized')is not False:
            raise ValueError('Current source-bound offline qualification is required before full PNR')
        evidence=q.get('evidence_sha256')
        if not isinstance(evidence,dict)or not evidence:
            raise ValueError('Offline qualification is missing its proof bindings')
        for name,expected in evidence.items():
            path=HERE.parent/name
            if not path.is_file()or digest(path)!=expected:
                raise ValueError('Offline proof changed since qualification: '+str(path))
        verify_parent_synthesis_inputs() # Verify frozen inputs; fresh synthesis plus PNR in one run all, no preflight compile.
        manifest_path.write_text(json.dumps({'verified': False, 'sources_sha256': inputs}, indent=2), encoding='utf-8')
        print('Building control bench; no hardware download.', flush=True)
        with (HERE / 'build_console.txt').open('w', encoding='utf-8') as log:
            started=time.time()
            process=subprocess.Popen([GW_SH, 'build.tcl'], cwd=HERE, stdout=log,
                                     stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            completed_since=None;exit_workaround=False;verified_output=None
            while process.poll() is None:
                trace=HERE/'impl/pnr'/(TOP+'.tr')
                console=(HERE/'build_console.txt').read_text(encoding='utf-8',errors='replace')
                synlog=HERE/'impl/gwsynthesis'/(TOP+'.log')
                if synlog.is_file() and synlog.stat().st_mtime>=started and 'GowinSynthesis finish' in console:
                    try:reject_connectivity_warnings(HERE)
                    except ValueError:
                        process.terminate();process.wait(timeout=10);raise
                finished=trace.exists() and trace.stat().st_mtime>=started and 'Generate file' in console and (TOP+'.tr" completed') in console
                if finished:
                    if completed_since is None:completed_since=time.monotonic()
                    if time.monotonic()-completed_since>=20:
                        # Some local gw_sh instances leave an idle process after
                        # all outputs are finished. Validate artifacts BEFORE
                        # terminating only the child launched by this build.
                        try:verified_output=verify(inputs)
                        finally:
                            process.terminate();process.wait(timeout=10)
                        exit_workaround=True;break
                if time.time()-started>5400:
                    process.terminate();process.wait(timeout=10)
                    raise RuntimeError('Compiler exceeded90minutes; source preserved')
                time.sleep(1)
            result_code=process.returncode
        if result_code:
            if not exit_workaround:raise RuntimeError(f'Gowin failed ({result_code}); see build_console.txt')
        for suffix in ('.tr','.rpt.txt','.fs'):
            output=HERE/'impl/pnr'/(TOP+suffix)
            if not output.exists() or output.stat().st_mtime<started:
                raise ValueError('Missing or stale build output: '+str(output))
        for name in (TOP+'.prj',TOP+'_syn_rsc.xml'):
            output=HERE/'impl/gwsynthesis'/name
            if not output.exists() or output.stat().st_mtime<started:
                raise ValueError('Missing or stale synthesis output: '+str(output))
        result = verified_output or verify(inputs)
        result['compiler_exit_workaround']=exit_workaround
        manifest_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'verified': result['verified'], 'fmax_mhz': result['fmax_mhz'],
                      'io_count': result['io_count'], 'user_code': result['bitstream']['user_code'],
                      'motor_ports': result['motor_ports']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
