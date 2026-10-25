"""Build an isolated B0B2 fixture. Never opens a programmer or serial port."""
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


def observer_reset(netlist, source):
    """Prove the unique boot==255/pose NAND. No caller-supplied net names."""
    rtl = (source / (TOP + '.v')).read_text()
    rtl = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', rtl)
    compact = re.sub(r'\s+', '', rtl)
    required = ("reg[7:0]boot=0;always@(posedgeclk50)if(boot!=255)boot<=boot+1'b1;",
                'wirerst_n=boot==255;', 'wireobserver_reset=!pose_valid||!previous_pose_valid;',
                'always@(posedgeclk50)if(!rst_n)previous_pose_valid<=0;elseprevious_pose_valid<=pose_valid;')
    if not all(fragment in compact for fragment in required):
        raise ValueError('Unexpected logical boot/observer reset definition')
    text = netlist.read_text()
    tops = list(re.finditer(r'\bmodule\s+' + TOP + r'\s*\([\s\S]*?\bendmodule\b', text))
    if len(tops) != 1:
        raise ValueError('Missing or duplicate top netlist module')
    block = tops[0][0]
    inits = dict(re.findall(r"defparam\s+(\w+)\.INIT\s*=\s*16'h([0-9a-fA-F]+)\s*;", block))
    luts = []
    for match in re.finditer(r'\bLUT4\s+(\w+)\s*\(([\s\S]*?)\);', block):
        pairs = re.findall(r'\.(\w+)\(\s*([^()]+?)\s*\)', match[2])
        ports = dict(pairs)
        if len(pairs) == 5 and set(ports) == {'F', 'I0', 'I1', 'I2', 'I3'}:
            luts.append(dict(instance=match[1], init=inits.get(match[1], '').upper(), ports=ports))
    drivers = {}
    for lut in luts:
        drivers.setdefault(lut['ports']['F'], []).append(lut)
    matches = []
    for lut in luts:
        inputs = [lut['ports']['I' + str(i)] for i in range(4)]
        if lut['init'] != '7FFF' or len(set(inputs)) != 4 or not {'previous_pose_valid', 'pose_valid'} <= set(inputs):
            continue
        nets = [net for net in inputs if net not in ('previous_pose_valid', 'pose_valid')]
        if any(len(drivers.get(net, [])) != 1 for net in nets):
            continue
        halves = [drivers[net][0] for net in nets]
        if any(half['init'] != '8000' for half in halves):
            continue
        bits = [{half['ports']['I' + str(i)] for i in range(4)} for half in halves]
        if any(len(group) != 4 for group in bits) or bits[0] & bits[1] or set.union(*bits) != {f'boot[{i}]' for i in range(8)}:
            continue
        net = lut['ports']['F']
        if re.fullmatch(r'[A-Za-z_]\w*', net) and len(drivers[net]) == 1:
            matches.append(dict(net=net, nand=lut, boot_and_halves=halves, boot_value=255))
    if len(matches) != 1:
        raise ValueError('Observer reset NAND is missing or ambiguous')
    return matches[0]


def synthesis_prefix(donor):
    console = (donor / 'console.log').read_bytes()
    matches = list(re.finditer(rb'(?m)^GowinSynthesis finish\r?$', console))
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous completed donor synthesis')
    end = console.find(b'\n', matches[0].end())
    return console[:end + 1] if end >= 0 else console


def netlist_project(source):
    """Preserve non-FileList project metadata; enable exactly VG, CST and SDC."""
    project = ET.parse(source / (TOP + '.gprj')).getroot()
    lists = project.findall('.//FileList')
    if len(lists) != 1 or lists[0] not in list(project):
        raise ValueError('Unexpected project FileList structure')
    files = lists[0]
    files.clear()
    for path, kind in [('impl/gwsynthesis/' + TOP + '.vg', 'file.netlist'),
                       (TOP + '.cst', 'file.cst'), (TOP + '.sdc', 'file.sdc')]:
        ET.SubElement(files, 'File', dict(path=path, type=kind, enable='1'))
    if len(project.findall('.//File')) != 3:
        raise ValueError('Project has file references outside its sole FileList')
    return (b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'
            + ET.tostring(project, encoding='utf-8') + b'\n')


def constraints(fixture, global_reset=None):
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
    if global_reset is not None:
        if not re.fullmatch(r'[A-Za-z_]\w*', global_reset):
            raise ValueError('Invalid proven global net')
        expected += [f'CLOCK_LOC "{global_reset}" BUFG = CE|SR|LOGIC;']
    if lines(cst) != expected:
        raise ValueError('Pin/electrical constraints differ from baseline')
    locations = re.findall(r'IO_LOC "([^"]+)" (\w+);', cst)
    if len(locations) != 17 or len(dict(locations)) != 17 or len({p for _, p in locations}) != 17:
        raise ValueError('Duplicate or missing pin locations')
    sdc = (fixture / (TOP + '.sdc')).read_text().strip()
    if sdc != 'create_clock -name clk50 -period 19.500 [get_ports {clk50}]':
        raise ValueError('Unexpected timing constraints or timing exceptions')
    return dict(locations)


def build_tcl(options, pnr_only=False):
    # Receipt options are parsed as data; do not admit additional Tcl commands.
    fixed = dict(top_module=TOP, output_base_name=TOP, user_code='0000B0B2',
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
    return text + ('run pnr\nexit\n' if pnr_only else 'run all\nexit\n')


def verify_current_source(fixture, manifest):
    """Shared full/derived audit; only proven CST, netlist GPRJ and Tcl may differ.

    Derived receipts bind a compatible full-build donor, its archived runner,
    completed synthesis prefix, exact copied VG, and unique reset structure.
    No chained provenance or caller-selected net/constraint exception is allowed.
    """
    source = ROOT / 'source'
    current = source_hashes(source)
    if not current or set(manifest.get('source_sha256', {})) != set(current):
        raise ValueError('Input hash coverage differs from the source file set')
    if Path(manifest.get('source_root', '')).resolve() != source.resolve():
        raise ValueError('Unexpected source root')
    derived = manifest.get('derived_netlist')
    logical = manifest.get('logical_source_sha256', current)
    if logical != current:
        raise ValueError('Logical source differs from current controlled source')
    exceptions = {'build.tcl'}
    global_reset = None
    if derived is not None:
        required = {'schema', 'donor_build', 'donor_inputs_sha256', 'donor_runner_sha256',
                    'synthesis_receipt_path', 'synthesis_receipt_sha256', 'netlist_path',
                    'netlist_sha256', 'observer_reset', 'global_observer_reset'}
        if (set(derived) != required or derived.get('schema') != 'b0b2.pnr-derived.v1'
                or derived.get('global_observer_reset') is not True
                or manifest.get('logical_source_sha256') != current):
            raise ValueError('Unknown or incomplete derived netlist contract')
        donor = Path(derived['donor_build']).resolve()
        if sha(donor / 'inputs.json') != derived['donor_inputs_sha256']:
            raise ValueError('Donor input receipt changed')
        donor_manifest = json.loads((donor / 'inputs.json').read_text())
        if donor_manifest.get('derived_netlist') is not None:
            raise ValueError('Chained derived netlists are not supported')
        verify_current_source(donor / 'fixture', donor_manifest)
        if sha(donor / 'build_runner.py') != donor_manifest['runner_sha256'] or derived['donor_runner_sha256'] != donor_manifest['runner_sha256']:
            raise ValueError('Donor archived runner changed')
        if derived['synthesis_receipt_path'] != 'donor_synthesis.log':
            raise ValueError('Unexpected synthesis receipt path')
        receipt = fixture.parent / derived['synthesis_receipt_path']
        if sha(receipt) != derived['synthesis_receipt_sha256'] or receipt.read_bytes() != synthesis_prefix(donor):
            raise ValueError('Donor synthesis completion prefix changed')
        relative = 'impl/gwsynthesis/' + TOP + '.vg'
        if derived['netlist_path'] != relative:
            raise ValueError('Unexpected derived netlist path')
        if sha(donor / 'fixture' / relative) != derived['netlist_sha256'] or sha(fixture / relative) != derived['netlist_sha256']:
            raise ValueError('Donor/derived netlist hash mismatch')
        proof = observer_reset(fixture / relative, source)
        if derived['observer_reset'] != proof:
            raise ValueError('Observer reset structure/proof mismatch')
        global_reset = proof['net']
        exceptions.update({TOP + '.cst', TOP + '.gprj'})
        base = (source / (TOP + '.cst')).read_bytes()
        if (fixture / (TOP + '.cst')).read_bytes() != base + (f'\nCLOCK_LOC "{global_reset}" BUFG = CE|SR|LOGIC;\n').encode('ascii'):
            raise ValueError('Physical CST differs from exact base plus proven global')
        if (fixture / (TOP + '.gprj')).read_bytes() != netlist_project(source):
            raise ValueError('Derived GPRJ differs from exact three-file netlist project')
    for item in ET.parse(fixture / (TOP + '.gprj')).findall('.//File'):
        allowed = set(current)
        if derived is not None:
            allowed.add('impl/gwsynthesis/' + TOP + '.vg')
        if item.attrib.get('enable') == '1' and item.attrib['path'].replace('\\', '/') not in allowed:
            raise ValueError('Project reference is outside the bound input set')
    for name, digest in manifest['source_sha256'].items():
        if sha(fixture / name) != digest:
            raise ValueError('Build source changed: ' + name)
        if name not in exceptions and current[name] != digest:
            raise ValueError('Current source differs from fixture: ' + name)
    if (fixture / 'build.tcl').read_text() != build_tcl(manifest['options'], derived is not None):
        raise ValueError('Build Tcl differs from bounded run/options contract')
    pins = constraints(fixture, global_reset)
    if pins != manifest.get('pins'):
        raise ValueError('Input manifest pin contract differs from the actual constraints')
    return pins


def prepare(output, place, route, replicate, pnr_only_from=None, global_observer_reset=False):
    if (pnr_only_from is None) != (not global_observer_reset):
        raise ValueError('PNR-only donor and proven global observer reset must be selected together')
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
    derived = None
    if pnr_only_from is not None:
        donor = pnr_only_from.resolve()
        donor_inputs_sha = sha(donor / 'inputs.json')
        donor_manifest = json.loads((donor / 'inputs.json').read_text())
        if donor_manifest.get('derived_netlist') is not None:
            raise ValueError('Chained derived netlists are not supported')
        verify_current_source(donor / 'fixture', donor_manifest)
        runner_sha = sha(donor / 'build_runner.py')
        if runner_sha != donor_manifest['runner_sha256']:
            raise ValueError('Donor archived runner changed')
        prefix = synthesis_prefix(donor)
        (output / 'donor_synthesis.log').write_bytes(prefix)
        relative = 'impl/gwsynthesis/' + TOP + '.vg'
        original = donor / 'fixture' / relative
        proof = observer_reset(original, source)
        netlist_sha = sha(original)
        (fixture / relative).parent.mkdir(parents=True)
        shutil.copyfile(original, fixture / relative)
        if sha(original) != netlist_sha or sha(fixture / relative) != netlist_sha:
            raise ValueError('Donor netlist changed while copying')
        derived = dict(schema='b0b2.pnr-derived.v1', donor_build=str(donor),
                       donor_inputs_sha256=donor_inputs_sha, donor_runner_sha256=runner_sha,
                       synthesis_receipt_path='donor_synthesis.log',
                       synthesis_receipt_sha256=sha(output / 'donor_synthesis.log'),
                       netlist_path=relative, netlist_sha256=netlist_sha,
                       observer_reset=proof, global_observer_reset=True)
        cst = fixture / (TOP + '.cst')
        cst.write_bytes(cst.read_bytes() + (f'\nCLOCK_LOC "{proof["net"]}" BUFG = CE|SR|LOGIC;\n').encode('ascii'))
        (fixture / (TOP + '.gprj')).write_bytes(netlist_project(source))
    options = dict(top_module=TOP, output_base_name=TOP, user_code='0000B0B2',
                   place_option=place, route_option=route, timing_driven=1,
                   replicate_resources=replicate, map_option=2, global_freq=50,
                   max_fanout=200, opt_goal='area', route_maxfan=23)
    (fixture / 'build.tcl').write_text(build_tcl(options, derived is not None))
    shutil.copyfile(Path(__file__), output / 'build_runner.py')
    files = {name: sha(fixture / name) for name in logical}
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256=files, logical_source_sha256=logical, pins=pins, options=options,
                    constraint_period_ns=19.5, hardware_clock_hz=50000000,
                    hardware_accessed=False, flash_changed=False,
                    flight_ready=False, source_root=str(source), runner_sha256=sha(Path(__file__)))
    if derived is not None:
        manifest['derived_netlist'] = derived
    write_json(output / 'inputs.json', manifest)
    verify_current_source(fixture, manifest)
    return fixture, manifest


def collect(output, returncode):
    if type(returncode) is not int:
        raise ValueError('Vendor exit code must be an integer, not a missing/boolean value')
    if (output / 'CANCELLED.json').exists():
        raise ValueError('Cancelled build cannot be accepted')
    fixture = output / 'fixture'
    manifest = json.loads((output / 'inputs.json').read_text())
    verify_current_source(fixture, manifest)
    if sha(output / 'build_runner.py') != manifest['runner_sha256']:
        raise ValueError('Archived build runner changed')
    console = (output / 'console.log').read_text(errors='replace')
    no_unexpected_synthesis = (manifest.get('derived_netlist') is None or
                               not re.search(r'\bGowinSynthesis\b|\bCompiling module\b|Running netlist conversion', console))
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
    observer_global = None
    observer_global_ok = True
    if manifest.get('derived_netlist') is not None:
        net = manifest['derived_netlist']['observer_reset']['net']
        row = re.search(r'^\s*' + re.escape(net) + r'\s*\|\s*(PRIMARY|LW)\s*\|', rpt, re.M)
        observer_global = row[1] if row else None
        observer_global_ok = observer_global is not None
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
        identity_ok = bool(re.search(r'UserCode:\s*0x0000b0b2\b', header, re.I))
    timed = bool(frequency and float(frequency[1]) + 0.0005 >= 1000 / 19.5
                 and all(v == dict(tns_ns=0.0, violated_endpoints=0) for v in summaries.values())
                 and clock_ok and all(v is not None and v >= 0 for v in minima.values()))
    result = dict(passed=bool(returncode == 0 and routed and timed and identity_ok
                              and actual_pins == manifest['pins'] and used_inputs_ok and observer_global_ok
                              and no_unexpected_synthesis),
                  vendor_returncode=returncode, routing_passed=routed,
                  unrouted_nets=int(unrouted[1]) if unrouted else None,
                  routing_status_proof=(('vendor exit zero, completed router and bitstream generation, '
                                         'full physical report; ' + ('explicit zero-unrouted count' if unrouted else
                                         'tool omits explicit zero-unrouted count')) if routed else
                                        'not established: vendor exit/completion, physical report or zero-unrouted requirements failed'),
                  observer_global_assignment=observer_global,
                  observer_global_contract_passed=observer_global_ok,
                  pnr_only_synthesis_absent=bool(no_unexpected_synthesis),
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
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('outputs_sha256', 'logical_source_sha256', 'derived_netlist')}), flush=True)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--prepare-only', action='store_true')
    ap.add_argument('--collect', type=Path)
    ap.add_argument('--place', type=int, default=2, choices=(0, 1, 2, 3))
    ap.add_argument('--route', type=int, default=2, choices=(0, 1, 2, 3))
    ap.add_argument('--replicate', type=int, default=1, choices=(0, 1))
    ap.add_argument('--pnr-only-from', type=Path)
    ap.add_argument('--global-observer-reset', action='store_true')
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
    output = args.output or REPO / 'out/B0B2' / datetime.now(timezone.utc).strftime('build_%Y%m%dT%H%M%SZ')
    output = output.resolve()
    fixture, _ = prepare(output, args.place, args.route, args.replicate,
                         args.pnr_only_from, args.global_observer_reset)
    print(json.dumps(dict(prepared=str(fixture), hardware_accessed=False)), flush=True)
    if args.prepare_only:
        return 0
    with (output / 'console.log').open('w') as log:
        run = subprocess.run([str(GOWIN), 'build.tcl'], cwd=fixture, stdout=log, stderr=subprocess.STDOUT)
    write_json(output / 'vendor_exit_code.json', dict(returncode=run.returncode))
    return 0 if collect(output, run.returncode)['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
