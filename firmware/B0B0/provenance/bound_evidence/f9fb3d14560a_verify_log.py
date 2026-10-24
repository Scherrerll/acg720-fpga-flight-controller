"""Validate archive hashes and replay raw chunks using recorded reset boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from protocol import receiver


# Older receiver versions omitted these derived annotations. Wire fields and
# every annotation actually present must still replay exactly; control-version
# logs did not predate this schema and therefore receive no missing-key waiver.
LEGACY_ADDED_METADATA = frozenset(('experimental_control','installation_qualified',
    'flight_ready','joint_xyz','position_hold_includes_height','standalone_altitude_mode',
    'xyz_requested','xyz_ready','xyz_active','horizontal_only','manual_throttle',
    'height_fusion_enabled','xy_control_reason','xy_shadow_active'))


def same_decoded(row, saved):
    if row == saved:
        return True
    if row.get('_protocol') == 'a579' and isinstance(saved, dict) and 'program_label' in saved:
        saved=dict(saved)
        if 'legacy_raw_label' in saved:return False
        saved['legacy_raw_label']=saved.pop('program_label')
        return row == saved
    legacy = row.get('_protocol') == 'a581' and row.get('version') == 1 or \
             row.get('_protocol') == 'a582' and row.get('version') in (1, 2, 3)
    return bool(legacy and isinstance(saved, dict) and not set(saved).difference(row) and
                set(row).difference(saved) <= LEGACY_ADDED_METADATA and
                all(row[key] == value for key, value in saved.items()))


def verify(archive):
    with zipfile.ZipFile(archive) as zipped:
        manifest=json.loads(zipped.read('manifest.json'))
        for name,digest in manifest['sha256'].items():
            h=hashlib.sha256()
            with zipped.open(name) as stream:
                while block:=stream.read(65536):h.update(block)
            assert h.hexdigest()==digest,f'Hash mismatch: {name}'
        def rows(name):
            with zipped.open(name) as stream:
                for line in stream:
                    try:yield json.loads(line)
                    except ValueError:raise AssertionError(f'Partial or invalid JSON in {name}')
        resets=iter(e for e in rows('events.jsonl') if e['kind'] in ('connected','disconnected','ingest_overflow'))
        pending=next(resets,None);decoder=receiver();offset=0;decoded_count=primary_count=0
        expected=rows('telemetry.jsonl')
        with zipped.open('raw.bin') as raw:
            for chunk in rows('chunks.jsonl'):
                while pending and pending['host_ns']<=chunk['host_ns']:
                    decoder.buffer.clear();pending=next(resets,None)
                assert chunk['offset']==offset,'Raw chunk offsets are not contiguous'
                data=raw.read(chunk['length']);assert len(data)==chunk['length'],'Raw prefix is shorter than chunks'
                offset+=len(data)
                for row in decoder.feed(data):
                    saved=next(expected,None)
                    assert saved is not None and same_decoded(row,saved['row']),f'Raw replay mismatch at decoded frame{decoded_count}'
                    decoded_count+=1;primary_count+=row['_protocol']=='a579'
            assert not raw.read(1),'Raw prefix has unindexed bytes'
        assert next(expected,None) is None,'Decoded log extends beyond raw snapshot'
        meta=json.loads(zipped.read('meta.json'))
        return dict(passed=True,raw_bytes=offset,decoded_frames=decoded_count,primary_frames=primary_count,
                    checksum_errors=decoder.checksum_errors,source=meta['source'],
                    reported_build_id=meta.get('reported_build_id'),hash_files=len(manifest['sha256']),
                    snapshot_utc=manifest.get('captured_utc'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path)
    args=parser.parse_args();print(json.dumps(verify(args.archive),ensure_ascii=False,indent=2))
