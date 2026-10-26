"""Verify delivered bytes and frozen B0B3 source; not a simulation or flight rerun."""
from pathlib import Path
import argparse,hashlib,json

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def sha(path):
    value=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-inputs',action='store_true',help='Also rehash the eight original local JSONL inputs; requires the H snapshot')
    args=parser.parse_args()
    manifest_path=HERE/'manifest.json'
    value=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert (HERE/'manifest.sha256').read_text(encoding='ascii').split()[0]==sha(manifest_path),'Manifest checksum mismatch'
    for name,record in value['files'].items():
        path=(REPO/name).resolve();assert path.is_relative_to(HERE),'Artifact path escapes follow-up'
        assert path.stat().st_size==record['bytes']and sha(path)==record['sha256'],name
    for name,record in value['existing_dependencies'].items():
        path=(REPO/name).resolve();assert path.is_relative_to(REPO),'Dependency escapes repository'
        assert path.stat().st_size==record['bytes']and sha(path)==record['sha256'],name
    ledger=json.loads((HERE/'input_ledger.json').read_text(encoding='utf-8'))
    source=REPO/'firmware/B0B3/source'
    current={path.relative_to(source).as_posix():sha(path)for path in source.rglob('*')if path.is_file()}
    assert current==ledger['current_b0b3_source_sha256'],'Frozen source set/bytes changed'
    external=0
    if args.external_inputs:
        for item in ledger['historical_sources']:
            path=Path(item['path']);assert path.stat().st_size==item['bytes']and sha(path)==item['sha256'],str(path)
            external+=1
    print(json.dumps(dict(passed=True,artifact_files=len(value['files']),frozen_source_files=len(current),
         external_sources_checked=external,manifest_sha256=sha(manifest_path),
         scope='Checks exact packaged hashes and source bindings; does not rerun C/RTL, reconstruct missing telemetry, access hardware or certify flight'),indent=2))

if __name__=='__main__':main()
