"""Local B0B4 ground station; optional stopped XY P/I through one serial owner."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import secrets
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
from xy_pi_control import XYPIController
from xy_pi_service import stopped_guard,handle_get as pi_get,handle_post as pi_post

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
    def __init__(self,root,config,no_serial=False,enable_xy_pi=False):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.dashboard=Dashboard(config['port']);self.config=dict(config)if no_serial else bind_config(config)
        self.lock=threading.RLock();self.no_serial=no_serial;self.stop=threading.Event()
        self.transport_lock=threading.RLock();self.transport_epoch=0;self.transport_connected=False
        self.primary_epoch=None;self.info_epoch=None;self.last_uptime=None
        self.pi=XYPIController(enabled=enable_xy_pi);self.pi_token=secrets.token_urlsafe(32)
        self.pi.connection(0,False,self.config['source'],self.config['baud'])
        self.recorder=Recorder(self.root,self.config,self.dashboard,row_handler=self._receive_row,
                               serial_writes_enabled=bool(enable_xy_pi and not no_serial and self.config['source']=='SiK'and self.config['baud']==115200))
        self.worker=threading.Thread(target=self.receive,name='single-serial-owner',daemon=True)
        if not no_serial:self.worker.start()

    def _transport(self,connected,error=None):
        with self.transport_lock:
            self.transport_epoch+=1;self.transport_connected=connected
            self.primary_epoch=None;self.info_epoch=None;self.last_uptime=None
            self.pi.connection(self.transport_epoch,connected,self.config['source'],self.config['baud'])
        self.dashboard.connection(connected,error)
        return self.transport_epoch

    def _receive_row(self,row,epoch):
        if epoch is None:return row.get('_protocol')!='a591'
        with self.transport_lock:
            if epoch!=self.transport_epoch or not self.transport_connected:return False
            protocol=row.get('_canonical_protocol',row.get('_protocol'))
            if row.get('_protocol')=='a591':self.pi.response(row,epoch);return False
            if protocol=='a580':
                uptime=row.get('uptime_ms')
                if type(uptime)is int:
                    if self.last_uptime is not None and uptime<self.last_uptime:
                        self._transport(True,'检测到 FPGA 重新启动，请重新查询参数');return False
                    self.last_uptime=uptime
                self.info_epoch=epoch
            if protocol=='a579':self.primary_epoch=epoch
        return True

    def parameter_stopped_guard(self):
        with self.transport_lock:
            if not self.transport_connected or self.primary_epoch!=self.transport_epoch or self.info_epoch!=self.transport_epoch:
                return False,'等待当前连接的完整停机遥测'
        if self.recorder.closed or self.recorder.error or self.recorder.dropped_chunks:
            return False,'日志/接收队列异常，请修复后重新连接'
        return stopped_guard(self.dashboard.snapshot())

    def receive(self):
        while not self.stop.is_set() and not self.recorder.closed:
            port=None
            try:
                expected=self.config.get('usb_device')
                current=next((p for p in ports() if p['port']==self.config['port']),None)
                if expected and current and expected['hwid']!=current['hwid']:raise OSError('该COM口对应的USB设备已改变，等待原设备或手动选择')
                port=serial.Serial(port=None,baudrate=self.config['baud'],timeout=.05,write_timeout=.5,rtscts=False,dsrdtr=False)
                port.dtr=False;port.rts=False;port.port=self.config['port'];port.open()
                epoch=self._transport(True)
                self.recorder.put('connection',(True,None))
                while not self.stop.is_set() and not self.recorder.closed:
                    with self.transport_lock:epoch=self.transport_epoch
                    self.pi.tick()
                    if self.recorder.error or self.recorder.dropped_chunks:raise OSError('日志/接收队列异常，参数会话已失效')
                    if self.pi.snapshot()['phase']=='queued_set':
                        safe,reason=self.parameter_stopped_guard()
                        if not safe:self.pi.invalidate('发送前停机预检失败：'+reason)
                    outgoing=self.pi.take_write(epoch)
                    if outgoing:
                        attempt=dict(transport_epoch=epoch,opcode=outgoing['opcode'],sequence=outgoing['sequence'],packet_hex=outgoing['packet'].hex())
                        if not self.recorder.put('pi_tx_attempt',attempt):raise OSError('发送记录不可用，已取消参数会话')
                        try:
                            count=port.write(outgoing['packet'])
                            self.pi.write_result(outgoing['token'],count)
                            if not self.recorder.put('pi_tx',dict(transport_epoch=epoch,opcode=outgoing['opcode'],sequence=outgoing['sequence'],packet_hex=outgoing['packet'].hex(),bytes_written=count)):
                                raise OSError('参数发送记录队列异常，结果未确认')
                            if count!=16:raise OSError('参数帧未完整写入，结果未知')
                        except (serial.SerialException,OSError)as exc:
                            self.recorder.put('pi_tx_error',dict(**attempt,error=str(exc),bytes_written=None))
                            self.pi.write_result(outgoing['token'],0,str(exc));raise
                    chunk=port.read(min(max(port.in_waiting,1),4096))
                    if chunk and not self.recorder.put('chunk_epoch',(epoch,chunk)):raise OSError('接收队列已满，参数结果未确认')
            except (serial.SerialException,OSError) as exc:
                self._transport(False,str(exc))
                self.recorder.put('connection',(False,str(exc)))
            finally:
                if self.transport_connected:self._transport(False,'串口已关闭')
                if port:port.close()
            self.stop.wait(1.5)

    def switch(self,config):
        with self.lock:
            if self.no_serial:raise ValueError('离线预览不打开串口；请退出预览后按操作说明启动')
            data=self.dashboard.snapshot().get('data') or {}
            if data.get('armed'):raise ValueError('已解锁时不能切换接收端口')
            if config['port'] not in {p['port'] for p in ports() if p['selectable']}:raise ValueError('选择有效USB串口；不能使用下载器')
            if config['baud'] not in (57600,115200):raise ValueError('波特率仅支持57600/115200')
            if config['source'] not in ('SiK','USB'):raise ValueError('Unknown source')
            config=bind_config(config)
            self.close_worker();self.recorder.close();self.config=config
            self.dashboard.clear_source(config['port']);self.stop=threading.Event()
            self.recorder=Recorder(self.root,config,self.dashboard,row_handler=self._receive_row,
                                   serial_writes_enabled=bool(self.pi.snapshot()['enabled']and config['source']=='SiK'and config['baud']==115200))
            self.worker=threading.Thread(target=self.receive,daemon=True)
            if not self.no_serial:self.worker.start()

    def close_worker(self):
        self.stop.set()
        self._transport(False,'服务关闭或切换串口')
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
                if pi_get(self,host,route):return
                if route=='/api/health':
                    enabled=bool(host.pi.snapshot()['enabled']and not host.no_serial and host.config['source']=='SiK'and host.config['baud']==115200)
                    self.json_response(200,dict(ok=True,read_only=not enabled,serial_writes=enabled,serial_write_scope='xy_pi_only'if enabled else'none'));return
                if route in ('/','/dashboard.html'):self.send_bytes(root_page.encode());return
                assets={'/logs':('logs-ui.html','text/html; charset=utf-8'),'/logs.js':('logs.js','text/javascript; charset=utf-8'),'/telemetry-ui.js':('telemetry-ui.js','text/javascript; charset=utf-8')}
                assets['/mtf-ui.js']=('mtf-ui.js','text/javascript; charset=utf-8')
                assets['/dashboard.js']=('dashboard.js','text/javascript; charset=utf-8')
                assets['/ui.css']=('ui.css','text/css; charset=utf-8')
                assets['/xy-pi-ui.js']=('xy-pi-ui.js','text/javascript; charset=utf-8')
                assets['/xy-pi-ui.css']=('xy-pi-ui.css','text/css; charset=utf-8')
                assets['/pi-help']=('pi-help.html','text/html; charset=utf-8')
                if route in assets:
                    name,mime=assets[route];self.send_bytes((HERE/name).read_bytes(),mime);return
                if route=='/api/state':
                    value=host.dashboard.snapshot();value['recording']=host.recorder.status();value['source']=host.config
                    value['receiver_profile']='mtf01p.b0b2_timeout_policy.v3'
                    value['ui_version']='flight-console.20261026.b0b4.xy-pi.v1'
                    self.json_response(200,value);return
                if route=='/api/ports':self.json_response(200,dict(ports=[]if host.no_serial else ports(),config=host.config));return
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
            if pi_post(self,host):return
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
    parser.add_argument('--port',help='实际遥测串口，禁止默认猜测 COM 号');parser.add_argument('--baud',type=int,choices=(57600,115200),default=115200)
    parser.add_argument('--source',choices=('SiK','USB'),default='SiK');parser.add_argument('--http-port',type=int,default=8765)
    parser.add_argument('--logs',type=Path,default=ROOT/'ground/runtime/B0B4');parser.add_argument('--no-serial',action='store_true')
    parser.add_argument('--enable-xy-pi',action='store_true',help='允许显式查询及停机 P/I 设置；仅 SiK 115200，单一串口所有者')
    args=parser.parse_args()
    if not 0<=args.http_port<=65535:parser.error('Invalid HTTP port')
    if not args.no_serial and not args.port:parser.error('--port is required unless --no-serial')
    if args.no_serial:args.port='offline'
    if not args.no_serial and args.port in {p['port'] for p in ports() if not p['selectable']}:parser.error('Cannot open the programmer as a telemetry port')
    host=Host(args.logs,dict(port=args.port,baud=args.baud,source=args.source),args.no_serial,args.enable_xy_pi)
    try:server=make_server(host,args.http_port)
    except Exception:host.close();raise
    enabled=bool(args.enable_xy_pi and not args.no_serial and args.source=='SiK'and args.baud==115200)
    print(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}',source=host.config,session=host.recorder.id,serial_writes_enabled=enabled,serial_write_scope='xy_pi_only'if enabled else'none',preview_only=args.no_serial)),flush=True)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    finally:host.close();server.server_close()


if __name__=='__main__':main()
