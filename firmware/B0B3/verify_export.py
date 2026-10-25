"""Verify only this lightweight B0B3 layout; never programs or uses origin paths."""
from pathlib import Path
import gzip,hashlib,json,math,re,sys

E=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def parse_timing(text):
 def section(start,end):
  match=re.search(r'^'+re.escape(start)+r'\s*$(.*?)^'+re.escape(end),text,re.S|re.M);assert match,('Missing timing table',start);return match[1]
 checks={}
 for name,start,end in [('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table'),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table'),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table')]:
  rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',section(start,end),re.M)
  assert rows,name;values=[float(row[1])for row in rows];assert all(math.isfinite(v)and v>=0 for v in values),(name,'Timing violation')
  checks[name]=dict(worst_slack_ns=min(values),reported_paths=len(rows))
 rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+?)\s+(clk50)\s+(\S+)\s*$',section('3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type'),re.M)
 assert rows;values=[float(row[1])for row in rows];assert all(math.isfinite(v)and v>=0 for v in values)
 checks['minimum_pulse_width']=dict(worst_slack_ns=min(values),reported_paths=len(rows))
 clock=re.search(r'^\s+1\s+clk50\s+Base\s+(\d+\.\d+)\s+',text,re.M);fmax=re.search(r'^\s+1\s+clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',text,re.M)
 assert clock and fmax and float(clock[1])==20 and math.isfinite(float(fmax[2]))and float(fmax[2])>=50,'Actual20ns clock/Fmax required'
 assert int(re.search(r'<Numbers of Setup Violated Endpoints>:(\d+)',text)[1])==int(re.search(r'<Numbers of Hold Violated Endpoints>:(\d+)',text)[1])==0
 return checks,float(fmax[2])
def main():
 manifest=E/'export_manifest.json';M=read(manifest);sidecar=(E/'export_manifest.sha256').read_text().strip().split();assert sidecar==[sha(manifest),'export_manifest.json']
 assert M['format_version']==1 and M['selected_original_fixture']=='builds/idle_integral_p3r0'
 records=M['files'];excluded=set(M['manifest_self_exclusions']);assert excluded=={'export_manifest.json','export_manifest.sha256','EXPORT_CHECK.json'}
 actual={p.relative_to(E).as_posix()for p in E.rglob('*')if p.is_file()};assert actual-excluded==set(records),'Missing or unmanifested export files'
 decompressed={};origin_index={};gzip_files=0
 for name,record in records.items():
  p=(E/name).resolve();assert p.is_relative_to(E)and p.is_file()and p.stat().st_size==record['size_bytes']and sha(p)==record['sha256'],(name,'Export byte/hash mismatch')
  if record['kind']=='generated_export_file':assert record['source']is None;continue
  assert record['kind']=='copied_origin_artifact';source=record['source'];assert source['root_label']=='runtime_xy_pi_20261026'and not Path(source['relative_path']).is_absolute()and '..'not in Path(source['relative_path']).parts
  transform=record['transform']['name']
  if transform=='byte_copy':assert record['sha256']==source['sha256']and record['size_bytes']==source['size_bytes']
  elif transform=='gzip':
   gzip_files+=1
   with p.open('rb')as f:header=f.read(10)
   assert header[:3]==b'\x1f\x8b\x08'and int.from_bytes(header[4:8],'little')==0 and header[3]&8==0,'Nondeterministic gzip header'
   assert record['transform']==dict(name='gzip',mtime=0,embedded_filename='',compression_level=9)
   h=hashlib.sha256();size=0
   with gzip.open(p,'rb')as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
   assert h.hexdigest()==source['sha256']and size==source['size_bytes'],(name,'Decompressed origin mismatch')
   decompressed[name]=dict(sha256=h.hexdigest(),size_bytes=size)
  else:raise AssertionError(('Unknown transform',transform))
  origin_index[source['relative_path']]=record
 q=read(E/'qualification.json');sr=read(E/'provenance/source_review.json');promotion=read(E/'provenance/promotions/idle_gain_integral_ce_promotion.json');timing=read(E/'physical/evidence/timing_review.json');frozen=read(E/'physical/evidence/build_input.json')
 assert q['status']=='offline_qualified_not_installed'and q['software_complete']is True and q['routing_timing_complete']is True and q['hardware_runtime_verified']is False and q['flash_written']is False and q['flight_dynamic_accepted']is False
 source=q['source_sha256'];assert source==M['selected_source_sha256']==sr['current_source_sha256']==promotion['to_source_sha256']and len(source)==55
 assert {p.relative_to(E/'source').as_posix()for p in(E/'source').rglob('*')if p.is_file()}==set(source)
 assert all(sha(E/'source'/n)==h for n,h in source.items())
 assert source['position/mtf_xyz_hold_control.v']=='b7eef6d33789523cd1e8ff81b05e75db91ab3c67bf76e03483dec356055fa1a6'and source['xy_pi_parameters.v']=='c3ab65d07c7b664268192a5b0de3acfb510efdac504a7a82cfdfa89e83d1b187'
 assert sr['unchanged_source_files']==45 and len(sr['changed_files'])==9 and sr['added_files']==['xy_pi_parameters.v']and sr['baseline_preserved']is True
 assert q['fixture']==promotion['selected_fixture']==M['selected_original_fixture']and q['physical_options']==dict(place=3,route=0,replicate_resources=0,map_option=2)and q['source_map_option']==2
 assert q['source_review_branch']=='idle_gain_integral_ce'and q['actual_period_ns']==20 and q['unrouted_nets']==0
 fs=E/'release/B0B3_selected_P3R0.fs';assert sha(fs)==q['bitstream_sha256']==promotion['bitstream_sha256']=='a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd'
 for name in ['current_P005_I0.fs','original_V15.fs']:assert sha(E/'release'/name)==sr['rollback_sha256'][name]
 assert len(list((E/'release').glob('*.fs')))==3
 with fs.open()as f:head=''.join(next(f,'')for _ in range(16))
 assert re.search(r'UserCode:\s*0x0000b0b3\b',head,re.I)
 assert decompressed['physical/acg720_ano_port.vg.gz']['sha256']==q['netlist_sha256']==frozen['donor_netlist_sha256']==promotion['netlist_sha256']=='4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb'
 assert decompressed['physical/acg720_ano_port.pr.gz']['sha256']==q['physical_design_sha256']
 evidence={'acg720_ano_port.tr':sha(E/'physical/acg720_ano_port.tr'),'acg720_ano_port.pr':decompressed['physical/acg720_ano_port.pr.gz']['sha256'],'acg720_ano_port.fs':sha(fs),'acg720_ano_port.sdc':sha(E/'source/acg720_ano_port.sdc'),'acg720_ano_port.vg':decompressed['physical/acg720_ano_port.vg.gz']['sha256']}
 assert timing['evidence_sha256']==evidence and timing['parser_sha256']==sha(E/'tools/original/inspect_timing.py')and sha(E/'physical/evidence/timing_review.json')==promotion['timing_review_sha256']
 text=(E/'physical/acg720_ano_port.tr').read_text(errors='replace');checks,fmax=parse_timing(text)
 assert set(checks)=={'setup','hold','recovery','removal','minimum_pulse_width'}and fmax==q['fmax_mhz']==M['physical']['fmax_mhz']==50.257
 for name,row in checks.items():assert row['worst_slack_ns']==timing['checks'][name]['worst_slack_ns']==q['timing_checks'][name]['worst_slack_ns']==M['physical']['slacks_ns'][name]and row['reported_paths']==timing['checks'][name]['reported_paths']
 assert timing['period_ns']==20 and timing['timing_passed']is True and timing['setup_violated_endpoints']==timing['hold_violated_endpoints']==0
 assert read(E/'physical/evidence/process_exit.json')['exit_code']==0
 log=(E/'physical/evidence/gowin.log').read_text(errors='replace');rpt=(E/'physical/acg720_ano_port.rpt.txt').read_text(errors='replace')
 assert 'Placement and routing completed'in log and 'Bitstream generation completed'in log and not re.search(r'\bERROR\s*\(',log)
 assert not any(int(n)>0 for n in re.findall(r'total\s+(\d+)\s+unrouted nets',log+rpt,re.I))
 cst=(E/'source/acg720_ano_port.cst').read_text();pins=dict(re.findall(r'IO_LOC\s+"([^"]+)"\s+(\w+)\s*;',cst))
 actual_pins={m[1]:(m[2],m[3])for m in re.finditer(r'^\s*(\w+)\s*\|[^|]*\|\s*(\w+)/\d+\s*\|\s*Y\s*\|\s*(in|out)\s*\|',rpt,re.M)}
 assert len(pins)==len(actual_pins)==18 and{n:p[0]for n,p in actual_pins.items()}==pins and actual_pins['radio_rx']==('B16','in')and actual_pins['radio_tx']==('B15','out')
 with gzip.open(E/'physical/acg720_ano_port.vg.gz','rt',errors='replace')as f:net=f.read()
 top=re.search(r'^module\s+acg720_ano_port\s*\(.*?^endmodule',net,re.M|re.S)[0];ports={n:direction for direction,n in re.findall(r'^(input|output|inout)\s+(?:wire\s+)?(\S+)\s*;',top,re.M)}
 assert len(ports)==18 and all(ports[n]==('input'if direction=='in'else'output')for n,(_,direction)in actual_pins.items())
 sdc=(E/'source/acg720_ano_port.sdc').read_text();assert re.findall(r'^create_clock.*$',sdc,re.M)==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]']and re.findall(r'^set_false_path.*$',sdc,re.M)==['set_false_path -from [get_ports {radio_rx}]']
 assert 'CLOCK_LOC "observer_reset" BUFG = CE|SR|LOGIC;'in cst and 'LOCAL_CLOCK'not in cst
 physical_tcl=(E/'physical/provenance/physical.tcl').read_text();assert sha(E/'physical/provenance/physical.gprj')==frozen['physical_project_sha256']
 for option,value in [('place_option',3),('route_option',0),('map_option',2),('replicate_resources',0)]:assert re.search(r'^set_option -'+option+r'\s+'+str(value)+r'\s*$',physical_tcl,re.M)
 assert 'set user_code = 0x0000B0B3'in(E/'physical/device.cfg').read_text()
 assert read(E/'provenance/netlist_audit.json')['netlist_sha256']==q['netlist_sha256']
 tests=E/'tests/evidence';assert read(tests/'protocol_results.json')['passed']is True and read(tests/'protocol_results.json')['register_cases']==121 and read(tests/'top_safety_results.json')['cases']==13 and read(tests/'link_results.json')['baseline_telemetry_bytes_equal']==644 and 'OK'in(tests/'host_tests.log').read_text()
 B=E/'proofs/candidates/idle_gain_integral_ce';pair=read(B/'verification/cycle_pair/results.json');reg=read(B/'verification/regressions/results.json')
 assert pair['passed']is True and pair['public_output_bits']==450 and 'total_cycles=1002843'in pair['checks'][-1]and 'nonzero_partial_I_rollbacks=2'in pair['checks'][-1]and reg['passed']is True and reg['candidate_source_sha256']==source and reg['top_safety_cases']==13
 for name in ['comm_compact','response_compact']:
  result=read(E/'proofs/candidates'/name/'verification/contract_results.json');assert result['passed']is True and result['canonical_wire_bytes_identical']==692 and result['last_byte_ack_count']==2
 assert read(E/'proofs/candidates/response_compact/verification/pair_results.json')['total_checked_responses']==126
 # Bounded in-memory negative: old19.5ns cannot pass despite a higher Fmax.
 changed=re.sub(r'(1\s+clk50\s+Base\s+)20\.000',r'\g<1>19.500',text,count=1)
 try:parse_timing(changed)
 except AssertionError:old_period_rejected=True
 else:raise AssertionError('19.5ns diagnostic was accepted')
 full=read(E/'provenance/full_delivery/delivery_manifest.json');assert(E/'provenance/full_delivery/delivery_manifest.sha256').read_text().split()[0]==sha(E/'provenance/full_delivery/delivery_manifest.json')
 bound_to_full=0
 for original,record in origin_index.items():
  if original in full['files']:assert full['files'][original]['sha256']==record['source']['sha256'];bound_to_full+=1
 out=dict(passed=True,scope='This lightweight export only; offline artifact/identity/raw-table verification; no original full2347-file verification, fresh synthesis/STA, programming or flight claim',manifest_sha256=sha(manifest),files_verified=len(records),bytes_verified=sum(row['size_bytes']for row in records.values()),copied_sources_bound_to_full_delivery_manifest=bound_to_full,deterministic_gzip_files_verified=gzip_files,selected_source_files=55,release_bitstreams=3,selected_physical_options=q['physical_options'],raw_timing_tables=checks,actual_fmax_mhz=fmax,actual_pin_rows=18,old19p5_rejected=old_period_rejected,installed=False,flash_written=False)
 if '--write-receipt'in sys.argv:(E/'EXPORT_CHECK.json').write_text(json.dumps(out,indent=2),encoding='utf8')
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
