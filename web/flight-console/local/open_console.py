"""Open the console through its loopback HTTP bridge, never as a file URL.

This launcher does not open or enumerate serial devices. A new bridge starts
without publication configuration. An existing identified bridge is reused
without changing its sharing state or replacing its process.
"""
from enum import Enum
import argparse
import errno
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser


HERE = Path(__file__).resolve().parent
DEFAULT_PORT = 8766
READY_SECONDS = 5.0


class Listener(Enum):
    ABSENT = 'absent'
    BRIDGE = 'bridge'
    OTHER = 'other'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def port_available(port):
    """Confirm an unresponsive loopback port is free without opening a listener."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            if sys.platform == 'win32' and hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                candidate.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            candidate.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False


def probe_bridge(port, timeout=.4):
    """Identify an existing bridge with one bounded, direct loopback HTTP GET."""
    url = f'http://127.0.0.1:{port}/api/capabilities'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(url, headers={'Accept': 'application/json',
                                                  'User-Agent': 'GMFLY-Local-Launcher/1.0'})
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(16385)
            if response.status != 200 or len(raw) > 16384:
                return Listener.OTHER
            if response.headers.get_content_type() != 'application/json':
                return Listener.OTHER
            if response.headers.get('X-Content-Type-Options') != 'nosniff':
                return Listener.OTHER
            if response.headers.get('Referrer-Policy') != 'no-referrer':
                return Listener.OTHER
            value = json.loads(raw)
            if (not isinstance(value, dict) or value.get('mode') != 'local'
                    or type(value.get('can_share_logs')) is not bool
                    or type(value.get('sharing_enabled')) is not bool
                    or 'share_url' not in value
                    or not (value['share_url'] is None or isinstance(value['share_url'], str))):
                return Listener.OTHER
            return Listener.BRIDGE
    except urllib.error.HTTPError:
        return Listener.OTHER
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, OSError) or getattr(reason, 'errno', None) in (errno.ECONNREFUSED, 10061):
            return Listener.ABSENT if port_available(port) else Listener.OTHER
        return Listener.OTHER
    except OSError:
        return Listener.ABSENT if port_available(port) else Listener.OTHER
    except (ValueError, TypeError):
        return Listener.OTHER


def start_bridge(port, popen=subprocess.Popen):
    command = [sys.executable, '-B', str(HERE / 'bridge.py'), '--port', str(port)]
    options = {'cwd': str(HERE), 'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL,
               'stderr': subprocess.DEVNULL, 'close_fds': True}
    if sys.platform == 'win32':
        options['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options['start_new_session'] = True
    return popen(command, **options)


def run(port=DEFAULT_PORT, *, no_browser=False, probe=probe_bridge, popen=subprocess.Popen,
        open_url=webbrowser.open, clock=time.monotonic, sleep=time.sleep):
    if type(port) is not int or not 1 <= port <= 65535:
        print('端口无效，请使用 1～65535。', file=sys.stderr)
        return 2
    url = f'http://127.0.0.1:{port}/'
    state = probe(port)
    if state is Listener.OTHER:
        print(f'端口 {port} 已被其他服务占用，未启动或替换任何进程。请先核对服务，或使用 --port 选择其他端口。', file=sys.stderr)
        return 2
    if state is Listener.ABSENT:
        try:
            process = start_bridge(port, popen)
        except OSError:
            print('本地监控服务无法启动，请检查 Python 与本目录文件。', file=sys.stderr)
            return 2
        deadline = clock() + READY_SECONDS
        while clock() < deadline:
            state = probe(port)
            if state is Listener.BRIDGE:
                break
            if process.poll() is not None:
                print('本地监控服务启动后退出，未打开页面。请检查 bridge.py 是否完整及端口是否可用。', file=sys.stderr)
                return 2
            # The first connect may time out while our child is binding. A
            # temporarily occupied but unidentified port is never opened; give
            # our live child the remaining readiness budget to identify itself.
            sleep(.1)
        if state is not Listener.BRIDGE:
            print(f'本地监控服务尚未就绪，未打开页面。请稍后重试；不会替换已有进程。端口：{port}', file=sys.stderr)
            return 2
        print('已启动本地 HTTP 监控；实时分享默认关闭。')
    else:
        print('已复用现有本地监控服务，保留原有分享状态。')
    if no_browser:
        print(f'本地监控已就绪：{url}')
    else:
        try:
            opened = open_url(url)
        except Exception:
            opened = False
        if not opened:
            print(f'浏览器未能自动打开，请手动访问：{url}', file=sys.stderr)
            return 1
        print(f'本地监控已打开：{url}')
    print('页面数据依赖现有地面接收服务；此入口不会连接串口。')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='以 HTTP 方式打开 GM-FLY 本地监控，不直接打开 HTML 文件。')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='本地端口，默认 8766')
    parser.add_argument('--no-browser', action='store_true', help='只准备 HTTP 服务，不自动打开浏览器')
    args = parser.parse_args(argv)
    return run(args.port, no_browser=args.no_browser)


if __name__ == '__main__':
    raise SystemExit(main())
