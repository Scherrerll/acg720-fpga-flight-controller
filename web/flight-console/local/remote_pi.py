"""Opt-in outbound XY P/I relay. No serial imports or arbitrary command routing."""
from __future__ import annotations
import argparse
import getpass
import json
import re
import secrets
import hashlib
from decimal import Decimal
import sys
import time
import warnings
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from urllib.parse import urlsplit

HEX = re.compile(r'[0-9a-f]{32}\Z')
IDENT = re.compile(r'[A-Za-z0-9_-]{8,90}\Z')
GAIN = re.compile(r'(?:0(?:\.\d{1,4})?|1(?:\.0{1,4})?)\Z')
CODES = {'queried','verified','unknown','cancelled','mismatch','locked','stale_sequence','nack','rejected','expired'}

class RelayError(Exception): pass

def origin(value, local=False):
    if not isinstance(value,str): raise ValueError('Invalid origin')
    u=urlsplit(value)
    if u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
        raise ValueError('Only an origin is allowed')
    if local:
        if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost'): raise ValueError('Upstream must be loopback HTTP')
    elif u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('127.0.0.1','localhost')):
        raise ValueError('Cloud must use HTTPS')
    if not u.hostname: raise ValueError('Missing host')
    _=u.port
    return value.rstrip('/')

@dataclass(repr=False)
class Config:
    site_url: str
    publish_token: str = field(repr=False)
    upstream: str = 'http://127.0.0.1:8765'
    def __post_init__(self):
        self.site_url=origin(self.site_url); self.upstream=origin(self.upstream,True)
        if not isinstance(self.publish_token,str) or not 32<=len(self.publish_token)<=4096 or any(ord(c)<33 or ord(c)>126 for c in self.publish_token):
            raise ValueError('Invalid publication credential')

def clean_status(s):
    """Never send the local session token, port, arbitrary errors or source metadata."""
    if not isinstance(s,dict): return {}
    r={k:s.get(k) is True for k in ('enabled','connected','can_query','can_set','supported','busy')}
    r['source']='SiK' if s.get('source')=='SiK' else None
    r['baud']=115200 if s.get('baud')==115200 else None
    r['epoch']=s.get('epoch') if type(s.get('epoch')) is int else None
    a=s.get('active')
    r['active']=None
    if isinstance(a,dict) and a.get('build') in ('0000B0B4','0000B0B5') and all(isinstance(a.get(k),str) and GAIN.fullmatch(a[k]) for k in ('p_text','i_text')) and type(a.get('generation')) is int and 0<=a['generation']<=0xffffffff:
        r['active']={k:a[k] for k in ('p_text','i_text','generation','build')}
        r['active']['age_ms']=a.get('age_ms') if type(a.get('age_ms')) in (int,float) and 0<=a['age_ms']<=1e10 else None
    return r

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class Client:
    def __init__(self,config):
        self.config=config
        self.local_instance=None
        self.local=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        self.cloud=urllib.request.build_opener(urllib.request.ProxyHandler(),NoRedirect())
    def request(self,local,path,payload=None,token=None):
        base=self.config.upstream if local else self.config.site_url
        headers={'User-Agent':'GMFLY-Remote-PI/1.0','Cache-Control':'no-store'}
        if local and payload is not None: headers.update({'Origin':base,'X-XY-PI-Token':token or ''})
        if not local: headers['X-Flight-Publish-Token']=self.config.publish_token
        data=None
        if payload is not None:
            data=json.dumps(payload,allow_nan=False,separators=(',',':')).encode(); headers['Content-Type']='application/json'
        try:
            req=urllib.request.Request(base+path,data=data,headers=headers,method='POST' if data is not None else 'GET')
            with (self.local if local else self.cloud).open(req,timeout=3) as response:
                raw=response.read(32769)
                if len(raw)>32768: raise RelayError('response_limit')
                value=json.loads(raw)
                if not isinstance(value,dict): raise RelayError('response_shape')
                return value
        except Exception:
            raise RelayError('request_unavailable') from None
    def session(self):
        token=self.request(True,'/api/xy-pi/session').get('token')
        if not isinstance(token,str) or not token:raise RelayError('session_unavailable')
        return token
    @staticmethod
    def identity(token):return hashlib.sha256(token.encode()).digest()
    def status(self):
        # Numeric connection epochs can repeat after Host restarts. Its private
        # random session token identifies that process without leaving loopback.
        token=self.session()
        value=self.request(True,'/api/xy-pi/status')
        after=self.session()
        if token!=after:
            self.local_instance=self.identity(after);raise RelayError('session_changed')
        self.local_instance=self.identity(token)
        return value
    def submit(self,action,payload,deadline=None,clock=time.monotonic):
        token=self.session()
        if deadline is not None and clock()>=deadline:raise RelayError('expired')
        if self.local_instance is None or self.identity(token)!=self.local_instance:raise RelayError('session_changed')
        return self.request(True,'/api/xy-pi/'+action,payload,token)
    def heartbeat(self,value):return self.request(False,'/api/remote-pi/heartbeat',value)
    def poll(self,epoch,challenge):return self.request(False,'/api/remote-pi/poll?epoch='+epoch+'&challenge='+challenge)
    def result(self,value):return self.request(False,'/api/remote-pi/result',value)

class Relay:
    def __init__(self,client,clock=time.monotonic,sleep=time.sleep):
        self.client,self.clock,self.sleep=client,clock,sleep
        self.epoch=secrets.token_hex(16);self.rotate()
        self.pending=None;self.pending_at=None;self.query_required=True;self.local_epoch=None;self.local_instance=None
    def rotate(self):self.challenge=secrets.token_hex(16);self.challenge_at=self.clock()
    def status(self):
        s=clean_status(self.client.status())
        if self.local_instance is not None and self.client.local_instance!=self.local_instance:
            self.query_required=True;self.epoch=secrets.token_hex(16);self.rotate()
        self.local_instance=self.client.local_instance
        if self.local_epoch is not None and s.get('epoch')!=self.local_epoch:self.query_required=True
        self.local_epoch=s.get('epoch')
        if self.query_required:s['can_set']=False
        return s
    def validate(self,command,poll,rtt):
        if not isinstance(command,dict):raise RelayError('invalid_command')
        common={'id','epoch','challenge','action','expected_epoch','created_at_ms','expires_at_ms'}
        extra={'p','i','expected_generation','confirmed_stopped'} if command.get('action')=='set' else set()
        if set(command)!=common|extra or command.get('action') not in ('query','set'):raise RelayError('invalid_command')
        if not isinstance(command.get('id'),str) or not IDENT.fullmatch(command['id']):raise RelayError('invalid_id')
        if command['epoch']!=self.epoch or command['challenge']!=self.challenge:raise RelayError('stale_challenge')
        if self.clock()-self.challenge_at>=10:raise RelayError('expired_challenge')
        values=[poll.get('server_now_ms'),command.get('created_at_ms'),command.get('expires_at_ms')]
        if any(type(v) is not int for v in values):raise RelayError('invalid_time')
        now,created,end=values
        if not 0<end-created<=8000 or not created<=now<end or end-now<=rtt*1000:raise RelayError('expired')
        if type(command.get('expected_epoch')) is not int:raise RelayError('invalid_epoch')
        if command['action']=='set':
            if command['confirmed_stopped'] is not True or type(command.get('expected_generation')) is not int or not 0<=command['expected_generation']<=0xffffffff:raise RelayError('invalid_set')
            if any(not isinstance(command.get(k),str) or not GAIN.fullmatch(command[k]) for k in ('p','i')):raise RelayError('invalid_gain')
        return self.clock()+(end-now)/1000-rtt
    def execute(self,c,deadline):
        # A second fresh local read closes the cloud-to-local state gap.
        s=self.client.status();safe=clean_status(s)
        instance=self.client.local_instance
        if instance!=self.local_instance:
            self.query_required=True;return {'code':'expired','active':None}
        if self.clock()>=deadline or s.get('epoch')!=c['expected_epoch']:return {'code':'expired','active':None}
        key='can_query' if c['action']=='query' else 'can_set'
        if safe.get(key) is not True:return {'code':'rejected','active':None}
        if c['action']=='set' and (self.query_required or not safe.get('supported') or not safe.get('active') or safe['active']['generation']!=c['expected_generation']):return {'code':'rejected','active':None}
        payload={'request_id':'remote-'+c['epoch']+'-'+hashlib.sha256(c['id'].encode()).hexdigest()[:32],'epoch':c['expected_epoch']}
        if c['action']=='set':payload.update({k:c[k] for k in ('p','i','expected_generation','confirmed_stopped')})
        # Exactly one local POST attempt. Response loss must never trigger retry.
        self.query_required=True
        reply=self.client.submit(c['action'],payload,deadline,self.clock)
        op=reply.get('operation_id')
        if type(op) is not int:raise RelayError('unknown')
        end=self.clock()+9
        while self.clock()<end:
            v=self.client.status()
            if v.get('epoch')!=c['expected_epoch'] or self.client.local_instance!=instance:raise RelayError('unknown')
            r=v.get('result') or {}
            if not v.get('busy') and r.get('operation_id')==op:
                code=r.get('code') if r.get('code') in CODES else 'unknown'
                active=clean_status(v).get('active')
                if code in ('queried','verified') and (active is None or code!=('queried' if c['action']=='query' else 'verified')):code='unknown'
                if code=='verified' and (Decimal(active['p_text'])!=Decimal(c['p']) or Decimal(active['i_text'])!=Decimal(c['i']) or active['generation']!=((c['expected_generation']+1)&0xffffffff)):code='unknown'
                if code in ('queried','verified'):self.query_required=False
                return {'code':code,'active':active,'operation_id':op}
            self.sleep(.1)
        raise RelayError('unknown')
    def step(self):
        if self.pending is not None:
            if self.clock()-self.pending_at>=55:
                self.pending=None;self.pending_at=None;self.query_required=True;self.rotate();return
            self.client.result(self.pending);self.pending=None;return
        if self.clock()-self.challenge_at>=10:self.rotate()
        snapshot=self.status()
        self.client.heartbeat({'epoch':self.epoch,'challenge':self.challenge,'status':snapshot})
        start=self.clock();poll=self.client.poll(self.epoch,self.challenge);rtt=self.clock()-start
        c=poll.get('command')
        if c is None:return
        deadline=self.validate(c,poll,rtt)
        # Consume the challenge BEFORE any local request; old mailbox can never replay.
        self.rotate()
        try:result=self.execute(c,deadline)
        except Exception:result={'code':'unknown','active':None};self.query_required=True
        self.pending={'epoch':c['epoch'],'id':c['id'],'challenge':c['challenge'],'intent':c,'result':result}
        self.pending_at=self.clock()
        self.client.result(self.pending);self.pending=None

def configuration(args):
    if args.prompt:
        with warnings.catch_warnings():
            # Never fall back to echoed stdin when no private console exists.
            warnings.simplefilter('error',getpass.GetPassWarning)
            token=getpass.getpass('Existing publish token (hidden): ')
        return Config(args.site_url or 'https://gmflylog.com',token,args.upstream or 'http://127.0.0.1:8765')
    if args.site_url or args.upstream:raise ValueError('Origin arguments require --prompt')
    line=sys.stdin.readline(8193)
    if len(line)>8192:raise ValueError()
    data=json.loads(line)
    if not isinstance(data,dict) or set(data)-{'site_url','publish_token','upstream'}:raise ValueError()
    return Config(**data)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--enable-remote-pi',action='store_true')
    ap.add_argument('--prompt',action='store_true',help='Read the publication credential privately from the console')
    ap.add_argument('--site-url',help='Cloud origin, with --prompt')
    ap.add_argument('--upstream',help='Existing loopback ground server origin, with --prompt')
    args=ap.parse_args()
    if not args.enable_remote_pi:ap.error('Explicit --enable-remote-pi is required; no relay started')
    try:
        relay=Relay(Client(configuration(args)))
    except Exception:ap.error('Invalid configuration or private console unavailable; credentials were not logged')
    print('Remote XY P/I relay started; local/FPGA checks remain authoritative.',flush=True)
    try:
        while True:
            try:relay.step()
            except Exception:pass # Never log URLs, credentials or device-private responses.
            time.sleep(.5)
    except KeyboardInterrupt:pass

if __name__=='__main__':main()
