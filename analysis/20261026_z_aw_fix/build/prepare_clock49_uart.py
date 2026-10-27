"""Parameterize only the UART transmit divisor in the incomplete isolated fallback workspace."""
from pathlib import Path
import datetime,hashlib,json
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_uart';W=R/'out/z_aw_fix_20261026/clock49_working/source';B=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not M.exists();M.mkdir()
changes={};name='core/spi_uart_modules.v';p=W/name;old=(B/name).read_bytes();assert p.read_bytes()==old
t=old.decode();nl='\r\n' if '\r\n' in t else '\n'
before='module uart_tx_115200 (';after='module uart_tx_115200 #(parameter integer BIT_TICKS=434) ('
assert t.count(before)==1;t=t.replace(before,after)
insert='    localparam [8:0] BAUD_RELOAD=BIT_TICKS-1;'+nl+'    initial if(BIT_TICKS<2 || BIT_TICKS>512) $error("UART bit divisor must fit9bits");'+nl
marker='    reg [8:0] baud = 0;';assert t.count(marker)==1;t=t.replace(marker,insert+marker)
assert t.count("9'd433")==2;t=t.replace("9'd433",'BAUD_RELOAD')
restored=t.replace(after,before).replace(insert,'').replace('BAUD_RELOAD',"9'd433");assert restored.encode()==old
p.write_bytes(t.encode());changes[name]={'old_sha256':sha(B/name),'new_sha256':sha(p),'default50_reversion_byte_exact':True}
name='telemetry_tx.v';p=W/name;old=(B/name).read_bytes();assert p.read_bytes()==old;t=old.decode()
before='parameter integer INFO_CALLER_SNAPSHOT=0)(';after='parameter integer INFO_CALLER_SNAPSHOT=0,parameter integer UART_BIT_TICKS=434)('
assert t.count(before)==1;t=t.replace(before,after)
before_call='uart_tx_115200 uart(';after_call='uart_tx_115200 #(.BIT_TICKS(UART_BIT_TICKS)) uart('
assert t.count(before_call)==1;t=t.replace(before_call,after_call)
assert t.replace(after,before).replace(after_call,before_call).encode()==old
p.write_bytes(t.encode());changes[name]={'old_sha256':sha(B/name),'new_sha256':sha(p),'default50_reversion_byte_exact':True}
(M/'SOURCE_BINDING.json').write_text(json.dumps({'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Only UART TX divisor and telemetry parameter forwarding in incomplete isolated working source. Default434 preserves50MHz. Full top still50MHz;425 at49MHz is not wired into the aircraft design yet. No SYN/PNR/device action.',
    'working_source':str(W),'changes':changes,'future_49MHz_divisor':425,'nominal_baud':115200,
    'actual_baud_from49MHz':49000000/425,'default50_reversion_byte_exact':True},indent=2)+'\n',encoding='utf8')
(W.parent/'WORK_PROGRESS_02_UART_NOT_FOR_BUILD.json').write_text(json.dumps({'scope':'Incomplete working source; no FPGA build qualification. Prior adapter and generated reference clocks remain separate tested components. Top and remaining timebase/ground integration pending.',
    'uart_binding_sha256':sha(M/'SOURCE_BINDING.json'),'working_source58':{p.relative_to(W).as_posix():sha(p) for p in W.rglob('*') if p.is_file()}},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared_only':True,'UART_sources_changed_in_isolated_work':list(changes),'default50_reversion_byte_exact':True,'clock49_or_hardware_integrated':False}))
