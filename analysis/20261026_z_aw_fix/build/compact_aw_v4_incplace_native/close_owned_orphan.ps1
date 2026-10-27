$ErrorActionPreference = 'Stop'
$repoRoot = 'C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller'
$verifyRoot = Join-Path $repoRoot 'out/z_aw_fix_20261026/compact_aw_v4_incplace_native/physical_p3r0_01/verification'
$processReceipt = Get-Content -LiteralPath (Join-Path $verifyRoot 'physical_process.json') -Raw | ConvertFrom-Json
$runnerReceipt = Get-Content -LiteralPath (Join-Path $repoRoot 'analysis/20261026_z_aw_fix/build/compact_aw_v4_incplace_native/physical_p3r0_01/runner_exit.json') -Raw | ConvertFrom-Json
if ($runnerReceipt.actual_p_wait -ne 1) { throw 'Expected actual supervisor assertion exit1' }
$ownProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($processReceipt.pid)"
if (-not $ownProcess) { throw 'Process already ended: do not invent exit' }
if ($ownProcess.ParentProcessId -ne $processReceipt.parent_pid) { throw 'Parent identity mismatch' }
if ($ownProcess.ExecutablePath -ne $processReceipt.command[0]) { throw 'Executable mismatch' }
if ($ownProcess.CommandLine -notlike "*$($processReceipt.command[1])*") { throw 'Exact task path mismatch' }
$expectedStart = [datetimeoffset]::Parse($processReceipt.started_utc).UtcDateTime
if ([math]::Abs(($ownProcess.CreationDate.ToUniversalTime() - $expectedStart).TotalSeconds) -gt 5) { throw 'Creation time mismatch' }
$ownHandle = Get-Process -Id $processReceipt.pid
$null = $ownHandle.Handle
$receiptPath = Join-Path $verifyRoot 'controlled_cancellation.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Never overwrite receipt' }
$record = [ordered]@{
    classification = 'cancelled_orphan_after_runner_assertion'
    reason = 'Actual native inc_place again reported2.82percent match and default fallback. Runner failed a too-strict wholeVG hash comparison before own-child wait. Stop only verified own orphan; preserve original root1 and no fabricated vendor p.wait.'
    pid = $ownProcess.ProcessId
    parent_pid = $ownProcess.ParentProcessId
    executable = $ownProcess.ExecutablePath
    command_line = $ownProcess.CommandLine
    created_utc = $ownProcess.CreationDate.ToUniversalTime().ToString('o')
    requested_utc = [datetime]::UtcNow.ToString('o')
    actual_vendor_p_wait = $null
    actual_runner_p_wait = 1
    wait_method = 'Verified System.Diagnostics.Process handle, Kill then WaitForExit; original Popen parent had already ended'
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$ownHandle.Kill()
$ownHandle.WaitForExit()
$record['observed_native_OS_exit_code'] = $ownHandle.ExitCode
$record['closed_utc'] = [datetime]::UtcNow.ToString('o')
$record['log_sha256_after_close'] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $verifyRoot 'physical.log')).Hash.ToLower()
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $verifyRoot 'controlled_cancellation_closed.json') -Encoding utf8
$record | ConvertTo-Json -Depth 6
