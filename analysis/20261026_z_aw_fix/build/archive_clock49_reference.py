"""Archive exact manufacturer-generated reference IP and a read-only timebase inventory."""
from pathlib import Path
import datetime,hashlib,json,re,shutil
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_generate';A=R/'out/z_aw_fix_20261026/clock49_generate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
ex=read(M/'exit.json');assert ex['normal_wait_return'] and ex['actual_p_wait']==0
D=M/'vendor_generated_reference';assert not D.exists();D.mkdir()
paths={'clock49.v':A/'ip/clock49/clock49.v','clock49_mod.v':A/'ip/clock49/clock49_mod.v',
       'clock49.ipc':A/'ip/clock49/clock49.ipc','pll_init.v':A/'project/clock49_generate/src/pll_init.v'}
items={}
for name,path in paths.items():
    data=path.read_bytes();assert b'pragma protect' not in data[:512]
    dest=D/name;dest.write_bytes(data);assert sha(dest)==sha(path)
    items[name]={'sha256':sha(dest),'bytes':len(data),'actual_generated_path':str(path)}
module=(D/'clock49_mod.v').read_text(encoding='utf8');wrapper=(D/'clock49.v').read_text(encoding='utf8')
params=dict(re.findall(r'defparam PLLA_inst\.(\w+)\s*=\s*([^;]+);',module))
assert params['FCLKIN']=='"50"' and params['IDIV_SEL']=='2' and params['MDIV_SEL']=='49' and params['ODIV0_SEL']=='25'
assert params['MDIV_FRAC_SEL']==params['ODIV0_FRAC_SEL']=='0'
assert params['CLKOUT0_PE_COARSE']==params['CLKOUT0_PE_FINE']=='0' and params['SSC_EN']=='"FALSE"'
assert 'defparam u_pll_init.CLK_PERIOD = 20;' in wrapper and 'defparam u_pll_init.MULTI_FAC = 49;' in wrapper
(M/'REFERENCE_IP_MANIFEST.json').write_text(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Exact manufacturer-generated reference only. Not integrated, synthesized, physically implemented or programmed into the aircraft.',
    'actual_generator_exit_sha256':sha(M/'exit.json'),'actual_generator_wait':0,'input_MHz':50,'requested_output_MHz':49,
    'generated_integer_ratio':{'input':50,'MDIV':49,'IDIV':2,'ODIV0':25,'ratio_output_MHz':49},
    'phase_coarse_and_fine':0,'spread_spectrum':False,'manufacturer_init_clock_MHz':50,'files':items},indent=2)+'\n',encoding='utf8')
source=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source';expected=read(O/'v4_release_proofs/RESULT.json')['source55']
assert {n:sha(source/n) for n in expected}==expected
pattern=re.compile(r'(?<![A-Za-z0-9_])(?:50000000|25000000|10000000|5000000|2500000|1000000|500000|50000|25000|434)(?![0-9])')
hits=[]
for name in expected:
    if Path(name).suffix not in ['.v','.vh']:continue
    for line,text in enumerate((source/name).read_text(encoding='utf8').splitlines(),1):
        if pattern.search(text):hits.append({'file':name,'line':line,'text':text.strip()})
(M/'TIMEBASE_INVENTORY_PENDING.json').write_text(json.dumps({'scope':'First-pass source-literal inventory only, not a complete dimensional audit or an approved replacement list. 50000 may mean a clock count or50000us; microsecond/domain constants must never be blindly scaled. No source changed.',
    'source55':expected,'candidate_clock_Hz':49000000,'basis_clock_Hz':50000000,'hits':hits,
    'required_review':['All functional logic in one actual49MHz data clock domain; manufacturer PLL initializer remains50MHz as generated.',
      'Actual UART bit timing, SPI/IMU periods, RC/PWM units and pulse stop checks.',
      'Tick-to-microsecond carry conversion, estimator/rate-control dt denominators, ms ages and watchdogs.',
      'Control wall-time periods, numerical precision, original protection and stop/landing behavior.',
      'Explicit49MHz-specific clock/source/STA/CDC gates and new full behavioral/physical validation; existing50MHz gates are not silently relaxed.']},indent=2)+'\n',encoding='utf8')
print(json.dumps({'exact_generated_reference_files_preserved':len(items),'timebase_literal_hits_for_review':len(hits),'clock_or_source_changed':False,'hardware_operation':False}))
