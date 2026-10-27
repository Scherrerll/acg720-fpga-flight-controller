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


def successful_wait(value):
    return isinstance(value, dict) and value.get('normal_wait_return') is True and type(value.get('actual_p_wait')) is int and value['actual_p_wait'] == 0


class FlashSession(b.Session):
    def __init__(self, folder, sram_receipt):
        super().__init__('sram', folder)
        self.stage = 'flash'; self.sram_receipt = Path(sram_receipt).resolve(); self.loaded_at = None
        self.reload_expected_from = None
        self.record.update(stage='flash', script_sha256=b.sha(__file__), frozen_bench_sha256=BENCH_SHA,
                           flash_write_attempted=False, flash_contents_certified=False,
                           independent_flash_verify_passed=False, current_operator_flash_assertion=True)

    def prior_sram(self):
        path = self.sram_receipt
        b.require(path.name == 'stage_report.json' and path.is_relative_to((b.REPO/'out').resolve()), 'Use explicit SRAM stage receipt under repository out')
        report = json.loads(path.read_text(encoding='utf-8'))
        b.require(report.get('schema') == 'b0b4.bench-stage.v1' and report.get('stage') == 'sram' and
                  report.get('passed') is True and report.get('sram_written') is True and report.get('flash_written') is False and
                  report.get('script_sha256') == BENCH_SHA and report.get('image_sha256') == b.IMAGE_SHA and
                  report.get('manifest_sha256') == b.MANIFEST_SHA and
                  [item.get('operation') for item in report.get('operations', [])] == [0, 2, 0], 'Successful fixed-image SRAM evidence required')
        for label in ('qualification', '01_identity_before_cables', '01_identity_before', '02_B0B4_sram_cables',
                      '02_B0B4_sram', '04_identity_B0B4_cables', '04_identity_B0B4'):
            exit_path = path.parent/(label+'_exit.json'); value = json.loads(exit_path.read_text(encoding='utf-8'))
            b.require(successful_wait(value), 'SRAM stage child did not normally wait zero: ' + label)
            for stream in ('stdout', 'stderr'):
                b.require(b.sha(path.parent/(label+'_'+stream+'.log')) == value[stream+'_sha256'], 'Prior SRAM log changed: ' + label)
        identity_text = ''.join((path.parent/('04_identity_B0B4_'+stream+'.log')).read_text(encoding='utf-8', errors='replace') for stream in ('stdout', 'stderr'))
        b.require(self.hw.identity(identity_text) == (0x0001481B, 0xB0B4), 'Saved SRAM JTAG identity is not B4')
        get_path = path.parent/'05_sram_default_GET.json'; value = json.loads(get_path.read_text(encoding='utf-8'))
        active = value.get('active') or {}; result = value.get('result') or {}
        b.require(value.get('supported') is True and value.get('busy') is False and result.get('code') == 'queried' and
                  result.get('operation_id') == value.get('operation_id') and active.get('build') == '0000B0B4' and
                  active.get('p_wire') == 1000 and active.get('i_wire') == 350 and type(active.get('generation')) is int and
                  active['generation'] == 0, 'Saved SRAM B4 default GET required')
        health_path = path.parent/'03_sram_healthy.json'; health = json.loads(health_path.read_text(encoding='utf-8'))
        samples = health.get('samples') or []
        b.require(len(samples) >= 5, 'Saved SRAM health samples missing')
        for sample in samples: b.stopped(sample)
        for first, last in zip(samples, samples[1:]):
            b.require(last.get('imu_diagnostic_fresh') is True and
                      all(type(last['imu_diagnostic'].get(k)) is int and last['imu_diagnostic'][k] > first['imu_diagnostic'][k]
                          for k in ('raw_count', 'accepted_count', 'pose_count')), 'Saved SRAM IMU counts did not progress')
        self.record['prior_sram'] = dict(path=str(path), sha256=b.sha(path), default_GET_sha256=b.sha(get_path), health_sha256=b.sha(health_path))
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
    parser.add_argument('--out', type=Path, default=b.DEFAULT_OUT)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(b.offline(), indent=2)); return
    b.require(args.bench_confirmed_current and args.flash_approved_current and args.sram_receipt is not None,
              'Explicit current bench/Flash approval and SRAM evidence path required')
    folder = args.out.resolve()/('flash_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    result = FlashSession(folder, args.sram_receipt).run()
    print(json.dumps(dict(passed=result['passed'], folder=str(folder), flash_contents_certified=result['flash_contents_certified'],
                          physical_cold_boot_verified=False, flight_ready=False), indent=2))


if __name__ == '__main__': main()
