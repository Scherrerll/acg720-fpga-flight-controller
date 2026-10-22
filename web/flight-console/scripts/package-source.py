"""Package only reviewed code/assets; never local data, dependencies or credentials."""
from pathlib import Path
import hashlib
import zipfile

root = Path(__file__).resolve().parent.parent
archive = root.parent / (root.name + '-source.zip')
files = [root / name for name in ('.gitignore', 'README.md', 'deployment.json', 'package.json', 'package-lock.json', 'edgeone.json')]
for folder in ('frontend', 'worker', 'platform', 'cloud-functions', 'tests'):
    files.extend(p for p in (root / folder).rglob('*') if p.is_file() and p.suffix in ('.js', '.mjs', '.html', '.css', '.svg', '.png'))
files.extend(root / 'local' / name for name in ('bridge.py', 'test_bridge.py', 'start-bridge.mjs', 'README.md'))
files.extend(root / 'scripts' / name for name in ('build-edgeone.mjs', 'package-source.py', 'smoke.mjs'))
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
    for path in sorted(set(files)):
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Unexpected package path')
        output.write(path, path.relative_to(root).as_posix())
print(archive)
print('files=' + str(len(files)))
print('sha256=' + hashlib.sha256(archive.read_bytes()).hexdigest())
