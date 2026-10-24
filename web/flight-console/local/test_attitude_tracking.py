import unittest
from attitude_tracking import tracking_fields, snapshot_tracking


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(_protocol='a579', sequence=42, flags=15,
                        target_roll_cdeg=725, target_pitch_cdeg=-850,
                        target_yaw_rate_cdeg_s=1234, gz_corrected=-164)

    def test_signed_reported_targets_and_body_rate_have_distinct_units(self):
        values = tracking_fields(self.row, 0xb0b0)
        self.assertEqual(values, dict(roll_sp_deg=7.25, pitch_sp_deg=-8.5,
                                     yaw_rate_sp_dps=12.34, yaw_rate_dps=-10))

    def test_unknown_firmware_protocol_missing_values_and_invalid_flags_stay_null(self):
        for row, build in [(self.row, None), (self.row, 0xb0ac),
                           ({**self.row, '_protocol': 'a582'}, 0xb0b0),
                           ({'_protocol': 'a579', 'flags': 15}, 0xb0b0)]:
            self.assertTrue(all(v is None for v in tracking_fields(row, build).values()))
        value = tracking_fields({**self.row, 'flags': 0}, 0xb0b0)
        self.assertTrue(all(v is None for v in value.values()))

    def test_snapshot_requires_current_primary_and_paired_firmware_identity(self):
        snapshot = dict(fresh=True, flight_info_fresh=True, sequence=42,
                        flight_info=dict(build_id=0xb0b0, sequence=42))
        self.assertEqual(snapshot_tracking(snapshot, self.row)['roll_sp_deg'], 7.25)
        for modified in [{**snapshot, 'fresh': False}, {**snapshot, 'sequence': 43},
                         {**snapshot, 'flight_info_fresh': False},
                         {**snapshot, 'flight_info': dict(build_id=0xb0b0, sequence=40)}]:
            self.assertTrue(all(v is None for v in snapshot_tracking(modified, self.row).values()))


if __name__ == '__main__':
    unittest.main()
