"""Independent read-only physical result audit; writes only this review JSON.

Protected placement files, if inventoried, receive opaque hashes only; no decoding.
"""
from pathlib import Path
import datetime,gzip,hashlib,json,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2].resolve()
M=R/'analysis/20261026_z_aw_fix/build/compact_aw_v22';P=M/'physical_p3r0_01'
A=R/'out/z_aw_fix_20261026/compact_aw_v22/physical_p3r0_01';S=A/'source';V=A/'verification';PNR=S/'impl/pnr'
EXPECTED_VG='e84a81f4a5abb4c15c9e599cc4c2d2e77397a328c9372d0a94c8949fbbf7f4f8'
seen={}
def safe(path):
    path=Path(path)
    if not path.is_absolute():path=R/path
    assert all(not (part.lower().startswith('.env') or part.lower().endswith('.env')) for part in path.parts),'Environment path excluded'
    for part in [path,*path.parents]:assert not part.is_symlink() and not part.is_junction(),'Link excluded'
    path=path.resolve();assert path.is_relative_to(R),'Path escapes repository'
    return path
def digest(data):return hashlib.sha256(data).hexdigest()
def blob(path):
    path=safe(path);data=path.read_bytes();seen[path.relative_to(R).as_posix()]={'sha256':digest(data),'bytes':len(data)};return data
def read(path):return json.loads(blob(path).decode('utf8'))
def text(path):return blob(path).decode('utf8',errors='strict').replace('\r\n','\n')
def zero(receipt):return type(receipt.get('actual_p_wait')) is int and receipt['actual_p_wait']==0 and receipt.get('normal_wait_return') is True
terminal=read(P/'TERMINAL_MANIFEST.json');raw=read(P/'INDEPENDENT_RAW_REVIEW.json')
assert seen[(P/'TERMINAL_MANIFEST.json').relative_to(R).as_posix()]['sha256']=='e2b8f9dbda0ecd2f16f45e485e9c7add75d99c6e7271a8dfeb6e8d798acf3b94'
assert seen[(P/'INDEPENDENT_RAW_REVIEW.json').relative_to(R).as_posix()]['sha256']=='dafa8ed37f1d3912dc2d8e988030645fa880ace0d79f26b56f2bf83f586f2117'
assert terminal['passed'] is raw['passed'] is True and all(raw['checks'].values())
for field in ['vendor_actual_p_wait','runner_actual_p_wait']:assert type(terminal[field]) is int and terminal[field]==0
assert terminal['vendor_normal_wait_return'] is terminal['runner_normal_wait_return'] is True
vendor=read(V/'physical_exit.json');runner=read(P/'runner_exit.json')
assert zero(vendor) and zero(runner) and not vendor.get('terminated_after_timeout') and not runner.get('terminated_after_timeout')
assert digest(blob(vendor['log']))==vendor['log_sha256']
for channel in ['stdout','stderr']:assert digest(blob(P/('runner.'+channel+'.log')))==runner[channel+'_sha256']
for name,item in terminal['artifacts'].items():
    data=blob(name);assert digest(data)==item['sha256'] and len(data)==item['bytes']
    stored=blob(item['preserved']);assert digest(stored)==item['preserved_sha256']
    assert (gzip.decompress(stored) if str(item['preserved']).endswith('.gz') else stored)==data
for name,expected in raw['raw_sha256'].items():assert digest(blob(name))==expected
freeze=read(M/'source_freeze.json');proof=read(M/'PROOF_BINDING.json');expected=freeze['source55']
assert len(expected)==55 and expected==proof['source55']==terminal['source55']
assert proof['passed'] is True
for base in [S,R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source']:
    assert {name:digest(blob(base/name)) for name in expected}==expected
vg=S/'impl/gwsynthesis/acg720_ano_port.vg'
assert digest(blob(vg))==digest(blob(R/'out/z_aw_fix_20261026/compact_aw_v22/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'))==EXPECTED_VG==terminal['vg_sha256']
helper=R/'firmware/B0B4/build_candidate.py'
assert digest(blob(helper))=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
assert digest(blob(V/'executed_run_physical.py'))==digest(blob(M/'run_physical.py'))==runner['runner_sha256']
assert 'helper.physical_audit(VG_SHA,expected)' in text(V/'executed_run_physical.py')
for name in ['acg720_ano_port.cst','acg720_ano_port.sdc']:
    assert blob(S/name)==blob(R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'/name)==blob(R/'firmware/B0B4/source'/name)
sdc=[x.strip() for x in text(S/'acg720_ano_port.sdc').splitlines() if x.strip() and not x.lstrip().startswith('#')]
assert sdc==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]','set_false_path -from [get_ports {radio_rx}]']
tcl=text(A/'physical.tcl');options=dict(re.findall(r'^set_option -(\w+) (.+)$',tcl,re.M))
assert options==dict(top_module='acg720_ano_port',output_base_name='acg720_ano_port',user_code='0000B0B4',place_option='3',route_option='0',timing_driven='1',replicate_resources='0',map_option='2',global_freq='50',max_fanout='200',opt_goal='area',route_maxfan='23')
assert tcl.splitlines()[0]=='open_project physical.gprj' and 'run pnr\nputs PHYSICAL_COMMAND_RETURNED_EOF' in tcl
project=ET.fromstring(blob(S/'physical.gprj'))
assert [(x.attrib['path'],x.attrib['type'],x.attrib['enable']) for x in project.findall('.//File')]==[
    ('impl/gwsynthesis/acg720_ano_port.vg','file.netlist','1'),('acg720_ano_port.cst','file.cst','1'),('acg720_ano_port.sdc','file.sdc','1')]
log=text(V/'physical.log')
assert log.rstrip().endswith('PHYSICAL_COMMAND_RETURNED_EOF') and 'Placement and routing completed' in log and 'Bitstream generation completed' in log
assert 'Skip synthesis' in log and re.findall(r'Reading netlist file: "([^"]+)"',log)==[str(vg)]
assert not re.search(r'\bERROR\b|\bunrouted\b',log,re.I)
tr=text(PNR/'acg720_ano_port.tr')
assert re.search(r'^\s*1\s+clk50\s+Base\s+20\.000\s+50\.000MHz',tr,re.M)
fmax=float(re.search(r'^\s*1\s+clk50\s+50\.000\(MHz\)\s+([\d.]+)\(MHz\)',tr,re.M)[1]);assert fmax==50.075
assert '<Numbers of Setup Violated Endpoints>:0' in tr and '<Numbers of Hold Violated Endpoints>:0' in tr
headers={'setup':('3.1.1 Setup Paths Table','3.1.2'), 'hold':('3.1.2 Hold Paths Table','3.1.3'),
         'recovery':('3.1.3 Recovery Paths Table','3.1.4'), 'removal':('3.1.4 Removal Paths Table','3.2'),
         'minimum_pulse_width':('3.2 Minimum Pulse Width Table','3.3')}
slacks={};counts={}
for kind,(start,end) in headers.items():
    part=tr.split('\n'+start,1)[1].split('\n'+end,1)[0]
    rows=re.findall(r'^\s*\d+\s+([-+]?\d+\.\d+)\s+',part,re.M)
    assert len(rows)==(10 if kind=='minimum_pulse_width' else 25)
    slacks[kind]=min(map(float,rows));counts[kind]=len(rows);assert slacks[kind]>=0
assert slacks==dict(setup=.030,hold=.200,recovery=12.073,removal=2.646,minimum_pulse_width=7.387)==raw['slacks_ns']
assert re.findall(r'^\s*(TC_\w+)\s+(Actived|Invalid)\s+(.+?)\s*$',tr,re.M)==[
    ('TC_CLOCK','Actived',sdc[0]),('TC_FALSE_PATH','Actived',sdc[1])]
rpt=text(PNR/'acg720_ano_port.rpt.txt');part=rpt.split('7. Pinout by Port Name',1)[1].split('\n8.',1)[0]
pins={}
for line in part.splitlines():
    cells=[x.strip() for x in line.split('|')]
    if len(cells)>5 and cells[4] in {'in','out'}:pins[cells[0]]=[cells[2].split('/')[0],cells[4]]
assert len(pins)==18 and pins==raw['pins']
assert {k:v[0] for k,v in pins.items()}==dict(re.findall(r'IO_LOC "([^"]+)" (\w+);',text(S/'acg720_ano_port.cst')))
fs=blob(PNR/'acg720_ano_port.fs');assert len(fs)==17456619 and digest(fs)=='199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610'
assert b'//UserCode: 0x0000b0b4' in fs[:2048] and b'//Device Version: B' in fs[:2048]
assert re.search(r'^set user_code = 0x0000B0B4$',text(PNR/'device.cfg'),re.M)
physical=read(V/'physical_audit.json');build=read(V/'build_result.json')
assert physical['passed'] is build['passed'] is True and all(x is True for x in physical['criteria'].values())
assert physical['source_sha256']==expected and physical['fmax_mhz']==fmax and physical['period_ns']==20
assert {k:v['worst_slack_ns'] for k,v in physical['checks'].items()}==slacks
assert build['netlist_sha256']==EXPECTED_VG and build['bitstream_sha256']==digest(fs)
output=D/'REVIEW.json';assert not output.exists()
review=dict(reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,findings=[],
    scope='Independent read-only raw physical evidence review of standard v22 P3/R0; no export, promotion, vendor, hardware or frozen-file mutation.',
    source55=expected,netlist_sha256=EXPECTED_VG,FS_sha256=digest(fs),FS_bytes=len(fs),vendor_actual_wait=0,runner_actual_wait=0,
    actual_receipt_types='Both actual_p_wait values are exactly int; both normal_wait_return values are exactly True.',
    period_ns=20,global_freq_mhz=50,fmax_mhz=fmax,slacks_ns=slacks,reported_path_counts=counts,violated_endpoints={'setup':0,'hold':0},pins=pins,
    timing_exceptions=sdc[1:],original_CST_SDC_byte_identical=True,original_physical_helper_unchanged=True,
    terminal_artifact_count=len(terminal['artifacts']),raw_declared_count=len(raw['raw_sha256']),evidence=seen,
    reviewer_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),qualification='Raw original 20ns/50MHz physical gates satisfied; release export/promotion not performed by this review.')
output.write_text(json.dumps(review,indent=2)+'\n',encoding='utf8')
print(json.dumps({'review':str(output),'passed':True,'sha256':digest(output.read_bytes()),'evidence_files':len(seen)}))
