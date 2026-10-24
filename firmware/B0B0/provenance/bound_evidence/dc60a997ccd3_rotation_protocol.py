"""A583: coherent host-receipt pair, never an exposure-synchronized integral."""
import binascii
import struct

FORMAT = ">BBHIIHI5iHH"
KEYS = ("version", "pair_flags", "pair_sequence", "received_uptime_ms",
        "distance_mm", "dt_ms", "pose_age_ticks", "vx_x100", "vy_x100",
        "gx_counts_q12", "gy_counts_q12", "gz_counts_q12", "reserved", "pickup_us")
assert struct.calcsize(FORMAT) == 42

def decode_rotation(packet):
    if len(packet) != 48 or packet[:2] != b"\xa5\x83":
        raise ValueError("A583 size/header")
    if binascii.crc_hqx(packet[2:-2], 0xffff) != int.from_bytes(packet[-2:], "big"):
        raise ValueError("A583 CRC")
    row = dict(zip(KEYS, struct.unpack(FORMAT, packet[4:-2])))
    if row["version"] != 1 or row["reserved"] or row["pair_flags"] & 0xf0:
        raise ValueError("A583 version/reserved")
    row["sequence"] = int.from_bytes(packet[2:4], "big")
    row["receipt_pair_valid"] = row["pair_flags"] == 15 and row["pose_age_ticks"] < 3000000
    row["exposure_time_aligned"] = False
    row["rotation_compensation_qualified"] = False
    # Q12 is fractional COUNTS in the protected 16.4 counts/(degree/s) domain.
    for axis in "xyz":
        row[f"g{axis}_deg_s"] = row[f"g{axis}_counts_q12"] / (4096 * 16.4)
    row["body_forward_mm_s"] = row["vy_x100"] / 100
    row["body_right_mm_s"] = -row["vx_x100"] / 100
    return row
