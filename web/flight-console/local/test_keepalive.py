import http.client
import unittest
import urllib.request
from unittest.mock import MagicMock, patch
from keepalive import PersistentHTTPS, ResponseTooLarge


def response(body=b'{}', status=200, close=False):
    value = MagicMock()
    value.status, value.will_close = status, close
    value.getheader.return_value = str(len(body))
    value.read.return_value = body
    return value


class KeepaliveTests(unittest.TestCase):
    def setUp(self):
        self.proxies = patch('keepalive.urllib.request.getproxies', return_value={})
        self.bypass = patch('keepalive.urllib.request.proxy_bypass', return_value=False)
        self.factory = patch('keepalive.http.client.HTTPSConnection')
        self.proxies.start(); self.bypass.start(); self.connection = self.factory.start()
        self.addCleanup(patch.stopall)
        self.connection.return_value.getresponse.return_value = response()
        self.transport = PersistentHTTPS('https://example.test')
        self.request = urllib.request.Request('https://example.test/api/health')

    def test_successive_health_and_live_requests_reuse_verified_https_connection(self):
        self.assertEqual(self.transport.read(self.request, 1024), b'{}')
        live = urllib.request.Request('https://example.test/api/publish/live', data=b'{}', headers={'X-Flight-Publish-Token': 'TEST_ONLY'})
        self.assertEqual(self.transport.read(live, 1024), b'{}')
        self.connection.assert_called_once_with('example.test', 443, timeout=8)
        self.assertEqual(self.connection.return_value.request.call_count, 2)

    def test_current_http_proxy_uses_connect_tunnel_and_authenticated_proxy_falls_back(self):
        with patch('keepalive.urllib.request.getproxies', return_value={'https': 'http://127.0.0.1:1234'}):
            self.transport.read(self.request, 1024)
        self.connection.assert_called_once_with('127.0.0.1', 1234, timeout=8)
        self.connection.return_value.set_tunnel.assert_called_once_with('example.test', 443)
        for proxy in ['https://proxy.test', 'http://user:password@proxy.test']:
            with patch('keepalive.urllib.request.getproxies', return_value={'https': proxy}):
                self.assertFalse(self.transport.supported())

    def test_dead_reused_socket_retries_once_but_initial_failure_does_not(self):
        first, second = MagicMock(), MagicMock()
        first.getresponse.side_effect = [response(), http.client.RemoteDisconnected()]
        second.getresponse.return_value = response()
        self.connection.side_effect = [first, second]
        self.transport.read(self.request, 1024)
        self.transport.read(self.request, 1024)
        self.assertEqual(self.connection.call_count, 2)
        first.close.assert_called_once()
        self.transport.close(); self.connection.reset_mock(); self.connection.side_effect = None
        self.connection.return_value.getresponse.side_effect = http.client.RemoteDisconnected()
        with self.assertRaises(http.client.RemoteDisconnected):
            self.transport.read(self.request, 1024)
        self.assertEqual(self.connection.call_count, 1)

    def test_server_close_rotates_connection(self):
        self.connection.return_value.getresponse.return_value = response(close=True)
        self.transport.read(self.request, 1024)
        self.transport.read(self.request, 1024)
        self.assertEqual(self.connection.call_count, 2)

    def test_redirect_and_large_response_close_without_following_or_truncating(self):
        self.connection.return_value.getresponse.return_value = response(status=302)
        with self.assertRaises(ValueError):
            self.transport.read(self.request, 1024)
        self.connection.return_value.getresponse.return_value = response(body=b'x' * 11)
        with self.assertRaises(ResponseTooLarge):
            self.transport.read(self.request, 10)
        self.assertIsNone(self.transport.connection)

    def test_other_origin_and_non_realtime_resources_are_rejected_before_request(self):
        for url in ['https://other.test/api/health', 'https://example.test/api/publish/log']:
            with self.assertRaises(ValueError):
                self.transport.read(urllib.request.Request(url), 1024)
        self.connection.assert_not_called()


if __name__ == '__main__':
    unittest.main()
