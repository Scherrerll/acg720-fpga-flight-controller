from test_tools import *
import sys
simulate('legacy_telemetry_wire',[FIX/'telemetry_tx.v',FIX/'core/spi_uart_modules.v'],ROOT/'tests/legacy_telemetry_wire.v')
source=(ROOT/'tests/legacy_telemetry_wire.v').read_text()
source=source.replace("{8'd2,8'd1,32'h0000b0ad", "{8'd4,8'd19,32'h0000b0b0").replace('telemetry_wire.hex','fallback_telemetry_wire.hex')
(ROOT/'tests/fallback_telemetry_wire.v').write_text(source)
simulate('fallback_telemetry_wire',[FIX/'telemetry_tx.v',FIX/'core/spi_uart_modules.v'],ROOT/'tests/fallback_telemetry_wire.v')
sys.path.insert(0,str(ROOT/'ground'))
from protocol import decode_info
data=bytes(int(x,16) for x in (ROOT/'tests/fallback_telemetry_wire.hex').read_text().split())
assert len(data)==1136
for offset in [256,824]:
    row=decode_info(data[offset:offset+40])
    assert row['build_id']==0xb0b0 and row['height_loss_fallback_active'] and row['motor_prepared'] and row['taking_off']
print('PASS B0B0 actual UART packet/CRC/state decode')
