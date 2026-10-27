"""Use real old/selected55 bytes in isolated temporary roots; never promote B4."""
from pathlib import Path
from contextlib import contextmanager
import copy,gzip,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from unittest import mock
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2]
spec=importlib.util.spec_from_file_location('lifecycle_export',R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py')
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)
v=x.validation
selected=R/'out/z_aw_fix_20261026/compact_aw_v22/physical_p3r0_01/source'
expected=x.read(x.HERE/'compact_aw_v22/PROOF_BINDING.json')['source55']
frozen=x.read(x.HERE.parent/'handoff_20261026/SOURCE_BINDINGS.json')
before=next(value for key,value in frozen['source_sha256'].items() if Path(frozen['roots'][key]).resolve()==(R/'firmware/B0B4/source').resolve())
prototype=R/'firmware/B0B4/source'
if {p:x.sha(prototype/p) for p in before}!=before:
    prototype=x.HERE.parent/'implementation_history/B4_initial_prototype_full55'
assert len(expected)==len(before)==55 and set(expected)==set(before)
assert {p:x.sha(selected/p) for p in expected}==expected and {p:x.sha(prototype/p) for p in before}==before
CONFLICTS={'acg720_ano_port.v','mtf_xyz_navigation_control.v','core/ano_flight_state.v','core/flight_core.v','core/height_loss_fallback.v',
           'position/mtf_shared_height_fusion.v','position/mtf_xyz_hold_control.v','position/pose_time_adapter.v','sensor/mtf01p_reader.v','sensor/mtf_shared_geometry.v'}
assert {p for p in expected if before[p]!=expected[p]}==CONFLICTS
measurements={}

@contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='lifecycle_unit_',dir=D) as value:
        root=Path(value).resolve();assert root.is_relative_to(D.resolve())
        old,new,backup,package=[root/name for name in ['prototype/source','selected/source','verified_initial55','package']]
        for name in before:
            for source,destination in [(prototype/name,old/name),(prototype/name,backup/name),(selected/name,new/name),(selected/name,package/'source'/name)]:
                destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        collector=x.EvidenceCollector(new,expected,dict(repo=R,source=new,metadata=root/'meta',proofs=root/'proofs',donor=root/'donor',attempt=root/'attempt',report=root/'report'))
        for name in before:collector.check(old/name,before[name]);collector.check(new/name,expected[name])
        mapping={old/name:(backup/name,before[name]) for name in expected}
        yield root,old,new,backup,package,collector,mapping

class Lifecycle(unittest.TestCase):
    def test_real55_positive_lifecycle_and_old_original_keys(self):
        with fixture() as (root,old,new,backup,package,c,mapping):
            self.assertEqual({name:x.sha(backup/name) for name in before},before)
            c.freeze_overwrites(mapping)
            for name in expected:shutil.copy2(new/name,old/name)
            index=json.loads(c.finish(package).read_text());archived=v.ArchivedEvidence(package,index)
            for name in expected:
                self.assertEqual(x.sha(old/name),expected[name])
                self.assertEqual(hashlib.sha256(c.blob(old/name,before[name])).hexdigest(),before[name])
                self.assertEqual(hashlib.sha256(archived.blob(old/name,before[name])).hexdigest(),before[name])
                self.assertEqual(hashlib.sha256(archived.blob(new/name,expected[name])).hexdigest(),expected[name])
                self.assertEqual(index['files'][v.evidence_key(old/name)]['sha256'],before[name])
            for name in CONFLICTS:self.assertFalse(index['files'][v.evidence_key(old/name)]['archive_path'].startswith('source/'))
            self.assertFalse((package/'qualification.json').exists())
            measurements['real55_positive']={'prototype_sha256':before,'selected_sha256':expected,'conflicting_files':sorted(CONFLICTS),'archived_original_keys':len(index['files']),'frozen_original_keys':len(c.frozen_overwrites),'qualified_package_created':False}
    def test_without_freeze_original_stale_failure_still_reproduces(self):
        with fixture() as (_,old,new,backup,package,c,mapping):
            for name in expected:shutil.copy2(new/name,old/name)
            with self.assertRaisesRegex(AssertionError,'Evidence changed before archiving'):c.finish(package)
    def test_wrong_requested_digest_cannot_relabel_frozen_history(self):
        with fixture() as (_,old,new,backup,package,c,mapping):
            c.freeze_overwrites(mapping);name=sorted(CONFLICTS)[0];shutil.copy2(new/name,old/name)
            with self.assertRaisesRegex(AssertionError,'Declared frozen evidence changed'):c.blob(old/name,expected[name])
    def test_bad_backup_or_changed_original_is_rejected_before_freezing(self):
        for location in ['backup','original']:
            with fixture() as (_,old,new,backup,package,c,mapping):
                name=sorted(CONFLICTS)[0];(backup/name if location=='backup' else old/name).write_bytes(b'tampered')
                with self.assertRaisesRegex(AssertionError,'Overwrite backup differs'):c.freeze_overwrites(mapping)
                self.assertEqual(c.frozen_overwrites,{})
    def test_unplanned_dependency_changes_remain_live_errors(self):
        with fixture() as (root,old,new,backup,package,c,mapping):
            ordinary=root/'ordinary_input.v';ordinary.write_bytes(b'original')
            c.blob(ordinary);c.freeze_overwrites(mapping);ordinary.write_bytes(b'changed')
            with self.assertRaisesRegex(AssertionError,'Evidence changed before archiving'):c.finish(package)
    def test_corrupt_frozen_bytes_are_rejected(self):
        with fixture() as (_,old,new,backup,package,c,mapping):
            c.freeze_overwrites(mapping);key=v.evidence_key(old/sorted(CONFLICTS)[0]);c.frozen_overwrites[key]=b'tampered'
            with self.assertRaisesRegex(AssertionError,'Frozen evidence changed'):c.blob(key)
            with self.assertRaisesRegex(AssertionError,'Frozen evidence changed before archiving'):c._write(key,package,c.files[key]['archive_path'])
    def test_gzip_frozen_bytes_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix='lifecycle_gzip_',dir=D) as value:
            root=Path(value).resolve();assert root.is_relative_to(D.resolve())
            original=root/'original.log';saved=root/'saved.log';data=b'actual old log\n'*20
            original.write_bytes(data);saved.write_bytes(data)
            c=x.EvidenceCollector(root,{},dict(repo=R));c.blob(original)
            c.freeze_overwrites({original:(saved,hashlib.sha256(data).hexdigest())});original.write_bytes(b'new log')
            index=json.loads(c.finish(root/'package').read_text());item=index['files'][v.evidence_key(original)]
            self.assertEqual(gzip.decompress((root/'package'/item['archive_path']).read_bytes()),data)
    def test_environment_paths_rejected_before_any_byte_read(self):
        with fixture() as (root,old,new,backup,package,c,mapping):
            normal=old/'acg720_ano_port.v';digest=before['acg720_ano_port.v']
            for values in [{root/'.env':(backup/'acg720_ano_port.v',digest)},{normal:(root/'deployment.env',digest)}]:
                with mock.patch.object(Path,'read_bytes',side_effect=AssertionError('must not read')):
                    with self.assertRaises(SystemExit):c.freeze_overwrites(values)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Lifecycle))
    if result.wasSuccessful():
        target=D/'TEST_MEASUREMENTS.json';assert not target.exists();target.write_text(json.dumps(measurements,indent=2)+'\n',encoding='utf8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
