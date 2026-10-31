"""Loopback-only UI assets and preview checks; no serial, external HTTP or user logs."""
from contextlib import ExitStack
from html.parser import HTMLParser
import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from unittest.mock import patch

import ground_server as gs
from preview_ui import make_preview

HERE = Path(__file__).resolve().parent


class RailLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_rail = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag=='nav':
            self.in_rail = 'rail' in attrs.get('class', '').split()
        elif self.in_rail and tag=='a':
            self.links.append(attrs)

    def handle_endtag(self, tag):
        if tag=='nav':
            self.in_rail = False


class UIAssetsTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(gs.serial, 'Serial', side_effect=AssertionError('Real serial forbidden')))
        self.stack.enter_context(patch.object(gs, 'ports', side_effect=AssertionError('Real device enumeration forbidden')))
        root = self.stack.enter_context(tempfile.TemporaryDirectory(prefix='gmfly-ui-test-'))
        self.host = gs.Host(root, dict(port='TEST_NO_DEVICE', source='SiK', baud=115200), no_serial=True)
        self.stack.callback(self.host.close)
        self.server = make_preview(self.host, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs=dict(poll_interval=.01), daemon=True)
        self.thread.start()
        self.stack.callback(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, route, method='GET', body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, route, body=body)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def get_json(self, route):
        status, _, body = self.request(route)
        self.assertEqual(status, 200)
        return json.loads(body)

    def test_local_assets_mime_and_bindings(self):
        for route, mime in [('/', 'text/html'), ('/logs', 'text/html'), ('/parameters', 'text/html'),
                            ('/dashboard.js', 'text/javascript'),
                            ('/logs.js', 'text/javascript'), ('/ui.css', 'text/css'),
                            ('/xy-pi-ui.css', 'text/css'), ('/xy-pi-ui.js', 'text/javascript'),
                            ('/gm-fly-mark.svg', 'image/svg+xml'), ('/gm-fly-wordmark.svg', 'image/svg+xml')]:
            with self.subTest(route=route):
                status, headers, body = self.request(route)
                self.assertEqual(status, 200)
                self.assertTrue(headers['Content-Type'].startswith(mime))
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                self.assertGreater(len(body), 20)
                if route=='/parameters':
                    self.assertIn(b'id="xy-pi-form"', body)
                    self.assertIn(b'src="/xy-pi-ui.js"', body)
        html = (HERE/'dashboard.html').read_text(encoding='utf8')
        ids = re.findall(r'\bid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))
        for identifier in ['horizon', 'trend', 'connection', 'build', 'age', 'headline-dot', 'snapshot',
                           'motors', 'channels', 'qualification', 'record-state']:
            self.assertIn(identifier, ids)
        self.assertNotIn('xy-pi-card', ids)
        self.assertNotIn('/xy-pi-ui.js', html)
        self.assertNotIn('/xy-pi-ui.css', html)
        parameters = (HERE/'parameters.html').read_text(encoding='utf8')
        parameter_ids = re.findall(r'\bid="([^"]+)"', parameters)
        self.assertEqual(len(parameter_ids), len(set(parameter_ids)))
        for suffix in ['card', 'title', 'active-p', 'active-i', 'generation', 'build', 'age', 'source',
                       'form', 'draft-state', 'p', 'i', 'range', 'validation', 'stopped', 'query',
                       'set', 'defaults', 'status']:
            self.assertIn('xy-pi-'+suffix, parameter_ids)
        self.assertIn('src="/xy-pi-ui.js"', parameters)
        self.assertIn('href="/xy-pi-ui.css"', parameters)
        for filename, route in [('dashboard.html', '/'), ('logs-ui.html', '/logs'),
                                ('parameters.html', '/parameters')]:
            with self.subTest(page=filename):
                page = (HERE/filename).read_text(encoding='utf8')
                navigation = RailLinks()
                navigation.feed(page)
                self.assertCountEqual([a['href'] for a in navigation.links], ['/', '/logs', '/parameters'])
                self.assertTrue(all('nav-item' in a.get('class', '').split() for a in navigation.links))
                current = [a for a in navigation.links if a.get('aria-current')=='page']
                self.assertEqual(len(current), 1)
                self.assertEqual(current[0]['href'], route)
                self.assertEqual([a for a in navigation.links if 'active' in a.get('class', '').split()], current)
        for filename in ['dashboard.html', 'logs-ui.html', 'parameters.html', 'ui.css', 'xy-pi-ui.css']:
            source = (HERE/filename).read_text(encoding='utf8')
            self.assertNotRegex(source, r'(?:src|href)=["\']https?://|@import\s|url\(["\']?https?://')
        self.assertIn("fetch('/api/state'", (HERE/'dashboard.js').read_text(encoding='utf8'))
        self.assertNotIn('/api/live', (HERE/'dashboard.js').read_text(encoding='utf8'))

    def test_empty_preview_is_read_only(self):
        health = self.get_json('/api/health')
        self.assertTrue(health['read_only'])
        self.assertFalse(health['serial_writes'])
        state = self.get_json('/api/state')
        self.assertFalse(state['fresh'])
        self.assertFalse(state['connected'])
        self.assertIsNone(state['data'])
        self.assertEqual(self.get_json('/api/ports')['ports'], [])
        pi = self.get_json('/api/xy-pi/status')
        self.assertFalse(pi['can_query'])
        self.assertFalse(pi['can_set'])

    def test_scenarios_and_real_synthetic_log_export(self):
        for scenario in ['live', 'stale', 'disconnected', 'b0b5', 'pi-ready', 'pi-busy', 'pi-unknown']:
            with self.subTest(scenario=scenario):
                self.assertEqual(self.request('/__preview?scenario='+scenario)[0], 303)
                state = self.get_json('/api/state')
                self.assertTrue(state['synthetic'])
                pi = self.get_json('/api/xy-pi/status')
                if scenario=='b0b5':
                    self.assertEqual(state['flight_info']['build_id'], 0xb0b5)
                    self.assertFalse(pi['supported'])
                    self.assertIsNone(pi['active'])
                if scenario=='pi-busy':
                    self.assertTrue(pi['busy'])
                    self.assertFalse(pi['can_set'])
                if scenario in ('stale', 'disconnected'):
                    self.assertFalse(state['fresh'])
                self.assertEqual(self.request('/api/xy-pi/set', 'POST', '{}')[0], 403)
        sessions = self.get_json('/api/logs')['sessions']
        self.assertEqual(len(sessions), 1)
        session_id = sessions[0]['id']
        analysis = self.get_json(f'/api/logs/{session_id}/analysis?field=roll_deg')
        self.assertEqual(analysis['primary_samples'], 32)
        for fmt in ['csv', 'zip']:
            status, headers, body = self.request(f'/api/logs/{session_id}/download?format={fmt}')
            self.assertEqual(status, 200)
            self.assertIn('attachment', headers['Content-Disposition'])
            self.assertGreater(len(body), 100)
        self.assertEqual(self.request('/__preview?scenario=logs-empty')[0], 303)
        self.assertEqual(self.get_json('/api/logs')['sessions'], [])


if __name__=='__main__':
    unittest.main()
