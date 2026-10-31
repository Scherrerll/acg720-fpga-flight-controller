"""Deterministic snapshot/ingest interleaving proof; no devices or live services."""
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from protocol import Dashboard, LegacyDashboard, base


SEED = next(json.loads(line)['row'] for line in
            Path(__file__).with_name('fixtures').joinpath('seed_primary.jsonl').read_text(encoding='utf8').splitlines()
            if json.loads(line).get('row', {}).get('_protocol') == 'a579')


class SnapshotAtomicTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.dashboard = Dashboard('OFFLINE')
        self.dashboard.clock = lambda: self.now
        self.dashboard.connection(True)
        self.publish(10)

    def publish(self, sequence):
        self.dashboard.ingest(dict(SEED, sequence=sequence))
        self.dashboard.ingest(dict(_protocol='a580', sequence=sequence,
                                   build_id=0xb0b2, uptime_ms=sequence * 100))
        self.dashboard.ingest(dict(_protocol='a585', sequence=sequence,
                                   build_id=0xb0b2, uptime_ms=sequence * 100))

    def interleave_snapshot(self, snapshot_class):
        """Probe ingestion exactly after a parent has copied its snapshot.

        A nonblocking lock probe makes the interleaving deterministic: the old
        code permits a complete new generation before the child continues;
        the fixed code defers ingestion until the complete snapshot returns.
        """
        copied, probed, done = threading.Event(), threading.Event(), threading.Event()
        errors, updated_during_snapshot = [], []
        original = snapshot_class.snapshot

        def publish_during_snapshot():
            try:
                if not copied.wait(2):
                    raise AssertionError('snapshot did not reach the copy boundary')
                acquired = self.dashboard.lock.acquire(blocking=False)
                updated_during_snapshot.append(acquired)
                if acquired:
                    self.dashboard.lock.release()
                    self.publish(11)
                probed.set()
                if not acquired:
                    self.publish(11)
            except BaseException as exc:
                errors.append(exc)
                probed.set()
            finally:
                done.set()

        def pause_after_copy(dashboard):
            result = original(dashboard)
            copied.set()
            if not probed.wait(2):
                raise AssertionError('writer did not probe the snapshot lock')
            return result

        worker = threading.Thread(target=publish_during_snapshot, daemon=True)
        worker.start()
        try:
            with patch.object(snapshot_class, 'snapshot', pause_after_copy):
                snapshot = self.dashboard.snapshot()
        finally:
            copied.set()
            worker.join(2)
        self.assertTrue(done.is_set(), 'ingestion must resume after snapshot returns')
        self.assertFalse(errors, repr(errors))
        return snapshot, updated_during_snapshot

    def test_primary_and_flight_info_are_one_snapshot_generation(self):
        snapshot, updated = self.interleave_snapshot(base.BmiDashboard)
        self.assertEqual((snapshot['sequence'], snapshot['flight_info']['sequence']), (10, 10))
        self.assertEqual(updated, [False], 'ingestion crossed a partially assembled snapshot')
        self.assertTrue(snapshot['fresh'])
        self.assertTrue(snapshot['flight_info_fresh'])
        after = self.dashboard.snapshot()
        self.assertEqual((after['sequence'], after['flight_info']['sequence']), (11, 11))

    def test_diagnostic_and_parent_snapshot_are_one_generation(self):
        snapshot, updated = self.interleave_snapshot(LegacyDashboard)
        self.assertEqual((snapshot['sequence'], snapshot['flight_info']['sequence'],
                          snapshot['imu_diagnostic']['sequence']), (10, 10, 10))
        self.assertEqual(updated, [False], 'ingestion crossed a partially assembled snapshot')
        self.assertTrue(snapshot['imu_diagnostic_fresh'])
        self.assertEqual(self.dashboard.snapshot()['imu_diagnostic']['sequence'], 11)

    def test_snapshot_does_not_align_or_refresh_unpaired_frames(self):
        # A primary can normally arrive before the matching information frame.
        self.dashboard.ingest(dict(SEED, sequence=11))
        snapshot = self.dashboard.snapshot()
        self.assertEqual((snapshot['sequence'], snapshot['flight_info']['sequence']), (11, 10))
        # Preserve even a larger source gap; only the bridge may reject it.
        self.dashboard.ingest(dict(SEED, sequence=12))
        snapshot = self.dashboard.snapshot()
        self.assertEqual((snapshot['sequence'], snapshot['flight_info']['sequence']), (12, 10))
        self.now += .501
        stale = self.dashboard.snapshot()
        self.assertFalse(stale['fresh'])
        self.assertIsNone(stale['sequence'])
        self.assertIsNone(stale['data'])
        self.assertEqual(stale['fresh_timeout_ms'], 500.0)
        self.assertGreater(stale['frame_age_ms'], stale['fresh_timeout_ms'])
        self.now += .5
        expired = self.dashboard.snapshot()
        self.assertFalse(expired['flight_info_fresh'])
        self.assertIsNone(expired['flight_info'])


if __name__ == '__main__':
    unittest.main()
