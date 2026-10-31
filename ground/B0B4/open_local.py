"""打开本地地面站；连接数传和无串口预览均需显式选择。"""
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


def get_json(port, path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(f'http://127.0.0.1:{port}{path}', timeout=.7) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('响应过大')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('无效响应')
    return value


def probe(port):
    """区分兼容真实站、离线站、空闲端口和未知服务。"""
    try:
        state = get_json(port, '/api/state')
        if state.get('ui_version') != UI_VERSION or state.get('receiver_profile') != PROFILE:
            return 'other'
        source = state.get('source')
        name = source.get('port') if isinstance(source, dict) else None
        if not isinstance(name, str) or not name.strip():
            return 'other'
        return 'preview' if name.strip().lower() == 'offline' else 'real'
    except (OSError, ValueError, TypeError, urllib.error.HTTPError):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
                if sys.platform == 'win32':
                    candidate.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                candidate.bind(('127.0.0.1', port))
            return 'free'
        except OSError:
            return 'other'


def select_sik():
    # Deliberately lazy: opening an existing service never enumerates devices.
    from serial.tools import list_ports
    matches = [p.device for p in list_ports.comports() if p.vid == 0x0403 and p.pid == 0x6015]
    if len(matches) != 1:
        raise ValueError(f'发现 {len(matches)} 个匹配的 SiK 数传；需要恰好一个，未选择串口。')
    return matches[0]


def compatible_build(port, build, require_enabled=False):
    try:
        status = get_json(port, '/api/xy-pi/status')
        if status.get('expected_build') != '0000' + build:
            return 'build'
        if require_enabled:
            health = get_json(port, '/api/health')
            if health.get('serial_writes') is not True or status.get('enabled') is not True:
                return 'disabled'
        return 'ok'
    except (OSError, ValueError, TypeError, urllib.error.HTTPError):
        return 'unavailable'


def run(port=None, no_browser=False, preview=False, connect_sik=False, enable_xy_pi=False, xy_pi_build='B0B4'):
    port = port if port is not None else (8874 if preview else 8765)
    if xy_pi_build not in ('B0B4', 'B0B5'):
        print('参数版本必须是 B0B4 或 B0B5。', file=sys.stderr)
        return 2
    if not 1 <= port <= 65535 or port == 8766:
        print('请选择有效的本地地面站端口；8766 留给网页旁路。', file=sys.stderr)
        return 2
    if preview and (connect_sik or enable_xy_pi):
        print('预览不能与连接数传或启用参数选项同时使用。', file=sys.stderr)
        return 2
    state = probe(port)
    desired = 'preview' if preview else 'real'
    if state == desired:
        compatibility = compatible_build(port, xy_pi_build, require_enabled=enable_xy_pi)
        if compatibility == 'build':
            print(f'已有地面站参数版本与所选 {xy_pi_build} 不一致；未更改或重启该服务。', file=sys.stderr)
            return 2
        if compatibility == 'disabled':
            print('已有接收器未启用参数入口；请按操作说明在维护窗口处理，未更改现有服务。', file=sys.stderr)
            return 2
        if compatibility != 'ok':
            print('无法核对已有地面站参数版本；未更改该服务。', file=sys.stderr)
            return 2
        print(f'已复用 {port} 本地地面站。')
    else:
        if state != 'free':
            print(f'端口 {port} 已被其他服务或不同模式的地面站占用，未更改该服务。', file=sys.stderr)
            return 2
        if not preview and not connect_sik:
            print('未找到真实接收器；请使用 --connect-sik 连接唯一 SiK 数传，或使用 --preview 查看离线页面。', file=sys.stderr)
            return 2
        command = [sys.executable, '-X', 'utf8', '-B', str(HERE/'launch.py')]
        if preview:
            command += ['--no-serial', '--logs', str(HERE.parent/'runtime'/'local-preview')]
        else:
            try:
                device = select_sik()
            except (ImportError, OSError, ValueError) as exc:
                print(f'无法选择 SiK 数传：{exc}', file=sys.stderr)
                return 2
            command += ['--port', device, '--source', 'SiK', '--baud', '115200',
                        '--logs', str(HERE.parent/'runtime'/xy_pi_build)]
            if enable_xy_pi:
                command.append('--enable-xy-pi')
        command += ['--xy-pi-build', xy_pi_build, '--http-port', str(port)]
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
        ready = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            if probe(port) == desired and process.poll() is None:
                if compatible_build(port, xy_pi_build, require_enabled=enable_xy_pi) != 'ok':
                    time.sleep(.1)
                    continue
                if preview:
                    ready = True
                    break
                try:
                    state = get_json(port, '/api/state')
                    source = state.get('source')
                    if state.get('connected') is True and isinstance(source, dict) and source.get('port') == device:
                        ready = True
                        break
                except (OSError, ValueError, TypeError, urllib.error.HTTPError):
                    pass
            time.sleep(.1)
        if not ready:
            if process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass
            print('地面站或数传未就绪，请检查 pyserial、串口和端口占用；未切换到预览。', file=sys.stderr)
            return 2
        print('已启动无串口预览。' if preview else '已启动 SiK 接收器；连接状态以页面遥测为准。')
    url = f'http://127.0.0.1:{port}/parameters'
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
    parser.add_argument('--port', type=int, help='地面站 HTTP 端口（默认接收 8765，预览 8874）')
    parser.add_argument('--no-browser', action='store_true', help='准备服务但不自动打开浏览器')
    parser.add_argument('--preview', action='store_true', help='显式打开无串口预览')
    parser.add_argument('--connect-sik', action='store_true', help='无已有服务时连接唯一匹配的 SiK 数传')
    parser.add_argument('--enable-xy-pi', action='store_true', help='新接收器显式启用本地参数入口')
    parser.add_argument('--xy-pi-build', choices=('B0B4', 'B0B5'), default='B0B4', help='选择与设备一致的参数版本（默认 B0B4）')
    args = parser.parse_args(argv)
    return run(args.port, args.no_browser, args.preview, args.connect_sik, args.enable_xy_pi, args.xy_pi_build)


if __name__ == '__main__':
    raise SystemExit(main())
