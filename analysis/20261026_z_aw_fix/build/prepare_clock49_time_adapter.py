"""Start an explicitly incomplete isolated fallback workspace, changing one timebase unit only."""
from pathlib import Path
import datetime,hashlib,json,shutil
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_time_adapter';W=R/'out/z_aw_fix_20261026/clock49_working';OLD=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not M.exists() and not W.exists()
expected=read(O/'v4_release_proofs/RESULT.json')['source55'];assert len(expected)==55 and {n:sha(OLD/n) for n in expected}==expected
assert (R/'analysis/20261026_z_aw_fix/USER_STEERING_20261027_49MHZ_FALLBACK.json').is_file()
M.mkdir();W.mkdir(parents=True);shutil.copytree(OLD,W/'source')
reference=O/'clock49_generate/vendor_generated_reference';refmanifest=read(O/'clock49_generate/REFERENCE_IP_MANIFEST.json')
for name in ['clock49.v','clock49_mod.v','pll_init.v']:
    assert sha(reference/name)==refmanifest['files'][name]['sha256']
    dest=W/'source/clock'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(reference/name,dest)
name='position/pose_time_adapter.v';path=W/'source'/name;raw=(OLD/name).read_bytes();text=raw.decode('utf8');nl='\r\n' if '\r\n' in text else '\n'
before='module pose_time_adapter(';after='module pose_time_adapter #(parameter integer CLOCK_HZ=50000000)('
assert text.count(before)==1;text=text.replace(before,after)
comment='// Convert ticks/50, carrying sub-microsecond ticks through valid tuples.'
assert text.count(comment)==1;text=text.replace(comment,'// Convert whole-MHz clock ticks to us, carrying sub-us ticks through valid tuples.')
assert text.count("7'd50")==4;text=text.replace("7'd50",'US_TICKS')
insert=" localparam [6:0] US_TICKS=CLOCK_HZ/1000000;"+nl+" initial if(CLOCK_HZ%1000000!=0 || CLOCK_HZ<1000000 || CLOCK_HZ>64000000)"+nl+"  $error(\"pose_time_adapter requires an integer1..64MHz clock\");"+nl
marker=' reg [31:0] dividend=0,quotient=0;';assert text.count(marker)==1;text=text.replace(marker,insert+marker)
path.write_bytes(text.encode())
restored=text.replace(after,before).replace('// Convert whole-MHz clock ticks to us, carrying sub-us ticks through valid tuples.',comment).replace(insert,'').replace('US_TICKS',"7'd50")
assert restored.encode()==raw
freeze={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Incomplete isolated49MHz fallback working source. Only tick-to-us unit parameterized so far; top remains50MHz and generated clock is NOT integrated. No FPGA build or hardware acceptance.',
    'working_source':str(W/'source'),'original_v4_source55':expected,'changed_unit':name,'original_unit_sha256':sha(OLD/name),'new_unit_sha256':sha(path),
    'exact_default50_source_reversion_sha256':hashlib.sha256(restored.encode()).hexdigest(),'default50_reversion_byte_exact':True,
    'generated_clock_reference_copied_not_instantiated':True,'working_source_file_count':58,'source55_or_58_qualification':False,
    'pending':'Clock wiring/reset, all other timebases/ground units, complete source freeze and new behavior/STA gates remain before any full fallback build.'}
(M/'SOURCE_BINDING.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
(W/'WORKING_NOT_FOR_BUILD.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
print(json.dumps({'isolated_working_source_created':True,'default50_reversion_byte_exact':True,'only_timebase_unit_changed':name,'clock49_not_instantiated':True,'vendor_or_hardware_started':False}))
