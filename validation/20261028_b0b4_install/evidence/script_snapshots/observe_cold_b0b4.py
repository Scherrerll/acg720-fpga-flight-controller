"""Read-only B0B4 cold-start observer; default is offline, never opens serial.

The existing COM17 ground owner alone sends one parameter GET. Physical power
removal (all LEDs off for >=5 seconds, then battery-only power) is a human fact
recorded separately. Software observations cannot certify that physical fact.
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
FLASH = Path(__file__).with_name('flash_b0b4.py')
FLASH_SHA = '0a50b2c822659b4efc5951ed781dc582bc4c4f874bc56dbdd6fc7d434b1d5a28'
IMAGE_SHA = '199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610'
if hashlib.sha256(BENCH.read_bytes()).hexdigest() != BENCH_SHA:
    raise ValueError('Frozen bench definitions changed')
SPEC = importlib.util.spec_from_file_location('b0b4_cold_frozen_bench', BENCH)
b = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(b)
COUNTERS = ('raw_count', 'accepted_count', 'pose_count')
FLAGS = ('calibrated', 'attitude_valid', 'sensor_ok')
OPERATIONS = ((0, '01_before_flash_B4'), (54, '04_B0B4_program_verify'),
              (1, '05_B0B4_reload'), (0, '07_B0B4_identity'),
              (66, '08_B0B4_independent_verify'), (1, '09_B0B4_final_reload'),
              (0, '11_B0B4_final_identity'))


def offline():
    """Local pins only: no HTTP, child process, programmer, or serial access."""
    b.require(b.sha(BENCH) == BENCH_SHA and b.sha(FLASH) == FLASH_SHA and
              b.sha(b.IMAGE) == IMAGE_SHA, 'Pinned cold-observation input changed')
    return dict(passed=True, offline=True, hardware_accessed=False, http_accessed=False,
                frozen_bench_sha256=BENCH_SHA, flash_script_sha256=FLASH_SHA,
                image_sha256=IMAGE_SHA, physical_cold_boot_verified=False, flight_ready=False)


def zero_wait(value):
    return isinstance(value, dict) and value.get('normal_wait_return') is True and \
        type(value.get('actual_p_wait')) is int and value['actual_p_wait'] == 0


def flash_evidence(receipt, root_receipt):
    """Bind actual root/child zero waits, fixed image, and unchanged Flash logs."""
    receipt = Path(receipt).resolve(); root_receipt = Path(root_receipt).resolve()
    out = (b.REPO/'out').resolve()
    b.require(receipt.name == 'stage_report.json' and receipt.is_relative_to(out) and
              root_receipt.is_relative_to(out), 'Explicit Flash receipts must be under repository out')
    report = json.loads(receipt.read_text(encoding='utf-8-sig'))
    root = json.loads(root_receipt.read_text(encoding='utf-8-sig'))
    b.require(report.get('schema') == 'b0b4.bench-stage.v1' and report.get('stage') == 'flash' and
              all(report.get(k) is True for k in ('passed', 'flash_written', 'flash_contents_certified',
                                                 'independent_flash_verify_passed')) and
              report.get('script_sha256') == FLASH_SHA and report.get('image_sha256') == IMAGE_SHA and
              report.get('manifest_sha256') == b.MANIFEST_SHA, 'Successful fixed-image Flash receipt required')
    b.require(zero_wait(root) and Path(root.get('stage_report', '')).resolve() == receipt and
              root.get('stage_report_sha256') == b.sha(receipt), 'Actual Flash root zero must bind the unchanged stage report')
    operations = report.get('operations') or []
    b.require([(v.get('operation'), v.get('label')) for v in operations] == list(OPERATIONS),
              'Flash operation sequence differs')
    bindings = {str(receipt): b.sha(receipt), str(root_receipt): b.sha(root_receipt)}
    labels = ['qualification'] + [label+suffix for _, label in OPERATIONS for suffix in ('_cables', '')]
    for label in labels:
        path = receipt.parent/(label+'_exit.json'); child = json.loads(path.read_text(encoding='utf-8-sig'))
        b.require(zero_wait(child), 'Flash child did not normally wait zero: '+label)
        bindings[str(path)] = b.sha(path)
        for stream in ('stdout', 'stderr'):
            log = receipt.parent/(label+'_'+stream+'.log')
            b.require(b.sha(log) == child.get(stream+'_sha256'), 'Flash child log changed: '+label)
            bindings[str(log)] = b.sha(log)
        if label in dict((label, op) for op, label in OPERATIONS):
            op = next(v for v in operations if v['label'] == label)
            b.require(child.get('args') == op.get('args'), 'Flash child arguments differ: '+label)
            if op['operation'] in (54, 66):
                b.require(op['args'][-4:] == ['--spiaddr', '0x000000', '--fsFile', str(b.IMAGE)],
                          'Flash child must use fixed SPI address and image')
    return dict(path=str(receipt), sha256=b.sha(receipt), root_path=str(root_receipt),
                root_sha256=b.sha(root_receipt), actual_p_wait=0, bound_inputs=bindings)


def brief(value):
    """Persist a telemetry allowlist, never session responses or raw radio bytes."""
    data = value.get('data') or {}; info = value.get('flight_info') or {}; imu = value.get('imu_diagnostic') or {}
    return dict(sequence=value.get('sequence'), info_sequence=info.get('sequence'),
                connected=value.get('connected'), fresh=value.get('fresh'),
                flight_info_fresh=value.get('flight_info_fresh'), uptime_ms=info.get('uptime_ms'),
                telemetry_build_id=info.get('build_id'), taking_off=info.get('taking_off'),
                imu_diagnostic_fresh=value.get('imu_diagnostic_fresh'),
                imu_sequence=imu.get('sequence'), imu_build_id=imu.get('build_id'),
                **{k: data.get(k) for k in (*FLAGS, 'armed', 'controller_enabled', 'command_fresh',
                                           'physical_output_active', 'pwm_us', 'command_us', 'rc_valid', 'rc_us')},
                **{k: imu.get(k) for k in COUNTERS})


def status_brief(value):
    active = value.get('active') or {}; result = value.get('result') or {}
    return dict(epoch=value.get('epoch'), operation_id=value.get('operation_id'), busy=value.get('busy'),
                supported=value.get('supported'), can_query=value.get('can_query'),
                active={k: active.get(k) for k in ('build', 'p_wire', 'i_wire', 'generation')},
                result={k: result.get(k) for k in ('code', 'operation_id')})


class StartupWaiting(RuntimeError):
    """Explicit receiver-not-valid state after independently observed boot evidence."""


class Observer:
    def __init__(self, folder, receipt, root_receipt, duration=600):
        b.require(type(duration) in (int, float) and 0 < duration <= 600, 'Observation limit must be <=600 seconds')
        self.folder = Path(folder); self.receipt = receipt; self.root_receipt = root_receipt
        self.duration = duration; self.deadline = None; self.stream = None
        self.record = dict(schema='b0b4.cold-observation.v1', stage='cold_observation', passed=False,
                           **{'pass': False}, started_utc=b.utc(), script_sha256=b.sha(__file__),
                           frozen_bench_sha256=BENCH_SHA, flash_script_sha256=FLASH_SHA, image_sha256=IMAGE_SHA,
                           observed_stale_or_offline=False, uptime_reset=False, healthy_new_boot=False,
                           default_GET=False, physical_cold_boot_verified=False, flight_ready=False,
                           human_power_cycle_fact_required=True, hardware_writes=False, serial_opened=False,
                           programmer_invoked=False, automatic_recovery=False, http_accessed=False,
                           observation_limit_s=duration)

    def persist(self):
        self.record['updated_utc'] = b.utc(); b.save(self.folder/'summary.json', self.record)

    def log(self, event, value=None, **extra):
        item = dict(utc=b.utc(), event=event, **extra)
        if value is not None: item['telemetry'] = brief(value)
        if self.stream is not None:
            self.stream.write(json.dumps(item, ensure_ascii=False)+'\n'); self.stream.flush()

    def read_stopped(self, allow_offline=False, allow_startup=False):
        """Retry only the exact same-group ValueError, bounded to three seconds."""
        deadline = min(time.monotonic()+3, self.deadline or float('inf'))
        while True:
            value = b.http('/api/state'); self.log('state', value)
            try:
                return b.stopped(value)  # UnsafeActivity always propagates immediately.
            except ValueError as exc:
                if str(exc) == 'Same-group telemetry required':
                    if time.monotonic() >= deadline: raise
                    self.log('same_group_wait'); time.sleep(.05); continue
                if allow_offline and str(exc) == 'Fresh live telemetry required':
                    return None
                baseline = self.record.get('baseline') or {}
                current = (value.get('flight_info') or {}).get('uptime_ms')
                before = baseline.get('uptime_ms')
                boot_seen = self.record['observed_stale_or_offline'] or self.record['uptime_reset'] or \
                    (type(current) is int and type(before) is int and 0 <= current < before)
                # All owner/identity/same-group/output guards ran before the RC guard.
                # Only an explicit receiver-not-valid state may wait during startup.
                if allow_startup and boot_seen and str(exc) == 'Complete live RC required' and \
                        (value.get('data') or {}).get('rc_valid') is False:
                    self.log('startup_wait', value, reason='RC receiver not valid yet')
                    raise StartupWaiting() from None
                raise

    def defaults(self, baseline_status):
        """One new GET through the existing owner; token exists only in memory."""
        self.read_stopped(); status = b.http('/api/xy-pi/status')
        b.require(status.get('busy') is False and status.get('can_query') is True and
                  type(status.get('epoch')) is int and status['epoch'] != baseline_status['epoch'],
                  'New boot transport epoch and idle query owner required')
        prior_operation = status.get('operation_id')
        token = b.http('/api/xy-pi/session').get('token')
        try:
            reply = b.http('/api/xy-pi/query', dict(request_id=self.folder.name+'-cold-default-GET',
                                                  epoch=status['epoch']), token)
        finally:
            token = None
        operation_id = reply.get('operation_id')
        b.require(type(operation_id) is int and operation_id != prior_operation and
                  operation_id != baseline_status.get('operation_id'), 'New GET operation required')
        deadline = min(time.monotonic()+7, self.deadline)
        while time.monotonic() < deadline:
            self.read_stopped(); value = b.http('/api/xy-pi/status')
            b.require(value.get('epoch') == status['epoch'], 'Transport epoch changed during cold GET')
            if value.get('busy') is False and value.get('operation_id') == operation_id:
                active = value.get('active') or {}; result = value.get('result') or {}
                b.require(value.get('supported') is True and result.get('code') == 'queried' and
                          result.get('operation_id') == operation_id and active.get('build') == '0000B0B4' and
                          type(active.get('p_wire')) is int and active['p_wire'] == 1000 and
                          type(active.get('i_wire')) is int and active['i_wire'] == 350 and
                          type(active.get('generation')) is int and active['generation'] == 0,
                          'Fresh A591 B0B4 cold defaults GET failed')
                saved = status_brief(value); b.save(self.folder/'default_GET.json', saved)
                return saved
            time.sleep(.1)
        raise TimeoutError('Cold default GET timed out; no automatic retry')

    def run(self):
        self.persist()
        try:
            self.record['pins'] = offline()
            self.record['prior_flash'] = flash_evidence(self.receipt, self.root_receipt)
            with (self.folder/'samples.jsonl').open('w', encoding='utf-8') as self.stream:
                self.record['http_accessed'] = True
                baseline = self.read_stopped(); uptime = baseline['flight_info'].get('uptime_ms')
                b.require(type(uptime) is int and uptime >= 0, 'Fresh baseline uptime required')
                before_status = b.http('/api/xy-pi/status')
                b.require(before_status.get('busy') is False and type(before_status.get('epoch')) is int,
                          'Idle baseline owner and epoch required')
                self.record.update(baseline=brief(baseline), baseline_status=status_brief(before_status),
                                   baseline_ready_utc=b.utc())
                b.save(self.folder/'baseline.json', self.record['baseline']); self.persist()
                print(json.dumps(dict(event='BASELINE_READY', folder=str(self.folder), baseline_uptime_ms=uptime,
                                      instruction='Human: remove all power, LEDs off >=5 seconds, then battery-only power; record that fact separately.',
                                      physical_cold_boot_verified=False)), flush=True)
                self.deadline = time.monotonic()+self.duration; good = []; last_uptime = uptime
                while time.monotonic() < self.deadline:
                    try:
                        value = self.read_stopped(allow_offline=True, allow_startup=True)
                    except StartupWaiting:
                        good = []; time.sleep(.2); continue
                    except OSError as exc:
                        self.record['observed_stale_or_offline'] = True; good = []
                        self.log('http_unavailable', error_type=type(exc).__name__)
                        time.sleep(.2); continue
                    if value is None:
                        self.record['observed_stale_or_offline'] = True; good = []
                        time.sleep(.2); continue
                    data = value['data']; info = value['flight_info']; imu = value.get('imu_diagnostic') or {}
                    current = info.get('uptime_ms'); b.require(type(current) is int and current >= 0, 'Valid uptime required')
                    if current < last_uptime:
                        self.record.update(uptime_reset=True, first_new_boot=brief(value)); good = []
                        self.log('uptime_reset', before_ms=last_uptime, after_ms=current)
                    last_uptime = current
                    healthy = all(data.get(k) is True for k in FLAGS) and value.get('imu_diagnostic_fresh') is True and \
                        imu.get('build_id') == 0xB0B2 and type(imu.get('sequence')) is int and \
                        all(type(imu.get(k)) is int and imu[k] >= 0 for k in COUNTERS)
                    if self.record['uptime_reset'] and healthy:
                        sample = brief(value)
                        if good and sample['sequence'] == good[-1]['sequence']:
                            time.sleep(.2); continue
                        if good and (current <= good[-1]['uptime_ms'] or
                                     any(imu[k] <= good[-1][k] for k in COUNTERS)):
                            good = []
                        good.append(sample)
                        if len(good) >= 10:
                            self.record.update(healthy_new_boot=True, healthy_new_boot_samples=good,
                                               after=sample, final_health={k: data[k] for k in FLAGS})
                            b.require(self.record['observed_stale_or_offline'], 'Power interruption telemetry gap required')
                            self.record['default_GET_result'] = self.defaults(before_status)
                            self.record['default_GET'] = True
                            bindings = self.record['prior_flash']['bound_inputs']
                            b.require(all(b.sha(p) == digest for p, digest in bindings.items()),
                                      'Flash evidence changed during observation')
                            self.record.update(passed=True, **{'pass': True}); break
                    else:
                        good = []
                    time.sleep(.2)
                else:
                    raise TimeoutError('No stopped healthy new boot and fresh B4 GET within observation limit')
        except Exception as exc:
            # Do not persist arbitrary external exception text or HTTP/session content.
            self.record['error_type'] = type(exc).__name__
            if type(exc) in (ValueError, TimeoutError, b.UnsafeActivity):
                self.record['error'] = str(exc)
            raise
        finally:
            self.stream = None; self.record['finished_utc'] = b.utc(); self.persist()
        return self.record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe', action='store_true')
    parser.add_argument('--flash-receipt', type=Path)
    parser.add_argument('--flash-root-receipt', type=Path)
    args = parser.parse_args(argv)
    if not args.observe:
        print(json.dumps(offline(), indent=2)); return
    b.require(args.flash_receipt is not None and args.flash_root_receipt is not None,
              'Successful Flash report and actual root-zero receipt required')
    folder = b.DEFAULT_OUT/('cold_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    result = Observer(folder, args.flash_receipt, args.flash_root_receipt).run()
    print(json.dumps(dict(passed=result['passed'], folder=str(folder), physical_cold_boot_verified=False,
                          human_power_cycle_fact_required=True, flight_ready=False)), flush=True)


if __name__ == '__main__': main()
