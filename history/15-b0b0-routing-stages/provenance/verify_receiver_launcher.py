"""Pure guard checks; never execute launcher main, serial I/O or subprocesses."""
import copy
import start_receivers as m
import install_sram as installer

s = dict(fresh=True, flight_info_fresh=True, flight_info=dict(build_id=0xB0AF),
         receiver_profile=m.PROFILE, serial_writes=False,
         recording=dict(source=dict(port='COM23', baud=115200, source='USB')),
         data=dict(armed=False, controller_enabled=False, physical_output_active=False,
                   command_us=[1000]*4, pwm_us=[1000]*4))
assert m.ready(s, 'COM23', 'USB')
for field in ['armed', 'controller_enabled']:
    for value in [None, True]:
        t = copy.deepcopy(s); t['data'][field] = value
        assert not m.stopped(t)
    t = copy.deepcopy(s); del t['data'][field]
    assert not m.stopped(t)
for field, value in [('serial_writes', True), ('serial_writes', None), ('fresh', False),
                     ('recording', None), ('flight_info', None)]:
    t = copy.deepcopy(s); t[field] = value
    assert not m.ready(t, 'COM23', 'USB')
for field, value in [('port', 'COM25'), ('baud', 57600), ('source', 'SiK')]:
    t = copy.deepcopy(s); t['recording']['source'][field] = value
    assert not m.ready(t, 'COM23', 'USB')
t = copy.deepcopy(s); t['flight_info']['build_id'] = 0xB0AC
assert m.ready(t, 'COM23', 'USB')
t['flight_info']['build_id'] = 0xB0A6
assert not m.ready(t, 'COM23', 'USB')
t['flight_info']['build_id'] = 0xB0B0
assert m.ready(t, 'COM23', 'USB')
def rejects(function, *args):
    try: function(*args)
    except ValueError: return
    raise AssertionError('Unsafe state accepted')

s['status'] = 'live'
s['data']['rc_us'] = [1500, 1500, 1000, 1500, 1000, 1500, 1000]
for build in (0xB0AC, 0xB0AF):
    t = copy.deepcopy(s); t['flight_info']['build_id'] = build
    assert installer.capture_predecessor(t) == build
    installer.predecessor_identity('0x0001481B 0x%08X' % build, build)
    other = 0xB0AF if build == 0xB0AC else 0xB0AC
    rejects(installer.predecessor_identity, '0x0001481B 0x%08X' % other, build)
    rejects(installer.stopped, t, other)
    for field in ['armed', 'controller_enabled', 'physical_output_active', 'pwm_us', 'command_us', 'rc_us']:
        missing = copy.deepcopy(t); del missing['data'][field]
        rejects(installer.capture_predecessor, missing)
    for field in ['status', 'fresh', 'flight_info_fresh', 'flight_info', 'receiver_profile', 'serial_writes']:
        missing = copy.deepcopy(t); del missing[field]
        rejects(installer.capture_predecessor, missing)
for build in (0xB0A6, 0xB0B0, None):
    t = copy.deepcopy(s); t['flight_info']['build_id'] = build
    rejects(installer.capture_predecessor, t)
assert installer.IMAGE_SHA == 'PENDING_OFFLINE_VERIFIED_BITSTREAM'
assert installer.RELEASE == installer.BASE
print('PASS pure launcher stopped/readiness guards; no services or hardware accessed')
