"""Launcher contract checks; no serial, real HTTP or child processes."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('live_launcher',Path(__file__).with_name('start-live-share.py'))
subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)
TOKEN='test-only-'+('x'*40)


class LauncherTests(unittest.TestCase):
    def launch(self,enabled,opt_in,site=subject.SITE):
        calls=[]
        def request(url,data=None):
            calls.append((url,data))
            return dict(mode='local',share_url=site,can_share_logs=True,sharing_enabled=enabled) if data is None else dict(sharing_enabled=True)
        output=io.StringIO()
        with patch.dict(os.environ,{'PUBLISH_TOKEN':TOKEN}),patch.object(subject,'request',side_effect=request),patch.object(subject.subprocess,'Popen',side_effect=AssertionError('Must reuse running sidecar')),contextlib.redirect_stdout(output):
            subject.main(['--enable-sharing'] if opt_in else [])
        self.assertNotIn(TOKEN,output.getvalue())
        return calls,output.getvalue()

    def test_enabled_bridge_is_reused_without_waiting_for_publish_lock(self):
        calls,out=self.launch(True,True);self.assertEqual(len(calls),1);self.assertIn('"sharing_enabled": true',out)

    def test_default_does_not_enable_sharing(self):
        calls,out=self.launch(False,False);self.assertEqual(len(calls),1);self.assertIn('"sharing_enabled": false',out)

    def test_explicit_opt_in_only_posts_boolean_toggle(self):
        calls,_=self.launch(False,True);self.assertEqual(calls[-1],('http://127.0.0.1:8766/api/sharing',{'enabled':True}))

    def test_different_destination_is_rejected(self):
        with self.assertRaises(RuntimeError):self.launch(False,True,'https://invalid.example')

    def test_quoted_private_credential_and_missing_value(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{},clear=True):
            p=Path(folder)/'.env';p.write_text('# ignored\nPUBLISH_TOKEN="'+TOKEN+'"\n',encoding='utf-8')
            self.assertEqual(subject.credential(p),TOKEN)
            p.write_text('OTHER=value\n',encoding='utf-8')
            with self.assertRaises(ValueError):subject.credential(p)


if __name__=='__main__':unittest.main(verbosity=2)
