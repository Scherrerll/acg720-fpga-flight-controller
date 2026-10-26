"""Compile/run actual frozen RTL; all generated artifacts stay in this folder."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / 'firmware/B0B3/source'
BIN = Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
OUT = HERE / 'rtl_attempt_03'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    tmp = OUT / 'tmp'
    tmp.mkdir()
    sources = sorted(SOURCE.rglob('*.v'))
    input_hashes = {p.relative_to(REPO).as_posix(): sha(p) for p in sources}
    input_hashes['analysis/20261026_flight_followup/height/height_path_tb.v'] = sha(HERE / 'height_path_tb.v')
    input_hashes['analysis/20261026_flight_followup/height/run_height_rtl.py'] = sha(Path(__file__))
    env = dict(os.environ, PATH=str(BIN) + os.pathsep + os.environ.get('PATH', ''), TMP=str(tmp), TEMP=str(tmp), TMPDIR=str(tmp))
    commands = []
    def run(name, args):
        start = time.monotonic()
        result = subprocess.run(list(map(str, args)), cwd=HERE, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace',
                                timeout=300, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        path = OUT / (name + '.log')
        path.write_text(result.stdout, encoding='utf8')
        record = dict(name=name, command=list(map(str, args)), exit_code=result.returncode,
                      seconds=round(time.monotonic() - start, 3), log_sha256=sha(path),
                      pass_lines=[s for s in result.stdout.splitlines() if s.startswith('PASS ')])
        commands.append(record)
        print(json.dumps({k: record[k] for k in ('name', 'exit_code', 'seconds', 'pass_lines')}), flush=True)
        if result.returncode != 0:
            raise RuntimeError(name + ' failed; see ' + str(path))
        return record
    passed = False
    try:
        run('compile', [BIN/'iverilog.exe', '-g2012', '-I', SOURCE, '-s', 'height_path_tb', '-o', OUT/'height_path.vvp',
                        HERE/'height_path_tb.v', *sources])
        for case in range(3):
            result = run('scenario_' + str(case), [BIN/'vvp.exe', OUT/'height_path.vvp', '+SCENARIO=' + str(case)])
            assert len(result['pass_lines']) == 1
        assert all(sha(REPO / n) == h for n, h in input_hashes.items())
        passed = True
    finally:
        (OUT/'rtl_results.json').write_text(json.dumps(dict(passed=passed,
            scope='Constructed normal 50MHz, 1ms pose/10ms MTF source tuples; not flight replay or plant simulation. '
                  'Assumes previously armed/taking-off healthy core state; no motor/arming proof.',
            input_sha256=input_hashes, commands=commands), indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
