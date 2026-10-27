"""Ask the official generator for exact50-to49MHz PLLA IP; no FPGA SYN/PNR or device access."""
from pathlib import Path
import datetime,hashlib,json,subprocess
R=Path(__file__).resolve().parents[3];M=Path(__file__).resolve().parent/'clock49_generate';A=R/'out/z_aw_fix_20261026/clock49_generate'
G=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/bin/gw_sh.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert not M.exists() and not A.exists()
assert sha(G)=='585c12968550a960d1021287742672ff9d6bbeaee5623f6811dfc1f907a4af41'
M.mkdir();A.mkdir(parents=True)
tcl='\n'.join([
    f'create_project -name clock49_generate -dir {{{(A/"project").as_posix()}}} -pn GW5AT-LV60PG484AC1/I0 -device_version B',
    f'create_ipc -name clock_plladv -module_name clock49 -language Verilog -dir {{{(A/"ip").as_posix()}}}',
    'set_property -dict {CONFIG.CLKIN_FREQ 50.000 CONFIG.CLKOUT0_FREQ 49.000 CONFIG.LOCK_EN true CONFIG.MDRP_CLK_FREQ 50} [get_ips clock49]',
    'puts CLOCK49_CONFIGURED_PROPERTIES_BEGIN','report_property [get_ips clock49]',
    'generate_target [get_ips clock49]',
    'puts CLOCK49_GENERATION_RETURNED_EOF','flush stdout',''])
script=A/'generate_clock49.tcl';script.write_text(tcl,encoding='utf8')
command=[str(G),str(script)]
record={'command':command,'started_utc':utc(),'cwd':str(A),'tool_sha256':sha(G),'script_sha256':sha(script),
    'scope':'Official PLL_ADV IP generation only, input50MHz/output49MHz exact tolerance0, phase/duty defaults unchanged. No top-source integration, FPGA SYN/PNR or programmer.'}
with (M/'generation.log').open('wb') as log:
    p=subprocess.Popen(command,cwd=A,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    record['pid']=p.pid;(M/'process.json').write_text(json.dumps(record,indent=2)+'\n');code=p.wait()
record.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),log_sha256=sha(M/'generation.log'))
(M/'exit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({'actual_IP_generation_wait':code,'log':str(M/'generation.log'),'FPGA_SYN_PNR_or_hardware_started':False}))
assert code==0 and 'CLOCK49_GENERATION_RETURNED_EOF' in (M/'generation.log').read_text(encoding='utf8',errors='replace')
files={p.relative_to(A).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in A.rglob('*') if p.is_file()}
(M/'GENERATED_FILES.json').write_text(json.dumps({'scope':'Manufacturer-generated scratch IP only; not an implemented or qualified firmware clock.',
    'input_MHz':50,'requested_output_MHz':49,'actual_generator_wait':code,'files':files},indent=2)+'\n',encoding='utf8')
