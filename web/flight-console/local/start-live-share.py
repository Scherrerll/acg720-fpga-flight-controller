"""Start the HTTP-only GM-FLY sidecar; --enable-sharing explicitly opts in.

Reads the existing publishing credential into memory and sends configuration
through stdin, never command arguments or output. Never opens a serial port.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

SITE = 'https://gmflylog.com'


def credential(path):
    value = os.environ.get('PUBLISH_TOKEN', '')
    if not value and path:
        for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
            key, sep, candidate = line.partition('=')
            if sep and key.strip() == 'PUBLISH_TOKEN':
                value = candidate.strip()
                if len(value)>=2 and value[0]==value[-1] and value[0] in ('"', "'"):
                    value=value[1:-1]
                break
    if len(value)<32 or any(ord(c)<33 or ord(c)>126 for c in value):
        raise ValueError('Existing PUBLISH_TOKEN is missing or invalid; no credential was printed')
    return value


def request(url, data=None):
    origin = url.rsplit('/api/',1)[0]
    headers = {'Content-Type':'application/json','Origin':origin} if data is not None else {}
    req=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=15 if data is not None else 3) as response:
        return json.load(response)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--token-env-file',type=Path)
    p.add_argument('--upstream',default='http://127.0.0.1:8765')
    p.add_argument('--port',type=int,default=8766)
    p.add_argument('--enable-sharing',action='store_true')
    a=p.parse_args(argv)
    # Reuse bridge validation; no running receiver or serial module is imported.
    from bridge import Config
    origin=f'http://127.0.0.1:{a.port}'
    config=Config(upstream=a.upstream,listen_port=a.port,site_url=SITE,publish_token=credential(a.token_env_file))
    try:cap=request(origin+'/api/capabilities')
    except OSError:cap=None
    started=False
    if cap is None:
        flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('bridge.py')),'--stdin-config'],
                               stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**flags)
        settings=dict(upstream=config.upstream,listen_port=config.listen_port,site_url=SITE,publish_token=config.publish_token)
        child.stdin.write((json.dumps(settings)+'\n').encode());child.stdin.close()
        for _ in range(40):
            if child.poll() is not None:raise RuntimeError('Sidecar could not start; check that its HTTP port is free')
            try:cap=request(origin+'/api/capabilities');break
            except OSError:time.sleep(.2)
        if cap is None:raise RuntimeError('Sidecar startup timed out')
        started=True
    if cap.get('mode')!='local' or cap.get('share_url')!=SITE or not cap.get('can_share_logs'):
        raise RuntimeError('This HTTP port belongs to a different preview/configuration; receiver was left untouched')
    if a.enable_sharing and not cap.get('sharing_enabled'):
        cap.update(request(origin+'/api/sharing',{'enabled':True}))
    print(json.dumps(dict(url=origin,site=SITE,started=started,sharing_enabled=cap.get('sharing_enabled'),serial_opened=False)))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError):
        print('GM-FLY sidecar could not start. Check receiver 8765, bridge port 8766 and the existing private credential file.',file=sys.stderr)
        raise SystemExit(1)
