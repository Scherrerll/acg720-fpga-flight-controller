"""Execute passive SiK summary, real UART, legacy byte preservation and parser proof."""
from pathlib import Path
import binascii
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

FW=Path(__file__).resolve().parents[1]
REPO=FW.parents[1]
OUT=REPO/'out/B0B2/sik'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,**{k:str(OUT) for k in ('TMP','TEMP','TMPDIR')})
    iv=os.environ.get('IVERILOG') or shutil.which('iverilog') or str(REPO.parents[1]/'.tools/iverilog/app/bin/iverilog.exe')
    vvp=os.environ.get('VVP') or str(Path(iv).with_name('vvp.exe' if os.name=='nt' else 'vvp'))
    def run(command):
        p=subprocess.run(list(map(str,command)),env=env,capture_output=True,text=True,timeout=180)
        print(p.stdout.strip(),flush=True)
        if p.stderr:print(p.stderr.strip(),file=sys.stderr)
        p.check_returncode()
        return p.stdout
    frozen=REPO/'firmware/B0B0/source_snapshot/telemetry_tx.v'
    baseline=json.loads((FW/'baseline.json').read_text(encoding='utf-8'))
    assert sha(frozen)==baseline['source_sha256']['telemetry_tx.v'],'frozen telemetry changed'
    golden=OUT/'telemetry_tx_golden.v'
    golden.write_text(frozen.read_text(encoding='utf-8').replace('module telemetry_tx #','module telemetry_tx_golden #'),encoding='utf-8')
    for name,files in [('sik_summary_tb',[FW/'source/sik_imu_diagnostic.v']),('sik_wire_tb',[FW/'source/telemetry_tx.v',FW/'source/core/spi_uart_modules.v',golden])]:
        target=OUT/(name+'.vvp')
        run([iv,'-g2012','-s',name,'-o',target,*files,FW/'tests'/(name+'.v')])
        stdout=run([vvp,target,'+WIRE='+str(OUT/'sik_wire.hex'),'+GOLDEN='+str(OUT/'legacy_wire.hex')])
        assert 'PASS '+name[:-3] in stdout, name+' did not complete'
    wire=bytes.fromhex((OUT/'sik_wire.hex').read_text());old=bytes.fromhex((OUT/'legacy_wire.hex').read_text())
    assert len(wire)==644 and len(old)==568 and wire[:568]==old,'legacy wire bytes changed'
    sizes=[224,32,40,128,96,48,76];headers=['a579','a57a','a580','a581','a582','a583','a585'];offset=0
    for size,header in zip(sizes,headers):
        p=wire[offset:offset+size];assert p[:2].hex()==header
        if header in ('a579','a57a'):
            xor=0
            for b in p[2:-1]:xor^=b
            assert xor==p[-1],header+' XOR'
        else:assert binascii.crc_hqx(p[2:-2],0xffff)==int.from_bytes(p[-2:],'big'),header+' CRC'
        offset+=size
    run([sys.executable,'-B','-m','unittest','discover','-s',FW/'tests','-p','test_protocol.py','-v'])
    files=[FW/'source'/f.attrib['path'] for f in ET.parse(FW/'source/acg720_ano_port.gprj').findall('.//File') if f.attrib.get('enable')=='1' and f.attrib.get('type')=='file.verilog']
    assert not any(p.name=='diagnostic_uart.v' for p in files)
    top=(FW/'source/acg720_ano_port.v').read_text(encoding='utf-8')
    assert 'ENABLE_USB_DIAGNOSTIC' not in top and 'assign uart_tx=telemetry_radio_tx;' in top
    run([iv,'-g2012','-s','acg720_ano_port','-I',FW/'source','-o',OUT/'top.vvp',*files])
    result=dict(schema='b0b2.sik-tests.v1',passed=True,hardware_accessed=False,legacy_bytes_equal=568,wire_bytes=644,frame_bytes=76,baud=115200,
        wire_sha256=sha(OUT/'sik_wire.hex'),golden_source_sha256=sha(frozen),
        source_sha256={p.relative_to(FW/'source').as_posix():sha(p) for p in (FW/'source').rglob('*') if p.is_file()})
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('PASS SiK summary + real 434-clock UART/CRC + frozen A579-A583 byte equality + parser/recorder + full top',flush=True)
if __name__=='__main__':main()
