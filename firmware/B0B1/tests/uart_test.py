"""Compile passive UART tests and validate actual 54-clock/bit wire bytes.

Run from any directory. Generated vvp/hex files stay under repo/out/B0B1.
The interop hex is intentionally available for the ground parser's own test.
"""
from pathlib import Path
import argparse
import binascii
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
FW = HERE.parent
REPO = FW.parents[1]
OUT = REPO / 'out' / 'B0B1'
SOURCE = FW / 'source' / 'diagnostic_uart.v'


def tool(name):
    found = os.environ.get(name.upper()) or shutil.which(name)
    if found:
        return found
    bundled = REPO.parents[1] / '.tools' / 'iverilog' / 'app' / 'bin' / (name + '.exe')
    if bundled.exists():
        return str(bundled)
    raise RuntimeError(f'{name} not found; set {name.upper()} to its executable')


def run_tb(name, extra=()):
    target = OUT / (name + '.vvp')
    env = dict(os.environ)
    temp = OUT / 'tmp'
    temp.mkdir(parents=True, exist_ok=True)
    env.update(TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))
    subprocess.run([tool('iverilog'), '-g2012', '-Wall', '-s', name, '-o', str(target),
                    str(SOURCE), str(HERE / (name + '.v'))],
                   check=True, env=env)
    result = subprocess.run([tool('vvp'), str(target), *extra], check=False, env=env,
                            capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode:
        print(result.stderr.strip(), file=sys.stderr)
        result.check_returncode()


def pattern(base, length):
    body = bytearray((base + j) & 255 for j in range(length))
    if length == 28:
        body[26] &= 0x3f
    elif length == 88:
        body[0] &= 7
        body[1] %= 10
        body[48] &= 3
    return bytes(body)


def check_wire():
    wire = bytes(int(x, 16) for x in (OUT / 'uart_interop.hex').read_text().split())
    sizes = {1: 26, 2: 28, 3: 88, 4: 40}
    frames = []
    offset = 0
    while offset < len(wire):
        assert wire[offset:offset + 3] == b'\xa5\x84\x01', (offset, 'header')
        kind = wire[offset + 3]
        size = sizes[kind] + 12
        packet = wire[offset:offset + size]
        assert len(packet) == size, (offset, 'truncated frame')
        assert int.from_bytes(packet[-2:], 'big') == binascii.crc_hqx(packet[2:-2], 0xffff), (offset, 'CRC')
        assert int.from_bytes(packet[4:6], 'big') == len(frames) % 65536, 'transmit sequence'
        frames.append((kind, int.from_bytes(packet[6:10], 'big'), packet[10:-2]))
        offset += size
    expected = {
        1: [(0xfffffff0, pattern(0x10, 26)), (0x10, pattern(0x50, 26))],
        2: [(0x01020304, pattern(0x80, 28)), (0x05060708, pattern(0xa0, 28))],
        3: [(0x11112222, pattern(0, 88)), (0x33334444, pattern(0x90, 88)), (0x55556666, pattern(0x40, 88))],
    }
    for kind, items in expected.items():
        actual = [(tick, body) for t, tick, body in frames if t == kind]
        assert actual == items, (kind, 'payload/timestamp/queue order', actual)
    statuses = [(tick, body) for t, tick, body in frames if t == 4]
    status_ticks = [int(x, 16) for x in (OUT / 'uart_status_ticks.hex').read_text().split()]
    assert [tick for tick, _ in statuses] == status_ticks, 'status capture timestamps'
    assert len(statuses) >= 3
    for (left, _), (right, _) in zip(statuses, statuses[1:]):
        assert (right - left) & 0xffffffff == 200000, 'status periodicity'
    status_body = (0x0123456789abcdef).to_bytes(8, 'big')
    status_body += b''.join(x.to_bytes(4, 'big') for x in [0xb0b1, 3, 3, 0, 0, 0x12345678, 1111, 999])
    assert all(body == status_body for _, body in statuses), 'status wire layout/counters'
    print(f'UART_WIRE_PASS frames={len(frames)} bytes={len(wire)} CRC/payload/capture-tick/concurrency/drop/retry/status verified')
    print(f'Interop bytes: {OUT / "uart_interop.hex"}')


def main():
    global SOURCE, OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE, help='Isolated UART RTL variant to test')
    parser.add_argument('--output', type=Path, default=OUT, help='Directory for generated simulation/hex files')
    args = parser.parse_args()
    SOURCE = args.source.resolve()
    OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    run_tb('uart_queue_tb')
    run_tb('uart_edge_tb')
    run_tb('uart_fault_loss_tb')
    run_tb('uart_serial_tb', [f'+HEX={OUT / "uart_interop.hex"}', f'+STATUS={OUT / "uart_status_ticks.hex"}'])
    check_wire()
    run_tb('uart_load_tb')


if __name__ == '__main__':
    main()
