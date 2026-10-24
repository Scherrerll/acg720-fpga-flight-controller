"""Launch the existing read-only receiver with additive target display/export.

The original receiver, decoder and archival evidence are left on disk unchanged.
Only fields already present in A579 are exposed. No programmer is imported.
"""
import argparse
import hashlib
import importlib
from pathlib import Path
import runpy
import sys

from attitude_tracking import FIELDS, snapshot_tracking, tracking_fields


def install(receiver_dir):
    receiver_dir = Path(receiver_dir).resolve()
    if not (receiver_dir / 'ground_server.py').is_file():
        raise ValueError('Existing receiver directory required')
    sys.path.insert(0, str(receiver_dir))
    protocol = importlib.import_module('protocol')
    analysis = importlib.import_module('analysis')
    recorder = importlib.import_module('recorder')
    original_snapshot = protocol.Dashboard.snapshot
    original_point = analysis.point
    original_recorder_init = recorder.Recorder.__init__

    def snapshot(self):
        result = original_snapshot(self)
        with self.lock:
            row = dict(self.latest_primary_row) if self.latest_primary_row else None
        result['tracking'] = snapshot_tracking(result, row)
        return result

    def point(record):
        result = original_point(record)
        result.update(tracking_fields(record.get('row', {}), record.get('_firmware_build_id')))
        return result

    def recorder_init(self, *args, **kwargs):
        original_recorder_init(self, *args, **kwargs)
        self.meta['reported_attitude_tracking'] = {
            'version': 1, 'firmware': 'B0B0', 'fields': FIELDS,
            'yaw_comparison': 'body rate deg/s, not heading angle',
            'software_sha256': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                for name in ('receiver_setpoints.py', 'attitude_tracking.py')}}
        self._write_meta()

    protocol.Dashboard.snapshot = snapshot
    analysis.point = point
    analysis.FIELDS.update(FIELDS)
    recorder.Recorder.__init__ = recorder_init
    return receiver_dir / 'ground_server.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('--receiver-dir', type=Path,
                        default=Path(__file__).resolve().parents[3] / 'ground' / 'B0B0')
    args, receiver_args = parser.parse_known_args()
    server = install(args.receiver_dir)
    sys.argv = [str(server), *receiver_args]
    runpy.run_path(str(server), run_name='__main__')


if __name__ == '__main__':
    main()
