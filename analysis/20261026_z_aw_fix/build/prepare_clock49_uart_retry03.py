"""Restore original RX RTL, use an even426 receive divisor, preserve all strict test expectations."""
from pathlib import Path
import ast,datetime,hashlib,json
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;M=O/'clock49_uart';W=R/'out/z_aw_fix_20261026/clock49_working/source';B=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not (M/'RX_EVEN_DIVISOR_REVIEW.json').exists()
failed=read(M/'proofs_retry02/vvp_exit.json');review=read(M/'RX_HALFBIT_REVIEW.json')
assert failed['actual_p_wait']==1 and failed['normal_wait_return'] and sha(W/'xy_pi_parameters.v')==review['new_source_sha256']
archive=M/'failed_halfbit_candidate.v';assert not archive.exists();archive.write_bytes((W/'xy_pi_parameters.v').read_bytes())
original=(B/'xy_pi_parameters.v').read_bytes();(W/'xy_pi_parameters.v').write_bytes(original);assert sha(W/'xy_pi_parameters.v')==review['original_source_sha256']
record={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Original receiver logic restored byte-exact. Only49MHz RX divisor changes from425 to426; TX remains425. Frozen50MHz/v14/prototype source never changed.',
    'ceil_halfbit_failed_wait':1,'ceil_failure_exit_sha256':sha(M/'proofs_retry02/vvp_exit.json'),'failed_ceil_candidate_sha256':sha(archive),
    'restored_original_RX_sha256':sha(W/'xy_pi_parameters.v'),
    'reason':'The odd425 receiver runs slightly faster than nominal115200; a one-clock half-bit shift did not avoid requalifying the remaining low stop interval. Choose nearest-even receive divisor426, preserving the original floor-half FSM and allowing its stop center to arrive later. This is a sampling configuration correction, not a byte/error/gap acceptance waiver.',
    'clock_Hz':49000000,'TX_BIT_TICKS':425,'RX_BIT_TICKS':426,
    'TX_baud':49000000/425,'RX_sampling_baud':49000000/426,
    'nearest_even_formula':'2 * floor((CLOCK_HZ + BAUD)/(2*BAUD)); yields434 at50MHz and426 at49MHz',
    'test_policy':'All normal256-byte, short3bit idle,16bad-stop, false-start and physical TX-width expectations remain unchanged.',
    'whole_firmware_or_hardware_qualified':False}
(M/'RX_EVEN_DIVISOR_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
parent=O/'verify_clock49_uart.py';t=parent.read_text(encoding='utf8')
assert t.count("D=M/'proofs'")==1;t=t.replace("D=M/'proofs'","D=M/'proofs_retry03'")
assert t.count('xy_pi_uart_rx #(.BIT_TICKS(425))')==2;t=t.replace('xy_pi_uart_rx #(.BIT_TICKS(425))','xy_pi_uart_rx #(.BIT_TICKS(426))')
marker='assert not D.exists();D.mkdir();T=D/\'tmp\';T.mkdir()';assert t.count(marker)==1
t=t.replace(marker,"assert sha(W/'xy_pi_parameters.v')==sha(B/'xy_pi_parameters.v')\n"+marker)
ast.parse(t);dest=O/'verify_clock49_uart_retry03.py';assert not dest.exists();dest.write_text(t,encoding='utf8')
(M/'RETRY03_DERIVATION.json').write_text(json.dumps({'parent_runner_sha256':sha(parent),'new_runner_sha256':sha(dest),
    'changes':'New output directory, source equality assertion and RX425 to426 only. Transmitter425, stimulus bytes/gaps, expected counts and all assertions unchanged.',
    'even_divisor_review_sha256':sha(M/'RX_EVEN_DIVISOR_REVIEW.json')},indent=2)+'\n',encoding='utf8')
(W.parent/'WORK_PROGRESS_04_RX_ORIGINAL_NOT_FOR_BUILD.json').write_text(json.dumps({'scope':'Incomplete fallback. RX original restored. Future49MHz top should use TX425/RX426 only after the full remaining integration and validation.',
    'review_sha256':sha(M/'RX_EVEN_DIVISOR_REVIEW.json'),'working_source58':{x.relative_to(W).as_posix():sha(x) for x in W.rglob('*') if x.is_file()}},indent=2)+'\n',encoding='utf8')
print('Restored original RX bytes; prepared426Rx/425Tx retry with strict unchanged stimulus and acceptance.')
