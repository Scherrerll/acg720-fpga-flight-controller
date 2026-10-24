"""Verify the 23/24 October archive without hardware or original machine paths."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def verify():
    archive=json.loads((ROOT/'docs/WORK_ARCHIVE_20261023_24.json').read_text(encoding='utf-8'))
    for item in archive['files']:
        path=(ROOT/item['path']).resolve()
        assert path.is_relative_to(ROOT),item['path']
        data=path.read_bytes()
        assert len(data)==item['bytes'] and sha(data)==item['sha256'],item['path']
        if item['gzip']:assert sha(gzip.decompress(data))==item['source_sha256'],item['path']
        elif not item['adapted']:assert item['sha256']==item['source_sha256'],item['path']
    release=ROOT/'firmware/B0B0'
    original=(release/'provenance/manifest.json').read_bytes()
    assert sha(original)==archive['original_frozen_manifest_sha256']
    frozen=json.loads(original)
    for name,digest in frozen['logical_source_sha256'].items():
        assert sha((release/'source_snapshot'/Path(name.replace('\\','/'))).read_bytes())==digest,name
    for name,digest in frozen['physical_inputs_sha256'].items():
        assert sha((release/'selected_physical'/Path(name.replace('\\','/'))).read_bytes())==digest,name
    assert sha((release/'release/acg720_ano_port.fs').read_bytes())==frozen['bitstream']['sha256']
    assert sha((release/'selected_netlist/acg720_ano_port.vg').read_bytes())=='0be62a85bf094d9102a6488b792c77c8cb9296d9a5b4aaa3e05a72ea96fd3500'
    references=0
    for node in ET.parse(release/'source_snapshot/acg720_ano_port.gprj').findall('.//File'):
        p=(release/'source_snapshot'/node.attrib['path'].replace('\\','/')).resolve()
        assert p.is_relative_to(release/'source_snapshot') and p.is_file(),str(p)
        references+=1
    for name in ['hardware_acceptance.json','powered_direction_acceptance.json','cold_boot_acceptance.json']:
        record=json.loads((release/'provenance/closure'/name).read_text(encoding='utf-8'))
        # Earlier hardware record has a different schema; original bytes are hash checked above.
        if 'passed' in record:assert record['passed'],name
    cold=json.loads((release/'provenance/closure/cold_boot_acceptance.json').read_text(encoding='utf-8'))
    assert cold['physical_power_cycle_verified'] and cold['battery_only_verified'] and not cold['flight_ready']
    return dict(passed=True,archive_files=len(archive['files']),source_files=len(frozen['logical_source_sha256']),
                project_references=references,bound_evidence_archived=archive['inherited_evidence_archived'],
                fmax_mhz=frozen['fmax_mhz'],hardware_accessed=False,full_original_qualification_replayed=False,flight_ready=False)


if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
