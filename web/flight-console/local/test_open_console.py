"""Launcher tests: loopback GETs and mocks, no subprocess/serial/cloud writes."""
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import socket
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error

import open_console as console


class Server:
    def __init__(self, identified=True, sharing=False):
        self.requests = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                owner.requests.append(('GET', self.path))
                value = {'mode': 'local', 'share_url': 'https://configured.example' if sharing else None,
                         'can_share_logs': sharing, 'sharing_enabled': sharing} if identified else {'other': True}
                raw = json.dumps(value).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                owner.requests.append(('POST', self.path))
                self.send_response(405)
                self.end_headers()

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class LauncherTests(unittest.TestCase):
    def invoke(self, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = console.run(**kwargs)
        return result, out.getvalue(), err.getvalue()

    def test_default_new_bridge_is_unconfigured_and_browser_waits_for_ready(self):
        events, current = [], [0.0]
        process = Mock(); process.poll.return_value = None
        states = iter([console.Listener.ABSENT, console.Listener.ABSENT, console.Listener.BRIDGE])

        def probe(port):
            self.assertEqual(port, 8766)
            state = next(states); events.append(state)
            return state

        popen = Mock(return_value=process)

        def browser(url):
            self.assertEqual(events[-1], console.Listener.BRIDGE)
            self.assertEqual(url, 'http://127.0.0.1:8766/')
            events.append('browser')
            return True

        result, out, err = self.invoke(probe=probe, popen=popen, open_url=browser,
                                      clock=lambda: current[0], sleep=lambda dt: current.__setitem__(0, current[0] + dt))
        self.assertEqual(result, 0); self.assertEqual(err, '')
        args, options = popen.call_args
        self.assertEqual(args[0], [console.sys.executable, '-B', str(console.HERE/'bridge.py'), '--port', '8766'])
        self.assertNotIn('--stdin-config', args[0]); self.assertNotIn('env', options)
        for stream in ('stdin', 'stdout', 'stderr'):
            self.assertEqual(options[stream], subprocess.DEVNULL)
        if console.sys.platform == 'win32':
            self.assertTrue(options['creationflags'] & subprocess.CREATE_NO_WINDOW)
        self.assertIn('默认关闭', out)

    def test_existing_bridge_is_reused_and_sharing_never_changed(self):
        with Server(sharing=True) as server:
            popen, browser = Mock(side_effect=AssertionError('No subprocess')), Mock(return_value=True)
            result, out, err = self.invoke(port=server.port, popen=popen, open_url=browser)
            self.assertEqual(result, 0); self.assertEqual(err, '')
            self.assertEqual(server.requests, [('GET', '/api/capabilities')])
            self.assertIn('保留原有分享状态', out)
            popen.assert_not_called(); browser.assert_called_once_with(f'http://127.0.0.1:{server.port}/')

    def test_spawn_bind_race_waits_through_unidentified_port_until_bridge_ready(self):
        states = iter([console.Listener.ABSENT, console.Listener.OTHER, console.Listener.BRIDGE])
        process = Mock(); process.poll.return_value = None
        browser = Mock(return_value=True); now = [0.0]
        result, out, err = self.invoke(probe=lambda port: next(states),
            popen=Mock(return_value=process), open_url=browser,
            clock=lambda: now[0], sleep=lambda dt: now.__setitem__(0, now[0] + dt))
        self.assertEqual(result, 0); self.assertEqual(err, '')
        browser.assert_called_once_with('http://127.0.0.1:8766/')

    def test_other_service_is_refused_without_subprocess_or_browser(self):
        with Server(identified=False) as server:
            popen, browser = Mock(), Mock()
            result, out, err = self.invoke(port=server.port, popen=popen, open_url=browser)
            self.assertEqual(result, 2); self.assertIn('其他服务占用', err)
            popen.assert_not_called(); browser.assert_not_called()
            self.assertEqual(server.requests, [('GET', '/api/capabilities')])

    def test_timeout_on_free_port_is_absent_after_exclusive_bind_check(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free:
            free.bind(('127.0.0.1', 0))
            port = free.getsockname()[1]
        opener = Mock()
        opener.open.side_effect = urllib.error.URLError(TimeoutError('loopback connect timeout'))
        with patch.object(console.urllib.request, 'build_opener', return_value=opener):
            self.assertEqual(console.probe_bridge(port), console.Listener.ABSENT)

    def test_timeout_on_bound_port_is_other_and_does_not_replace_service(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.URLError(TimeoutError('loopback connect timeout'))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            if console.sys.platform == 'win32' and hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                occupied.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            occupied.bind(('127.0.0.1', 0))
            port = occupied.getsockname()[1]
            with patch.object(console.urllib.request, 'build_opener', return_value=opener):
                self.assertEqual(console.probe_bridge(port), console.Listener.OTHER)
                popen, browser = Mock(), Mock()
                result, out, err = self.invoke(port=port, popen=popen, open_url=browser)
                self.assertEqual(result, 2)
                popen.assert_not_called(); browser.assert_not_called()

    def test_http_error_never_falls_back_to_free_port_assumption(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError('http://127.0.0.1:8766/api/capabilities', 404, 'missing', {}, None)
        with patch.object(console.urllib.request, 'build_opener', return_value=opener), patch.object(console, 'port_available') as available:
            self.assertEqual(console.probe_bridge(8766), console.Listener.OTHER)
            available.assert_not_called()

    def test_bridge_config_defaults_disable_publication(self):
        import bridge
        config = bridge.Config(listen_port=0)
        self.assertFalse(config.sharing)
        self.assertFalse(bridge.Bridge(config).sharing_enabled)

    def test_redirect_cannot_send_probe_to_another_host(self):
        class Redirect(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(302); self.send_header('Location', 'https://must-not-be-contacted.example/'); self.end_headers()
        server = ThreadingHTTPServer(('127.0.0.1', 0), Redirect)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            self.assertEqual(console.probe_bridge(server.server_port), console.Listener.OTHER)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_failed_child_and_timeout_do_not_open_browser(self):
        process = Mock(); process.poll.return_value = 1
        browser = Mock()
        result, out, err = self.invoke(probe=lambda port: console.Listener.ABSENT,
                                      popen=Mock(return_value=process), open_url=browser)
        self.assertEqual(result, 2); self.assertIn('启动后退出', err); browser.assert_not_called()
        process.poll.return_value = None
        now = [0.0]
        result, out, err = self.invoke(probe=lambda port: console.Listener.ABSENT,
            popen=Mock(return_value=process), open_url=browser,
            clock=lambda: now[0], sleep=lambda seconds: now.__setitem__(0, now[0] + seconds))
        self.assertEqual(result, 2); self.assertIn('尚未就绪', err); browser.assert_not_called()

    def test_browser_failure_shows_usable_http_root(self):
        result, out, err = self.invoke(probe=lambda port: console.Listener.BRIDGE, open_url=Mock(return_value=False))
        self.assertEqual(result, 1); self.assertIn('http://127.0.0.1:8766/', err)
        self.assertNotIn('file:', out + err)

    def test_no_browser_option_prepares_service_without_opening(self):
        browser = Mock(side_effect=AssertionError('No browser'))
        result, out, err = self.invoke(no_browser=True, probe=lambda port: console.Listener.BRIDGE, open_url=browser)
        self.assertEqual(result, 0); self.assertEqual(err, '')
        self.assertIn('本地监控已就绪：http://127.0.0.1:8766/', out)
        browser.assert_not_called()
        with patch.object(console, 'run', return_value=0) as run:
            self.assertEqual(console.main(['--no-browser']), 0)
            run.assert_called_once_with(8766, no_browser=True)

    def test_cmd_is_ascii_and_launches_python_entrypoint(self):
        raw = (console.HERE.parent/'启动本地监控.cmd').read_bytes()
        text = raw.decode('ascii')
        self.assertIn('%~dp0local\\open_console.py', text)
        self.assertIn('pause', text)
        self.assertEqual(text.count('%*'), 2)
        source = Path(console.__file__).read_text(encoding='utf8')
        self.assertNotIn('import serial', source)
        self.assertNotIn('comports', source)


if __name__ == '__main__':
    unittest.main()
