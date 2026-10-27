from pathlib import Path
import hashlib,json,math,re,xml.etree.ElementTree as ET
SOURCE=VERIFY=ATTEMPT=None
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def physical_audit(vg_sha, expected):
    syn=json.loads((VERIFY/'native_synthesis_audit.json').read_text(encoding='utf8'))
    assert syn['passed'] and syn['source55']==expected and syn['netlist_sha256']==vg_sha
    assert sha(SOURCE/'acg720_ano_port.gprj')==syn['project_sha256']
    for name in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']:
        data=json.loads((VERIFY/name).read_text(encoding='utf8'))
        assert data['passed'] and sha(VERIFY/name)==syn[name.replace('.json','_sha256')]
    clock_audit=json.loads((VERIFY/'strict_ff_clock_audit.json').read_text(encoding='utf8'))
    assert clock_audit['all_FF_CLK50'] and not clock_audit['bad']
    project_files=[f.attrib for f in ET.parse(SOURCE/'acg720_ano_port.gprj').findall('.//File')]
    native_project=any(f.get('type')=='file.verilog' and f.get('enable')=='1' for f in project_files) and not any(f.get('type')=='file.netlist' for f in project_files)
    base=SOURCE/'impl/pnr/acg720_ano_port'
    tr=base.with_suffix('.tr'); rpt=base.with_suffix('.rpt.txt'); fs=base.with_suffix('.fs')
    pr=base.with_suffix('.pr'); cfg=base.parent/'device.cfg'
    for p in (tr,rpt,fs,pr,cfg):assert p.is_file(),('missing physical artifact',str(p))
    text=tr.read_text(errors='replace'); report=rpt.read_text(errors='replace'); log=(VERIFY/'physical.log').read_text(errors='replace')
    def section(start,end):
        m=re.search(r'^'+re.escape(start)+r'\s*$(.*?)^'+re.escape(end),text,re.S|re.M); assert m,('missing raw timing table',start); return m[1]
    checks={}
    for name,start,end in [('setup','3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('hold','3.1.2 Hold Paths Table','3.1.3 Recovery Paths Table'),('recovery','3.1.3 Recovery Paths Table','3.1.4 Removal Paths Table'),('removal','3.1.4 Removal Paths Table','3.2 Minimum Pulse Width Table')]:
        rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',section(start,end),re.M)
        assert rows,('empty timing table',name)
        checks[name]=dict(worst_slack_ns=min(float(r[1])for r in rows),reported_paths=len(rows),worst_path=rows[0])
    rows=re.findall(r'^\s+(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(.+?)\s+(clk50)\s+(\S+)\s*$',section('3.2 Minimum Pulse Width Table','3.3 Timing Report By Analysis Type'),re.M)
    assert rows
    checks['minimum_pulse_width']=dict(worst_slack_ns=min(float(r[1])for r in rows),reported_paths=len(rows),worst_path=rows[0])
    clock=re.search(r'^\s+1\s+clk50\s+Base\s+(\d+\.\d+)\s+',text,re.M)
    fmax=re.search(r'^\s+1\s+clk50\s+([\d.]+)\(MHz\)\s+([\d.]+)\(MHz\)',text,re.M)
    assert clock and fmax
    setup=int(re.search(r'<Numbers of Setup Violated Endpoints>:(\d+)',text)[1]); hold=int(re.search(r'<Numbers of Hold Violated Endpoints>:(\d+)',text)[1])
    expected_pins=dict(re.findall(r'IO_LOC\s+"([^"]+)"\s+(\w+)\s*;',(SOURCE/'acg720_ano_port.cst').read_text()))
    pins={m[1]:(m[2],m[3])for m in re.finditer(r'^\s*(\w+)\s*\|[^|]*\|\s*(\w+)/\d+\s*\|\s*Y\s*\|\s*(in|out)\s*\|',report,re.M)}
    header=fs.open('rb').read(4096).decode('ascii',errors='replace')
    unrouted=[int(x)for x in re.findall(r'total\s+(\d+)\s+unrouted nets',log+report,re.I)]
    criteria=dict(actual_period_20ns=float(clock[1])==20, fmax_at_least_50=math.isfinite(float(fmax[2])) and float(fmax[2])>=50,
        setup_hold_endpoints_zero=setup==hold==0,all_five_nonnegative=all(math.isfinite(c['worst_slack_ns'])and c['worst_slack_ns']>=0 for c in checks.values()),
        full_route='Placement and routing completed' in log and 'Bitstream generation completed' in log and not any(unrouted),
        physical_command_returned='PHYSICAL_COMMAND_RETURNED_EOF' in log,only_new_vg=sha(SOURCE/'impl/gwsynthesis/acg720_ano_port.vg')==vg_sha,
        native_RTL_project=native_project,
        native_synthesis_audited=all(marker in log for marker in ['GowinSynthesis finish','SYNTHESIS_COMMAND_RETURNED_EOF','SYNTHESIS_AUDIT_RETURNED_EOF']) and 'Skip synthesis, because there is only one netlist file' not in log,
        constrained_frequency_50=float(fmax[1])==50,

        pins18=len(expected_pins)==len(pins)==18 and {n:x[0]for n,x in pins.items()}==expected_pins and pins.get('radio_rx')==('B16','in')and pins.get('radio_tx')==('B15','out'),
        fs_usercode_b4=bool(re.search(r'UserCode:\s*0x0000b0b4\b',header,re.I)),
        cfg_usercode_b4=bool(re.search(r'set user_code = 0x0000B0B4\b',cfg.read_text(),re.I)))
    evidence=[tr,rpt,fs,pr,cfg,SOURCE/'acg720_ano_port.sdc',SOURCE/'acg720_ano_port.cst',SOURCE/'acg720_ano_port.gprj',SOURCE/'impl/gwsynthesis/acg720_ano_port.vg',VERIFY/'physical.log',VERIFY/'physical_exit.json',ATTEMPT/'physical.tcl']
    out=dict(passed=all(criteria.values()),criteria=criteria,period_ns=float(clock[1]),fmax_mhz=float(fmax[2]),checks=checks,
        setup_violated_endpoints=setup,hold_violated_endpoints=hold,unrouted_reports=unrouted,pins=pins,
        source_sha256=expected,evidence_sha256={str(p.relative_to(ATTEMPT)):sha(p)for p in evidence})
    out.update(workflow='native_RTL_project_SYN_audit_PNR_one_vendor_process',native_synthesis_audit_sha256=sha(VERIFY/'native_synthesis_audit.json'))
    write('physical_audit.json',out)
    assert out['passed'],('physical qualification failed',criteria,str(VERIFY/'physical_audit.json'))
    return out

