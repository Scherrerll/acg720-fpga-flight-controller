from test_tools import *
names=['core/flight_core.v','core/height_loss_fallback.v','core/ano_flight_state.v','core/control_gate.v','core/motor_pwm.v',
 'core/rtl/quad_mixer_feedback.v','core/rtl/ano_rate_control.v','core/rtl/ano_yaw_control.v','core/rtl/pid_divide_signed64.v',
 'core/rtl/ano_rc_angle_targets.v','core/rtl/ano_manual_angles.v','position/ano_xy_divide36.v','position/ano_xy_stick.v']
simulate('nominal_core_equivalence',[FIX/n for n in names]+[ROOT/'reference/flight_core_b0ae.v',ROOT/'tests/external_models.v'],ROOT/'tests/nominal_core_equivalence.v')
