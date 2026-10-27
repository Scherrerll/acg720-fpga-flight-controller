"""Run an unmodified-stimulus legacy runner and record actual subprocess returns."""
from pathlib import Path
import datetime,hashlib,json,os,runpy,subprocess,sys,traceback
O=Path(__file__).resolve().parent
target=Path(sys.argv[1]).resolve();args=sys.argv[2:];D=target.parent/'actual_child_receipts';assert not D.exists();D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
real=subprocess.run;counter=0;receipts=[]
def wrapped(*a,**kw):
 global counter
 counter+=1;p=D/f'{counter:02d}_exit.json';command=a[0] if a else kw['args'];j={'command':list(map(str,command)),'cwd':str(kw.get('cwd',Path.cwd())),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  c=real(*a,**kw);j.update(normal_return=True,actual_completedprocess_returncode=c.returncode)
 except BaseException as e:
  j.update(normal_return=False,error=repr(e));p.write_text(json.dumps(j,indent=2)+'\n');raise
 j['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for stream in ['stdout','stderr']:
  value=getattr(c,stream,None)
  if isinstance(value,str):value=value.encode('utf8')
  if isinstance(value,bytes):
   log=D/f'{counter:02d}.{stream}.log';log.write_bytes(value);j[f'{stream}_path']=str(log);j[f'{stream}_sha256']=sha(log)
 p.write_text(json.dumps(j,indent=2)+'\n');receipts.append({'path':str(p),'sha256':sha(p)})
 print(json.dumps({'actual_child_receipt':str(p),'actual_completedprocess_returncode':c.returncode}),flush=True)
 return c
subprocess.run=wrapped;sys.argv=[str(target),*args];sys.path.insert(0,str(target.parent))
runpy.run_path(str(target),run_name='__main__')
(D/'INDEX.json').write_text(json.dumps({'passed':all(json.loads(Path(x['path']).read_text())['actual_completedprocess_returncode']==0 for x in receipts),'target_sha256':sha(target),'recorder_sha256':sha(Path(__file__)),'receipts':receipts},indent=2)+'\n')
