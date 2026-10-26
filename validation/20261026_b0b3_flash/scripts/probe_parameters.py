"""One explicit parameter GET through the running ground station; never SET."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,time,urllib.request,uuid
from flash_b0b3 import get,stopped,sha

HERE=Path(__file__).resolve().parent
BASE='http://127.0.0.1:8765'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['after_flash','after_cold_boot'],required=True)
    args=parser.parse_args();path=HERE/(args.stage+'_parameters.json')
    assert not path.exists(),'Keep the previous receipt; do not overwrite'
    report=dict(passed=False,stage=args.stage,started_utc=datetime.now(timezone.utc).isoformat(),
                request_type='GET only',parameter_values_written=False,script_sha256=sha(Path(__file__)))
    try:
        stopped(get('/api/state'))
        status=get('/api/xy-pi/status')
        assert status['can_query'] and not status['busy'],'Parameter service unavailable or busy'
        token=get('/api/xy-pi/session')['token']
        body=dict(request_id=str(uuid.uuid4()),epoch=status['epoch'])
        request=urllib.request.Request(BASE+'/api/xy-pi/query',data=json.dumps(body).encode('utf-8'),
                  headers={'Content-Type':'application/json','Origin':BASE,'X-XY-PI-Token':token},method='POST')
        with urllib.request.urlopen(request,timeout=4)as response:
            assert response.status==202
            accepted=json.load(response)
        report.update(request=body,accepted=accepted)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            status=get('/api/xy-pi/status')
            if status['operation_id']==accepted['operation_id'] and not status['busy']:break
            time.sleep(.1)
        else:raise TimeoutError('No completed parameter GET')
        report['response']=status
        assert status['result']['code']=='queried' and status['supported'],'B0B3 capability not confirmed'
        active=status['active']
        assert (active['build']=='0000B0B3' and active['p_wire']==500 and active['i_wire']==0
                and active['generation']==0),'New boot default pair/generation not confirmed'
        stopped(get('/api/state'));report['passed']=True
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc);raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
