"""Independent raw artifact review. Reads no inspect_timing JSON or parser code."""
from pathlib import Path
from decimal import Decimal
import datetime,hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];F=R/'builds/idle_integral_p3r0';S=F/'source';P=S/'impl/pnr';O=R/'review'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
paths={'TR':P/'acg720_ano_port.tr','RPT':P/'acg720_ano_port.rpt.txt','FS':P/'acg720_ano_port.fs','PR':P/'acg720_ano_port.pr','VG':S/'impl/gwsynthesis/acg720_ano_port.vg','SDC':S/'acg720_ano_port.sdc','CST':S/'acg720_ano_port.cst','TCL':F/'physical.tcl','project':S/'physical.gprj','log':F/'verification/gowin.log','input':F/'verification/build_input.json','process':F/'verification/process.json','exit':F/'verification/process_exit.json','donor_TCL':R/'candidates/idle_gain_integral_ce/synth_only.tcl','donor_input':R/'candidates/idle_gain_integral_ce/verification/synthesis_input.json'}
before={k:sha(v)for k,v in paths.items()};tr=paths['TR'].read_text();rpt=paths['RPT'].read_text();log=paths['log'].read_text();sdc=paths['SDC'].read_text();cst=paths['CST'].read_text();tcl=paths['TCL'].read_text();core=tr[tr.index('Note:Core Timing Report'):]
num=lambda x:Decimal(x)
def section(a,b):
 start=next(i for i,l in enumerate(core.splitlines())if l.strip()==a);lines=core.splitlines();end=next(i for i in range(start+1,len(lines))if lines[i].strip()==b);return lines[start+1:end]
table_specs=[('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table',25),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table',25),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table',25),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table',25),('min_pulse','3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type',10)]
tables={}
for label,a,b,count in table_specs:
 rows=[]
 for line in section(a,b):
  words=line.split()
  if words and words[0].isdigit():
   slack=num(words[1]);assert slack.is_finite()and slack>=0,(label,line);rows.append({'number':int(words[0]),'slack_ns':str(slack),'raw':line.strip()})
 assert [x['number']for x in rows]==list(range(1,count+1)),(label,len(rows))
 tables[label]={'reported_rows':len(rows),'minimum_slack_ns':str(min(num(x['slack_ns'])for x in rows)),'rows':rows}
clockrows=[l.split()for l in section('2.2 Clock Summary','2.3 Max Frequency Summary')if l.split()and l.split()[0].isdigit()]
assert len(clockrows)==1 and clockrows[0][1:3]==['clk50','Base']and num(clockrows[0][3])==20 and clockrows[0][4]=='50.000MHz'
frows=[l.split()for l in section('2.3 Max Frequency Summary','2.4 Total Negative Slack Summary')if l.split()and l.split()[0].isdigit()]
assert len(frows)==1 and frows[0][1]=='clk50';fmax=num(frows[0][3].removesuffix('(MHz)'));assert fmax.is_finite()and fmax>=50
violations={}
for label in ['Setup','Hold']:
 m=re.search(r'^<Numbers of '+label+r' Violated Endpoints>:(\d+)\s*$',core,re.M);assert m;violations[label.lower()]=int(m[1]);assert int(m[1])==0
commands=[l.strip()for l in sdc.splitlines()if l.strip()and not l.lstrip().startswith('#')]
assert commands==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]','set_false_path -from [get_ports {radio_rx}]']
def normalized(p):return str(p).replace('\\','/').lower()
def field(text,key):
 m=re.search(r'<'+re.escape(key)+r'>:\s*([^\r\n]+)',text);assert m,key;return m[1].strip()
for text in [core,rpt]:
 assert normalized(field(text,'Design File'))==normalized(paths['VG'])
 assert normalized(field(text,'Physical Constraints File'))==normalized(paths['CST'])
 assert normalized(field(text,'Timing Constraints File'))==normalized(paths['SDC'])
 assert field(text,'Part Number')=='GW5AT-LV60PG484AC1/I0'and field(text,'Device Version')=='B'
inputs=json.loads(paths['input'].read_text());proc=json.loads(paths['process'].read_text());ex=json.loads(paths['exit'].read_text())
assert ex['exit_code']==0 and normalized(proc['source_directory'])==normalized(S)
assert before['VG']=='4497e28d79a30da7487a40449d0f0ed19735d1859d2601f0d972f51344b9d9eb'==inputs['donor_netlist_sha256']
donor_inputs=json.loads(paths['donor_input'].read_text())
assert before['donor_TCL']==inputs['tcl_sha256']==donor_inputs['tcl_sha256']
assert before['project']==inputs['physical_project_sha256']
assert before['TCL']=='8cb88e3b7042d5cd6862197e382847727e586a31dbea492ba5da7ecd7a186f41'
assert before['SDC']==inputs['source_sha256']['acg720_ano_port.sdc']and before['CST']==inputs['source_sha256']['acg720_ano_port.cst']
assert inputs['mode']=='physical-only exact-netlist PNR; no synthesis rerun'
assert inputs['physical_options']=={'place':3,'route':0,'map_option':2,'replicate_resources':0}
assert re.findall(r'^set_option -place_option (\d+)$',tcl,re.M)==['3']and re.findall(r'^set_option -route_option (\d+)$',tcl,re.M)==['0']
assert re.findall(r'^run (\S+)$',tcl,re.M)==['pnr']and not re.search(r'^exit\s*$',tcl,re.M)
for token in ['Skip synthesis, because there is only one netlist file in this project','Placement and routing completed','Bitstream generation completed','Generate file "'+str(paths['TR'])+'" completed','PHYSICAL_COMMAND_RETURNED_EOF']:assert token in log,token
assert not re.search(r'^\s*ERROR\s*\(',log,re.M)and not re.search(r'\bunrouted\b',log,re.I)
filelist=ET.parse(paths['project']).getroot().find('FileList');assert len(filelist)==3
assert {(n.attrib['path'],n.attrib['type'])for n in filelist}=={('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')}
with paths['FS'].open()as f:header=''.join(next(f)for _ in range(24))
assert '//File Title: Bitstream file'in header and '//Part Number: GW5AT-LV60PG484AC1/I0'in header and '//Device Version: B'in header and '//UserCode: 0x0000b0b3'in header and '//CRCCheck: ON'in header
start=datetime.datetime.fromisoformat(proc['started_utc']);end=datetime.datetime.fromisoformat(ex['ended_utc']);fresh={}
for label in ['FS','TR','RPT','PR']:
 p=paths[label];st=p.stat();birth=getattr(st,'st_birthtime',st.st_ctime);assert st.st_size>0 and start.timestamp()<=birth<=end.timestamp()+1 and start.timestamp()<=st.st_mtime<=end.timestamp()+1
 fresh[label]={'bytes':st.st_size,'creation_utc':datetime.datetime.fromtimestamp(birth,datetime.timezone.utc).isoformat(),'mtime_utc':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat()}
localzone=datetime.timezone(datetime.timedelta(hours=8))
created={}
for name,text in [('TR',core),('RPT',rpt),('FS',header)]:
 m=re.search(r'(?:<Created Time>:|//Created Time:)\s*([^\r\n]+)',text);assert m
 stamp=datetime.datetime.strptime(m[1].strip(),'%a %b %d %H:%M:%S %Y').replace(tzinfo=localzone);assert start<=stamp<=end
 created[name]=stamp.isoformat()
locations=dict(re.findall(r'^IO_LOC\s+"([^"]+)"\s+(\w+);',cst,re.M));assert len(locations)==18
io_options={name:dict(re.findall(r'(\w+)=([\w.]+)',spec))for name,spec in re.findall(r'^IO_PORT\s+"([^"]+)"\s+([^;]+);',cst,re.M)}
pins={}
for line in rpt.splitlines():
 cols=[x.strip()for x in line.split('|')]
 if len(cols)>7 and cols[2]in ['in','out','inout']and cols[1]not in ['','-']:
  name=cols[1];assert name not in pins;assert locations[name]==cols[0].split('/')[0]
  options=io_options[name];assert options['IO_TYPE']==cols[5]and options['PULL_MODE']==cols[7]
  if 'DRIVE'in options:assert options['DRIVE']==cols[6]
  pins[name]={'location':cols[0],'direction':cols[2],'IO_TYPE':cols[5],'drive':cols[6],'pull':cols[7]}
assert set(pins)==set(locations)and len(pins)==18 and sum(p['direction']=='out'for p in pins.values())==13
assert pins['radio_rx']['location'].split('/')[0]=='B16'and pins['radio_rx']['direction']=='in'and pins['radio_rx']['pull']=='UP'
assert pins['radio_tx']['location'].split('/')[0]=='B15'and pins['radio_tx']['direction']=='out'
vgtext=paths['VG'].read_text();top=re.search(r'^module acg720_ano_port\s*\(.*?^endmodule',vgtext,re.M|re.S)[0]
ports={name:direction for direction,name in re.findall(r'^(input|output|inout)\s+(\w+)\s*;',top,re.M)}
assert len(ports)==18 and set(ports)==set(pins)and all(pins[k]['direction']=={'input':'in','output':'out','inout':'inout'}[v]for k,v in ports.items())
after={k:sha(v)for k,v in paths.items()};assert before==after,'fixture evidence changed during review'
out={'passed':True,'scope':'Independent raw TR/RPT/log/SDC/CST/VG/FS/PR and process/project identity review; no inspect_timing code or JSON consumed; no source/build/hardware changes','fixture':str(F),'actual_process_start_utc':start.isoformat(),'actual_exit_utc':end.isoformat(),'actual_exit_code':0,'physical_options':inputs['physical_options'],'Tcl_identity_separation':{'inherited_build_input_tcl_sha256':inputs['tcl_sha256'],'inherited_field_is_exact_donor_synthesis_Tcl':True,'actual_physical_Tcl_sha256':before['TCL'],'actual_physical_project_sha256':before['project'],'note':'No claim that inherited tcl_sha256 binds physical.tcl. Actual physical Tcl reviewed and hashed separately here; old receipts are not modified.'},'clock_period_ns':'20.000','Fmax_MHz':str(fmax),'violated_endpoints':violations,'tables':tables,'fresh_outputs':fresh,'embedded_created_local':created,'FS_header':header,'pins18':pins,'all_pin_sources_agree':'CST locations + raw RPT active rows + raw VG top directions','stable_before_after_hashes':True,'evidence_sha256':{str(paths[k].relative_to(R)):v for k,v in before.items()},'reviewer_script_sha256':sha(Path(__file__)),'limitation':'Reported five worst-path tables and explicit setup/hold zero-violation summary verified; not a new STA run, complete functional equivalence proof, hardware download, wiring check, flight or closed-loop acceptance.'}
(O/'B7_P3R0_RAW_REVIEW.json').write_text(json.dumps(out,indent=2))
rows='\n'.join(f'| {k} | {v["reported_rows"]} | +{v["minimum_slack_ns"]} |'for k,v in tables.items())
report=f'''# Independent raw B7 P3R0 artifact review

PASS for the existing exact physical fixture `builds/idle_integral_p3r0`. This review did not read `inspect_timing` code or its JSON. It directly checked the final raw TR/RPT/log/SDC/CST/VG/FS/PR, actual process receipts and netlist-only physical project. No synthesis, PNR, source/constraint/build-output change, process operation or hardware access was performed.

The actual process started {start.isoformat()} and returned0 at {end.isoformat()}. The log independently records skipped synthesis, placement/routing completion, bitstream completion and the EOF completion sentinel, without ERROR or an unrouted-net report. The physical project contains exactly one netlist plus CST/SDC, and the actual Tcl/options are place3/route0/map2/replicate0. Generic build-input started_utc is donor-inherited; output freshness was checked against the actual process start instead.

The build-input `tcl_sha256` is also donor-inherited: `{inputs['tcl_sha256']}` exactly matches the donor's `synth_only.tcl` and its original synthesis receipt. It is not a physical Tcl binding. The actual separate `physical.tcl` has SHA256 `{before['TCL']}` and is independently read/hashed here; its generated project SHA256 `{before['project']}` exactly matches `physical_project_sha256`. No old receipt was rewritten. This explicit separation must be retained in execution/release provenance.

The raw TR and RPT name this fixture's exact VG/CST/SDC and GW5AT-LV60PG484AC1/I0, device versionB. Actual VG SHA256 is `{before['VG']}`. SDC has exactly clk50 period20.000ns and the existing radio_rx false path; no additional command or internal timing exception was introduced. TR clock summary has one base clk50, actual Fmax{fmax}MHz, setup and hold violated endpoints both0.

Every numeric row in the five raw summary tables was parsed independently and checked finite/nonnegative:

| Table | Reported rows checked | Minimum slack ns |
|---|---:|---:|
{rows}

FS, TR, RPT and PR are all nonempty and were created/last-written after the actual process start and before its exit. Embedded FS/RPT/TR created times are07:07:45/07:07:49/07:07:51 local, respectively. FS header identifies GW5AT-60B, the correct part/package, UserCode0x0000b0b3 and CRCCheckON. The FS is{fresh['FS']['bytes']}bytes with SHA256 `{before['FS']}`; TR SHA256 `{before['TR']}`. All input/output evidence hashes matched before and after the review, so no mutable partial file was accepted.

All18 active raw physical-report pin rows exactly match the18 CST locations and18 raw VG top-level directions (13 outputs). All IO types, specified pull modes and output drive settings match. Radio RX isB16/input/PULL_MODE=UP; radio TX isB15/output. This establishes software artifact/pin identity, not current physical wiring.

Detailed rows, all18 pin assignments, timestamps, raw FS header and hashes for all{len(paths)} evidence files are in [B7_P3R0_RAW_REVIEW.json](B7_P3R0_RAW_REVIEW.json). Script SHA256 `{out['reviewer_script_sha256']}`. Scope is the existing raw implementation/timing evidence only, not a new STA run, whole-netlist functional equivalence proof, hardware or flight acceptance.
'''
(O/'B7_P3R0_RAW_REVIEW.md').write_text(report)
print(json.dumps({'passed':True,'Fmax_MHz':str(fmax),'table_minima':{k:v['minimum_slack_ns']for k,v in tables.items()},'rows_checked':sum(v['reported_rows']for v in tables.values()),'pins':len(pins),'FS_sha256':before['FS'],'TR_sha256':before['TR'],'report_sha256':sha(O/'B7_P3R0_RAW_REVIEW.md'),'json_sha256':sha(O/'B7_P3R0_RAW_REVIEW.json')},indent=2))
