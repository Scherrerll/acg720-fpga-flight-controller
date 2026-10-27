"""Seal an already qualified B0B4 package; never build or program hardware."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
B4 = REPO / 'firmware/B0B4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', help='Unique evidence label, e.g. offline or cold_boot')
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z][a-z0-9_]{0,47}', args.label)
    qualification = json.loads((B4 / 'qualification.json').read_text(encoding='utf8'))
    physical = qualification['physical']
    assert qualification['passed'] and physical['passed']
    assert all(physical['criteria'].values())
    assert physical['period_ns'] == 20 and physical['fmax_mhz'] >= 50
    assert physical['setup_violated_endpoints'] == physical['hold_violated_endpoints'] == 0
    assert set(physical['checks']) == {'setup', 'hold', 'recovery', 'removal', 'minimum_pulse_width'}
    assert all(v['worst_slack_ns'] >= 0 for v in physical['checks'].values())
    expected = qualification['source_sha256']
    assert len(expected) == 55
    source_files = {p.relative_to(B4 / 'source').as_posix(): p
                    for p in (B4 / 'source').rglob('*') if p.is_file()}
    assert source_files.keys() == expected.keys()
    assert all(not Path(name).name.lower().startswith('.env')
               and not Path(name).name.lower().endswith('.env')
               and '.env' not in [s.lower() for s in Path(name).suffixes]
               and not path.is_symlink()
               and path.resolve().is_relative_to((B4 / 'source').resolve())
               for name, path in source_files.items())
    assert {name: sha(path) for name, path in source_files.items()} == expected
    assert sha(B4 / qualification['release_bitstream']) == qualification['bitstream_sha256']

    manifest = B4 / 'release_manifest.json'
    checksum = B4 / 'release_manifest.sha256'
    previous = None
    if manifest.exists() or checksum.exists():
        assert manifest.is_file() and checksum.is_file()
        assert sha(manifest) == checksum.read_text(encoding='ascii').split()[0]
        archive = B4 / 'evidence/manifest_history' / args.label
        assert not archive.exists(), 'Never replace a previous manifest receipt'
        archive.mkdir(parents=True)
        (archive / manifest.name).write_bytes(manifest.read_bytes())
        (archive / checksum.name).write_bytes(checksum.read_bytes())
        previous = {'path': (archive / manifest.name).relative_to(REPO).as_posix(),
                    'sha256': sha(archive / manifest.name)}

    excluded = {manifest.resolve(), checksum.resolve()}
    files = []
    for root in [B4, REPO / 'ground/B0B4']:
        for path in sorted(root.rglob('*')):
            # Check names before opening any file. Secrets and runtime caches never enter a package.
            if path.name.lower().startswith('.env') or path.name.lower().endswith('.env') or '.env' in [s.lower() for s in path.suffixes]:
                continue
            if any(part in {'__pycache__', 'node_modules', 'runtime'} for part in path.relative_to(root).parts):
                continue
            if path.suffix.lower() in {'.pyc', '.pyo'} or path.resolve() in excluded:
                continue
            if not path.is_file():
                continue
            assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
            files.append({'path': path.relative_to(REPO).as_posix(),
                          'sha256': sha(path), 'bytes': path.stat().st_size})
    result = {'sealed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'label': args.label,
              'scope': 'Saved B0B4 firmware, selected evidence and ground package; hardware status is recorded separately in qualification.json.',
              'qualification_sha256': sha(B4 / 'qualification.json'),
              'previous_manifest': previous, 'files': files}
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    checksum.write_text(sha(manifest) + '  release_manifest.json\n', encoding='ascii')
    print(json.dumps({'sealed': True, 'label': args.label, 'files': len(files),
                      'manifest_sha256': sha(manifest), 'hardware_operation': False}))


if __name__ == '__main__':
    main()
