"""Navigation observers v1..3 and unqualified experimental control v4."""
import binascii
import struct

FORMAT = '>BBBBQ4I11i3hHBB8s'
KEYS = ('version', 'flags', 'axis_mapping', 'rotation_policy', 'fpga_uptime_ms',
        'navigation_sequence', 'source_age_ms', 'dt_us', 'reason', 'height_mm',
        'body_vx_q16', 'body_vy_q16', 'world_vx_q16', 'world_vy_q16',
        'fused_vx_q16', 'fused_vy_q16', 'fused_height_mm', 'fused_vz_q16',
        'position_x_q8', 'position_y_q8', 'shadow_roll_cdeg', 'shadow_pitch_cdeg',
        'shadow_throttle_delta_us', 'shadow_flags', 'mapping_verified',
        'rotation_verified', 'reserved')
assert struct.calcsize(FORMAT) == 90
FORMAT_V3 = '>BBBBQ4I11i3hHBBHHi'
KEYS_V3 = KEYS[:-1] + ('z_collective_us', 'z_reason', 'target_height_mm')
assert struct.calcsize(FORMAT_V3) == 90
RECEIVER_PROFILE = 'mtf01p.b0b2_timeout_policy.v3'
NAV_BUILD_VERSIONS = {0xb0a8: 1, 0xb0a9: 2, 0xb0aa: 3, 0xb0ab: 4, 0xb0ac: 4, 0xb0ad: 4, 0xb0ae: 5, 0xb0af: 5, 0xb0b0: 5, 0xb0b2: 5}
MTF_BUILD_VERSIONS = {0xb0a7: 1, 0xb0a8: 1, 0xb0a9: 1, 0xb0aa: 1, 0xb0ab: 2, 0xb0ac: 2, 0xb0ad: 2, 0xb0ae: 2, 0xb0af: 2, 0xb0b0: 2, 0xb0b2: 2}
OBSERVER_BUILDS = frozenset((0xb0a7, 0xb0a8, 0xb0a9, 0xb0aa))


def identity_matches(info, navigation):
    return bool(info and NAV_BUILD_VERSIONS.get(info.get('build_id')) == navigation.get('version'))


def mtf_identity_matches(info, mtf):
    if info and info.get('build_id')==0xb0b2 and info.get('version')==5:
        return bool(mtf and mtf.get('version')==3)
    return bool(info and MTF_BUILD_VERSIONS.get(info.get('build_id')) == mtf.get('version'))


def firmware_label(build):
    if build==0xb0b2:
        return 'B0B2 · 动态样本策略修复候选 · 待验收'
    if build==0xb0b0:
        return 'B0B0 · 综合连接修复候选 · 待验收'
    if build==0xb0af:
        return 'B0AF · 测高失效降级候选 · 待验收'
    if build==0xb0ae:
        return 'B0AE · 匿名控制逻辑候选 · 待实物验收'
    if build in (0xb0ab,0xb0ac,0xb0ad):
        return f'{build:04X} · XYZ控制候选 · 实物资格未完成 · DO_NOT_PROGRAM'
    if build in OBSERVER_BUILDS:
        return f'{build:04X} · 停机观察版 · 四路停机'
    return '固件身份未知／过期 · 停机锁资格未确认' if build is None else f'{build:04X} · 停机锁资格未确认'

FIELDS = {
    'nav_height_mm': 'MTF 垂直高度 mm（临时估计）',
    'nav_body_vx_mm_s': 'MTF 机体前向速度 mm/s（方向待验收）',
    'nav_body_vy_mm_s': 'MTF 机体右向速度 mm/s（方向待验收）',
    'nav_world_vx_mm_s': 'MTF 局部X速度 mm/s（未补偿转动）',
    'nav_world_vy_mm_s': 'MTF 局部Y速度 mm/s（未补偿转动）',
    'nav_fused_vx_mm_s': '融合局部X速度 mm/s（观察值）',
    'nav_fused_vy_mm_s': '融合局部Y速度 mm/s（观察值）',
    'nav_fused_height_mm': '融合高度 mm（观察值）',
    'nav_fused_vz_mm_s': '融合垂直速度 mm/s（观察值）',
    'nav_position_x_mm': '局部X积分位置 mm（无绝对参照）',
    'nav_position_y_mm': '局部Y积分位置 mm（无绝对参照）',
    'nav_shadow_roll_deg': '定点横滚指令 °（控制接入按版本）',
    'nav_shadow_pitch_deg': '定点俯仰指令 °（控制接入按版本）',
    'nav_shadow_throttle_delta_us': '定点垂直油门增量 μs（控制接入按版本）',
    'nav_source_age_ms': '导航传感器年龄 ms',
    'nav_position_reason': '位置积分状态原因位（原码）',
    'nav_z_collective_us': 'XYZ定点总油门指令 μs（控制接入按版本）',
    'nav_z_reason': 'XYZ定点垂直控制原因位（原码）',
    'nav_target_height_mm': 'XYZ定点目标高度 mm（观察值）',
}


def decode_nav(packet):
    if len(packet) != 96 or packet[:2] != b'\xa5\x82':
        raise ValueError('A582 size/header')
    if binascii.crc_hqx(packet[2:-2], 0xffff) != int.from_bytes(packet[-2:], 'big'):
        raise ValueError('A582 CRC')
    row = dict(zip(KEYS, struct.unpack(FORMAT, packet[4:-2])))
    tail = row.pop('reserved')
    if row['version'] not in (1, 2, 3, 4, 5):
        raise ValueError('A582 version/reserved')
    xyz = row['version'] in (3, 4)
    control = row['version'] in (4, 5)
    if xyz:
        collective, z_reason, target = struct.unpack('>HHi', tail)
        row.update(z_collective_us=collective, z_reason=z_reason, target_height_mm=target)
        shadow = row['shadow_flags']
        pairs = [(shadow >> shift) & 3 for shift in (0, 2, 4)]
        if any(pair not in (0, 3) for pair in pairs):
            raise ValueError('A582 XYZ qualifications must agree on all axes')
        if row['reason'] & (1 << 17) or not row['reason'] & (1 << 19):
            raise ValueError('A582 XYZ requires enabled Z fusion and incomplete physical qualification')
        if shadow & 0x30:
            # The controller limits its target to the prior valid measured
            # height (0..5000 mm) +/-2000 mm. Target is a signed control
            # setpoint; it can lead the measured height without changing the
            # separate 0..5000 mm sensor eligibility contract.
            if pairs[:2] != [3, 3] or not 1000 <= collective <= 2000 or not -2000 <= target <= 7000:
                raise ValueError('A582 XYZ active collective/target/qualification')
        elif any((collective, target, row['shadow_roll_cdeg'], row['shadow_pitch_cdeg'],
                  row['shadow_throttle_delta_us'])):
            raise ValueError('A582 inactive XYZ commands must be zero')
    elif row['version']==5:
        collective,z_reason,target=struct.unpack('>HHi',tail)
        row.update(z_collective_us=collective,z_reason=z_reason,target_height_mm=target)
        shadow=row['shadow_flags']
        if row['reason'] & (1<<17) or not row['reason'] & (1<<19):raise ValueError('A582 ANO height/qualification contract')
        if shadow & 0x20 and shadow & 0x3b != 0x3b:raise ValueError('A582 ANO XY requires Z-active and XY-ready/requested')
        if shadow & 0x10:
            if not shadow & 1 or not shadow & 4 or not 1000<=collective<=2000 or not -2000<=target<=7000:raise ValueError('A582 ANO Z active qualifications')
        elif any((collective,target,row['shadow_throttle_delta_us'])):raise ValueError('A582 ANO inactive Z command')
        if not shadow & 0x20 and any((row['shadow_roll_cdeg'],row['shadow_pitch_cdeg'])):raise ValueError('A582 ANO inactive XY commands')
    elif any(tail):
        raise ValueError('A582 version/reserved')
    xy_only = row['version'] == 2
    if xy_only and (row['flags'] & 8 or row['shadow_flags'] & 0x15 or
                    row['fused_vz_q16'] != 0 or row['shadow_throttle_delta_us'] != 0):
        raise ValueError('A582 XY-only cannot publish altitude-control qualifications')
    if (row['flags'] & 0xc0) != (0x80 if control else 0x40):
        raise ValueError('A582 versioned control/stop-lock contract')
    if row['axis_mapping'] not in (0, 1) or row['rotation_policy'] != 0:
        raise ValueError('A582 unknown mapping/rotation policy')
    if row['mapping_verified'] not in (0, 1) or row['rotation_verified'] not in (0, 1):
        raise ValueError('A582 qualification flags')
    if control and (row['mapping_verified'] or row['rotation_verified']):
        raise ValueError('A582 experimental physical qualification remains incomplete')
    # All sixteen bits are defined: low six shadow flags, high ten position reasons.
    position_reason = (row['shadow_flags'] >> 6) & 0x3ff
    row.update(sequence=int.from_bytes(packet[2:4], 'big'),
               horizontal_only=xy_only,manual_throttle=xy_only,
               height_fusion_enabled=not xy_only,
               position_hold_includes_height=not xy_only,
               standalone_altitude_mode=row['version'] == 1,
               joint_xyz=xyz,
               xy_control_reason=(row['reason'] >> 20) & 0xfff if row['version'] in (2, 3, 4, 5) else None,
               xy_shadow_active=bool(row['shadow_flags'] & 0x20),
               xyz_requested=bool(row['shadow_flags'] & 8) if row['version']==5 else xyz and bool(row['shadow_flags'] & 0x0c),
               xyz_ready=(xyz or row['version']==5) and (row['shadow_flags'] & 3)==3,
               xyz_active=(xyz or row['version']==5) and (row['shadow_flags'] & 0x30)==0x30,
               ano_control=row['version']==5,vertical_active=bool(row['shadow_flags'] & 0x10),
               nav_position_reason=position_reason,
               shadow_readiness_flags=row['shadow_flags'] & 0x3f,
               module_link_fresh=bool(row['flags'] & 1) and row['source_age_ms'] < 100,
               native_range_fresh=bool(row['flags'] & 1) and row['source_age_ms'] < 100,
               native_height_ready=bool(row['flags'] & 2),
               provisional_world_velocity_ready=bool(row['flags'] & 4),
               height_fusion_ready=bool(row['flags'] & 8),
               velocity_fusion_ready=bool(row['flags'] & 16),
               position_accumulator_ready=bool(row['flags'] & 32) and position_reason == 0,
               physical_motor_stop_lock=not control, control_input=control, flight_ready=False,
               experimental_control=control, installation_qualified=False,
               status_qualified=False, rotation_compensated=False,
               coordinate_frame='provisional_body_and_local_axes',
               position_reference='velocity_integral_only')
    return row


def display_values(row, fresh=True):
    values = dict.fromkeys(FIELDS)
    if not fresh:
        return values
    xyz = row.get('joint_xyz', row.get('version') in (3, 4))
    values['nav_source_age_ms'] = row['source_age_ms']
    values['nav_position_reason'] = row['nav_position_reason']
    if xyz:
        values['nav_z_reason'] = row['z_reason']
    if not row['module_link_fresh']:
        return values
    if row['native_height_ready']:
        values['nav_height_mm'] = row['height_mm']
    if row['axis_mapping'] == 1 and row['provisional_world_velocity_ready']:
        for frame in ('body', 'world'):
            for axis in ('x', 'y'):
                values[f'nav_{frame}_v{axis}_mm_s'] = row[f'{frame}_v{axis}_q16'] / 65536
    if row['height_fusion_ready']:
        values['nav_fused_height_mm'] = row['fused_height_mm']
        values['nav_fused_vz_mm_s'] = row['fused_vz_q16'] / 65536
    if row['axis_mapping'] == 1 and row['velocity_fusion_ready']:
        for axis in ('x', 'y'):
            values[f'nav_fused_v{axis}_mm_s'] = row[f'fused_v{axis}_q16'] / 65536
    if row['axis_mapping'] == 1 and row['position_accumulator_ready']:
        for axis in ('x', 'y'):
            values[f'nav_position_{axis}_mm'] = row[f'position_{axis}_q8'] / 256
    commands_visible = not xyz or row.get('xyz_active', bool(row['shadow_flags'] & 0x30))
    if commands_visible and row['shadow_readiness_flags'] & 2 and row['axis_mapping'] == 1 and (row['position_accumulator_ready'] or row.get('ano_control')):
        values['nav_shadow_roll_deg'] = row['shadow_roll_cdeg'] / 100
        values['nav_shadow_pitch_deg'] = row['shadow_pitch_cdeg'] / 100
    if commands_visible and row['shadow_readiness_flags'] & 1 and row['height_fusion_ready']:
        values['nav_shadow_throttle_delta_us'] = row['shadow_throttle_delta_us']
        if xyz and row['axis_mapping'] == 1 and row['position_accumulator_ready']:
            values['nav_z_collective_us'] = row['z_collective_us']
            values['nav_target_height_mm'] = row['target_height_mm']
    if row.get('ano_control') and row.get('vertical_active') and row['height_fusion_ready']:
        values['nav_z_reason']=row['z_reason'];values['nav_z_collective_us']=row['z_collective_us'];values['nav_target_height_mm']=row['target_height_mm']
    return values
