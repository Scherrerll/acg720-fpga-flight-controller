"""Verify exported B0AE bytes, project references, and source-bound evidence. No hardware."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'firmware/B0AE'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    export = json.loads((RELEASE / 'source_export.json').read_text(encoding='utf-8'))
    for entry in export['files']:
        path = (ROOT / entry['path']).resolve()
        if not path.is_relative_to(ROOT) or sha(path) != entry['sha256']:
            raise ValueError('Export changed: ' + entry['path'])
    historical_count=0
    for manifest in ('origins_manifest.json','early_manifest.json','late_manifest.json'):
        data=json.loads((ROOT/'history'/manifest).read_text(encoding='utf-8'))
        for entry in data['files']:
            path=(ROOT/'history'/entry['export_path']).resolve()
            if not path.is_relative_to(ROOT/'history') or sha(path)!=entry['sha256']:
                raise ValueError('Historical export changed: '+entry['export_path'])
            historical_count+=1
    host=json.loads((ROOT/'ground/export_manifest.json').read_text(encoding='utf-8'))
    host_count=0
    for entry in host['files']+host['generated_files']:
        path=(ROOT/entry['export']).resolve()
        expected=entry.get('export_sha256',entry.get('sha256'))
        if not path.is_relative_to(ROOT) or sha(path)!=expected:
            raise ValueError('Ground export changed: '+entry['export'])
        host_count+=1
    asset_count=0
    for name in ('mechanical/export_manifest.json','hardware/source_manifest.json'):
        asset_manifest=json.loads((ROOT/name).read_text(encoding='utf-8'))
        for entry in asset_manifest['files']:
            path=(ROOT/entry['path']).resolve()
            if not path.is_relative_to(ROOT) or sha(path)!=entry['sha256']:
                raise ValueError('Hardware asset export changed: '+entry['path'])
            if path.stat().st_size!=entry['bytes']:
                raise ValueError('Hardware asset size changed: '+entry['path'])
            asset_count+=1
    projects = list(ROOT.glob('history/**/*.gprj')) + [RELEASE/'fixture/acg720_ano_port.gprj']
    count = 0
    for project in projects:
        for node in ET.parse(project).findall('.//File'):
            name = node.attrib['path'].replace('\\', '/')
            path = (project.parent / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError('Missing/escaping project source: ' + str(project) + ': ' + name)
            count += 1
    qualification = json.loads((RELEASE/'provenance/qualification.json').read_text(encoding='utf-8'))
    for name, expected in qualification['sources_sha256'].items():
        if sha(RELEASE/'fixture'/name) != expected:
            raise ValueError('Qualified FPGA source mismatch: ' + name)
    baseline = json.loads((RELEASE/'provenance/baseline.json').read_text(encoding='utf-8'))
    for name, expected in baseline['original_sources'].items():
        if sha(RELEASE/'reference'/Path(name).name) != expected:
            raise ValueError('Original ANO reference changed: ' + name)
    selector = json.loads((RELEASE/'provenance/selected_release.json').read_text(encoding='utf-8'))
    if sha(RELEASE/'provenance/offline_release.json') != selector['offline_release_sha256']:
        raise ValueError('Selected offline release evidence changed')
    tcl = (RELEASE/'fixture/build.tcl').read_text(encoding='utf-8')
    settings = dict(re.findall(r'^set_option\s+-(\w+)\s+(\S+)\s*$', tcl, re.M))
    expected = dict(global_freq='50', map_option='2', max_fanout='200',
                    place_option='3', route_option='2', replicate_resources='0', user_code='0000B0AE')
    if any(settings.get(k) != v for k, v in expected.items()):
        raise ValueError('Selected build settings changed')
    if not (RELEASE/'provenance/DO_NOT_PROGRAM').is_file():
        raise ValueError('Offline candidate marker missing')
    return {'passed': True, 'b0ae_export_files': len(export['files']),
            'historical_hashes_verified':historical_count,
            'ground_hashes_verified':host_count,
            'hardware_asset_hashes_verified':asset_count,
            'gprj_count': len(projects), 'project_file_references': count,
            'hardware_accessed': False, 'full_historical_qualification_replayed': False}

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))

