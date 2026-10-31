"""打开本地地面站 P/I 页；已有服务优先，新预览不连接串口。"""
import argparse
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
UI_VERSION = 'flight-console.20261026.b0b4.xy-pi.v1'
PROFILE = 'mtf01p.b0b2_timeout_policy.v3'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def probe(port):
    """检查接口兼容性；返回 local、free 或 other，不更改服务状态。"""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(f'http://127.0.0.1:{port}/api/state', timeout=.7) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024:
                return 'other'
            state = json.loads(raw)
        if (isinstance(state, dict) and state.get('ui_version') == UI_VERSION
                and state.get('receiver_profile') == PROFILE):
            return 'local'
        return 'other'
    except (OSError, ValueError, TypeError, urllib.error.HTTPError):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
                if sys.platform == 'win32':
                    candidate.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                candidate.bind(('127.0.0.1', port))
            return 'free'
        except OSError:
            return 'other'


def run(port=8874, no_browser=False):
    if not 1 <= port <= 65535 or port == 8766:
        print('请选择有效的本地地面站端口；8766 留给网页旁路。', file=sys.stderr)
        return 2
    # 先复用常规接收器，再检查预览端口；不修改已有实例的固件版本或写入配置。
    selected = None
    states = {}
    for candidate in dict.fromkeys((8765, port)):
        states[candidate] = probe(candidate)
        if states[candidate] == 'local':
            selected = candidate
            print(f'已复用 {candidate} 本地地面站。')
            break
    if selected is None:
        if states[port] != 'free':
            print(f'端口 {port} 已被其他服务占用，请使用 --port 选择空闲端口。', file=sys.stderr)
            return 2
        command = [sys.executable, '-X', 'utf8', '-B', str(HERE/'launch.py'),
                   '--no-serial', '--xy-pi-build', 'B0B5', '--http-port', str(port),
                   '--logs', str(HERE.parent/'runtime'/'local-preview')]
        options = dict(cwd=HERE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, close_fds=True)
        if sys.platform == 'win32':
            options['creationflags'] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            options['start_new_session'] = True
        try:
            process = subprocess.Popen(command, **options)
        except OSError:
            print('无法启动地面站，请检查 Python 和依赖安装。', file=sys.stderr)
            return 2
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if probe(port) == 'local':
                selected = port
                break
            if process.poll() is not None:
                break
            time.sleep(.1)
        if selected is None:
            print('地面站未就绪，请检查 Python、pyserial 及端口占用。', file=sys.stderr)
            return 2
        print('已启动无串口本地预览；接收器和参数写入尚未连接。')
    url = f'http://127.0.0.1:{selected}/parameters'
    print(f'本地 P/I 页面：{url}')
    if not no_browser:
        try:
            opened = webbrowser.open(url)
        except Exception:
            opened = False
        if not opened:
            print('请手动打开上方网址。', file=sys.stderr)
            return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8874, help='无已有服务时使用的预览端口')
    parser.add_argument('--no-browser', action='store_true', help='准备服务但不自动打开浏览器')
    args = parser.parse_args(argv)
    return run(args.port, args.no_browser)


if __name__ == '__main__':
    raise SystemExit(main())
