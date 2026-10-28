"""Public cycle comparison against frozen navigation+height-fusion sources."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
IV=REPO.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
PRIM=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def references(out):
    result=[];baseline=json.loads((ROOT/'candidate/BASELINE.json').read_text())['source_sha256']
    for rel,name in [('mtf_xyz_navigation_control.v','navigation_reference.v'),('position/mtf_shared_height_fusion.v','height_fusion_reference.v')]:
        source=REPO/'firmware/B0B4/source'/rel;assert sha(source)==baseline[rel]
        text=source.read_text()
        for module in ('mtf_xyz_navigation_control','mtf_shared_height_fusion'):text=re.sub(r'\b'+module+r'\b',module+'_reference',text)
        p=out/name;p.write_text(text);result.append(p)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--tests',type=Path,required=True);args=parser.parse_args()
    source=args.source.resolve();out=REPO/'out/water_drive_20261028'/('nav_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    tmp=out/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    files=[source/f.attrib['path'] for f in ET.parse(source/'acg720_ano_port.gprj').findall('.//File') if f.attrib.get('type')=='file.verilog' and f.attrib.get('enable')=='1']+[PRIM]+references(out)+[args.tests.resolve()/'tb_navigation_equivalence.v']
    inputs={str(p):sha(p) for p in files};target=out/'navigation.vvp'
    compiled=subprocess.run([str(IV),'-g2012','-s','tb_navigation_equivalence','-I',str(source),'-o',str(target)]+[str(p) for p in files],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    (out/'compile.log').write_bytes(compiled.stdout);assert compiled.returncode==0,compiled.stdout.decode(errors='replace')
    simulation=subprocess.run([str(VVP),str(target)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=420,creationflags=subprocess.CREATE_NO_WINDOW)
    (out/'simulation.log').write_bytes(simulation.stdout)
    result=dict(passed=simulation.returncode==0 and b'PASS' in simulation.stdout,compile_exit=compiled.returncode,sim_exit=simulation.returncode,inputs=inputs,output=simulation.stdout.decode(errors='replace'))
    (out/'results.json').write_text(json.dumps(result,indent=2));assert all(sha(Path(n))==h for n,h in inputs.items())
    print(result['output'],flush=True);print('RESULTS',out,flush=True);assert result['passed']
if __name__=='__main__':main()
