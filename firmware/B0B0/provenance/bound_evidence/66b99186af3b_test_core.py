from test_tools import *
model=Path(json.loads((ROOT/'baseline.json').read_text())['parent']).parent/'b0ac_algorithm_review_20261020T090039Z/external_producer_models.v'
names=['core/flight_core.v','core/ano_flight_state.v','core/control_gate.v','core/motor_pwm.v',
 'core/rtl/quad_mixer_feedback.v','core/rtl/ano_rate_control.v','core/rtl/ano_yaw_control.v',
 'core/rtl/pid_divide_signed64.v','core/rtl/ano_rc_angle_targets.v','core/rtl/ano_manual_angles.v','position/ano_xy_divide36.v']
print(simulate('core_control',[FIX/n for n in names]+[model],ROOT/'tests/core_control.v'))
