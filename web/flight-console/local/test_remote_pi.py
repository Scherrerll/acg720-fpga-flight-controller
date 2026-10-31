import unittest
from unittest.mock import patch
from types import SimpleNamespace
import getpass
import warnings
from remote_pi import Relay, RelayError, Config, clean_status, Client, configuration

ACTIVE={'p_text':'0.1000','i_text':'0.0350','generation':0,'build':'0000B0B4','age_ms':0}
class Fake:
    def __init__(self):
        self.local_instance='fixture-server'
        self.value={'epoch':1,'enabled':True,'connected':True,'source':'SiK','baud':115200,'can_query':True,'can_set':True,'supported':True,'busy':False,'active':dict(ACTIVE)}
        self.command=None;self.posts=[];self.results=[];self.fail_post=False;self.fail_result=False
    def status(self):return dict(self.value)
    def heartbeat(self,v):self.heartbeat_value=v
    def poll(self,epoch,challenge):return {'server_now_ms':1000,'command':self.command}
    def submit(self,action,payload,*args):
        self.posts.append((action,payload))
        if self.fail_post:raise RelayError('lost_response')
        if action=='set':self.value['active']=dict(ACTIVE,p_text=payload['p'],i_text=payload['i'],generation=1)
        self.value['result']={'code':'queried' if action=='query' else 'verified','operation_id':2}
        return {'operation_id':2}
    def result(self,v):
        self.results.append(v)
        if self.fail_result:raise RelayError('cloud_down')

def cmd(relay,action='query',**extra):
    v={'id':'operation_123','epoch':relay.epoch,'challenge':relay.challenge,'action':action,'expected_epoch':1,'created_at_ms':900,'expires_at_ms':8000}
    if action=='set':v.update(p='0.1000',i='0.0350',expected_generation=0,confirmed_stopped=True)
    v.update(extra);return v

class Tests(unittest.TestCase):
    def test_origins_and_credentials(self):
        for upstream in ('http://example.com','https://localhost','http://localhost:8765/secret','http://user@localhost:8765'):
            with self.assertRaises(ValueError):Config('https://example.test','a'*32,upstream)
        for token in ('a','a'*31,'a'*32+'\n'):
            with self.assertRaises(ValueError):Config('https://example.test',token)
        self.assertNotIn('SECRET',repr(Config('https://example.test','SECRET'*8)))
    def test_prompt_refuses_echo_fallback(self):
        args=SimpleNamespace(prompt=True,site_url='https://example.test',upstream=None)
        with patch('remote_pi.getpass.getpass',return_value='s'*32):
            self.assertEqual(configuration(args).publish_token,'s'*32)
        def fallback(*args):warnings.warn('would echo',getpass.GetPassWarning);return 's'*32
        with patch('remote_pi.getpass.getpass',side_effect=fallback):
            with self.assertRaises(getpass.GetPassWarning):configuration(args)
    def test_status_allowlist(self):
        v=clean_status({'token':'SECRET','port':'COM1','block_reason':'SECRET C:/private.txt',**Fake().value})
        self.assertNotIn('SECRET',str(v));self.assertNotIn('port',v)
        self.assertIsNone(clean_status({'active':dict(ACTIVE,build='0000BEEF')})['active'])
    def test_query_and_replay(self):
        f=Fake();r=Relay(f);f.command=cmd(r);r.step()
        self.assertEqual(len(f.posts),1);self.assertFalse(r.query_required)
        self.assertEqual(f.results[-1]['result']['code'],'queried')
        with self.assertRaises(RelayError):r.step()
        self.assertEqual(len(f.posts),1)
    def test_ground_restart_with_reused_numbers_cannot_confirm_old_operation(self):
        f=Fake();r=Relay(f);r.query_required=False;f.command=cmd(r,'set')
        original=f.submit
        def restarted(*args):
            reply=original(*args);f.local_instance='replacement-server';return reply
        f.submit=restarted;r.step()
        self.assertEqual(f.results[-1]['result']['code'],'unknown');self.assertTrue(r.query_required)
        self.assertEqual(len(f.posts),1)
    def test_ground_restart_rotates_remote_identity_and_revokes_write(self):
        f=Fake();r=Relay(f);r.status();r.query_required=False
        old_epoch=r.epoch;old_challenge=r.challenge;f.local_instance='replacement-server'
        status=r.status()
        self.assertNotEqual(r.epoch,old_epoch);self.assertNotEqual(r.challenge,old_challenge)
        self.assertFalse(status['can_set']);self.assertTrue(r.query_required)
    def test_write_requires_remote_query_even_if_local_readback_exists(self):
        f=Fake();r=Relay(f);f.command=cmd(r,'set');r.step()
        self.assertEqual(f.results[-1]['result']['code'],'rejected');self.assertFalse(f.posts)
    def test_set_verified_no_auto_retry(self):
        f=Fake();r=Relay(f);r.query_required=False;f.command=cmd(r,'set');r.step()
        self.assertEqual(f.results[-1]['result']['code'],'verified');self.assertEqual(len(f.posts),1)
        self.assertLess(len(f.posts[0][1]['request_id']),129)
    def test_post_response_lost_publishes_unknown_only(self):
        f=Fake();r=Relay(f);r.query_required=False;f.fail_post=True;f.command=cmd(r,'set');r.step()
        self.assertEqual(f.results[-1]['result']['code'],'unknown');self.assertTrue(r.query_required)
        with self.assertRaises(RelayError):r.step()
        self.assertEqual(len(f.posts),1)
    def test_result_upload_can_retry_without_local_post(self):
        f=Fake();r=Relay(f);f.command=cmd(r);f.fail_result=True
        with self.assertRaises(RelayError):r.step()
        self.assertIsNotNone(r.pending);f.fail_result=False;r.step()
        self.assertEqual(len(f.posts),1);self.assertIsNone(r.pending)
    def test_expired_or_changed_or_extra_commands_never_submit(self):
        for extra in ({'expires_at_ms':1000},{'expected_epoch':2},{'path':'/api/arm'},{'epoch':'a'*32},{'action':'arm'}):
            f=Fake();r=Relay(f);f.command=cmd(r,**extra)
            try:r.step()
            except RelayError:pass
            self.assertFalse(f.posts)
    def test_final_local_guard_and_generation(self):
        for change in ({'can_set':False},{'supported':False},{'active':dict(ACTIVE,generation=1)}):
            f=Fake();r=Relay(f);r.query_required=False;f.value.update(change);f.command=cmd(r,'set');r.step()
            self.assertFalse(f.posts)
    def test_invalid_gain_no_submission(self):
        for gain in ('nan','0.10001','1.1','1e-2','-0.1',0.1):
            f=Fake();r=Relay(f);r.query_required=False;f.command=cmd(r,'set',p=gain)
            with self.assertRaises(RelayError):r.step()
            self.assertFalse(f.posts)
    def test_expiry_rechecked_after_local_session_request(self):
        c=Client(Config('https://example.test','a'*32))
        with patch.object(c,'request',return_value={'token':'local-secret'}) as request:
            with self.assertRaises(RelayError):c.submit('set',{},deadline=1,clock=lambda:2)
            self.assertEqual(request.call_count,1)
    def test_server_changes_between_status_and_submit_no_post(self):
        c=Client(Config('https://example.test','a'*32));c.local_instance=c.identity('previous-local-session')
        with patch.object(c,'request',return_value={'token':'new-local-session'}) as request:
            with self.assertRaisesRegex(RelayError,'session_changed'):c.submit('set',{})
            self.assertEqual(request.call_count,1)
    def test_status_cannot_cross_ground_process_restart(self):
        c=Client(Config('https://example.test','a'*32))
        replies=[{'token':'old-local-session'},dict(Fake().value),{'token':'new-local-session'}]
        with patch.object(c,'request',side_effect=replies):
            with self.assertRaisesRegex(RelayError,'session_changed'):c.status()

if __name__=='__main__':unittest.main()
