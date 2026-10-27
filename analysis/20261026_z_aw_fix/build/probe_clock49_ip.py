"""Inspect official PLL_ADV properties in a new scratch project; no SYN/PNR or device action."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[3];M=Path(__file__).resolve().parent/'clock49_probe';A=R/'out/z_aw_fix_20261026/clock49_probe'
G=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not M.exists() and not A.exists()
assert sha(G)=='585c12968550a960d1021287742672ff9d6bbeaee5623f6811dfc1f907a4af41'
M.mkdir();A.mkdir(parents=True)
project=(A/'project').as_posix();ip=(A/'ip').as_posix()
assert not any(c in project+ip for c in '{}\r\n')
tcl='\n'.join([
    f'create_project -name clock49_probe -dir {{{project}}} -pn GW5AT-LV60PG484AC1/I0 -device_version B',
    f'create_ipc -name clock_plladv -module_name clock49 -language Verilog -dir {{{ip}}}',
    'puts CLOCK_IP_PROPERTIES_BEGIN','list_property [get_ips clock49]',
    'puts CLOCK_IP_DEFAULTS_BEGIN','report_property [get_ips clock49]',
    'puts CLOCK_IP_QUERY_RETURNED_EOF','flush stdout',''])
script=A/'query_properties.tcl';script.write_text(tcl,encoding='utf8')
command=[str(G),str(script)]
record={'command':command,'started_utc':utc(),'cwd':str(A),'tool_sha256':sha(G),'script_sha256':sha(script),
    'scope':'Official IP property query only; scratch project/IPC creation, no FPGA SYN/PNR or programmer.'}
with (M/'query.log').open('wb') as log:
    p=subprocess.Popen(command,cwd=A,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=p.pid;(M/'process.json').write_text(json.dumps(record,indent=2)+'\n');code=p.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),log_sha256=sha(M/'query.log'))
(M/'exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({'actual_IP_query_wait':code,'log':str(M/'query.log'),'SYN_PNR_or_hardware_started':False}))
assert code==0 and 'CLOCK_IP_QUERY_RETURNED_EOF' in (M/'query.log').read_text(encoding='utf8',errors='replace')
