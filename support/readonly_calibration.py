"""Disabled calibration seam for the portable read-only telemetry viewer.

The real calibration implementation is intentionally not packaged.
"""


class CalibrationError(Exception):
    def __init__(self, code, message, http_status=409):
        super().__init__(message)
        self.code, self.message, self.http_status = code, message, http_status


class LevelCalibration:
    def __init__(self, *_args, **_kwargs):
        pass

    def connection(self, _connected):
        pass

    def observe(self, _row, _received):
        pass

    def status(self):
        return dict(state='idle', applied=False, read_only=True,
                    application_enabled=False, can_capture=False,
                    can_apply=False, can_cancel=False,
                    message='Portable read-only export: calibration disabled')
