"""Local SiK/USB receiver, automatic flight logs, existing dashboard + replay."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import zipfile

import serial
import serial.tools.list_ports
from protocol import Dashboard,ROOT,base
from recorder import Recorder,FILES
from analysis import analyze,export_csv,FIELDS

HERE=Path(__file__).resolve().parent


def ports():
    return [dict(port=p.device,description=p.description,hwid=p.hwid,
                 vid=p.vid,pid=p.pid,serial_number=p.serial_number,
                 selectable=(p.vid is not None and (p.vid,p.pid)!=(0x403,0x6014)))
            for p in serial.tools.list_ports.comports() if p.vid is not None]


def bind_config(config):
    result=dict(config)
    identity=next((p for p in ports() if p['port']==config['port']),None)
    if identity:
        known_source={(0x403,0x6015):'SiK',(0x1a86,0x7523):'USB'}.get((identity['vid'],identity['pid']))
        if known_source and config['source']!=known_source:raise ValueError(f"{config['port']}识别为{known_source}，请正确选择来源")
    result['usb_device']=identity
    return result


class Host:
    def __init__(self,root,config,no_serial=False):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.dashboard=Dashboard(config['port']);self.config=bind_config(config)
        self.lock=threading.RLock();self.no_serial=no_serial;self.stop=threading.Event()
        self.recorder=Recorder(self.root,self.config,self.dashboard)
        self.worker=threading.Thread(target=self.receive,name='serial-read-only',daemon=True)
        if not no_serial:self.worker.start()

    def receive(self):
        while not self.stop.is_set() and not self.recorder.closed:
            port=None
            try:
                expected=self.config.get('usb_device')
                current=next((p for p in ports() if p['port']==self.config['port']),None)
                if expected and current and expected['hwid']!=current['hwid']:raise OSError('该COM口对应的USB设备已改变，等待原设备或手动选择')
                port=serial.Serial(port=None,baudrate=self.config['baud'],timeout=.2,rtscts=False,dsrdtr=False)
                port.dtr=False;port.rts=False;port.port=self.config['port'];port.open()
                self.recorder.put('connection',(True,None))
                while not self.stop.is_set() and not self.recorder.closed:
                    chunk=port.read(min(max(port.in_waiting,1),4096))
                    if chunk:self.recorder.put('chunk',chunk)
            except (serial.SerialException,OSError) as exc:
                self.recorder.put('connection',(False,str(exc)))
            finally:
                if port:port.close()
            self.stop.wait(1.5)

    def switch(self,config):
        with self.lock:
            data=self.dashboard.snapshot().get('data') or {}
            if data.get('armed'):raise ValueError('已解锁时不能切换接收端口')
            if config['port'] not in {p['port'] for p in ports() if p['selectable']}:raise ValueError('选择有效USB串口；不能使用下载器')
            if config['baud'] not in (57600,115200):raise ValueError('波特率仅支持57600/115200')
            if config['source'] not in ('SiK','USB'):raise ValueError('Unknown source')
            config=bind_config(config)
            self.close_worker();self.recorder.close();self.config=config
            self.dashboard.clear_source(config['port']);self.stop=threading.Event()
            self.recorder=Recorder(self.root,config,self.dashboard)
            self.worker=threading.Thread(target=self.receive,daemon=True)
            if not self.no_serial:self.worker.start()

    def close_worker(self):
        self.stop.set()
        if self.worker.is_alive():self.worker.join(timeout=3)
        if self.worker.is_alive():raise RuntimeError('旧串口尚未关闭，未启动第二接收器')

    def close(self):
        self.close_worker();self.recorder.close();self.dashboard.connection(False,'服务已停止')

    def logpath(self,identifier):
        if not re.fullmatch(r'\d{8}T\d{6}Z_[0-9a-f]{8}',identifier):raise ValueError('Invalid session ID')
        path=self.root/identifier
        if path.is_symlink() or not path.is_dir():raise ValueError('Unknown session')
        return path

    def sessions(self):
        result=[]
        for path in sorted(self.root.iterdir(),reverse=True):
            if not path.is_dir() or path.is_symlink():continue
            try:
                self.logpath(path.name)
                meta=json.loads((path/'meta.json').read_text(encoding='utf-8'))
                result.append(dict(id=path.name,meta=meta,active=path.name==self.recorder.id and not self.recorder.closed,
                                   bytes=sum(p.stat().st_size for p in path.iterdir() if p.is_file())))
            except (OSError,ValueError):continue
            if len(result)>=200:break
        return result


def make_server(host,port):
    server=base.viewer.make_server(host.dashboard,port)
    original=server.RequestHandlerClass
    root_page=(HERE/'dashboard.html').read_text(encoding='utf-8')
    downloads=threading.BoundedSemaphore(2)

    class Handler(original):
        def send_bytes(self,body,mime='text/html; charset=utf-8',filename=None):
            self.send_response(200);self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            self.end_headers();self.wfile.write(body)

        def stream(self,file,mime,name):
            file.seek(0,2);size=file.tell();file.seek(0)
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(size))
            self.send_header('Content-Disposition',f'attachment; filename="{name}"');self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers();shutil.copyfileobj(file,self.wfile,64*1024)

        def do_GET(self):
            if not self.local_host():self.send_error(403);return
            url=urllib.parse.urlsplit(self.path);route=url.path
            try:
                if route in ('/','/dashboard.html'):self.send_bytes(root_page.encode());return
                assets={'/logs':('logs-ui.html','text/html; charset=utf-8'),'/logs.js':('logs.js','text/javascript; charset=utf-8'),'/telemetry-ui.js':('telemetry-ui.js','text/javascript; charset=utf-8')}
                assets['/mtf-ui.js']=('mtf-ui.js','text/javascript; charset=utf-8')
                assets['/dashboard.js']=('dashboard.js','text/javascript; charset=utf-8')
                assets['/ui.css']=('ui.css','text/css; charset=utf-8')
                if route in assets:
                    name,mime=assets[route];self.send_bytes((HERE/name).read_bytes(),mime);return
                if route=='/api/state':
                    value=host.dashboard.snapshot();value['recording']=host.recorder.status();value['source']=host.config
                    value['receiver_profile']='mtf01p.b0ae_ano_control.v5'
                    value['ui_version']='flight-console.20261021.ano.v1'
                    self.json_response(200,value);return
                if route=='/api/ports':self.json_response(200,dict(ports=ports(),config=host.config));return
                if route=='/api/recorder':self.json_response(200,host.recorder.status());return
                if route=='/api/logs':self.json_response(200,dict(sessions=host.sessions(),fields=FIELDS));return
                match=re.fullmatch(r'/api/logs/([^/]+)/(analysis|download)',route)
                if match:
                    identifier,action=match.groups();path=host.logpath(identifier)
                    args=urllib.parse.parse_qs(url.query)
                    if action=='analysis':
                        value=analyze(path,args.get('field',['throttle_us'])[0],float(args.get('start',[0])[0]),float(args.get('end',['inf'])[0]),int(args.get('limit',[2000])[0]))
                        self.json_response(200,value);return
                    if not downloads.acquire(blocking=False):self.send_error(429);return
                    try:
                        fmt=args.get('format',['zip'])[0]
                        if fmt=='csv':
                            with tempfile.TemporaryFile(mode='w+',encoding='utf-8',newline='',dir=host.root) as tmp:
                                tmp.write('\ufeff');export_csv(path,tmp);tmp.flush();tmp.seek(0)
                                with tempfile.TemporaryFile(dir=host.root) as binary:
                                    for line in tmp:binary.write(line.encode('utf-8'))
                                    self.stream(binary,'text/csv; charset=utf-8',identifier+'.csv')
                        elif fmt=='zip':
                            recorder=host.recorder
                            snapshot=recorder.capture_snapshot() if identifier==recorder.id else dict(
                                sizes={name:(path/name).stat().st_size for name in FILES if (path/name).exists()},inline={})
                            with tempfile.TemporaryFile(dir=host.root) as tmp:
                                manifest={}
                                with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                                    for name in FILES:
                                        file=path/name
                                        if name not in snapshot['sizes'] or file.is_symlink():continue
                                        inline=snapshot['inline'].get(name)
                                        if inline is not None:
                                            archive.writestr(name,inline);manifest[name]=hashlib.sha256(inline).hexdigest();continue
                                        left=snapshot['sizes'][name];digest=hashlib.sha256()
                                        with file.open('rb') as inp,archive.open(name,'w') as out:
                                            while left:
                                                block=inp.read(min(left,65536))
                                                if not block:break
                                                out.write(block);digest.update(block);left-=len(block)
                                        manifest[name]=digest.hexdigest()
                                    archive.writestr('manifest.json',json.dumps(dict(sha256=manifest,active_snapshot=identifier==recorder.id,
                                        captured_utc=snapshot.get('utc'),status=snapshot.get('status'),
                                        scope='Writer-barrier prefix snapshot for active session; crashed sessions may have a partial final record'),indent=2))
                                self.stream(tmp,'application/zip',identifier+'.zip')
                        else:raise ValueError('Unknown export format')
                    finally:downloads.release()
                    return
                if route.startswith('/api/calibration/'):
                    super().do_GET();return
                super().do_GET()
            except (ValueError,TypeError) as exc:self.json_response(400,dict(error=str(exc)))
            except FileNotFoundError:self.send_error(404)
            except (BrokenPipeError,ConnectionResetError):pass
            except OSError as exc:self.json_response(500,dict(error=f'日志读取失败: {exc}'))

        def do_POST(self):
            if not self.local_host():self.send_error(403);return
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
                self.send_error(403);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=4096:raise ValueError('Body length')
                data=json.loads(self.rfile.read(length))
                if self.path=='/api/mark':
                    text=str(data.get('text','')).strip()
                    if not text or len(text)>500:raise ValueError('标记长度1~500字')
                    if not host.recorder.put('mark',text):raise ValueError('记录器不可用')
                elif self.path=='/api/connection':
                    config=dict(port=str(data['port']),baud=int(data['baud']),source=str(data['source']))
                    host.switch(config)
                elif self.path=='/api/service/stop':
                    if (host.dashboard.snapshot().get('data') or {}).get('armed'):raise ValueError('已解锁时不能关闭日志服务')
                    self.json_response(200,dict(ok=True,stopping=True))
                    threading.Thread(target=self.server.shutdown,daemon=True).start()
                    return
                else:self.send_error(403);return # No firmware/calibration/control POSTs.
                self.json_response(200,dict(ok=True,recording=host.recorder.status()))
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:self.json_response(400,dict(error=str(exc)))
            except (OSError,RuntimeError) as exc:self.json_response(500,dict(error=str(exc)))

    server.RequestHandlerClass=Handler
    return server


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',default='COM17');parser.add_argument('--baud',type=int,choices=(57600,115200),default=115200)
    parser.add_argument('--source',choices=('SiK','USB'),default='SiK');parser.add_argument('--http-port',type=int,default=8765)
    parser.add_argument('--logs',type=Path,default=ROOT/'flight_logs');parser.add_argument('--no-serial',action='store_true')
    args=parser.parse_args()
    if not 0<=args.http_port<=65535:parser.error('Invalid HTTP port')
    if not args.no_serial and args.port in {p['port'] for p in ports() if not p['selectable']}:parser.error('Cannot open the programmer as a telemetry port')
    host=Host(args.logs,dict(port=args.port,baud=args.baud,source=args.source),args.no_serial)
    try:server=make_server(host,args.http_port)
    except Exception:host.close();raise
    print(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}',source=host.config,session=host.recorder.id,serial_writes=False)),flush=True)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    finally:host.close();server.server_close()


if __name__=='__main__':main()
