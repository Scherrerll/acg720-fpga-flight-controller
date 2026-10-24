"""Start the receiver without PowerShell policy changes or duplicate services."""
from pathlib import Path
import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--usb',action='store_true',help='Use COM23 wired telemetry instead of COM17 SiK')
args=parser.parse_args()
root=Path(__file__).resolve().parent
try:
    with socket.create_connection(('127.0.0.1',8765),timeout=2):occupied=True
except ConnectionRefusedError:occupied=False
except OSError as exc:
    print(f'Cannot check local port8765: {exc}. No other process was stopped.');sys.exit(1)
if occupied:
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/state',timeout=3) as response:state=json.load(response)
        assert 'recording' in state and 'source' in state and state.get('serial_writes') is False
        assert state.get('receiver_profile')=='mtf01p.b0ae_ano_control.v5','Existing receiver has a different profile. Keep it running until the planned handover; no process was stopped.'
        print('Existing read-only receiver is running. Change source in its Logs page if required.')
        webbrowser.open('http://127.0.0.1:8765/');sys.exit(0)
    except Exception as exc:
        print(f'Port8765 is occupied by another service: {exc}. No process was stopped.');sys.exit(1)
child=subprocess.Popen([sys.executable,'-u',str(root/'ground_server.py'),
    '--port','COM23' if args.usb else 'COM17','--source','USB' if args.usb else 'SiK',
    '--baud','115200','--http-port','8765'],cwd=root.parent)
try:
    deadline=time.monotonic()+10
    while child.poll() is None and time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/api/state',timeout=1) as response:state=json.load(response)
            if 'recording' in state:break
        except OSError:pass
        time.sleep(.1)
    if child.poll() is not None:raise SystemExit(child.returncode)
    webbrowser.open('http://127.0.0.1:8765/')
    raise SystemExit(child.wait())
except KeyboardInterrupt:
    try:
        request=urllib.request.Request('http://127.0.0.1:8765/api/service/stop',data=b'{}',headers={'Content-Type':'application/json'})
        urllib.request.urlopen(request,timeout=3).close()
        child.wait(timeout=8)
    except (OSError,subprocess.TimeoutExpired):print('Receiver may still be stopping; logs are preserved.')
