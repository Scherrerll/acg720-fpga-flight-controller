"""Only after genuine independent50MHz acceptance, cancel one exact owned vendor child."""
from pathlib import Path
import argparse,ctypes,datetime,hashlib,json,subprocess
from ctypes import wintypes
O=Path(__file__).resolve().parent;R=O.parents[2]
targets={
 'v14_p3':('compact_aw_v14','compact_aw_v14','physical_p3r0_01'),
 'v14_p2':('compact_aw_v14','compact_aw_v14','physical_p2r0_01'),
 'v4_rep1':('compact_aw_v4_rep1_followup','compact_aw_v4','physical_p3r0_rep1_01'),
 'v4_fan100_native_p3':('compact_aw_v4_fan100_native','compact_aw_v4_fan100_native','physical_p3r0_01'),
 'v4_fan100_native_p2':('compact_aw_v4_fan100_native','compact_aw_v4_fan100_native','physical_p2r0_01'),
 'v4_native_p3':('compact_aw_v4_native','compact_aw_v4_native','physical_p3r0_01'),
 'v4_native_p2':('compact_aw_v4_native','compact_aw_v4_native','physical_p2r0_01'),
 'v13_native_p3':('compact_aw_v13_native','compact_aw_v13_native','physical_p3r0_01'),
 'v13_native_p2':('compact_aw_v13_native','compact_aw_v13_native','physical_p2r0_01'),
 'v13_map1_p3':('compact_aw_v13_map1','compact_aw_v13_map1','physical_p3r0_01'),
 'v13_map1_p2':('compact_aw_v13_map1','compact_aw_v13_map1','physical_p2r0_01'),
 'v13_p3':('compact_aw_v13','compact_aw_v13','physical_p3r0_01'),
 'v13_p2':('compact_aw_v13','compact_aw_v13','physical_p2r0_01'),
 'v12_p3':('compact_aw_v12','compact_aw_v12','physical_p3r0_01'),
 'v12_p2':('compact_aw_v12','compact_aw_v12','physical_p2r0_01'),
 'data_p2':('compact_aw_v4_data_routing_followup','compact_aw_v4','physical_p2r0_data_route_01'),
 'v11_p3':('compact_aw_v11','compact_aw_v11','physical_p3r0_01'),
 'v11_p2':('compact_aw_v11','compact_aw_v11','physical_p2r0_01'),
 'v4_clockbuf1':('compact_aw_v4_clockbuf1_followup','compact_aw_v4','physical_p3r0_clkbuf1_01')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('target',choices=targets);p.add_argument('--selected-report',required=True);args=p.parse_args()
    selected=Path(args.selected_report).resolve();assert selected.is_relative_to(O)
    manifest=selected/'TERMINAL_MANIFEST.json';review=selected/'INDEPENDENT_RAW_REVIEW.json';m=read(manifest);v=read(review)
    assert m['passed'] and m['vendor_actual_p_wait']==m['runner_actual_p_wait']==0
    assert v['passed'] and all(v['checks'].values()) and v['period_ns']==20 and v['fmax_mhz']>=50
    assert v['violated_endpoints']=={'setup':0,'hold':0} and all(x>=0 for x in v['slacks_ns'].values())
    for name,digest in v['raw_sha256'].items():
        f=(R/name).resolve();assert f.is_relative_to(R) and f.name.lower()!='deployment.env' and '.env' not in f.suffixes;assert sha(f)==digest
    meta,variant,label=targets[args.target];report=O/meta/label;A=R/'out/z_aw_fix_20261026'/variant/label;V=A/'verification'
    assert report.resolve()!=selected and (report/'runner_process.json').is_file()
    if (V/'physical_exit.json').is_file():print('Target already terminal; no process operation.');return
    receipt=read(V/'physical_process.json');pid=int(receipt['pid']);cmd=receipt['command']
    assert len(cmd)==2 and Path(cmd[1]).resolve()==(A/'physical.tcl').resolve()
    assert Path(cmd[0]).name.lower()=='gw_sh.exe' and not (V/'controlled_cancellation.json').exists()
    if '_native' in variant:
        log=(V/'physical.log').read_text(encoding='utf8',errors='replace')
        assert 'SYNTHESIS_AUDIT_RETURNED_EOF' in log and 'Running placement' in log,'Wait for actual SYN audit and PNR before cancelling a native combined process; never orphan a SYN child.'
    query=f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}'; if($null -eq $p){{throw 'Owned vendor no longer live'}}; [pscustomobject]@{{ProcessId=$p.ProcessId;ParentProcessId=$p.ParentProcessId;CreationUtc=$p.CreationDate.ToUniversalTime().ToString('o');ExecutablePath=$p.ExecutablePath;CommandLine=$p.CommandLine}} | ConvertTo-Json -Compress"
    cim=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True))
    assert cim['ProcessId']==pid and cim['ParentProcessId']==receipt['parent_pid'] and cim['CommandLine'].casefold()==' '.join(cmd).casefold()
    assert Path(cim['ExecutablePath']).resolve()==Path(cmd[0]).resolve()
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME)]
    h=k.OpenProcess(0x1000|0x0001|0x100000,False,pid);assert h,ctypes.get_last_error()
    try:
        name=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(name));assert k.QueryFullProcessImageNameW(h,0,name,ctypes.byref(size))
        assert Path(name.value).resolve()==Path(cmd[0]).resolve()
        created,ended,kernel,user=(wintypes.FILETIME() for _ in range(4));assert k.GetProcessTimes(h,ctypes.byref(created),ctypes.byref(ended),ctypes.byref(kernel),ctypes.byref(user))
        ticks=(created.dwHighDateTime<<32)|created.dwLowDateTime;born=datetime.datetime.fromtimestamp((ticks-116444736000000000)/1e7,datetime.timezone.utc)
        assert abs((born-datetime.datetime.fromisoformat(receipt['started_utc'])).total_seconds())<2
        assert abs((born-datetime.datetime.fromisoformat(cim['CreationUtc'])).total_seconds())<.01
        record={'requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'cancelled_after_qualified_selection',
            'reason':'First complete-route50MHz candidate has passed direct independent raw review. Stop only this other owned physical calculation before canonical promotion.',
            'pid':pid,'parent_pid':receipt['parent_pid'],'command':cmd,'native_handle_creation_utc':born.isoformat(),'fresh_CIM_identity':cim,
            'selected_manifest':str(manifest),'selected_manifest_sha256':sha(manifest),'selected_independent_review_sha256':sha(review),
            'log_prefix_sha256':sha(V/'physical.log'),'process_receipt_sha256':sha(V/'physical_process.json'),'canceller_sha256':sha(Path(__file__)),
            'requested_native_exit_code':1,'actual_vendor_wait':'Read original runner physical_exit.json after actual p.wait, never inferred from termination request.'}
        (V/'controlled_cancellation.json').write_text(json.dumps(record,indent=2)+'\n');assert k.TerminateProcess(h,1),ctypes.get_last_error()
        print('Terminated exact verified owned vendor handle only; wait for original vendor/runner receipts.')
    finally:k.CloseHandle(h)
if __name__=='__main__':main()
