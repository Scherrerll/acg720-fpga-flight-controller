from test_tools import *
import binascii,struct,sys
old=Path(json.loads((ROOT/'baseline.json').read_text())['parent'])/'tests/telemetry_wire.v'
s=old.read_text();(ROOT/'tests/legacy_telemetry_wire.v').write_text(s)
simulate('legacy_telemetry_wire',[FIX/'telemetry_tx.v',FIX/'core/spi_uart_modules.v'],ROOT/'tests/legacy_telemetry_wire.v')
sys.path.insert(0,str(ROOT/'ground'))
from nav_protocol import FORMAT_V3,decode_nav
from protocol import decode_info
body=struct.pack(FORMAT_V3,5,0xbf,1,0,123400,1,10,20000,1<<19,234,0,0,0,0,0,0,234,0,0,0,0,0,0,0x15,0,0,1400,0,600)
s=s.replace("{8'd2,8'd1,32'h0000b0ad", "{8'd3,8'd15,32'h0000b0ae").replace('.nav_body(720\'d0)',f".nav_body(720'h{body.hex()})").replace('telemetry_wire.hex','ano_telemetry_wire.hex')
(ROOT/'tests/ano_telemetry_wire.v').write_text(s)
simulate('ano_telemetry_wire',[FIX/'telemetry_tx.v',FIX/'core/spi_uart_modules.v'],ROOT/'tests/ano_telemetry_wire.v')
raw=bytes(int(x,16)for x in (ROOT/'tests/ano_telemetry_wire.hex').read_text().split())
info=[];nav=[]
for i in range(len(raw)-39):
 if raw[i:i+2]==b'\xa5\x80':
  try:info.append(decode_info(raw[i:i+40]))
  except ValueError:pass
 if raw[i:i+2]==b'\xa5\x82':
  try:nav.append(decode_nav(raw[i:i+96]))
  except ValueError:pass
assert len(info)==len(nav)==2
assert all(n['vertical_active'] and not n['xyz_requested'] and n['target_height_mm']==600 for n in nav)
assert all(n['build_id']==0xb0ae and n['motor_prepared'] and n['taking_off'] for n in info)
print('B0AE actual UART framing/CRC/parser roundtrip passed')
