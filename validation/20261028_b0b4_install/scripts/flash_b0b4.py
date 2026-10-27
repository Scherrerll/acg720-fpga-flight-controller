"""Separate, explicitly selected B0B4 Flash stage; no automatic recovery.

Imports the frozen SRAM definitions, never their main/old install entry points.
Default is offline. This script never opens serial; only query-only ground HTTP.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time

BENCH = Path(__file__).with_name('bench_b0b4.py')
BENCH_SHA = '24e10d00c7321ba9141c86812df05a6c9a0753404124c861c24879fe5ff01a67'
if hashlib.sha256(BENCH.read_bytes()).hexdigest() != BENCH_SHA:
    raise ValueError('Frozen bench definitions changed')
SPEC = importlib.util.spec_from_file_location('b0b4_frozen_bench_definitions', BENCH)
b = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(b)
COMPLETION = Path(__file__).with_name('sram_completion_b0b4.py')
COMPLETION_SHA = '522e7e0bbe6780c44877512338b45f7697788274b1511953ea88ff61f96628f8'
if hashlib.sha256(COMPLETION.read_bytes()).hexdigest() != COMPLETION_SHA:
    raise ValueError('Frozen completion definitions changed')
SPEC = importlib.util.spec_from_file_location('b0b4_frozen_completion_definitions', COMPLETION)
c = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(c)


def successful_wait(value):
    return isinstance(value, dict) and value.get('normal_wait_return') is True and type(value.get('actual_p_wait')) is int and value['actual_p_wait'] == 0


class FlashSession(c.SameGroupGuard, b.Session):
    bench = b

    def __init__(self, folder, sram_receipt, completion_receipt=None, completion_root=None):
        super().__init__('sram', folder)
        self.stage = 'flash'; self.sram_receipt = Path(sram_receipt).resolve(); self.loaded_at = None
        self.reload_expected_from = None
        self.completion_receipt = completion_receipt; self.completion_root = completion_root
        self.record.update(stage='flash', script_sha256=b.sha(__file__), frozen_bench_sha256=BENCH_SHA,
                           frozen_completion_sha256=COMPLETION_SHA,
                           flash_write_attempted=False, flash_contents_certified=False,
                           independent_flash_verify_passed=False, current_operator_flash_assertion=True)

    def prior_sram(self):
        path = self.sram_receipt
        b.require(self.completion_receipt is not None and self.completion_root is not None, 'Explicit completed no-rewrite SRAM evidence and actual root0 required')
        completed_path = Path(self.completion_receipt).resolve(); root_path = Path(self.completion_root).resolve()
        b.require(completed_path.name == 'stage_report.json' and completed_path.is_relative_to((b.REPO/'out').resolve()) and
                  root_path.is_relative_to((b.REPO/'out').resolve()), 'Completion receipts must be under repository out')
        completed = json.loads(completed_path.read_text(encoding='utf-8-sig')); root = json.loads(root_path.read_text(encoding='utf-8-sig'))
        b.require(completed.get('schema') == 'b0b4.sram-completion.v1' and completed.get('stage') == 'sram_completion' and
                  completed.get('passed') is True and completed.get('sram_installation_completed') is True and
                  completed.get('additional_sram_write') is False and completed.get('script_sha256') == COMPLETION_SHA and
                  completed.get('image_sha256') == b.IMAGE_SHA and completed.get('manifest_sha256') == b.MANIFEST_SHA and
                  Path(completed.get('original_stage','')).resolve() == path and
                  [item.get('operation') for item in completed.get('operations',[])] == [0], 'Exact no-rewrite SRAM completion required')
        b.require(successful_wait(root) and Path(root.get('stage_report','')).resolve() == completed_path and
                  root.get('stage_report_sha256') == b.sha(completed_path), 'Completion actual root0 must bind the unchanged completion report')
        report, bindings = c.original_evidence(path, completed.get('original_root'), self.hw)
        b.require(completed.get('bound_original_inputs') == bindings, 'Completion original SRAM bindings differ')
        for label in ('01_current_B4_identity_cables','01_current_B4_identity'):
            value = json.loads((completed_path.parent/(label+'_exit.json')).read_text(encoding='utf-8-sig'))
            b.require(successful_wait(value), 'Completion child did not normally wait zero: '+label)
            for stream in ('stdout','stderr'):
                b.require(b.sha(completed_path.parent/(label+'_'+stream+'.log')) == value[stream+'_sha256'], 'Completion log changed')
        identity_text = ''.join((completed_path.parent/('01_current_B4_identity_'+stream+'.log')).read_text(encoding='utf-8',errors='replace') for stream in ('stdout','stderr'))
        b.require(self.hw.identity(identity_text) == (0x0001481B,0xB0B4), 'Completion JTAG identity is not B4')
        get_path = completed_path.parent/'03_fresh_B4_default_GET.json'; value = json.loads(get_path.read_text(encoding='utf-8-sig'))
        active = value.get('active') or {}; result = value.get('result') or {}
        b.require(value.get('supported') is True and value.get('busy') is False and result.get('code') == 'queried' and
                  result.get('operation_id') == value.get('operation_id') and active.get('build') == '0000B0B4' and
                  active.get('p_wire') == 1000 and active.get('i_wire') == 350 and type(active.get('generation')) is int and
                  active['generation'] == 0, 'Saved SRAM B4 default GET required')
        health_path = completed_path.parent/'02_current_B4_health.json'; health = json.loads(health_path.read_text(encoding='utf-8-sig'))
        samples = health.get('samples') or []
        b.require(len(samples) >= 5, 'Saved SRAM health samples missing')
        for sample in samples: b.stopped(sample)
        for first, last in zip(samples, samples[1:]):
            b.require(last.get('imu_diagnostic_fresh') is True and
                      all(type(last['imu_diagnostic'].get(k)) is int and last['imu_diagnostic'][k] > first['imu_diagnostic'][k]
                          for k in ('raw_count', 'accepted_count', 'pose_count')), 'Saved SRAM IMU counts did not progress')
        self.inventory = report['programmer']; self.cable = report['cable']
        self.record['prior_sram'] = dict(path=str(path), sha256=b.sha(path), original_root_actual_p_wait=1,
                                        completion_path=str(completed_path), completion_sha256=b.sha(completed_path),
                                        completion_root=str(root_path), completion_root_sha256=b.sha(root_path), completion_actual_p_wait=0,
                                        default_GET_sha256=b.sha(get_path), health_sha256=b.sha(health_path))
        self.persist()

    def operation(self, operation, label):
        b.require(type(operation) is int and operation in (0, 1, 54, 66), 'Operation outside fixed Flash whitelist')
        if operation == 1:
            b.require(self.reload_expected_from in (54, 66), 'Reload allowed only immediately after successful fixed-image 54/66')
        b.offline(); location = self.bind(label)
        if operation == 1:
            # Flash program/verify can leave configuration stopped and telemetry stale.
            # This sole planned reload permits stale data, but fresh activity is fatal.
            value = b.http('/api/state')
            b.require(isinstance(value, dict), 'Invalid owner telemetry object')
            b.no_activity(value)
            b.save(self.folder/(label+'_reload_boundary.json'), dict(after_successful_operation=self.reload_expected_from, state=value))
            self.reload_expected_from = None  # Never retry a possibly attempted reload automatically.
        else:
            b.require(self.reload_expected_from is None, 'Successful 54/66 must be followed directly by its planned reload')
            b.save(self.folder/(label+'_stopped.json'), self.guard())
        args = [str(b.CLI), '--device', 'GW5AT-60B', '--cable-index', '1', '--location', str(location), '--run', str(operation)]
        if operation in (54, 66):
            b.require(b.sha(b.IMAGE) == b.IMAGE_SHA, 'B4 image changed at Flash boundary')
            args += ['--spiaddr', '0x000000', '--fsFile', str(b.IMAGE)]
        if operation == 54: self.record['flash_write_attempted'] = True
        self.record['operations'].append(dict(operation=operation, label=label, args=args)); self.persist()
        output = self.child(args, label)
        b.require('Finished.' in output and not re.search(r'\b(error|failed)\b', output, re.I), 'Programmer output failed: ' + label)
        if operation == 0:
            identity = self.hw.identity(output)
            b.require(identity == (0x0001481B, 0xB0B4), 'Current device/UserCode must be B4')
            return identity
        if operation == 54:
            b.require('Program and Verify Flash successfully.' in output, 'Missing Flash program-and-verify success')
            self.record['flash_written'] = True
            self.reload_expected_from = 54
        if operation == 66:
            b.require('Verify Flash successfully.' in output, 'Missing independent Flash verify success')
            self.record['independent_flash_verify_passed'] = True
            self.reload_expected_from = 66
        if operation == 1: self.loaded_at = time.monotonic()
        self.persist()

    def run(self):
        self.persist()
        try:
            self.record['pins'] = b.offline()
            text = self.child([sys.executable, '-B', str(b.REPO/'firmware/B0B4/verify_release.py'), '--external-build'], 'qualification', 300)
            b.require(json.loads(text).get('passed') is True, 'Full offline qualification failed')
            spec = importlib.util.spec_from_file_location('b0b4_flash_inventory_definitions_only', b.HELPER)
            self.hw = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.hw)
            self.prior_sram()
            initial = self.guard(); uptime = initial['flight_info'].get('uptime_ms')
            b.require(type(uptime) is int and uptime >= 0, 'Current healthy uptime required')
            self.record['hardware_accessed'] = True
            self.operation(0, '01_before_flash_B4')
            self.health('02_current_sram_health', time.monotonic()-uptime/1000)
            self.defaults('03_before_flash_default_GET')
            self.operation(54, '04_B0B4_program_verify')
            self.operation(1, '05_B0B4_reload')
            self.health('06_B0B4_stopped_health', self.loaded_at)
            self.operation(0, '07_B0B4_identity')
            self.operation(66, '08_B0B4_independent_verify')
            self.operation(1, '09_B0B4_final_reload')
            self.health('10_B0B4_final_health', self.loaded_at)
            self.operation(0, '11_B0B4_final_identity')
            self.defaults('12_final_default_GET')
            self.record.update(passed=True, flash_contents_certified=True)
        except Exception as exc:
            self.record.update(error=type(exc).__name__+': '+str(exc), automatic_recovery=False)
            raise
        finally: self.persist()
        return self.record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--bench-confirmed-current', action='store_true')
    parser.add_argument('--flash-approved-current', action='store_true')
    parser.add_argument('--sram-receipt', type=Path)
    parser.add_argument('--sram-completion-receipt', type=Path)
    parser.add_argument('--completion-root-receipt', type=Path)
    parser.add_argument('--out', type=Path, default=b.DEFAULT_OUT)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(b.offline(), indent=2)); return
    b.require(args.bench_confirmed_current and args.flash_approved_current and args.sram_receipt is not None and
              args.sram_completion_receipt is not None and args.completion_root_receipt is not None,
              'Explicit current bench/Flash approval and SRAM evidence path required')
    folder = args.out.resolve()/('flash_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    result = FlashSession(folder, args.sram_receipt, args.sram_completion_receipt, args.completion_root_receipt).run()
    print(json.dumps(dict(passed=result['passed'], folder=str(folder), flash_contents_certified=result['flash_contents_certified'],
                          physical_cold_boot_verified=False, flight_ready=False), indent=2))


if __name__ == '__main__': main()
