"""Cancel exactly the owned dense-timing vendor via a verified live native handle."""
from pathlib import Path
import ctypes,datetime,hashlib,json,subprocess
from ctypes import wintypes
O=Path(__file__).resolve().parent;R=O.parents[2]
V=R/'out/z_aw_fix_20261026/compact_aw_v4_timing/physical_p3r0_01/verification'
receipt=json.loads((V/'physical_process.json').read_text());pid=int(receipt['pid']);assert pid==57240
assert not (V/'physical_exit.json').exists() and not (V/'controlled_cancellation.json').exists()
cmd=receipt['command'];assert Path(cmd[1])==R/'out/z_aw_fix_20261026/compact_aw_v4_timing/physical_p3r0_01/physical.tcl'
query=f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}'; if($null -eq $p){{throw 'Owned vendor not live'}}; [pscustomobject]@{{ProcessId=$p.ProcessId;ParentProcessId=$p.ParentProcessId;CreationUtc=$p.CreationDate.ToUniversalTime().ToString('o');ExecutablePath=$p.ExecutablePath;CommandLine=$p.CommandLine}} | ConvertTo-Json -Compress"
cim=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True))
assert cim['ProcessId']==pid and cim['ParentProcessId']==receipt['parent_pid']
assert cim['CommandLine'].casefold()==' '.join(cmd).casefold()
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
    started=datetime.datetime.fromisoformat(receipt['started_utc']);observed=datetime.datetime.fromisoformat(cim['CreationUtc'])
    assert abs((born-started).total_seconds())<2 and abs((born-observed).total_seconds())<.01
    now=datetime.datetime.now(datetime.timezone.utc);assert (now-started).total_seconds()>40*60
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'requested_utc':now.isoformat(),'classification':'cancelled_dense_mapping_deprioritized',
        'reason':'Dense timing-goal map adds4666LUT; after>40min vendor CPU activity but no stage beyond Routing0, reassign one of two owned physical slots to109 raw-report-based critical-cell placement on the smaller known-fullroute v4 VG. This is scheduling cancellation, not a vendor route/timing failure.',
        'pid':pid,'parent_pid':receipt['parent_pid'],'command':cmd,'native_handle_creation_utc':born.isoformat(),'fresh_CIM_identity':cim,
        'identity_checks':['exact recorded PID/parent/command','native image path','native creation time matches fresh CIM and original launch'],
        'log_prefix_sha256':sha(V/'physical.log'),'process_receipt_sha256':sha(V/'physical_process.json'),
        'next_preparation_sha256':sha(O/'compact_aw_v4_partial_floorplan_followup/PREPARATION.json'),
        'requested_native_exit_code':1,'actual_vendor_wait':'Must come from original still-running runner physical_exit.json after real p.wait(); never inferred here.'}
    (V/'controlled_cancellation.json').write_text(json.dumps(record,indent=2)+'\n')
    assert k.TerminateProcess(h,1),ctypes.get_last_error()
    print('Requested termination through verified owned vendor handle only; original supervisor will record actual waits.')
finally:k.CloseHandle(h)
