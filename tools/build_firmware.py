"""Portable OFFLINE B0AE build using the unchanged selected TCL. Never programs hardware."""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import datetime
import xml.etree.ElementTree as ET
from verify_export import ROOT, RELEASE, sha, verify

PINS = {'clk50':'Y18','imu_sck':'E17','imu_mosi':'C20','imu_miso':'D19',
        'imu_cs_n':'E18','imu_gyro_cs_n':'F20','rc_ppm_in':'B17','uart_tx':'M15',
        'led2':'L21','led3':'K21','motor1_pwm':'D17','motor2_pwm':'C17',
        'motor3_pwm':'E16','motor4_pwm':'D16','range_rx':'C14','range_tx':'C15','radio_tx':'B15'}

def check_build(folder):
    top='acg720_ano_port'
    pnr=folder/'impl/pnr'
    command_path=pnr/'cmd.do'
    command=command_path.read_text(encoding='utf-8')
    actual=dict(re.findall(r'^-(\w+)\s+(\S+)\s*$',command,re.M))
    if actual.get('place_option')!='3' or actual.get('route_option')!='2' or \
       float(actual.get('global_freq','0'))!=50 or not re.search(r'^-timing\s*$',command,re.M) or \
       re.search(r'^-replicate(?:\s|$)',command,re.M):
        raise ValueError('Actual PNR options differ from selected build')
    synthesis_path=folder/'impl/gwsynthesis'/(top+'.prj')
    syn={n.attrib.get('type'):n.attrib.get('value') for n in ET.parse(synthesis_path).findall('.//Option')}
    if any(syn.get(k)!=v for k,v in dict(map_option='2',max_fanout='200',opt_goal='area').items()) or \
       float(syn.get('global_freq','0'))!=50:
        raise ValueError('Actual synthesis options differ from selected build')
    timing=(pnr/(top+'.tr')).read_text(encoding='utf-8', errors='replace')
    resources=(pnr/(top+'.rpt.txt')).read_text(encoding='utf-8', errors='replace')
    console=(folder/'build_console.txt').read_text(encoding='utf-8', errors='replace')
    if re.search(r'ERROR\s*\(', console+resources) or re.search(r'\b[1-9][0-9]*\s+unrouted nets\b', resources):
        raise ValueError('Compiler errors or unrouted nets')
    if not all(s in console for s in ('Placement and routing completed','Bitstream generation completed')):
        raise ValueError('Missing successful compiler completion')
    fmax=re.search(r'clk50\s+50\.000\(MHz\)\s+([0-9.]+)\(MHz\)',timing)
    if not fmax or float(fmax.group(1))<50:
        raise ValueError('Missing or failed 50 MHz timing')
    for kind in ('setup','hold'):
        row=re.search(r'clk50\s+'+kind+r'\s+(-?[0-9.]+)\s+([0-9]+)',timing)
        if not row or float(row.group(1)) or int(row.group(2)):
            raise ValueError('Failed '+kind+' timing')
    pins=dict(re.findall(r'^(\w+)\s+\|\s+-\s+\|\s+(\w+)/\d+\s+\|',resources,re.M))
    if pins != PINS:
        raise ValueError('Placed pins differ from selected source')
    fs=pnr/(top+'.fs')
    with fs.open(encoding='ascii',errors='replace') as stream:
        header=''.join(next(stream,'') for _ in range(15))
    if not re.search(r'UserCode:\s*0x0*B0AE\b',header,re.I):
        raise ValueError('Unexpected bitstream UserCode')
    return {'passed':True,'fmax_mhz':float(fmax.group(1)), 'pins':pins,
            'actual_pnr_options':actual,'actual_synthesis_options':syn,
            'reports_sha256':{str(p.relative_to(folder)).replace('\\','/'):sha(p) for p in
                (command_path,synthesis_path,pnr/(top+'.tr'),pnr/(top+'.rpt.txt'),folder/'build_console.txt')},
            'bitstream_sha256':sha(fs),'hardware_programmed':False,'flight_ready':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gw-sh',default=os.environ.get('GW_SH') or shutil.which('gw_sh'))
    parser.add_argument('--execute',action='store_true',help='Actually run synthesis and routing (offline only)')
    args=parser.parse_args()
    proof=verify()
    if not args.execute:
        print(json.dumps({'export_verified':proof,'compiler':args.gw_sh,'build_started':False},indent=2))
        return
    if not args.gw_sh or not Path(args.gw_sh).is_file():
        parser.error('Provide --gw-sh or GW_SH pointing to Gowin 1.9.12.04 gw_sh.exe')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'out'/('b0ae_'+stamp)
    shutil.copytree(RELEASE/'fixture',folder)
    before={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
    with (folder/'build_console.txt').open('w',encoding='utf-8') as log:
        subprocess.run([args.gw_sh,'build.tcl'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,check=True)
    for name,expected in before.items():
        if sha(folder/name)!=expected:
            raise ValueError('Source changed during build: '+name)
    result=check_build(folder)
    result['historical_bitstream_match']=(result['bitstream_sha256']==
        '7cef4a47a17d2a03709d0b7f5bdb7c1b46c030a33c72876db65aba2e0b953a80')
    (folder/'export_build_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(folder),'result':result},indent=2))

if __name__=='__main__':main()

