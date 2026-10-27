"""Exact v18 source55 copy; only the extension snapshot bank becomes28 SPs."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
OLD=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v21/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=O.parent/'compact_aw_v18/source_freeze.json';parent=json.loads(freeze.read_text(encoding='utf8'))['source55']
assert not NEW.exists() and len(parent)==55
assert all(not any(part.lower().startswith('.env') for part in Path(n).parts) for n in parent)
assert all(sha(OLD/n)==h for n,h in parent.items())
for n in parent:
    p=NEW/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/n,p)
assert {n:sha(NEW/n) for n in parent}==parent
name='acg720_ano_port.v';before=(NEW/name).read_bytes()
a=b' reg [863:0] core_q=0;reg core_initialized=0;reg [887:0] extension_q=0;reg [215:0] acceleration_q=0;\n always @(posedge clk50) if(!telemetry_snapshot_hold) begin core_initialized<=1;core_q<=core_body;extension_q<=extension;acceleration_q<=acceleration_body;range_diagnostic_q<=range_diagnostic_body;end\n'
b=b' reg [863:0] core_q=0;reg core_initialized=0;wire [887:0] extension_q;reg [215:0] acceleration_q=0;\n always @(posedge clk50) if(!telemetry_snapshot_hold) begin core_initialized<=1;core_q<=core_body;acceleration_q<=acceleration_body;range_diagnostic_q<=range_diagnostic_body;end\n gw5_snapshot_bram #(.WIDTH(888)) extension_storage(.clk(clk50),.enable(!telemetry_snapshot_hold),.data(extension),.q(extension_q));\n'
assert before.count(a)==1;start=before.index(a);after=before.replace(a,b);(NEW/name).write_bytes(after)
assert after.replace(b,a)==before and before[:start]==after[:start] and before[start+len(a):]==after[start+len(b):]
expected={n:sha(NEW/n) for n in parent};assert [n for n in expected if expected[n]!=parent[n]]==[name]
diff=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='v18/'+name,tofile='v21/'+name))
(O/'source_changes.diff').write_text(diff,encoding='utf8',newline='')
basis=dict(baseline_source_root=str(OLD),candidate_source_root=str(NEW),transformations={name:dict(edits=[[a.decode(),b.decode()]],
    original_region_byte_start=start,original_region_bytes=len(a),candidate_region_bytes=len(b),
    prefix_sha256=hashlib.sha256(before[:start]).hexdigest(),suffix_sha256=hashlib.sha256(before[start+len(a):]).hexdigest(),
    reverse_exact_bytes=True,outside_region_exact_bytes=True,baseline_sha256=parent[name],candidate_sha256=expected[name])},
    unchanged_files=54,zero_added_clock_cycles_intent=True,physical_SP_banks=28,
    reference_standalone_proof=str(R/'analysis/agent_reviews/extension_bram_20261027/RESULT.json'),
    reference_standalone_proof_sha256=sha(R/'analysis/agent_reviews/extension_bram_20261027/RESULT.json'),
    scope='Only extension_q888 storage changes. Parent v18 cached velocity, controller/FSM, all other snapshots and every source/config byte outside this one top region remain exact. New integration proofs and physical qualification are separate.')
(O/'SOURCE_EQUIVALENCE_BASIS.json').write_text(json.dumps(basis,indent=2)+'\n',encoding='utf8')
review='''# v21: extension-only same-edge SP snapshot

The exact frozen v18 source55 is copied. Only one top region changes:
extension_q[887:0] becomes a WIDTH888 gw5_snapshot_bram instance with the exact
original enable !telemetry_snapshot_hold. Other assignments in the original
posedge block remain on that edge. There is no added reset, phase, clock,
latency, mask, gain, SDC/CST, build option or public interface change.

The unchanged wrapper selects28 SP BIT_WIDTH32 banks, READ_MODE0 bypass output,
WRITE_MODE01 write-through, all-byte AD000f, RESET0, zero default INIT. The
unmodified complete vendor functional model has independently passed WIDTH888
against initialized enabled FF semantics, including pre-clock0, same-edge,
hold, enable X/Z and payload X/Z. The Icarus default FF branch is not evidence
for hardware SP behavior: new integration and original-top13 runs explicitly
select GW5_USE_VENDOR_BRAM, add a fixture-only GSR root and inspect elaborated
SP count. Source/proof/vendor qualification are separate gates.

New actual-top integration may force only the extension source payload and
the serializer's transport-busy acknowledgment boundary. It must leave boot,
reset, snapshot hold, serializer state/ticks/index/cache and storage untouched.
Natural short/long-period scheduling, same-edge snapshot888, all public ports,
start/data/hold and complete protocol sequence/XOR/CRC are compared. This is
payload-boundary and byte-ack integration, not a physical UART/whole-flight
qualification. Original top13 stimulus is reused byte-for-byte; its existing
internal safety/RX forces remain explicitly part of that separate test scope.

Historical47-SP core/info/rotation experiments passed functional models but
failed routing. Extension was not moved in those trials. No timing benefit
is inferred; synthesis-only preparation must retain strict mapped SP CLK50
checks, and vendor execution waits for independent review.
'''
(O/'source_review.md').write_text(review,encoding='utf8')
out=dict(prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source55=expected,baseline_source55=parent,
    baseline_source_freeze_sha256=sha(freeze),source_review_sha256=sha(O/'source_review.md'),
    source_equivalence_basis_sha256=sha(O/'SOURCE_EQUIVALENCE_BASIS.json'),source_changes_diff_sha256=sha(O/'source_changes.diff'),
    copied_frozen_source_files=55,changed_files=[name],unchanged_files=54,source_root=str(NEW),
    proof_and_physical_status='Unqualified source candidate; new proofs and actual synthesis/physical results are required separately.')
(O/'source_freeze.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,changed_files=[name],unchanged_files=54,reverse_exact_bytes=True)))
