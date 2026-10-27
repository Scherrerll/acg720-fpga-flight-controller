"""Complete the saved B4 SRAM stage after its transient same-group GET failure.

No SRAM/Flash/reload operations exist here. Old root1 and all old files remain.
Default is offline; live execution only reads JTAG0 and uses query-only HTTP.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import time

BENCH = Path(__file__).with_name('bench_b0b4.py')
BENCH_SHA = '24e10d00c7321ba9141c86812df05a6c9a0753404124c861c24879fe5ff01a67'
if hashlib.sha256(BENCH.read_bytes()).hexdigest() != BENCH_SHA:
    raise ValueError('Frozen bench definitions changed')
SPEC = importlib.util.spec_from_file_location('b0b4_completion_frozen_bench', BENCH)
b = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(b)


def successful_wait(value, code=0):
    return isinstance(value, dict) and value.get('normal_wait_return') is True and type(value.get('actual_p_wait')) is int and value['actual_p_wait'] == code


def strict_stopped(owner, timeout=3.0):
    """Only this exact inter-frame mismatch is retriable; final data stay strict."""
    deadline = owner.time.monotonic() + timeout
    while True:
        try:
            return owner.stopped(owner.http('/api/state'))
        except ValueError as exc:
            if str(exc) != 'Same-group telemetry required' or owner.time.monotonic() >= deadline:
                raise
            owner.time.sleep(.05)


class SameGroupGuard:
    bench = b

    def guard(self):
        owner = self.bench
        value = strict_stopped(owner)
        owner.require(owner.http('/api/xy-pi/status').get('busy') is False, 'Parameter transaction is busy')
        return value

    def defaults(self, label):
        owner = self.bench
        self.guard(); status = owner.http('/api/xy-pi/status')
        owner.require(status.get('can_query') is True and type(status.get('epoch')) is int, 'Ground owner cannot query')
        token = owner.http('/api/xy-pi/session').get('token')
        reply = owner.http('/api/xy-pi/query', dict(request_id=self.folder.name+'-'+label, epoch=status['epoch']), token)
        token = None
        operation_id = reply.get('operation_id'); owner.require(type(operation_id) is int, 'Query not accepted')
        deadline = owner.time.monotonic()+7
        while owner.time.monotonic() < deadline:
            strict_stopped(owner); value = owner.http('/api/xy-pi/status')
            owner.require(value.get('epoch') == status['epoch'], 'Transport epoch changed during GET')
            if value.get('busy') is False and value.get('operation_id') == operation_id:
                owner.save(self.folder/(label+'.json'), value)
                active = value.get('active') or {}; result = value.get('result') or {}
                owner.require(value.get('supported') is True and result.get('code') == 'queried' and result.get('operation_id') == operation_id and
                              active.get('build') == '0000B0B4' and active.get('p_wire') == 1000 and active.get('i_wire') == 350 and
                              type(active.get('generation')) is int and active['generation'] == 0, 'Fresh A591 B0B4 default GET failed')
                return value
            owner.time.sleep(.1)
        raise ValueError('Fresh default GET timed out; no automatic retry')


def original_evidence(path, root_receipt, hw):
    path = Path(path).resolve(); root_receipt = Path(root_receipt).resolve()
    b.require(path.name == 'stage_report.json' and path.is_relative_to((b.REPO/'out').resolve()) and
              root_receipt.is_relative_to((b.REPO/'out').resolve()), 'Explicit original receipts must be under repository out')
    report = json.loads(path.read_text(encoding='utf-8-sig')); root = json.loads(root_receipt.read_text(encoding='utf-8-sig'))
    b.require(root.get('schema') == 'b0b4.observed-tool-exit.v1' and successful_wait(root, 1) and root.get('tool_exit_code') == 1 and
              Path(root.get('original_stage_report', '')).resolve() == path and root.get('original_stage_report_sha256') == b.sha(path) and
              root.get('observed_error') == 'ValueError: Same-group telemetry required' and
              root.get('directly_captured_root_stdout_file') is False,
              'Original observed tool root1 record must bind the unchanged stage report; no new Popen wait is inferred')
    b.require(report.get('schema') == 'b0b4.bench-stage.v1' and report.get('stage') == 'sram' and
              report.get('passed') is False and report.get('error') == 'ValueError: Same-group telemetry required' and
              report.get('sram_written') is True and report.get('flash_written') is False and
              report.get('script_sha256') == BENCH_SHA and report.get('image_sha256') == b.IMAGE_SHA and
              report.get('manifest_sha256') == b.MANIFEST_SHA and
              [item.get('operation') for item in report.get('operations', [])] == [0, 2, 0], 'Original stage failure must be only the saved same-group GET window')
    bindings = {str(path): b.sha(path), str(root_receipt): b.sha(root_receipt)}
    for label in ('qualification', '01_identity_before_cables', '01_identity_before', '02_B0B4_sram_cables',
                  '02_B0B4_sram', '04_identity_B0B4_cables', '04_identity_B0B4'):
        exit_path = path.parent/(label+'_exit.json'); value = json.loads(exit_path.read_text(encoding='utf-8'))
        b.require(successful_wait(value), 'Original successful child wait is not exact zero: '+label)
        bindings[str(exit_path)] = b.sha(exit_path)
        for stream in ('stdout', 'stderr'):
            log = path.parent/(label+'_'+stream+'.log')
            b.require(b.sha(log) == value[stream+'_sha256'], 'Original log changed: '+label)
            bindings[str(log)] = b.sha(log)
        if label in ('01_identity_before', '02_B0B4_sram', '04_identity_B0B4'):
            expected = next(item['args'] for item in report['operations'] if item['label'] == label)
            b.require(value.get('args') == expected, 'Original operation/actual-child arguments differ')
            if label == '02_B0B4_sram':
                b.require(expected[-2:] == ['--fsFile', str(b.IMAGE)], 'Original SRAM operation used a different image')
    text = ''.join((path.parent/('04_identity_B0B4_'+s+'.log')).read_text(encoding='utf-8', errors='replace') for s in ('stdout','stderr'))
    b.require(hw.identity(text) == (0x0001481B, 0xB0B4), 'Original completed JTAG identity is not B4')
    health_path = path.parent/'03_sram_healthy.json'; health = json.loads(health_path.read_text(encoding='utf-8'))
    samples = health.get('samples') or []; b.require(len(samples) >= 5, 'Original SRAM health samples missing')
    for sample in samples: b.stopped(sample)
    for first, last in zip(samples, samples[1:]):
        b.require(last.get('imu_diagnostic_fresh') is True and
                  all(type(last['imu_diagnostic'].get(k)) is int and last['imu_diagnostic'][k] > first['imu_diagnostic'][k]
                      for k in ('raw_count','accepted_count','pose_count')), 'Original successful IMU samples did not progress')
    bindings[str(health_path)] = b.sha(health_path)
    return report, bindings


class Completion(SameGroupGuard, b.Session):
    bench = b

    def __init__(self, folder, original, original_root):
        super().__init__('preflight', folder)
        self.original = Path(original); self.original_root = Path(original_root)
        self.record.update(stage='sram_completion', schema='b0b4.sram-completion.v1', script_sha256=b.sha(__file__),
                           frozen_bench_sha256=BENCH_SHA, original_stage_root_actual_p_wait=1, additional_sram_write=False,
                           original_root_evidence_kind='Observed completed functions.write_stdin/PowerShell LASTEXITCODE; no directly captured root stdout or new Popen wait')

    def operation(self, operation, label):
        b.require(type(operation) is int and operation == 0, 'Completion permits identity0 only; no reload or programming')
        return super().operation(operation, label)

    def run(self):
        self.persist()
        try:
            self.record['pins'] = b.offline()
            spec = importlib.util.spec_from_file_location('b0b4_completion_inventory_definitions_only', b.HELPER)
            self.hw = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.hw)
            original, bindings = original_evidence(self.original, self.original_root, self.hw)
            self.record.update(original_stage=str(self.original.resolve()), original_root=str(self.original_root.resolve()), bound_original_inputs=bindings)
            self.inventory = original['programmer']; self.cable = original['cable']
            initial = self.guard(); uptime = initial['flight_info'].get('uptime_ms')
            b.require(type(uptime) is int and uptime >= 0, 'Current uptime required')
            self.record['hardware_accessed'] = True
            b.require(self.operation(0, '01_current_B4_identity') == (0x0001481B, 0xB0B4), 'Current device must remain B4')
            self.health('02_current_B4_health', time.monotonic()-uptime/1000)
            self.defaults('03_fresh_B4_default_GET')
            b.require(all(b.sha(path) == digest for path, digest in bindings.items()), 'Original evidence changed during completion')
            self.record.update(passed=True, sram_installation_completed=True)
        except Exception as exc:
            self.record.update(error=type(exc).__name__+': '+str(exc), automatic_recovery=False)
            raise
        finally: self.persist()
        return self.record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--bench-confirmed-current', action='store_true')
    parser.add_argument('--original-stage', type=Path)
    parser.add_argument('--original-root-receipt', type=Path)
    parser.add_argument('--out', type=Path, default=b.DEFAULT_OUT)
    args = parser.parse_args()
    if not args.execute: print(json.dumps(b.offline(), indent=2)); return
    b.require(args.bench_confirmed_current and args.original_stage and args.original_root_receipt, 'Current bench assertion and original actual root1 evidence required')
    folder = args.out.resolve()/('sram_completion_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    result = Completion(folder, args.original_stage, args.original_root_receipt).run()
    print(json.dumps(dict(passed=result['passed'], original_stage_root_actual_p_wait=1, additional_sram_write=False, folder=str(folder)), indent=2))


if __name__ == '__main__': main()
