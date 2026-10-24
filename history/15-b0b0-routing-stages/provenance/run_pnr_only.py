"""Re-run only offline PNR from the qualified, connectivity-checked netlist.

No FPGA, Flash, serial I/O, receiver replacement or control commands.
Original RTL, constraints, synthesis and PNR options remain unchanged.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent
FIX = ROOT / 'fixture'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def require(condition, text):
    if not condition:
        raise ValueError(text)


def main():
    spec = importlib.util.spec_from_file_location('pnr_verified_builder', FIX / 'build_project.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.static_contract()
    inputs = b.source_hashes()
    q = load(ROOT / 'qualification.json')
    require(q['offline_tests_passed'] and q['sources_sha256'] == inputs, 'Current qualification required')
    for name, digest in q['evidence_sha256'].items():
        require(sha(ROOT / name) == digest, 'Proof changed: ' + name)
    previous = load(FIX / 'build_manifest.json')
    require(previous['sources_sha256'] == inputs, 'Netlist build source selection changed')
    proof = load(ROOT / 'hardware/full_build_connectivity.json')
    netlist = FIX / 'impl/gwsynthesis/acg720_ano_port.vg'
    synlog = FIX / 'impl/gwsynthesis/acg720_ano_port.log'
    require(sha(netlist) == proof['netlist_sha256'].lower() and
            sha(synlog) == proof['log_sha256'].lower() and proof['target_warning_count'] == 0,
            'Qualified full-design connectivity evidence changed')
    b.reject_connectivity_warnings(FIX)
    script = (FIX / 'build.tcl').read_text(encoding='utf-8')
    require(script.splitlines().count('run all') == 1, 'Expected frozen build script')
    runfile = FIX / 'pnr_only.tcl'
    runfile.write_text(script.replace('run all', 'run pnr'), encoding='utf-8')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = ROOT / 'hardware' / ('pnr_retry_' + stamp)
    folder.mkdir(parents=True)
    for name in ['build_console.txt', 'build_manifest.json']:
        if (FIX / name).exists():
            shutil.copy2(FIX / name, folder / ('previous_' + name))
    if (FIX / 'impl/pnr').is_dir():
        shutil.copytree(FIX / 'impl/pnr', folder / 'previous_pnr')
    record = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  passed=False, hardware_accessed=False, flash_changed=False, flight_ready=False,
                  reused_netlist_sha256=sha(netlist), synthesis_log_sha256=sha(synlog),
                  qualified_sources=inputs, driver_sha256=sha(Path(__file__)),
                  run_script_sha256=sha(runfile), limit_minutes=90,
                  note='PNR starts from placement; the stopped route state is not resumed.')
    print(json.dumps(dict(pnr_only=True, netlist_verified=True, evidence=str(folder))), flush=True)
    started = time.time()
    process = None
    try:
        with (FIX / 'build_console.txt').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([b.GW_SH, str(runfile)], cwd=FIX, stdout=log,
                                       stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            record['owned_process_id'] = process.pid
            (folder / 'run.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
            complete_since = None
            workaround = False
            actual = None
            while process.poll() is None:
                trace = FIX / 'impl/pnr/acg720_ano_port.tr'
                console = (FIX / 'build_console.txt').read_text(encoding='utf-8', errors='replace')
                finished = (trace.exists() and trace.stat().st_mtime >= started and
                            'Generate file' in console and 'acg720_ano_port.tr" completed' in console)
                if finished:
                    if complete_since is None:
                        complete_since = time.monotonic()
                    if time.monotonic() - complete_since >= 20:
                        try:
                            actual = b.verify(inputs)
                        finally:
                            process.terminate()
                            process.wait(timeout=10)
                        workaround = True
                        break
                if time.time() - started > 5400:
                    raise RuntimeError('PNR-only exceeded 90 minutes; source and logs preserved')
                time.sleep(1)
        require(process.returncode == 0 or workaround, 'PNR compiler failed')
        require(sha(netlist) == record['reused_netlist_sha256'], 'Synthesis netlist changed during PNR')
        require(sha(synlog) == record['synthesis_log_sha256'], 'Synthesis diagnostics changed during PNR')
        for suffix in ['.tr', '.rpt.txt', '.fs']:
            p = FIX / 'impl/pnr' / ('acg720_ano_port' + suffix)
            require(p.exists() and p.stat().st_mtime >= started, 'Missing or stale PNR output: ' + suffix)
        actual = actual or b.verify(inputs)
        actual.update(pnr_only_reused_synthesis=True, pnr_driver_sha256=record['driver_sha256'],
                      pnr_script_sha256=record['run_script_sha256'],
                      compiler_exit_workaround=workaround, connectivity_evidence_sha256=sha(ROOT / 'hardware/full_build_connectivity.json'))
        (FIX / 'build_manifest.json').write_text(json.dumps(actual, indent=2), encoding='utf-8')
        record.update(passed=True, bitstream=actual['bitstream'], fmax_mhz=actual['fmax_mhz'],
                      unrouted_nets=actual['unrouted_nets'], slack=actual['slack'])
        print(json.dumps({k: record[k] for k in ['passed', 'fmax_mhz', 'unrouted_nets', 'slack', 'bitstream']}), flush=True)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        record['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (folder / 'run.json').write_text(json.dumps(record, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
