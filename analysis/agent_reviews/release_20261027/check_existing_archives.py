"""Run the focused suite using already-created immutable proof/SYN test archives."""
from pathlib import Path
import importlib.util,json,sys,unittest
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('existing_release_evidence_tests',D/'test_release_evidence.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
archives={}
for path in sorted(D.glob('*proof_SYN_archive_*/evidence/selected/EVIDENCE_INDEX.json'),key=lambda p:p.stat().st_mtime,reverse=True):
    index=json.loads(path.read_text());family=Path(index['origins']['metadata']).name.removeprefix('compact_aw_')
    if family in {'v17','v20','v21','v22'} and family not in archives:
        collector,qualification=m.live(family);m.with_synthesis(collector,qualification)
        archives[family]=(path.parents[2],index,qualification)
assert set(archives)=={'v17','v20','v21','v22'}
def setup(cls):
    cls.helper_before=m.export.sha(m.REPO/'firmware/B0B4/build_candidate.py')
    cls.collector,_=m.live('v17')
    cls.package,cls.index,cls.qualification=archives['v17']
    cls.index_path=cls.package/'evidence/selected/EVIDENCE_INDEX.json'
    cls.new_archives={family:archives[family] for family in ['v20','v21','v22']}
m.EvidenceTests.setUpClass=classmethod(setup)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(m.EvidenceTests))
raise SystemExit(0 if result.wasSuccessful() else 1)
