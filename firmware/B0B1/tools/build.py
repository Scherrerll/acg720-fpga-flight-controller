"""Build an isolated B0B1 fixture. Never opens a programmer or serial port."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
TOP = 'acg720_ano_port'
GOWIN = Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')


def source_hashes(source):
    return {p.relative_to(source).as_posix(): sha(p)
            for p in source.rglob('*') if p.is_file()}


def constraints(fixture):
    refs = ET.parse(fixture / (TOP + '.gprj')).findall('.//File')
    for typ, expected in [('file.sdc', TOP + '.sdc'), ('file.cst', TOP + '.cst')]:
        actual = [f.attrib['path'] for f in refs
                  if f.attrib.get('enable') == '1' and f.attrib.get('type') == typ]
        if actual != [expected]:
            raise ValueError('Unexpected enabled constraints: ' + repr(actual))
    cst = (fixture / (TOP + '.cst')).read_text()
    baseline = (REPO / 'firmware/B0B0/source_snapshot' / (TOP + '.cst')).read_text()
    lines = lambda s: [x.strip() for x in s.splitlines() if x.strip() and not x.lstrip().startswith('//')]
    expected = lines(baseline)
    if lines(cst) != expected:
        raise ValueError('Pin/electrical constraints differ from baseline')
    locations = re.findall(r'IO_LOC "([^"]+)" (\w+);', cst)
    if len(locations) != 17 or len(dict(locations)) != 17 or len({p for _, p in locations}) != 17:
        raise ValueError('Duplicate or missing pin locations')
    sdc = (fixture / (TOP + '.sdc')).read_text().strip()
    if sdc != 'create_clock -name clk50 -period 19.500 [get_ports {clk50}]':
        raise ValueError('Unexpected timing constraints or timing exceptions')
    return dict(locations)


def build_tcl(options):
    # Receipt options are parsed as data; do not admit additional Tcl commands.
    fixed = dict(top_module=TOP, output_base_name=TOP, user_code='0000B0B1',
                 timing_driven=1, map_option=2, global_freq=50, max_fanout=200,
                 opt_goal='area', route_maxfan=23)
    if set(options) != set(fixed) | {'place_option', 'route_option', 'replicate_resources'}:
        raise ValueError('Unexpected build option set')
    if any(options[k] != v for k, v in fixed.items()):
        raise ValueError('Unexpected fixed build option')
    for key, allowed in [('place_option', range(4)), ('route_option', range(4)), ('replicate_resources', range(2))]:
        if type(options[key]) is not int or options[key] not in allowed:
            raise ValueError('Unexpected physical build option')
    text = 'open_project ' + TOP + '.gprj\n'
    text += ''.join(f'set_option -{k} {v}\n' for k, v in options.items())
    return text + 'run all\nexit\n'


def verify_current_source(fixture, manifest):
    """Full builds only: exact source, generated Tcl, unchanged pins and clock."""
    source = ROOT / 'source'
    current = source_hashes(source)
    if not current or set(manifest.get('source_sha256', {})) != set(current):
        raise ValueError('Input hash coverage differs from the source file set')
    if Path(manifest.get('source_root', '')).resolve() != source.resolve():
        raise ValueError('Unexpected source root')
    if manifest.get('derived_netlist') is not None:
        raise ValueError('Derived netlists are not supported by this repair build')
    for item in ET.parse(fixture / (TOP + '.gprj')).findall('.//File'):
        if item.attrib.get('enable') == '1' and item.attrib['path'].replace('\\', '/') not in current:
            raise ValueError('Project reference is outside the bound input set')
    for name, digest in manifest['source_sha256'].items():
        if sha(fixture / name) != digest:
            raise ValueError('Build source changed: ' + name)
        if name != 'build.tcl' and current[name] != digest:
            raise ValueError('Current source differs from fixture: ' + name)
    if (fixture / 'build.tcl').read_text() != build_tcl(manifest['options']):
        raise ValueError('Build Tcl differs from bounded run/options contract')
    pins = constraints(fixture)
    if pins != manifest.get('pins'):
        raise ValueError('Input manifest pin contract differs from the actual constraints')
    return pins


def prepare(output, place, route, replicate):
    if output.exists():
        raise ValueError('Refuse to overwrite an existing build directory')
    source = ROOT / 'source'
    fixture = output / 'fixture'
    shutil.copytree(source, fixture)
    refs = ET.parse(fixture / (TOP + '.gprj')).findall('.//File')
    for item in refs:
        if not (fixture / item.attrib['path']).is_file():
            raise ValueError('Missing project source: ' + item.attrib['path'])
    pins = constraints(fixture)
    logical = source_hashes(source)
    options = dict(top_module=TOP, output_base_name=TOP, user_code='0000B0B1',
                   place_option=place, route_option=route, timing_driven=1,
                   replicate_resources=replicate, map_option=2, global_freq=50,
                   max_fanout=200, opt_goal='area', route_maxfan=23)
    (fixture / 'build.tcl').write_text(build_tcl(options))
    shutil.copyfile(Path(__file__), output / 'build_runner.py')
    files = {name: sha(fixture / name) for name in logical}
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256=files, pins=pins, options=options,
                    constraint_period_ns=19.5, hardware_clock_hz=50000000,
                    hardware_accessed=False, flash_changed=False,
                    flight_ready=False, source_root=str(source), runner_sha256=sha(Path(__file__)))
    write_json(output / 'inputs.json', manifest)
    verify_current_source(fixture, manifest)
    return fixture, manifest


def collect(output, returncode):
    if type(returncode) is not int:
        raise ValueError('Vendor exit code must be an integer, not a missing/boolean value')
    fixture = output / 'fixture'
    manifest = json.loads((output / 'inputs.json').read_text())
    verify_current_source(fixture, manifest)
    if sha(output / 'build_runner.py') != manifest['runner_sha256']:
        raise ValueError('Archived build runner changed')
    console = (output / 'console.log').read_text(errors='replace')
    pnr = fixture / 'impl/pnr'
    rpt_path = pnr / (TOP + '.rpt.txt')
    timing_path = pnr / (TOP + '.tr')
    rpt = rpt_path.read_text(errors='replace') if rpt_path.exists() else ''
    timing = timing_path.read_text(errors='replace') if timing_path.exists() else ''
    if 'Note:Core Timing Report' in timing:
        timing = timing[timing.index('Note:Core Timing Report'):]
    errors = re.findall(r'^.*ERROR[^\r\n]*', console + '\n' + rpt, re.M)
    unrouted = re.search(r'total\s+(\d+)\s+unrouted nets', rpt)
    routed = (returncode == 0 and 'Placement and routing completed' in console
              and 'Bitstream generation completed' in console
              and 'Running routing:' in rpt and 'Total Routing:' in rpt
              and not errors and not (unrouted and int(unrouted[1])))
    frequency = re.search(r'clk50\s+[\d.]+\(MHz\)\s+([\d.]+)\(MHz\)', timing)
    summaries = {}
    for kind in ('setup', 'hold'):
        m = re.search(r'clk50\s+' + kind + r'\s+(-?[\d.]+)\s+(\d+)', timing)
        summaries[kind] = dict(tns_ns=float(m[1]), violated_endpoints=int(m[2])) if m else None
    actual_pins = dict(re.findall(r'^(\w+)\s+\|\s*-\s*\|\s*(\w+)/\d+\s*\|', rpt, re.M))
    minima = {}
    for begin, end, kind in [
        ('3.1.1 Setup Paths Table', '3.1.2 Hold Paths Table', 'setup'),
        ('3.1.2 Hold Paths Table', '3.1.3 Recovery Paths Table', 'hold'),
        ('3.1.3 Recovery Paths Table', '3.1.4 Removal Paths Table', 'recovery'),
        ('3.1.4 Removal Paths Table', '3.2 Minimum Pulse Width Table', 'removal'),
        ('3.2 Minimum Pulse Width Table', '3.3 Timing Report By Analysis Type', 'minimum_pulse_width')]:
        a = timing.find(begin)
        b = timing.find(end, a + len(begin)) if a >= 0 else -1
        if b < 0 and kind == 'minimum_pulse_width':
            b = timing.find('3.3.1 Setup Analysis Report', a + len(begin))
        values = re.findall(r'^\s+\d+\s+(-?[\d.]+)\s+', timing[a:b], re.M) if a >= 0 and b >= 0 else []
        minima[kind] = min(map(float, values)) if values else None
    clock_rows = []
    if '2.2 Clock Summary' in timing and '2.3 Max Frequency Summary' in timing:
        block = timing[timing.index('2.2 Clock Summary'):timing.index('2.3 Max Frequency Summary')]
        clock_rows = re.findall(r'^\s+\d+\s+(\S+)\s+(\S+)\s+([\d.]+)\s+', block, re.M)
    clock_ok = clock_rows == [('clk50', 'Base', '19.500')]
    cmd_path = pnr / 'cmd.do'
    cmd = dict(re.findall(r'^-(\w+)[ \t]+([^\r\n]+)', cmd_path.read_text(), re.M)) if cmd_path.exists() else {}
    used_inputs_ok = all(k in cmd and Path(cmd[k].strip()).resolve() == (fixture / n).resolve()
                         for k, n in [('d', 'impl/gwsynthesis/' + TOP + '.vg'),
                                      ('cst', TOP + '.cst'), ('sdc', TOP + '.sdc')])
    fs = pnr / (TOP + '.fs')
    identity_ok = False
    if fs.exists():
        with fs.open() as stream:
            header = ''.join(next(stream, '') for _ in range(15))
        identity_ok = bool(re.search(r'UserCode:\s*0x0000b0b1\b', header, re.I))
    timed = bool(frequency and float(frequency[1]) + 0.0005 >= 1000 / 19.5
                 and all(v == dict(tns_ns=0.0, violated_endpoints=0) for v in summaries.values())
                 and clock_ok and all(v is not None and v >= 0 for v in minima.values()))
    result = dict(passed=bool(returncode == 0 and routed and timed and identity_ok
                              and actual_pins == manifest['pins'] and used_inputs_ok),
                  vendor_returncode=returncode, routing_passed=routed,
                  unrouted_nets=int(unrouted[1]) if unrouted else None,
                  routing_status_proof=('vendor exit zero, completed router and bitstream generation, '
                                        'full physical report; tool omits explicit zero-unrouted count'),
                  timing_passed=timed, summaries=summaries,
                  fmax_mhz=float(frequency[1]) if frequency else None,
                  worst_reported_slack_ns=minima, report_clock_contract_passed=clock_ok,
                  actual_input_paths_passed=used_inputs_ok, timing_exceptions_added=False,
                  logical_source_sha256=manifest.get('logical_source_sha256'),
                  derived_netlist=manifest.get('derived_netlist'),
                  audit_runner_sha256=sha(Path(__file__)),
                  identity_passed=identity_ok, pin_contract_passed=actual_pins == manifest['pins'],
                  errors=errors, hardware_accessed=False, flash_changed=False,
                  flight_ready=False, inputs_sha256=sha(output / 'inputs.json'),
                  outputs_sha256={str(p.relative_to(output)).replace('\\', '/'): sha(p)
                                  for p in pnr.glob('*') if p.is_file()})
    if fs.exists():
        result['bitstream'] = dict(path=str(fs), sha256=sha(fs))
    write_json(output / 'result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'outputs_sha256'}), flush=True)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--collect', type=Path)
    ap.add_argument('--place', type=int, default=2, choices=(0, 1, 2, 3))
    ap.add_argument('--route', type=int, default=2, choices=(0, 1, 2, 3))
    ap.add_argument('--replicate', type=int, default=1, choices=(0, 1))
    args = ap.parse_args()
    if args.collect:
        output = args.collect.resolve()
        exit_path = output / 'vendor_exit_code.json'
        if exit_path.exists():
            returncode = json.loads(exit_path.read_text())['returncode']
        else:
            previous = output / 'result.json'
            if not previous.exists():
                raise ValueError('Cannot collect before the actual vendor process exits')
            archived = output / 'initial_vendor_result.json'
            if not archived.exists():
                shutil.copyfile(previous, archived)
            returncode = json.loads(archived.read_text())['vendor_returncode']
        return 0 if collect(output, returncode)['passed'] else 1
    output = args.output or REPO / 'out/B0B1' / datetime.now(timezone.utc).strftime('build_%Y%m%dT%H%M%SZ')
    fixture, _ = prepare(output.resolve(), args.place, args.route, args.replicate)
    print(json.dumps(dict(prepared=str(fixture), hardware_accessed=False)), flush=True)
    if args.prepare_only:
        return 0
    with (output / 'console.log').open('w') as log:
        run = subprocess.run([str(GOWIN), 'build.tcl'], cwd=fixture, stdout=log, stderr=subprocess.STDOUT)
    write_json(output / 'vendor_exit_code.json', dict(returncode=run.returncode))
    return 0 if collect(output, run.returncode)['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
