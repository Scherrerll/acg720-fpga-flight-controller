"""Authorized default-pair bench proof via the same local API as the page."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import urllib.request
import uuid

OUT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8765'

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=4) as response:
        return json.load(response)

def post(path, body, token):
    request = urllib.request.Request(BASE + path, data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type':'application/json', 'Origin':BASE, 'X-XY-PI-Token':token}, method='POST')
    with urllib.request.urlopen(request, timeout=4) as response:
        assert response.status == 202
        return json.load(response)

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def wait_operation(operation_id):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        status = get('/api/xy-pi/status')
        if status['operation_id'] == operation_id and not status['busy']:
            return status
        time.sleep(.1)
    raise TimeoutError('No completed result; never retry SET automatically')

def main():
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(), passed=False,
                  scope='Default P=.05/I=0 bench GET, one SET, independent automatic GET; no gain change or Flash',
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), posts=[])
    try:
        before = get('/api/xy-pi/status')
        save('pi_status_before.json', before)
        assert before['can_query'] is True and before['busy'] is False
        token = get('/api/xy-pi/session')['token']
        query = dict(request_id=str(uuid.uuid4()), epoch=before['epoch'])
        ack = post('/api/xy-pi/query', query, token)
        report['posts'].append(dict(path='/api/xy-pi/query', body=query, accepted=ack))
        queried = wait_operation(ack['operation_id'])
        save('pi_query_result.json', queried)
        report['queried'] = queried
        assert queried['result']['code'] == 'queried', 'Parameter capability GET did not succeed'
        active = queried['active']
        assert active['build'] == 0xB0B3 and active['p_wire'] == 500 and active['i_wire'] == 0, 'Unexpected initial default or build'
        deadline = time.monotonic() + 8
        while True:
            ready = get('/api/xy-pi/status')
            if ready['can_set']:
                break
            if time.monotonic() >= deadline:
                raise ValueError('Stop preflight remains blocked: ' + ready['block_reason'])
            time.sleep(.04)
        assert ready['epoch'] == queried['epoch'] and ready['active']['generation'] == active['generation']
        save('telemetry_before_parameter_set.json', get('/api/state'))
        change = dict(request_id=str(uuid.uuid4()), epoch=ready['epoch'], expected_generation=active['generation'],
                      p='0.0500', i='0.0000', confirmed_stopped=True)
        ack = post('/api/xy-pi/set', change, token)
        report['posts'].append(dict(path='/api/xy-pi/set', body=change, accepted=ack))
        verified = wait_operation(ack['operation_id'])
        save('pi_set_and_independent_readback.json', verified)
        report['verified'] = verified
        assert verified['result']['code'] == 'verified', 'SET not independently verified; do not retry'
        assert verified['active']['p_wire'] == 500 and verified['active']['i_wire'] == 0
        assert verified['active']['build'] == 0xB0B3
        save('telemetry_after_parameter_set.json', get('/api/state'))
        report['passed'] = True
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save('default_pi_bench_report.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
