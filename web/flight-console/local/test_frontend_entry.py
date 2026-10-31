"""Real static entry resources over temporary loopback HTTP; no polling/serial."""
import re
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
import bridge

class FrontendEntryTests(unittest.TestCase):
    def test_real_entry_assets_and_parameter_alias(self):
        frontend=Path(__file__).resolve().parents[1]/'frontend'
        observer=bridge.Bridge(bridge.Config(listen_port=0))
        server=bridge.make_server(observer,frontend)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def get(path):
            with opener.open(base+path,timeout=3) as response:return response.headers.get_content_type(),response.read()
        try:
            mime,html=get('/');self.assertEqual(mime,'text/html')
            self.assertIn('启动本地监控.cmd',html.decode('utf8'))
            assets=set(re.findall(r'(?:href|src)="(\./[^"#]+)"',html.decode('utf8')))
            self.assertIn('./local-entry.js',assets)
            for asset in assets:
                mime,body=get('/'+asset[2:])
                self.assertTrue(body,asset);self.assertNotIn(b'<!doctype html>',body.lower(),asset)
                if asset.endswith('.css'):self.assertEqual(mime,'text/css',asset)
                if asset.endswith('.js'):self.assertIn(mime,('application/javascript','text/javascript'),asset)
                if asset.endswith('.svg'):self.assertEqual(mime,'image/svg+xml',asset)
            for path in ('/parameters','/parameters/'):
                mime,body=get(path);self.assertEqual(mime,'text/html');self.assertIn(b'id="pi-card"',body)
            for path in ('/%2e%2e/README.md','/api/connection'):
                with self.assertRaises(urllib.error.HTTPError) as caught:get(path)
                self.assertEqual(caught.exception.code,404)
            self.assertFalse(observer.sharing_enabled)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)

if __name__=='__main__':unittest.main()
