"""Preserve the real failure, fix only odd half-bit rounding in isolated RX and rerun identical stimuli."""
from pathlib import Path
import ast,datetime,hashlib,json
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_uart';W=R/'out/z_aw_fix_20261026/clock49_working/source';B=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not (M/'RX_HALFBIT_REVIEW.json').exists()
failure=read(M/'proofs/vvp_exit.json');assert failure['normal_wait_return'] and failure['actual_p_wait']==1
diag=M/'recovery_diagnostic/vvp.log';text=diag.read_text(encoding='utf8')
assert 'RX49 t_ns=193539.269 valid=0 error=1' in text and 'RX50 t_ns=224050.001 valid=1 error=0 data=00' in text
p=W/'xy_pi_parameters.v';old=(B/'xy_pi_parameters.v').read_bytes();assert p.read_bytes()==old
before=b'ticks<=BIT_TICKS/2-1;';after=b'ticks<=(BIT_TICKS+1)/2-1;'
assert old.count(before)==1;candidate=old.replace(before,after);p.write_bytes(candidate)
assert candidate.replace(after,before)==old
record={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Only the isolated49MHz fallback RX candidate changes; frozen50MHz/v14/prototype sources remain untouched. Original UART failure and diagnostic retained.',
    'actual_first_vvp_wait':1,'first_failure_exit_sha256':sha(M/'proofs/vvp_exit.json'),'actual_diagnostic_log_sha256':sha(diag),
    'root_cause':'At nominal115200 input the425 odd-divisor floor half-bit sample starts one clock early; the short bad-stop recovery trace rejects the next valid byte and later emitsfc, while the original434/50MHz receiver accepts00. Round half-bit up instead; even434 remains217 before the minus1, odd425 becomes213 instead of212.',
    'original_source_sha256':sha(B/'xy_pi_parameters.v'),'new_source_sha256':sha(p),
    'default434_half_bit_constant_unchanged':(434//2)==((434+1)//2),
    'candidate425_half_bit_ticks':(425+1)//2,'old425_half_bit_ticks':425//2,
    'test_policy':'Keep the exact original short-idle, bad-stop, false-start and all256-byte expectations. No larger idle gap, no discarded-junk waiver, no lowered acceptance.',
    'full_firmware_or_hardware_qualified':False}
(M/'RX_HALFBIT_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
original_script=O/'verify_clock49_uart.py';t=original_script.read_text(encoding='utf8')
assert t.count("D=M/'proofs'")==1;t=t.replace("D=M/'proofs'","D=M/'proofs_retry02'")
assert t.count("B/'xy_pi_parameters.v'")==2;t=t.replace("B/'xy_pi_parameters.v'","W/'xy_pi_parameters.v'")
marker='assert not D.exists();D.mkdir();T=D/\'tmp\';T.mkdir()';assert t.count(marker)==1
t=t.replace(marker,"rx_review=json.loads((M/'RX_HALFBIT_REVIEW.json').read_text(encoding='utf8'))\nassert sha(W/'xy_pi_parameters.v')==rx_review['new_source_sha256']\n"+marker)
ast.parse(t);dest=O/'verify_clock49_uart_retry02.py';assert not dest.exists();dest.write_text(t,encoding='utf8')
(M/'RETRY02_DERIVATION.json').write_text(json.dumps({'parent_runner_sha256':sha(original_script),'new_runner_sha256':sha(dest),
    'test_stimulus_text_unchanged':True,'changes':'Output directory only and use the one-line RX candidate with a source-hash assertion. Testbench bytes and all expected values remain unchanged.',
    'RX_review_sha256':sha(M/'RX_HALFBIT_REVIEW.json')},indent=2)+'\n',encoding='utf8')
(W.parent/'WORK_PROGRESS_03_RX_NOT_FOR_BUILD.json').write_text(json.dumps({'scope':'Incomplete isolated fallback; only leaf units have been adapted. No49MHz top integration or full build acceptance.',
    'RX_review_sha256':sha(M/'RX_HALFBIT_REVIEW.json'),'working_source58':{x.relative_to(W).as_posix():sha(x) for x in W.rglob('*') if x.is_file()}},indent=2)+'\n',encoding='utf8')
print('Prepared odd-half-bit RX candidate and an identical-stimulus retry; original failure preserved.')
