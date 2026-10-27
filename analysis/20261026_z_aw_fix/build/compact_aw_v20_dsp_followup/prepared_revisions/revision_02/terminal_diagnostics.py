"""Pure diagnostic truth gates; no process, filesystem or vendor operations."""
def successful_receipt(receipt):
    return (isinstance(receipt, dict) and receipt.get('normal_wait_return') is True
            and type(receipt.get('actual_p_wait')) is int and receipt['actual_p_wait'] == 0)

def terminal_status(result, vendor, runner, audit, unrouted, physical_log):
    result_passed = isinstance(result, dict) and result.get('passed') is True
    vendor_ok, runner_ok = successful_receipt(vendor), successful_receipt(runner)
    if result_passed and vendor_ok and runner_ok:
        return True, 'full_gate_pass'
    physical_passed = result_passed or (isinstance(audit, dict) and audit.get('passed') is True)
    if runner is None:
        return False, 'awaiting_runner_exit_receipt'
    if vendor is None:
        return False, 'runner_ended_without_vendor_exit_receipt'
    if physical_passed and vendor_ok and not runner_ok:
        return False, 'runner_failed_after_physical_gate_pass'
    if not vendor_ok:
        return False, ('vendor_nonzero_route_failure' if any(unrouted) or 'DesRoute failed.' in physical_log
                       else 'vendor_exit_not_successful')
    criteria = audit.get('criteria', {}) if isinstance(audit, dict) else {}
    timing = ['actual_period_20ns', 'fmax_at_least_50', 'setup_hold_endpoints_zero', 'all_five_nonnegative']
    if criteria.get('full_route') is True and any(criteria.get(k) is False for k in timing):
        return False, 'completed_full_route_timing_failure'
    if not runner_ok:
        return False, 'runner_failed_or_not_normal'
    return False, 'physical_gate_or_artifact_failure'
