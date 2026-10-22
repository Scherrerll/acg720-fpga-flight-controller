# Portable read-only ground station

Python 3.10+ and `pyserial` are required. Keep `ground/` and `support/` adjacent;
the original workspace, FPGA tools, vendor libraries and flight logs are not needed.
Files derive from the selected B0AE ground station. `export_manifest.json` records
original source hashes, export hashes and changes; it does not grant an additional
license to third-party material. Original source headers remain in copied modules.

From the export root:

```sh
python -m pip install -r ground/requirements.txt
python -B ground/launch.py --no-serial --logs ground/runtime --http-port 8765
```

Open `http://127.0.0.1:8765/` manually. `--http-port` is configurable; 0 asks the OS
for an available port, printed at startup. HTTP binds only to 127.0.0.1.
To receive telemetry, omit `--no-serial` and explicitly provide the device:

```sh
python -B ground/launch.py --port COM5 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

Use your actual port (`/dev/ttyUSB0` on Linux); no original COM17/COM23 default is
assumed. Baud choices are 57600/115200 and source labels are SiK/USB.
Opening the serial device is opt-in through that command. The receiver never calls
serial write; calibration, firmware programming and aircraft command endpoints are
absent/blocked. DTR/RTS are configured false before opening, as in the source.
The Logs page can change receiver source, add local markers, analyze recorded
sessions and download CSV/ZIP snapshots; these actions do not command the aircraft.
In offline mode device enumeration and receiver source switching are disabled.

`--logs` is required. Use an external writable directory or ignored `ground/runtime/`.
The program does not stop existing services, take over occupied ports, or open a
browser automatically. Ctrl+C stops this instance and closes its log writer.
Sessions contain raw serial bytes, USB identifiers and host timestamps; keep runtime
data out of source control. No historical raw logs or calibration receipts ship here.
The displayed PWM is received telemetry, not a live physical waveform measurement.

Offline proof, without opening any serial device or listening socket:

```sh
python -B -m unittest discover -s ground -p "test_*.py" -v
```

The focused tests use synthetic CRC frames, temporary logs and in-memory HTTP
requests. `test_ano_control.py` is preserved source coverage. Historical
`test_system.py`, `test_mtf.py` and `test_review_fixes.py` were excluded because they
depend on original logs/test fixtures; no portable pass is claimed for them.
No real browser, serial link, FPGA hardware or existing flight recordings were
used to verify this export.
