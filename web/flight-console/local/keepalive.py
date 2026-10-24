"""Verified-TLS keepalive for the existing realtime publisher destination.

Uses the current system proxy. Unusual/authenticated proxy configurations stay
on the existing urllib transport; no proxy/security setting is changed.
"""
import http.client
import threading
import urllib.parse
import urllib.request


class ResponseTooLarge(Exception):
    pass


class PersistentHTTPS:
    def __init__(self, origin):
        self.origin = urllib.parse.urlsplit(origin)
        self.connection = None
        self.lock = threading.Lock()

    def _route(self):
        if self.origin.scheme != 'https':
            return None
        host, port = self.origin.hostname, self.origin.port or 443
        proxy = None if urllib.request.proxy_bypass(host) else urllib.request.getproxies().get('https')
        if not proxy:
            return host, port, None
        parsed = urllib.parse.urlsplit(proxy if '://' in proxy else 'http://' + proxy)
        if parsed.scheme != 'http' or not parsed.hostname or parsed.username or parsed.password:
            return None
        return parsed.hostname, parsed.port or 80, (host, port)

    def supported(self):
        return self._route() is not None

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def read(self, request, limit, timeout=8):
        target = urllib.parse.urlsplit(request.full_url)
        if (target.scheme, target.hostname, target.port or 443) != (self.origin.scheme, self.origin.hostname, self.origin.port or 443):
            raise ValueError('Unexpected realtime origin')
        if (request.get_method(), target.path) not in (('GET', '/api/health'), ('POST', '/api/publish/live')) or target.query:
            raise ValueError('Unsupported realtime resource')
        route = self._route()
        if route is None:
            raise ValueError('Existing proxy transport required')
        with self.lock:
            reused = self.connection is not None
            for attempt in range(2):
                try:
                    if self.connection is None:
                        self.connection = http.client.HTTPSConnection(route[0], route[1], timeout=timeout)
                        if route[2] is not None:
                            self.connection.set_tunnel(*route[2])
                    path = target.path or '/'
                    if target.query:
                        path += '?' + target.query
                    self.connection.request(request.get_method(), path, body=request.data, headers=dict(request.header_items()))
                    response = self.connection.getresponse()
                    if not 200 <= response.status < 300:
                        raise ValueError('Realtime service unavailable')
                    length = response.getheader('Content-Length')
                    if length is not None and int(length) > limit:
                        raise ResponseTooLarge()
                    data = response.read(limit + 1)
                    if len(data) > limit:
                        raise ResponseTooLarge()
                    if response.will_close:
                        self.close()
                    return data
                except (OSError, http.client.HTTPException):
                    self.close()
                    # A dead reused socket may retry one idempotent health/live
                    # request. Initial connection failures do not get doubled.
                    if not reused or attempt:
                        raise
                except (ValueError, ResponseTooLarge):
                    self.close()
                    raise
