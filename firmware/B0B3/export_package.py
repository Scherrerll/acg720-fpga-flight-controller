"""Create the B0B3 lightweight export once; never mutate its qualified origin."""
from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,sys

E=Path(__file__).resolve().parent
R=Path('C:/Users/ScherrerL/Desktop/apple/runtime_xy_pi_20261026')
F=R/'builds/idle_integral_p3r0'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert not(E/'export_manifest.json').exists(),'Never overwrite an existing export'
markers=[R/'delivery_manifest.json',R/'delivery_manifest.sha256',R.parent/'runtime_xy_pi_20261026_delivery.zip',R.parent/'runtime_xy_pi_20261026_delivery.zip.sha256']
origin_before={str(p):dict(sha256=sha(p),size_bytes=p.stat().st_size)for p in markers}
q=read(R/'qualification.json');sr=read(R/'verification/source_review.json');full=read(R/'delivery_manifest.json')
assert q['status']=='offline_qualified_not_installed'and q['fixture']=='builds/idle_integral_p3r0'and q['source_review_branch']=='idle_gain_integral_ce'
assert q['source_sha256']==sr['current_source_sha256']and len(q['source_sha256'])==55
assert q['bitstream_sha256']=='a5b893b25a5e510348c8a4ac75c914b8a14473bbfb054b4cc4040b86800f64dd'and q['netlist_sha256']=='4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb'
records={}
def put(rel,dest=None,compress=False):
 p=R/rel;assert p.is_file(),rel
 target=E/(dest or rel);assert target.is_relative_to(E)and not target.exists(),str(target)
 target.parent.mkdir(parents=True,exist_ok=True)
 original=dict(root_label='runtime_xy_pi_20261026',relative_path=p.relative_to(R).as_posix(),sha256=sha(p),size_bytes=p.stat().st_size)
 if rel in full['files']:assert original['sha256']==full['files'][rel]['sha256'],'Origin changed after full delivery: '+rel
 if compress:
  with p.open('rb')as source,target.open('wb')as output:
   with gzip.GzipFile(filename='',fileobj=output,mode='wb',compresslevel=9,mtime=0)as zipped:shutil.copyfileobj(source,zipped,1024*1024)
  transform=dict(name='gzip',mtime=0,embedded_filename='',compression_level=9)
 else:shutil.copyfile(p,target);transform=dict(name='byte_copy')
 records[target.relative_to(E).as_posix()]=dict(kind='copied_origin_artifact',source=original,transform=transform,sha256=sha(target),size_bytes=target.stat().st_size)
 print('COPY '+str(target.relative_to(E)),flush=True)
def generated(name):
 p=E/name;assert p.is_file();records[name]=dict(kind='generated_export_file',source=None,transform=dict(name='generated_for_new_layout',generator='export_package.py'),sha256=sha(p),size_bytes=p.stat().st_size)

for n,h in q['source_sha256'].items():assert sha(R/'source'/n)==h;put('source/'+n)
for n in ['xy_pi_cli.py','requirements.txt','PROTOCOL.md','source_changes.diff','qualification.json','environment_manifest.json']:put(n)
for src,dest in [('README.md','docs/README.runtime.original.md'),('DELIVERY_REPORT.md','docs/DELIVERY_REPORT.runtime.original.md'),('TASK_OWNER.json','provenance/TASK_OWNER.json'),('verification/source_review.json','provenance/source_review.json'),('verification/netlist_audit.json','provenance/netlist_audit.json'),('delivery_manifest.json','provenance/full_delivery/delivery_manifest.json'),('delivery_manifest.sha256','provenance/full_delivery/delivery_manifest.sha256')]:put(src,dest)
for name in ['comm_compact_promotion.json','response_compact_promotion.json','map1_default_promotion.json','idle_gain_integral_ce_promotion.json']:put('verification/'+name,'provenance/promotions/'+name)
put('builds/idle_integral_p3r0/source/impl/pnr/acg720_ano_port.fs','release/B0B3_selected_P3R0.fs')
for name in ['current_P005_I0.fs','original_V15.fs']:put('rollback/'+name,'release/'+name)
put('builds/idle_integral_p3r0/source/impl/gwsynthesis/acg720_ano_port.vg','physical/acg720_ano_port.vg.gz',True)
put('builds/idle_integral_p3r0/source/impl/pnr/acg720_ano_port.pr','physical/acg720_ano_port.pr.gz',True)
for name in ['acg720_ano_port.tr','acg720_ano_port.rpt.txt','acg720_ano_port.pin.html','acg720_ano_port.log','acg720_ano_port.timing_paths','device.cfg']:put('builds/idle_integral_p3r0/source/impl/pnr/'+name,'physical/'+name)
for name in ['build_input.json','process.json','process_exit.json','timing_review.json','gowin.log']:put('builds/idle_integral_p3r0/verification/'+name,'physical/evidence/'+name)
put('builds/idle_integral_p3r0/physical.tcl','physical/provenance/physical.tcl')
put('builds/idle_integral_p3r0/source/physical.gprj','physical/provenance/physical.gprj')
for name in ['inspect_timing.py','audit_netlist.py']:put(name,'tools/original/'+name)
for name in ['verify_protocol.py','verify_control.py','verify_link.py','verify_top_safety.py','test_host.py']:put(name,'tests/original/'+name)
verification_names=['protocol_results.json','protocol_tb.v','protocol_tb.log','protocol_tb.compile.log','uart_tb.v','uart_tb.log','uart_tb.compile.log','control_results.json','control_tb.v','control.log','control.compile.log','mtf_xyz_hold_control_p005.v','mtf_xyz_hold_control_v15.v','link_results.json','link_tb.v','link.log','link.compile.log','telemetry_before.v','top_safety_results.json','top_safety_tb.v','top_safety.log','top_safety.compile.log','host_tests.log','baseline_preservation_final.log','legacy_timing_rejection.json','check_legacy_timing_rejection.py']
for name in verification_names:put('verification/'+name,'tests/evidence/'+name)
for p in(R/'verification/timing_parser_legacy19p5').rglob('*'):
 if p.is_file()and p.suffix.lower()in{'.tr','.log','.json'}:put(p.relative_to(R).as_posix(),'tests/evidence/legacy19p5/'+p.relative_to(R/'verification/timing_parser_legacy19p5').as_posix())
for name in ['source/telemetry_tx.v','source/position/mtf_xyz_hold_control.v','baseline/mtf_xyz_hold_control.v']:put('test_baseline/'+name,'tests/references/'+name)
review_names=['REVIEW.md','bounds.json','CURRENT_REVIEW.md','CONTENTION_RESULT.md','verify_contention.py','compact_promotion_addendum.md','compact_promotion_addendum.json','RESPONSE_COMPACT_ADDENDUM.md','response_compact_review.json','IDLE_GAIN_CE_RELEASE_ADDENDUM.md','idle_gain_ce_release_review.json','IDLE_GAIN_INTEGRAL_CE_INDEPENDENT_REVIEW.md','idle_gain_integral_ce_independent_review.json','IDLE_GAIN_INTEGRAL_CE_RELEASE_ADDENDUM.md','idle_gain_integral_ce_release_review.json','actual_b7_selection_guard_validation.json','B7_P3R0_RAW_REVIEW.md','B7_P3R0_RAW_REVIEW.json','audit_b7_p3r0_raw.py']
for name in review_names:put('review/'+name,'proofs/review/'+name)
excluded_suffixes={'.vvp','.pyc','.exe','.dll','.o','.obj','.bin','.binx','.fs','.pr','.db','.p','.bak','.user','.pid'}
caches={'__pycache__','tmp','temp','.cache','cache','.pytest_cache'}
def retained(p):return p.suffix.lower()not in excluded_suffixes and not(caches&{n.casefold()for n in p.parts})and not p.name.startswith('orchestrator.')
for candidate in ['comm_compact','response_compact','idle_gain_ce','idle_gain_integral_ce']:
 base=R/'candidates'/candidate
 for p in sorted(base.rglob('*')):
  if not p.is_file()or not retained(p.relative_to(base)):continue
  rel=p.relative_to(R).as_posix();dest='proofs/'+rel
  if p.suffix.lower()=='.vg':put(rel,dest+'.gz',True)
  elif 'impl'in p.relative_to(base).parts:
   if p.suffix.lower()in{'.xml','.log','.prj','.tcl','.html'}:put(rel,dest)
  else:put(rel,dest)
for p in(R/'review/contention').rglob('*'):
 if p.is_file()and retained(p.relative_to(R/'review/contention')):put(p.relative_to(R).as_posix(),'proofs/review/contention/'+p.relative_to(R/'review/contention').as_posix())
for p in sorted((R/'analysis_flights').iterdir()):
 if p.is_file()and p.suffix.lower()in{'.py','.md','.json','.csv','.txt','.diff'}:put(p.relative_to(R).as_posix(),'analysis/'+p.name)

readme='''# B0B3：XY P/I runtime parameters — offline qualified, NOT installed

This is a lightweight export of the selected `idle_gain_integral_ce` (B7) result, not the full original delivery tree. No hardware, SRAM/Flash programming or flight verification was performed for this image. Python verifier command: `python -B verify_export.py`. It checks this export layout using only the standard library; it does not invoke the original full-delivery verifier or claim its2,347-file archive is present.

## Selected result

GW5AT-LV60PG484AC1/I0, UserCodeB0B3. Physical options are **place3 / route0 / map2 / replicate0**, exactly matching the archived physical driver/project. The unchanged source `build.tcl` defaults to place2/route0; this default is not the selected physical profile. The selected exact VG, full-route PR, raw TR/pin/report/log/process receipts and three FS files are supplied. VG/PR are deterministic gzip streams (mtime0, no embedded filename); their original sizes/hashes are recorded in export_manifest.json. Decompress only into a separate scratch copy when a tool needs the raw files.

Actual clock20.000ns, Fmax50.257MHz, zero setup/hold violated endpoints. Raw worst slacks (ns): setup+0.102, hold+0.145, recovery+11.895, removal+3.312, minimum pulse+7.387. Full route and bitstream completed with actual process exit0. The verifier independently parses all five raw summary tables and18pin assignments, checks clocks/constraints and binds source55, selected VG/PR/FS/TR to qualification and original timing receipts. This verifies supplied offline evidence, not a fresh STA run or external IO/aircraft dynamics.

## Scope and changes

Relative to the frozen P005/I0 source:45files byte-identical,9existing files changed,1new bank module. Only the XY optical-flow velocity P/I become live shared parameters; default P=.05/I=0. Public units remain deg/(cm/s) and deg/(cm/s·s), range0..1 in .0001 steps. The runtime I path preserves original error/dt/clamp/reset/retention semantics. P+I+FF uses signed36 Q16 before the existing angle clamp, fixing legal high-P overflow. A real stopped-output/pre-arm-intent gate, cancelled-idle atomic commit and coherent per-callback pair prevent arm/commit and half-pair races.

New B16 RX is115200 8N1 with synchronization, fixed framing/CRC/timeouts, GET/SET, replay/range/status checks. Existing single-UART telemetry stays intact; bank holds a response until the final byte completes. Compact response storage and state0 work/saved-I sampling change internal structure while public outputs remain cycle-equivalent; private idle snapshots can differ. B7's real450-bit comparison spans1,002,843cycles, including2nonzero partial-I rollbacks. Focused numerical, protocol121/extended126, safety13, complete692-byte wire and four-client contention evidence are included. Shared math adds latency: measured contention XY maximum355.84us at50MHz, with accelerated arrivals and original dt; this is not flight dynamics evidence.

Parameters are **volatile for this power cycle only**. One request in flight; extra requests while held are ignored, and SET is not automatically retried. Valid CH5-high pre-arm intent rejects writes; successful SET ACK is followed by independent GET. See PROTOCOL.md. CLI requires pyserial and a separately authorized stopped maintenance window with one serial owner; COM numbers and physical wiring must be rechecked. No interface use is authorized by this export itself.

`release/B0B3_selected_P3R0.fs` is the qualified new image; `current_P005_I0.fs` and `original_V15.fs` are the preserved fallbacks. No automatic installer/programmer is supplied. Keep the selected image uninstalled until the user's specific hardware action is authorized. No new flight acceptance is implied: height-loss first cause and rotation/surface/loop dynamics remain open, as explained in analysis/FINDINGS.md.

## Evidence and omission boundaries

Every copied byte has an original runtime-relative path, SHA256 and size in export_manifest.json; gzip records additionally bind decompressed identity. Generated export files are separately labelled. `provenance/full_delivery/` contains only the original full manifest and sidecar for provenance, not all its files. Its historical scripts/manifests retain original paths, statuses and omitted VVP references; they are evidence, not a promise that the original full finalizer can run here. The final selected source/qualification/promotion/B7 raw review take precedence over earlier unselected/checkpoint wording. Original focused drivers/TBs/references are preserved without edits; rerunning them requires path/tool adaptation in a fresh scratch tree (Icarus/Gowin libraries are external dependencies), not writes into this frozen export.

Unselected reset, map1, serial-CRC, body-only and bounded-counter experiments and huge failed implementation copies are omitted; the small map1 promotion receipt is retained only as B7's working-restoration history. No .db/.p, vendor manuals/reference libraries, third-party P2 reference code, raw flight JSONL/video or full delivery ZIP is redistributed. Derived flight CSV/JSON and reports are included. Analysis scripts still require the original external handoff/H/P2/raw-log inputs listed in analysis/DEPENDENCIES.md; they are not standalone data collectors or reproducible without those separately held inputs.

The original runtime delivery manifest and ZIP remain untouched. Git staging/commit/publication, repository-wide progress documentation and hardware operations are outside this exporter.
'''
(E/'README.md').write_text(readme,encoding='utf8')
(E/'analysis/DEPENDENCIES.md').write_text('''# External analysis inputs (not redistributed)\n\nThe copied analysis scripts are original evidence readers. read_numbered.py resolves the original handoff workspace/H snapshot, its P2/ANO reference tree and frozen RTL/baseline; analyze_evidence.py additionally reads the original hardware/recent_telemetry.jsonl/samples.jsonl/telemetry_clip.jsonl files listed in its DATA dictionary. audit_sources.py needs the original source index/reference files. None of that third-party code, source package, raw JSONL or video is included here. Derived CSV/JSON/report outputs are preserved as generated evidence, with original hashes/path references, not claimed independently regenerable from this lightweight export. See FINDINGS.md for scope, epochs/sequences and unresolved causes.\n''',encoding='utf8')
for name in ['README.md','analysis/DEPENDENCIES.md','export_package.py','verify_export.py']:generated(name)
assert all(sha(p)==v['sha256']and p.stat().st_size==v['size_bytes']for p,v in((Path(p),v)for p,v in origin_before.items())),'Original delivery marker changed'
manifest=dict(format_version=1,scope='Lightweight selected offline-qualified B7 export; NOT installed; independent export verifier only',selected_original_fixture=q['fixture'],source_origin_root_label=R.name,original_full_delivery_markers=origin_before,selected_source_sha256=q['source_sha256'],qualification_sha256=sha(R/'qualification.json'),physical=dict(place=3,route=0,map_option=2,replicate_resources=0,period_ns=20.0,fmax_mhz=50.257,slacks_ns=dict(setup=.102,hold=.145,recovery=11.895,removal=3.312,minimum_pulse_width=7.387)),omissions=['full2347-file delivery and its ZIP','all failed/unselected physical projects and nonselected experimental branches','compiled simulation/cache objects','vendor manuals/libraries and third-party P2/ANO reference code','raw flight JSONL/videos and external handoff/H inputs','.db/.p and alternate raw implementation binaries'],manifest_self_exclusions=['export_manifest.json','export_manifest.sha256','EXPORT_CHECK.json'],files=records)
(E/'export_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8');(E/'export_manifest.sha256').write_text(sha(E/'export_manifest.json')+'  export_manifest.json\n',encoding='ascii')
print(json.dumps(dict(export_files=len(records),export_bytes=sum(v['size_bytes']for v in records.values()),manifest_sha256=sha(E/'export_manifest.json'),origin_markers_unchanged=True),indent=2),flush=True)
