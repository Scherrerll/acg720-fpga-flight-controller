"""Read-only evidence audit. Prints JSON; does not run simulation, vendor or devices."""
from pathlib import Path
from datetime import datetime, timezone
import binascii
import hashlib
import json

REPO = Path(__file__).resolve().parents[3]
FW = REPO / 'firmware/B0B2'
PROOF = FW / 'evidence/v2_projection_proof'
ARCHIVE = FW / 'evidence/source_revisions/copy99_v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sources(folder):
    return {p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob('*') if p.is_file()}

def main():
    current = sources(FW/'source')
    archive = load(ARCHIVE/'index.json')
    index = load(PROOF/'index.json')
    integration = load(FW/'evidence/v2_integration.json')
    projection = load(PROOF/'projection_result.json')
    sik = load(PROOF/'sik_result.json')
    assert len(current) == len(archive['source_sha256']) == 53
    assert sources(ARCHIVE/'source') == archive['source_sha256']
    for name, expected in archive['artifacts_sha256'].items():
        assert sha(ARCHIVE/name) == expected, name
    assert sha(ARCHIVE/'index.json') == integration['prior_revision_sha256']
    assert current == index['source_sha256'] == integration['source_sha256']
    assert current == projection['source_sha256'] == sik['source_sha256']
    assert archive['source_sha256'] == integration['previous_source_sha256']
    changed = sorted(k for k in current if current[k] != archive['source_sha256'][k])
    assert changed == ['sik_imu_diagnostic.v', 'telemetry_tx.v']
    assert changed == sorted(integration['changed_source_files'])
    assert integration['unchanged_source_files'] == 51
    for name, record in index['files'].items():
        assert sha(PROOF/name) == record['sha256'], name
        assert (PROOF/name).stat().st_size == record['bytes'], name
    for name, origin in index['origin_files'].items():
        assert sha(REPO/origin) == index['files'][name]['sha256'], origin
    for name, expected in integration['prototype_evidence'].items():
        assert sha(REPO/name) == expected, name
    for record in projection['inputs'].values():
        assert sha(Path(record['path'])) == record['sha256']
    for record in projection['tools'].values():
        assert sha(Path(record['path'])) == record['sha256']
    for name, expected in projection['artifacts_sha256'].items():
        assert sha(Path(projection['output'])/name) == expected, name
    for command in projection['commands']:
        assert type(command['returncode']) is int and command['returncode'] == 0
        assert sha(Path(projection['output'])/command['log']) == command['log_sha256']
    for i, command in enumerate(sik['commands']):
        assert type(command['returncode']) is int and command['returncode'] == 0
        assert sha(PROOF/f'sik_step_{i:02d}.log') == command['log_sha256']
    scripts = {**projection['verification_scripts_sha256'], **sik['verification_scripts_sha256']}
    for name, expected in scripts.items():
        assert sha(REPO/name) == expected, name
    assert projection['passed'] is True and projection['source_unchanged'] is True
    assert projection['inputs_unchanged'] is True and projection['tools_unchanged'] is True
    assert projection['preserved_summary_bits'] == 448
    assert projection['unavailable_summary_slots'] == {
        'latest_rejected_source_id': [319, 288], 'first_protection_time_ms_low32': [95, 64]}
    assert projection['full_protocol_equivalence'] is False
    assert sik['passed'] is True and sik['source_unchanged'] is True
    old_tx = (ARCHIVE/'source/telemetry_tx.v').read_text()
    new_tx = (FW/'source/telemetry_tx.v').read_text()
    needle = "diagnostic_packet={16'ha585,8'd1,8'd1,"
    assert old_tx.count(needle) == 1
    assert old_tx.replace(needle, "diagnostic_packet={16'ha585,8'd2,8'd1,") == new_tx
    old_sik = (PROOF/'reference_v1.v').read_text()
    assert old_sik.replace('module sik_imu_diagnostic(', 'module sik_original(') == (PROOF/'reference_renamed.v').read_text()
    baseline = load(FW/'baseline.json')
    frozen = REPO/'firmware/B0B0/source_snapshot/telemetry_tx.v'
    assert sha(frozen) == baseline['source_sha256']['telemetry_tx.v'] == sik['golden_source_sha256']
    wire = bytes.fromhex((PROOF/'sik_wire.hex').read_text())
    golden = bytes.fromhex((PROOF/'legacy_wire.hex').read_text())
    assert len(wire) == 644 and len(golden) == 568 and wire[:568] == golden
    frames = []
    offset = 0
    for size, header in zip([224,32,40,128,96,48,76], ['a579','a57a','a580','a581','a582','a583','a585']):
        packet = wire[offset:offset+size]
        assert packet[:2].hex() == header
        if header in ['a579', 'a57a']:
            checksum = 0
            for value in packet[2:-1]:
                checksum ^= value
            assert checksum == packet[-1]
            kind = 'xor'
        else:
            checksum = binascii.crc_hqx(packet[2:-2], 0xffff)
            assert checksum == int.from_bytes(packet[-2:], 'big')
            kind = 'CRC16-CCITT-FALSE'
        sequence = int.from_bytes(packet[4:6] if header == 'a585' else packet[2:4], 'big')
        frames.append(dict(header=header, offset=offset, bytes=size, checksum_kind=kind,
                           checksum=checksum, sequence=sequence))
        offset += size
    assert len({frame['sequence'] for frame in frames}) == 1
    a585 = wire[568:]
    assert a585[2:4] == bytes([2, 1])
    body = a585[10:74]
    assert body[24:28] == bytes(4) and body[52:56] == bytes(4)
    binding = load(PROOF/'formal_shadow_binding.json')
    synthesis = load(PROOF/'formal_synthesis_result.json')
    assert binding['formal_synthesis_result_sha256'] == sha(PROOF/'formal_synthesis_result.json')
    assert synthesis['logical_source_sha256'] == current
    assert binding['same_vg'] is False and binding['full_netlist_equivalence_proved'] is False
    assert sha(PROOF/'formal_resource.xml') == sha(PROOF/'shadow_resource.xml')
    assert sources(FW/'source') == current, 'source changed during review'
    result = dict(
        schema='b0b2.independent-v2-control-passivity-review.v1',
        reviewed_at_utc=datetime.now(timezone.utc).isoformat(),
        audit_passed=True, source_stable=True, source_sha256=current,
        prior_source_sha256=archive['source_sha256'], changed_source_files=changed,
        unchanged_source_files=51, archive_artifacts_verified=len(archive['artifacts_sha256']),
        proof_files_verified=len(index['files']), proof_origin_bindings_verified=len(index['origin_files']),
        integration_prototype_bindings_verified=len(integration['prototype_evidence']),
        important_bindings={
            'prior_revision_index': sha(ARCHIVE/'index.json'),
            'integration': sha(FW/'evidence/v2_integration.json'),
            'projection_index': sha(PROOF/'index.json'),
            'projection_result': sha(PROOF/'projection_result.json'),
            'sik_result': sha(PROOF/'sik_result.json'),
            'golden_telemetry': sha(frozen),
            'audit_script': sha(Path(__file__)),
        },
        telemetry_delta_after_newline_normalization='exactly one version literal 1 to 2',
        reference_delta_after_newline_normalization='exactly one module declaration rename',
        projection_bits=448, capture_tick_bits=32, coverage=projection['coverage'],
        window_coverage=projection['window_coverage'],
        unavailable_slots=projection['unavailable_summary_slots'],
        wire_frames=frames, legacy_bytes_equal=568, wire_bytes=644,
        read_only_review=True, simulations_started=0, vendor_started=False, hardware_accessed=False,
        full_512_equivalence=False, full_netlist_equivalence=False,
        physical_acceptance=False, flight_ready=False,
        review_scope='Read-only source delta, static passivity cone, existing bounded simulation evidence and independent byte/checksum/hash recomputation; no new simulations.')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
