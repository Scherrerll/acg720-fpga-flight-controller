"""Pure XY P/I transactions; the existing serial owner performs every write."""
from collections import OrderedDict
import argparse
import importlib.util
import hashlib
import math
from pathlib import Path
import threading
import time


_CODEC_PATH = Path(__file__).resolve().parents[2] / 'firmware/B0B4/xy_pi_cli.py'
_SPEC = importlib.util.spec_from_file_location('b0b4_frozen_xy_pi_codec', _CODEC_PATH)
_CODEC = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CODEC)
encode_request = _CODEC.encode_request
gain = _CODEC.gain

# Byte-for-byte copy of the B0B5 codec from the manifest-bound review package:
# analysis/20261028_water_drive/qualified_offline_B0B5/xy_pi_cli.py
# Its parameter request/response format matches B0B4 except the A591 identity.
# B0B5 flight_core also enforces water_neutral && !water_enabled at commit.
# A changed package must be reviewed again.
_B0B5_CODEC_PATH = Path(__file__).resolve().parent / 'b0b5_xy_pi_codec.py'
_B0B5_CODEC_SHA256 = '869a061525ea11e25288acd187b61d848a12ebd2b51e2235f549e11699ef12b0'
_CODECS = {'B0B4': _CODEC}


def _codec_for_build(build):
    if build not in ('B0B4', 'B0B5'):
        raise ValueError('Parameter build must be exactly B0B4 or B0B5.')
    if build not in _CODECS:
        if hashlib.sha256(_B0B5_CODEC_PATH.read_bytes()).hexdigest() != _B0B5_CODEC_SHA256:
            raise ValueError('B0B5 codec differs from the reviewed package.')
        spec = importlib.util.spec_from_file_location('b0b5_frozen_xy_pi_codec', _B0B5_CODEC_PATH)
        codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codec)
        _CODECS[build] = codec
    return _CODECS[build]


def decode_parameter_response(packet, build='B0B4'):
    """Register this complete frame in PacketReceiver, never a parallel stream."""
    codec = _codec_for_build(build)
    row = codec.decode_response(packet)
    if row['opcode'] not in (1, 2) or row['status'] not in codec.STATUS:
        raise ValueError('unsupported parameter opcode/status')
    return dict(row, _protocol='a591')


class XYPIError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _uint32(value):
    return type(value) is int and 0 <= value <= 0xffffffff


def _gain_text(value):
    return f'{value // 10000}.{value % 10000:04d}'


class XYPIController:
    """One GET or SET-plus-readback operation, with no transport dependency.

    ``take_write`` marks an attempt before returning bytes. An I/O failure can
    therefore never turn a possibly transmitted SET into a safe retry. Callers
    must pass the receive connection epoch through to ``response``.
    """
    def __init__(self, enabled=False, clock=time.monotonic, sequence_start=None, timeout=3, build='B0B4'):
        _codec_for_build(build)
        self._build = '0000' + build
        if sequence_start is None:
            sequence_start = (time.time_ns() // 1000000) & 0xffffffff
        if not _uint32(sequence_start):
            raise XYPIError('invalid', 'Sequence start must fit unsigned 32 bits.')
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise XYPIError('invalid', 'Timeout must be a positive finite number.')
        self._lock = threading.RLock()
        self._clock = clock
        self._timeout = timeout
        self._next_sequence = sequence_start
        self._next_operation = 1
        self._next_token = 1
        self._requests = OrderedDict()
        self._enabled = bool(enabled)
        self._connected = False
        self._source = 'SiK'
        self._baud = 115200
        self._epoch = None
        self._supported = False
        self._active = None
        self._active_at = None
        self._phase = 'idle'
        self._operation_id = None
        self._operation = None
        self._command = None
        self._deadline = None
        self._result = None

    def connection(self, epoch, connected, source='SiK', baud=115200):
        with self._lock:
            changed = (epoch, bool(connected), source, baud) != (
                self._epoch, self._connected, self._source, self._baud)
            if changed:
                self._invalidate_locked('Connection or source changed; query again.')
            self._epoch = epoch
            self._connected = bool(connected)
            self._source = source
            self._baud = baud

    def invalidate(self, reason):
        with self._lock:
            self._invalidate_locked(str(reason))

    def _invalidate_locked(self, reason):
        self._supported = False
        self._active = None
        self._active_at = None
        if self._operation is not None:
            code = 'unknown' if self._operation['set_attempted'] else 'cancelled'
            self._finish_locked(code, reason)
        elif self._operation_id is not None and self._result['code'] not in ('unknown', 'mismatch'):
            sequence = self._result['sequence'] if self._result else None
            self._result = dict(code='cancelled', message=reason,
                                operation_id=self._operation_id, sequence=sequence)

    def _check_connection_locked(self, epoch):
        if not self._enabled:
            raise XYPIError('unsupported', 'Parameter controls are disabled.')
        if epoch != self._epoch:
            raise XYPIError('stale', 'Connection changed; query the current connection.')
        if not self._connected:
            raise XYPIError('notconnected', 'No serial connection.')
        if self._source != 'SiK' or self._baud != 115200:
            raise XYPIError('unsupported', 'Parameters require the SiK 115200 connection.')
        if self._operation is not None:
            raise XYPIError('busy', 'A parameter operation is already in flight.')

    def _cached_locked(self, request_id, intent):
        if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
            raise XYPIError('invalid', 'request_id must contain 1..128 characters.')
        if request_id in self._requests:
            previous, operation_id = self._requests[request_id]
            if previous != intent:
                raise XYPIError('invalid', 'request_id was already used for a different intent.')
            return operation_id
        return None

    def _sequence_locked(self):
        if self._next_sequence > 0xffffffff:
            raise XYPIError('invalid', 'Sequence space exhausted; automatic wrap is disabled.')
        result = self._next_sequence
        self._next_sequence += 1
        return result

    def _begin_locked(self, request_id, intent, opcode, target=None):
        sequence = self._sequence_locked()
        operation_id = self._next_operation
        self._next_operation += 1
        self._operation_id = operation_id
        self._operation = dict(sequence=sequence, target=target, set_attempted=False, ack=None)
        self._result = None
        self._requests[request_id] = (intent, operation_id)
        if len(self._requests) > 32:
            self._requests.popitem(last=False)
        self._queue_locked(opcode, sequence, 'queued_set' if opcode == 2 else 'queued_get')
        return operation_id

    def request_get(self, request_id, epoch):
        with self._lock:
            self._expire_locked()
            intent = ('get', epoch)
            cached = self._cached_locked(request_id, intent)
            if cached is not None:
                return cached
            self._check_connection_locked(epoch)
            return self._begin_locked(request_id, intent, 1)

    def request_set(self, p_text, i_text, request_id, expected_generation, epoch):
        with self._lock:
            self._expire_locked()
            # Keep the exact submitted decimal intent; never accept floats and
            # never silently round values onto the wire grid.
            if not isinstance(p_text, str) or not isinstance(i_text, str):
                raise XYPIError('invalid', 'P and I must be decimal strings.')
            try:
                p_wire, i_wire = gain(p_text), gain(i_text)
            except (argparse.ArgumentTypeError, ArithmeticError, ValueError, TypeError) as exc:
                raise XYPIError('invalid', str(exc)) from exc
            if not _uint32(expected_generation):
                raise XYPIError('invalid', 'Expected generation must fit unsigned 32 bits.')
            intent = ('set', p_text, i_text, expected_generation, epoch)
            cached = self._cached_locked(request_id, intent)
            if cached is not None:
                return cached
            self._check_connection_locked(epoch)
            if not self._supported or self._active is None:
                raise XYPIError('unsupported', 'A successful GET is required before SET.')
            if expected_generation != self._active['generation']:
                raise XYPIError('stale', 'Generation changed; query before a new SET.')
            return self._begin_locked(request_id, intent, 2, (p_wire, i_wire))

    def _queue_locked(self, opcode, sequence, phase):
        p_wire, i_wire = self._operation['target'] if opcode == 2 else (0, 0)
        self._command = dict(token=None, opcode=opcode, sequence=sequence,
                             packet=encode_request(opcode, sequence, p_wire, i_wire))
        self._phase = phase
        self._deadline = self._clock() + self._timeout

    def take_write(self, epoch):
        with self._lock:
            self._expire_locked()
            if epoch != self._epoch or not self._connected or self._command is None:
                return None
            phases = {'queued_get': 'await_get', 'queued_set': 'await_set_ack',
                      'queued_verify_get': 'await_verify_get'}
            if self._phase not in phases:
                return None
            self._phase = phases[self._phase]
            self._command['token'] = self._next_token
            self._next_token += 1
            self._deadline = self._clock() + self._timeout
            if self._command['opcode'] == 2:
                self._operation['set_attempted'] = True
                self._active = None
                self._active_at = None
            return dict(self._command)

    def write_result(self, token, count, error=None):
        with self._lock:
            if self._command is None or self._command['token'] is None or token != self._command['token']:
                return
            if error is not None or type(count) is not int or count != len(self._command['packet']):
                code = 'unknown' if self._operation['set_attempted'] else 'cancelled'
                self._finish_locked(code, 'Serial write failed or was incomplete; query again.', invalidate=True)

    def decode_parameter_response(self, packet):
        return decode_parameter_response(packet, self._build[4:])

    def _valid_response(self, row):
        return (isinstance(row, dict) and row.get('_protocol') == 'a591'
                and type(row.get('protocol')) is int and row['protocol'] == 1
                and type(row.get('opcode')) is int and row['opcode'] in (1, 2)
                and type(row.get('status')) is int and row['status'] in _CODEC.STATUS
                and _uint32(row.get('sequence')) and _uint32(row.get('generation'))
                and all(type(row.get(k)) is int and 0 <= row[k] <= 10000 for k in ('p_wire', 'i_wire'))
                and row.get('build') == self._build)

    def _observe_locked(self, row):
        self._active = dict(p_text=_gain_text(row['p_wire']), i_text=_gain_text(row['i_wire']),
                            p_wire=row['p_wire'], i_wire=row['i_wire'],
                            generation=row['generation'], build=row['build'])
        self._active_at = self._clock()

    def response(self, row, epoch):
        with self._lock:
            self._expire_locked()
            if (epoch != self._epoch or not self._connected or self._command is None
                    or self._phase not in ('await_get', 'await_set_ack', 'await_verify_get')
                    or not self._valid_response(row)
                    or row['opcode'] != self._command['opcode']
                    or row['sequence'] != self._command['sequence']):
                return
            if row['status'] != 0:
                if self._phase == 'await_verify_get':
                    self._finish_locked('unknown', 'SET acknowledged, but independent GET failed; query again.', invalidate=True)
                else:
                    code = {4: 'locked', 5: 'stale_sequence'}.get(row['status'], 'nack')
                    if self._phase == 'await_set_ack':
                        self._observe_locked(row)
                    else:
                        self._supported = False
                        self._active = None
                        self._active_at = None
                    self._finish_locked(code, 'FPGA rejected the request: ' + _CODEC.STATUS[row['status']] + '. No automatic retry.')
                return
            if self._phase == 'await_get':
                self._observe_locked(row)
                self._supported = True
                self._finish_locked('queried', 'Active parameters queried; valid for this power cycle only.')
            elif self._phase == 'await_set_ack':
                if (row['p_wire'], row['i_wire']) != self._operation['target']:
                    self._finish_locked('mismatch', 'SET ACK values differ from the requested pair; query again.', invalidate=True)
                    return
                self._operation['ack'] = (row['p_wire'], row['i_wire'], row['generation'])
                try:
                    sequence = self._sequence_locked()
                except XYPIError:
                    self._finish_locked('unknown', 'SET acknowledged; sequence space prevents independent GET.', invalidate=True)
                    return
                self._queue_locked(1, sequence, 'queued_verify_get')
            else:
                observed = (row['p_wire'], row['i_wire'], row['generation'])
                if observed != self._operation['ack']:
                    self._finish_locked('mismatch', 'Independent GET differs from the SET ACK; query again.', invalidate=True)
                    return
                self._observe_locked(row)
                self._supported = True
                self._finish_locked('verified', 'SET ACK and independent GET verified; this power cycle only.')

    def _finish_locked(self, code, message, invalidate=False):
        sequence = self._operation['sequence']
        self._result = dict(code=code, message=message, operation_id=self._operation_id, sequence=sequence)
        self._operation = None
        self._command = None
        self._deadline = None
        self._phase = 'idle'
        if invalidate:
            self._supported = False
            self._active = None
            self._active_at = None

    def _expire_locked(self):
        if self._operation is not None and self._clock() >= self._deadline:
            if self._operation['set_attempted']:
                self._finish_locked('unknown', 'SET outcome or readback is unknown; query before a new SET.', invalidate=True)
            elif self._phase == 'queued_set':
                self._finish_locked('cancelled', 'SET expired before a wire attempt.', invalidate=True)
            else:
                self._finish_locked('timeout', 'GET timed out; parameter support is unconfirmed.', invalidate=True)

    def tick(self):
        with self._lock:
            self._expire_locked()

    def snapshot(self):
        with self._lock:
            self._expire_locked()
            active = dict(self._active) if self._active is not None else None
            if active is not None:
                active['age_ms'] = max(0, round((self._clock() - self._active_at) * 1000, 1))
            return dict(enabled=self._enabled, connected=self._connected, expected_build=self._build,
                        source=self._source, baud=self._baud, epoch=self._epoch,
                        supported=self._supported, busy=self._operation is not None,
                        phase=self._phase, operation_id=self._operation_id, active=active,
                        result=dict(self._result) if self._result is not None else None)
