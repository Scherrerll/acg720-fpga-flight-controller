"""Real loopback HTTP across JS cloud worker and Python relay; fake ground only."""
import json
from pathlib import Path
import subprocess
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from remote_pi import Config,Client,Relay

class Integration(unittest.TestCase):
 def test_query_set_roundtrip_with_real_schema_no_device(self):
  state={'enabled':True,'connected':True,'source':'SiK','baud':115200,'epoch':7,'can_query':True,'can_set':True,'supported':True,'busy':False,
   'active':{'p_text':'0.1000','i_text':'0.0350','generation':0,'build':'0000B0B5','age_ms':0}}
  posts=[]
  class Ground(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def reply(self,value,status=200):
    data=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
   def do_GET(self):self.reply({'token':'loopback-session-private'} if self.path.endswith('/session') else state)
   def do_POST(self):
    if self.headers.get('X-XY-PI-Token')!='loopback-session-private':self.reply({},403);return
    v=json.loads(self.rfile.read(int(self.headers['Content-Length'])));posts.append((self.path,v))
    if self.path.endswith('/set'):state['active'].update(p_text=v['p'],i_text=v['i'],generation=1)
    state['result']={'code':'verified' if self.path.endswith('/set') else 'queried','operation_id':len(posts)}
    self.reply({'operation_id':len(posts)},202)
  local=ThreadingHTTPServer(('127.0.0.1',0),Ground)
  thread=threading.Thread(target=local.serve_forever,daemon=True);thread.start()
  child=subprocess.Popen(['node',str(Path(__file__).resolve().parents[1]/'tests/preview-server.mjs'),'--test-fixture'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   cloud=json.loads(child.stdout.readline())['url'];operator='test-operator-'+'a'*32
   def api(path,body=None):
    request=urllib.request.Request(cloud+'/api/remote-pi/'+path,headers={'X-Flight-Control-Token':operator,'Origin':cloud,'Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=4) as r:return json.load(r)
   relay=Relay(Client(Config(cloud,'test-publisher-'+'b'*32,f'http://127.0.0.1:{local.server_port}')))
   relay.step();status=api('status')
   self.assertTrue(status['status']['can_query']);self.assertFalse(status['status']['can_set'])
   self.assertNotIn('loopback-session-private',json.dumps(status))
   for action,identifier in [('query','query_integration'),('set','set_integration')]:
    status=api('status')
    command={'id':identifier,'epoch':status['epoch'],'challenge':status['challenge'],'action':action,'expected_epoch':7}
    if action=='set':command.update(p='0.1200',i='0.0400',expected_generation=0,confirmed_stopped=True)
    api('command',command);relay.step()
    result=api(f'result/{relay.epoch}/{identifier}')['result']
    self.assertEqual(result['code'],'queried' if action=='query' else 'verified')
    self.assertEqual(result['active']['build'],'0000B0B5')
    relay.step()
   self.assertEqual(len(posts),2);self.assertEqual(state['active']['generation'],1)
   self.assertEqual(state['active']['p_text'],'0.1200')
  finally:
   child.terminate();child.wait(timeout=5);child.stdout.close();child.stderr.close()
   local.shutdown();local.server_close();thread.join(timeout=2)

if __name__=='__main__':unittest.main()
