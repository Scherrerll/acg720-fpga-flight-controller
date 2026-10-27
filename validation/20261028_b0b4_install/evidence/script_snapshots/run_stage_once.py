"""Capture the actual root child wait and logs for one explicitly selected stage."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPTS = {'completion': 'sram_completion_b0b4.py', 'flash': 'flash_b0b4.py', 'cold': 'observe_cold_b0b4.py'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=tuple(SCRIPTS), required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('stage_arguments', nargs=argparse.REMAINDER)
    opts = parser.parse_args()
    script = HERE / SCRIPTS[opts.stage]
    if sha(script) != opts.expected_sha256:
        raise ValueError('Reviewed stage script changed')
    arguments = opts.stage_arguments
    if arguments[:1] == ['--']:
        arguments = arguments[1:]
    folder = REPO / 'out/b0b4_install_20261028' / ('root_' + opts.stage + '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, '-B', '-X', 'utf8', str(script), *arguments]
    receipt = dict(command=command, script_sha256=sha(script), launcher_sha256=sha(Path(__file__)),
                   started_utc=datetime.now(timezone.utc).isoformat(), normal_wait_return=False, actual_p_wait=None)
    save(folder / 'process.json', receipt)
    print('ROOT_STAGE_STARTED ' + str(folder), flush=True)
    try:
        with (folder / 'stdout.log').open('wb') as stdout, (folder / 'stderr.log').open('wb') as stderr:
            child = subprocess.Popen(command, cwd=REPO, stdout=stdout, stderr=stderr,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            receipt['pid'] = child.pid
            save(folder / 'process.json', receipt)
            result = child.wait()
            receipt.update(normal_wait_return=True, actual_p_wait=result)
        if result == 0 and opts.stage in ('completion', 'flash'):
            summary = json.loads((folder / 'stdout.log').read_text(encoding='utf-8'))
            report = Path(summary['folder']).resolve() / 'stage_report.json'
            if not report.is_relative_to((REPO / 'out/b0b4_install_20261028').resolve()):
                raise ValueError('Stage report escaped this session output')
            receipt.update(stage_report=str(report), stage_report_sha256=sha(report))
    except Exception as exc:
        receipt['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        receipt.update(finished_utc=datetime.now(timezone.utc).isoformat(),
                       stdout_sha256=sha(folder / 'stdout.log'), stderr_sha256=sha(folder / 'stderr.log'))
        save(folder / 'exit.json', receipt)
    print(json.dumps(dict(folder=str(folder), normal_wait_return=receipt['normal_wait_return'], actual_p_wait=result)), flush=True)
    raise SystemExit(result)

if __name__ == '__main__':
    main()
