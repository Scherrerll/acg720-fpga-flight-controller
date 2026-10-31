"""B0B5 串口 XY P/I 参数工具：串口须独占；参数仅本次上电有效，不写 Flash；实物测试范围另见版本记录。"""
# 中文说明：本工具仅与 B0B5 参数协议通信；串口由一个程序独占，运行前须释放其他接收程序。
import argparse,binascii,json,struct,time
from decimal import Decimal,InvalidOperation

STATUS={0:'OK',1:'FORMAT',2:'CRC',3:'RANGE',4:'LOCKED',5:'STALE_SEQUENCE',6:'OPCODE'}
# 参数以万分之一为单位在线上传输，例如 0.1000 对应整数 1000；CRC 覆盖协议体。
def encode_request(op,seq,p=0,i=0):
 body=struct.pack('>BBBBIHH',1,op,16,0,seq,p,i)
 return b'\xa5\x90'+body+binascii.crc_hqx(body,0xffff).to_bytes(2,'big')
# 严格检查应答长度、CRC、版本和构建标识，避免把其他固件的应答误认为 B0B5。
def decode_response(packet):
 if len(packet)!=24 or packet[:2]!=b'\xa5\x91':raise ValueError('response frame length/header')
 if binascii.crc_hqx(packet[2:-2],0xffff)!=int.from_bytes(packet[-2:],'big'):raise ValueError('response CRC')
 version,op,length,status,seq,p,i,generation,build=struct.unpack('>BBBBIHHII',packet[2:-2])
 if version!=1 or length!=24 or build!=0xb0b5:raise ValueError('unsupported parameter feature/build')
 if p>10000 or i>10000:raise ValueError('response gain range')
 return dict(protocol=version,opcode=op,status=status,status_name=STATUS.get(status,'UNKNOWN'),sequence=seq,
  p=p/10000,i=i/10000,p_wire=p,i_wire=i,generation=generation,build=f'{build:08X}',persistence='this power cycle only')
# 串口可能拆包或粘包：缓存后按帧头寻找完整的 24 字节应答，校验失败逐字节重新同步。
class ResponseStream:
 def __init__(self):self.buffer=bytearray()
 def feed(self,data):
  self.buffer.extend(data);rows=[]
  while True:
   at=self.buffer.find(b'\xa5\x91')
   if at<0:
    self.buffer[:]=self.buffer[-1:] if self.buffer[-1:]==b'\xa5' else b''
    return rows
   if at:del self.buffer[:at]
   if len(self.buffer)<24:return rows
   try:row=decode_response(bytes(self.buffer[:24]))
   except ValueError:del self.buffer[0];continue
   del self.buffer[:24];rows.append(row)
# 使用十进制定点输入检查，限制为 0～1 且步长为 0.0001，避免浮点取整误差。
def gain(text):
 try:scaled=Decimal(text)*10000
 except InvalidOperation:raise argparse.ArgumentTypeError('gain must be a decimal number')
 if not scaled.is_finite() or scaled!=scaled.to_integral_value() or not 0<=scaled<=10000:
  raise argparse.ArgumentTypeError('gain must be 0..1 inclusive, in steps of 0.0001')
 return int(scaled)
# 每次交易只接收操作码和序号匹配的应答；SET 超时不会自动重发，避免重复修改参数。
def exchange(port,stream,op,seq,p=0,i=0,timeout=3):
 port.write(encode_request(op,seq,p,i));port.flush();until=time.monotonic()+timeout
 while time.monotonic()<until:
  for row in stream.feed(port.read(max(1,min(port.in_waiting,4096)))):
   if row['sequence']==seq and row['opcode']==op:return row
 raise TimeoutError('No matching response. SET is never automatically retransmitted; query before a new SET.')
# GET 查询当前值；SET 收到成功应答后还会发起独立 GET 核对，参数仅在本次上电期间有效。
def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--port',required=True,help='exclusive serial port; use only after the current owner has released it')
 a.add_argument('--seq',type=int,help='fresh unsigned 32-bit SET sequence; strictly increasing during this boot')
 sub=a.add_subparsers(dest='command',required=True);sub.add_parser('get')
 s=sub.add_parser('set');s.add_argument('--p',type=gain,required=True);s.add_argument('--i',type=gain,required=True)
 args=a.parse_args();seq=args.seq if args.seq is not None else (time.time_ns()//1000000)&0xffffffff
 if not 0<=seq<=0xffffffff:a.error('--seq must fit unsigned 32 bits')
 import serial
 try:
  with serial.Serial(args.port,115200,timeout=.05,write_timeout=1) as port:
   stream=ResponseStream();op=1 if args.command=='get' else 2
   row=exchange(port,stream,op,seq,getattr(args,'p',0),getattr(args,'i',0));print(json.dumps(row,ensure_ascii=False,indent=2))
   if row['status']!=0:raise RuntimeError(row['status_name']+'; active values above were read from FPGA')
   if op==2:
    readback=exchange(port,stream,1,(seq+1)&0xffffffff)
    if not (readback['status']==0 and readback['generation']==row['generation'] and (readback['p_wire'],readback['i_wire'])==(args.p,args.i)):
     raise RuntimeError('independent GET mismatch')
    print('ACK + independent GET verified. Parameters apply to this power cycle only; no Flash was written.')
 except serial.SerialException as e:
  raise SystemExit(f'Serial unavailable (possibly owned by the ground receiver): {e}')
if __name__=='__main__':main()
