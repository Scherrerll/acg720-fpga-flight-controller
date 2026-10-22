"""MTF-01P (MicoAir) Micolink monitor for a standalone bench check.

Reads the module's UART (Micolink protocol), validates every frame checksum and
decodes the ranging+flow payload (msg_id 0x51). Prints a 1 Hz health summary and
optionally records a CSV for later axis/scale review. This script does NOT talk
to the FPGA and never writes to the module.

Micolink frame: 0xEF | dev_id | sys_id | msg_id | seq | len | payload[len] | sum
checksum = (sum of the first len+6 bytes) & 0xFF
msg 0x51 payload (20 bytes, little endian):
  u32 time_ms, u32 distance_mm (0 = invalid, min 10),
  u8 strength, u8 precision, u8 tof_status, u8 rsvd,
  s16 flow_vel_x, s16 flow_vel_y   [cm/s at 1 m height],
  u8 flow_quality, u8 flow_status, u16 rsvd2

Usage:
  python micolink_monitor.py --self-test
  python micolink_monitor.py --port COM24 --csv mtf01p_bench.csv
"""
from __future__ import annotations

import argparse
import csv
import struct
import sys
import time

HEAD = 0xEF
MSG_RANGE_SENSOR = 0x51
PAYLOAD_FMT = '<IIBBBBhhBBH'


class MicolinkParser:
    def __init__(self):
        self.state = 0
        self.msg = {'head': 0, 'dev': 0, 'sys': 0, 'id': 0, 'seq': 0,
                    'len': 0, 'payload': bytearray(), 'checksum': 0}
        self.frames = 0
        self.checksum_errors = 0
        self.length_errors = 0
        self.byte_count = 0

    def feed(self, data: int):
        """Feed one byte; return a dict on a valid complete frame, else None."""
        self.byte_count += 1
        s = self.state
        if s == 0:
            if data == HEAD:
                self.msg['head'] = data
                self.msg['payload'] = bytearray()
                self.state = 1
        elif s == 1:
            self.msg['dev'] = data
            self.state = 2
        elif s == 2:
            self.msg['sys'] = data
            self.state = 3
        elif s == 3:
            self.msg['id'] = data
            self.state = 4
        elif s == 4:
            self.msg['seq'] = data
            self.state = 5
        elif s == 5:
            self.msg['len'] = data
            if data == 0:
                self.state = 7
            elif data > 64:
                self.length_errors += 1
                self.state = 0
            else:
                self.state = 6
        elif s == 6:
            self.msg['payload'].append(data)
            if len(self.msg['payload']) == self.msg['len']:
                self.state = 7
        elif s == 7:
            self.msg['checksum'] = data
            expected = 0
            raw = bytes([self.msg['head'], self.msg['dev'], self.msg['sys'],
                         self.msg['id'], self.msg['seq'], self.msg['len']])
            raw += bytes(self.msg['payload'])
            for byte in raw:
                expected = (expected + byte) & 0xFF
            self.state = 0
            if expected == self.msg['checksum']:
                self.frames += 1
                return dict(self.msg)
            self.checksum_errors += 1
        else:
            self.state = 0
        return None


def decode_range(payload: bytes):
    fields = struct.unpack(PAYLOAD_FMT, payload) if len(payload) >= struct.calcsize(PAYLOAD_FMT) else None
    if not fields:
        return None
    time_ms, distance_mm, strength, precision, tof_status, _rsvd, vx, vy, quality, flow_status, _rsvd2 = fields
    return dict(time_ms=time_ms, distance_mm=distance_mm, strength=strength,
                precision=precision, tof_status=tof_status,
                flow_vel_x=vx, flow_vel_y=vy, flow_quality=quality,
                flow_status=flow_status, distance_valid=distance_mm >= 10)


def self_test():
    def frame(seq, time_ms, distance_mm, strength, precision, tof, vx, vy, quality, fstatus):
        payload = struct.pack(PAYLOAD_FMT, time_ms, distance_mm, strength, precision,
                              tof, 0, vx, vy, quality, fstatus, 0)
        raw = bytes([HEAD, 0x10, 0x01, MSG_RANGE_SENSOR, seq, len(payload)]) + payload
        return raw + bytes([sum(raw) & 0xFF, 0x00])

    parser = MicolinkParser()
    frames = []
    for seq in range(5):
        for byte in frame(seq, seq * 10, 1234 + seq, 40, 2, 0, 12 - seq, -3, 66, 1):
            got = parser.feed(byte)
            if got:
                frames.append(got)
    assert len(frames) == 5, len(frames)
    decoded = [decode_range(f['payload']) for f in frames if f['id'] == MSG_RANGE_SENSOR]
    assert len(decoded) == 5
    assert decoded[0]['distance_mm'] == 1234 and decoded[0]['flow_vel_x'] == 12
    assert decoded[4]['flow_vel_y'] == -3 and decoded[4]['distance_valid'] is True
    # Corrupted checksum must be rejected.
    bad = bytearray(frame(9, 0, 300, 10, 1, 0, 1, 2, 50, 1))
    bad[-2] ^= 0xFF
    before = parser.checksum_errors
    for byte in bad:
        parser.feed(byte)
    assert parser.checksum_errors == before + 1
    print('SELF_TEST PASS: 5 frames decoded, checksum corruption rejected')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--csv')
    ap.add_argument('--duration', type=float, default=0, help='seconds, 0 = until Ctrl+C')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.port:
        ap.error('--port is required (or use --self-test)')
    try:
        import serial  # pyserial
    except ImportError:
        sys.exit('pyserial is required: pip install pyserial')
    parser = MicolinkParser()
    csv_file = open(args.csv, 'w', newline='', encoding='utf-8') if args.csv else None
    writer = None
    if csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['wall_s', 'time_ms', 'distance_mm', 'strength', 'precision',
                         'tof_status', 'flow_vel_x', 'flow_vel_y', 'flow_quality',
                         'flow_status'])
    last = time.monotonic()
    frames_in_window = 0
    started = time.monotonic()
    try:
        with serial.Serial(args.port, args.baud, timeout=0.2) as link:
            while True:
                chunk = link.read(256)
                for byte in chunk:
                    frame = parser.feed(byte)
                    if not frame:
                        continue
                    frames_in_window += 1
                    if frame['id'] != MSG_RANGE_SENSOR:
                        continue
                    decoded = decode_range(frame['payload'])
                    if decoded is None:
                        continue
                    if writer:
                        writer.writerow([f'{time.monotonic() - started:.3f}', decoded['time_ms'],
                                         decoded['distance_mm'], decoded['strength'],
                                         decoded['precision'], decoded['tof_status'],
                                         decoded['flow_vel_x'], decoded['flow_vel_y'],
                                         decoded['flow_quality'], decoded['flow_status']])
                    now = time.monotonic()
                    if now - last >= 1.0:
                        print(f"frames/s={frames_in_window / (now - last):5.1f} "
                              f"dist={decoded['distance_mm']:5d}mm({decoded['distance_valid']}) "
                              f"vx={decoded['flow_vel_x']:6d} vy={decoded['flow_vel_y']:6d} "
                              f"q={decoded['flow_quality']:3d} fstat={decoded['flow_status']} "
                              f"str={decoded['strength']:3d} tof={decoded['tof_status']} "
                              f"csum_err={parser.checksum_errors}", flush=True)
                        frames_in_window = 0
                        last = now
                if args.duration and time.monotonic() - started >= args.duration:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        if csv_file:
            csv_file.close()
        print(f"total frames={parser.frames} checksum_errors={parser.checksum_errors} "
              f"length_errors={parser.length_errors} bytes={parser.byte_count}")


if __name__ == '__main__':
    main()
