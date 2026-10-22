"""BMI088 stopped-image viewer. Serial reads only; calibration is disabled.

Uses the existing dashboard display and authoritative BMI088 packet decoder.
It never imports FirmwareCalibration, opens a programmer, or loads prior IMU
calibration records. Run this only after the hardware capture releases COM23.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
VIEWER_DIR = HERE
DECODER_PATH = HERE / 'monitor_control.py'
DISABLED_CALIBRATION_STORE = HERE / 'NO_CALIBRATION'
PROGRAM_LABEL = "BMI088 适配诊断 · 四路 1000 μs 停机锁定 · 只读监控"

# Load an isolated module, without calling its live main() or application worker.
# Its imports require its own directory; no source file is changed.
if str(VIEWER_DIR) not in sys.path:
    sys.path.insert(0, str(VIEWER_DIR))
_spec = importlib.util.spec_from_file_location("bmi_readonly_viewer", VIEWER_DIR / "server.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load the existing dashboard viewer")
viewer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(viewer)
CalibrationError = viewer.CalibrationError


class ReadOnlyCalibration:
    """Frontend-compatible disabled status; no file reads/writes or callbacks."""

    def __init__(self, store_path, **_):
        self.path = Path(store_path)
        self.applied_fact = None
        self.receipt_provider = None
        # Disabled export calibration never inspects local files.

    def connection(self, connected):
        pass

    def observe(self, row, received):
        pass

    def status(self):
        # Re-check on both /api/state and /api/calibration/status. A long-lived
        # viewer must not keep a previous firmware's zero-check receipt after
        # the stopped SRAM image or measured reference has been replaced.
        if self.receipt_provider is not None:
            self.applied_fact = self.receipt_provider()
        message = "BMI088 当前仅显示数据，水平参考采集、应用和取消均已禁用。当前镜像没有匹配的水平零点验收记录，不能用旧镜像的检查结果代替。"
        result = {"state": "idle", "applied": False, "message": message,
                "application_enabled": False, "guard": False, "eligible": False,
                "eligibility_reason": message, "apply_available": False,
                "apply_readiness_reason": message, "can_capture": False,
                "can_apply": False, "can_cancel": False,
                "requires_usb_programmer": False, "restarts_fpga": False,
                "sample_count": 0, "collected_seconds": 0, "read_only": True}
        if self.applied_fact:
            result.update(state="applied", applied=True,
                          message="BMI088 水平安装参考已写入 FPGA 并实测验证；当前网页保持只读监控。",
                          measured_mean_cdeg=self.applied_fact["mean_body_cdeg"],
                          application_result={"firmware_sha256": self.applied_fact["bitstream_sha256"]})
        return result

    @staticmethod
    def _blocked():
        raise CalibrationError("read_only", "BMI088 当前为只读换装验证，校准操作已禁用", 409)

    def begin(self, *_):
        self._blocked()

    def apply(self, *_):
        self._blocked()

    def cancel(self):
        self._blocked()


# Dashboard's constructor now receives this read-only object from the outset;
# even transient loading of its original level_calibration.json is impossible.
viewer.LevelCalibration = ReadOnlyCalibration


class BmiDashboard(viewer.Dashboard):
    def __init__(self, port="offline", no_serial=True, clock=time.monotonic,
                 calibration_store=DISABLED_CALIBRATION_STORE):
        super().__init__(port=port, demo=False, no_serial=no_serial, clock=clock,
                         calibration_store=calibration_store, apply_callback=None)
        self._calibration_receipt_enabled = not no_serial
        self.calibration.receipt_provider = self._current_level_application

    def _current_level_application(self):
        return None  # Export never loads machine-local calibration receipts.

    def snapshot(self):
        result = super().snapshot()
        result.update(imu_model="BMI088", read_only=True, serial_writes=False,
                      calibration_application_enabled=False,
                      program_label=PROGRAM_LABEL, motor_stop_lock_expected=True)
        if result["data"] is not None:
            result["data"]["program_label"] = PROGRAM_LABEL
            result["motor_stop_lock_observed"] = (
                result["data"]["pwm_us"] == [1000] * 4 and
                result["data"]["command_us"] == [1000] * 4 and
                not result["data"]["physical_output_active"] and
                not result["data"]["armed"] and
                not result["data"]["controller_enabled"] and
                not result["data"]["command_fresh"])
        else:
            result["motor_stop_lock_observed"] = None
        # Expose the same decoded primary epoch for direction/bias diagnostics.
        # These are filtered, bias-corrected BODY counts, not native die data.
        with self.lock:
            row = dict(self.latest_primary_row) if self.latest_primary_row else None
        result["gyro_body_counts"] = None
        if result["fresh"] and row and row.get("sequence") == result.get("sequence"):
            result["gyro_body_counts"] = [row.get(name) for name in
                                          ("gx_corrected", "gy_corrected", "gz_corrected")]
        result["gyro_counts_per_dps"] = 16.4
        return result


def make_receiver():
    decoder = viewer.load_decoder(DECODER_PATH)

    class BmiOnlyDecoder:
        HEADER, SIZE = decoder.HEADER, decoder.SIZE
        ACCEL_DECODER = decoder.ACCEL_DECODER
        RANGE_DECODER = decoder.RANGE_DECODER

        @staticmethod
        def decode(packet):
            row = decoder.decode(packet)
            if row.get("who") == 0x47:
                raise ValueError("Legacy ICM42688 identity is not BMI088 telemetry")
            return row

    receiver = viewer.PacketReceiver([BmiOnlyDecoder])
    if set(receiver.protocols) != {decoder.HEADER, b"\xa5\x7a", b"\xa5\x7b"}:
        raise ValueError("Only the current BMI088 primary, A57A and A57B protocols are allowed")
    return receiver

