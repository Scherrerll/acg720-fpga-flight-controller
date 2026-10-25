"""Read-only serial capture or offline A584 verification; never transmits bytes."""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import time

if __package__:
    from .protocol import FrameParser, StreamTracker
else:
    from protocol import FrameParser, StreamTracker


def open_read_only_serial(port, baud):
    import serial  # Optional dependency; offline decoding uses only stdlib.
    device = serial.Serial(port=None, baudrate=baud, timeout=0.2,
                           xonxoff=False, rtscts=False, dsrdtr=False)
    # Configure inactive states before opening. Some USB drivers can still
    # glitch modem-control lines on open; software cannot guarantee otherwise.
    device.dtr = False
    device.rts = False
    device.port = port
    device.open()
    return device


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=pathlib.Path, help="Existing raw.bin; no serial access")
    source.add_argument("--port", help="Explicit diagnostic USB serial port")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--output", type=pathlib.Path, required=True, help="New directory, never overwritten")
    parser.add_argument("--duration", type=float, help="Optional positive serial capture seconds")
    args = parser.parse_args(argv)
    if args.baud <= 0 or (args.duration is not None and args.duration <= 0):
        parser.error("baud and duration must be positive")
    if args.input and args.duration is not None:
        parser.error("--duration is for serial captures only")
    if args.input and not args.input.is_file():
        parser.error("--input must be an existing file")
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("--output already exists; choose a new directory")
    framing, tracker = FrameParser(), StreamTracker()
    read_errors, capture_errors, interrupted, error = 0, 0, False, None
    operation = "open_output"
    start = time.monotonic()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    device = None
    try:
        with (args.output / "raw.bin").open("xb") as raw, (args.output / "decoded.jsonl").open("x", encoding="utf-8") as decoded:
            operation = "open_input" if args.input else "open_serial"
            device = args.input.open("rb") if args.input else open_read_only_serial(args.port, args.baud)
            capture_started = time.monotonic()
            while args.duration is None or time.monotonic() - capture_started < args.duration:
                operation = "read"
                chunk = device.read(32768)
                if not chunk:
                    if args.input:
                        break
                    continue
                received_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                received_ns = time.monotonic_ns()
                operation = "write_raw"
                raw.write(chunk)
                operation = "decode_and_write_json"
                for frame in framing.feed(chunk):
                    for record in tracker.ingest(frame):
                        record["host_chunk_received_utc"] = received_utc
                        record["host_chunk_monotonic_ns"] = received_ns
                        record["host_time_basis"] = "offline_decode" if args.input else "serial_read_completion"
                        decoded.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                raw.flush()
                decoded.flush()
            operation = "recover_eof_and_write_json"
            for frame in framing.recover_eof():
                for record in tracker.ingest(frame):
                    record["host_chunk_received_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    record["host_chunk_monotonic_ns"] = time.monotonic_ns()
                    record["host_time_basis"] = "end_of_input_recovery"
                    decoded.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    except KeyboardInterrupt:
        interrupted = True
    except Exception as exc:
        if operation == "read":
            read_errors += 1
        else:
            capture_errors += 1
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if device is not None:
            try:
                device.close()
            except Exception as exc:
                capture_errors += 1
                if error is None:
                    error = f"{type(exc).__name__}: {exc}"
                    operation = "close_input"
        summary = dict(schema="b0b1.diagnostic.capture.v1", started_utc=started_utc,
            source=dict(input=str(args.input.resolve()) if args.input else None,
                        port=args.port, baud=args.baud if args.port else None),
            serial_writes=False, requested_dtr=False, requested_rts=False,
            parser=framing.finish(), stream=tracker.summary(), read_errors=read_errors,
            capture_errors=capture_errors, error_phase=operation if error else None,
            interrupted=interrupted, error=error, elapsed_host_s=time.monotonic() - start)
        (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str((args.output / "summary.json").resolve()))
    if error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
