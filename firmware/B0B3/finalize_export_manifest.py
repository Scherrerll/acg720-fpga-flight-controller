"""Bind stable export-build logs after the one-shot exporter has finished."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=json.loads((E/'export_manifest.json').read_text(encoding='utf8'))
assert '"origin_markers_unchanged": true'in(E/'export_build.stdout.log').read_text()and not(E/'export_build.stderr.log').read_text()
for name in ['export_build.stdout.log','export_build.stderr.log','finalize_export_manifest.py']:
 p=E/name;assert name not in M['files'];M['files'][name]=dict(kind='generated_export_file',source=None,transform=dict(name='generated_for_new_layout',generator='finalize_export_manifest.py'),sha256=sha(p),size_bytes=p.stat().st_size)
for original,record in M['original_full_delivery_markers'].items():
 p=Path(original);assert sha(p)==record['sha256']and p.stat().st_size==record['size_bytes'],'Original delivery changed'
(E/'export_manifest.json').write_text(json.dumps(M,indent=2,ensure_ascii=False),encoding='utf8');(E/'export_manifest.sha256').write_text(sha(E/'export_manifest.json')+'  export_manifest.json\n',encoding='ascii')
print(json.dumps(dict(files=len(M['files']),manifest_sha256=sha(E/'export_manifest.json'),origin_markers_unchanged=True),indent=2))
