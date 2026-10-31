# 中文注释索引

本包逐个补齐自写源码。端口名、参数名、协议名、寄存器常量、综合指令和高云工程格式保留原文。

| 文件 | 类别 | 中文注释段数 | 模块 |
|---|---|---:|---|
| [acg720_ano_port.cst](source_cn/acg720_ano_port.cst) | 约束配置（语法与命令保留） | 2 | — |
| [acg720_ano_port.gprj](source_cn/acg720_ano_port.gprj) | 高云工程配置（原样保留） | 0 | — |
| [acg720_ano_port.sdc](source_cn/acg720_ano_port.sdc) | 约束配置（语法与命令保留） | 2 | — |
| [acg720_ano_port.v](source_cn/acg720_ano_port.v) | 自写源码 | 60 | acg720_ano_port、nav_control_handoff |
| [build.tcl](source_cn/build.tcl) | 自写源码 | 5 | — |
| [calibration.vh](source_cn/calibration.vh) | 自写源码 | 4 | — |
| [core/ano_attitude_estimator.v](source_cn/core/ano_attitude_estimator.v) | 自写源码 | 106 | ano_attitude_estimator、ano_attitude_mul32、ano_attitude_div64、ano_attitude_sqrt64 |
| [core/ano_flight_state.v](source_cn/core/ano_flight_state.v) | 自写源码 | 14 | ano_flight_state |
| [core/bmi088_reader.v](source_cn/core/bmi088_reader.v) | 自写源码 | 23 | bmi088_reader |
| [core/control_gate.v](source_cn/core/control_gate.v) | 自写源码 | 33 | control_gate |
| [core/cordic_atan2.v](source_cn/core/cordic_atan2.v) | 自写源码 | 8 | cordic_atan2 |
| [core/flight_core.v](source_cn/core/flight_core.v) | 自写源码 | 129 | flight_core |
| [core/height_loss_fallback.v](source_cn/core/height_loss_fallback.v) | 自写源码 | 16 | height_loss_fallback |
| [core/imu_checked_guard_pipelined.v](source_cn/core/imu_checked_guard_pipelined.v) | 自写源码 | 25 | imu_checked_guard_pipelined |
| [core/imu_diagnostic_tap.v](source_cn/core/imu_diagnostic_tap.v) | 自写源码 | 12 | imu_diagnostic_tap |
| [core/imu_pipeline_pipelined.v](source_cn/core/imu_pipeline_pipelined.v) | 自写源码 | 18 | imu_pipeline |
| [core/imu_temporal_check_pipelined.v](source_cn/core/imu_temporal_check_pipelined.v) | 自写源码 | 16 | imu_temporal_check |
| [core/motor_pwm.v](source_cn/core/motor_pwm.v) | 自写源码 | 19 | motor_pwm |
| [core/rc_ppm.v](source_cn/core/rc_ppm.v) | 自写源码 | 27 | rc_ppm |
| [core/rtl/ano_manual_angles.v](source_cn/core/rtl/ano_manual_angles.v) | 自写源码 | 17 | ano_manual_angles |
| [core/rtl/ano_rate_control.v](source_cn/core/rtl/ano_rate_control.v) | 自写源码 | 42 | ano_rate_control、ano_multiply_signed64_32 |
| [core/rtl/ano_rc_angle_targets.v](source_cn/core/rtl/ano_rc_angle_targets.v) | 自写源码 | 31 | ano_rc_angle_targets、ano_rc_sqrt50 |
| [core/rtl/ano_yaw_control.v](source_cn/core/rtl/ano_yaw_control.v) | 自写源码 | 21 | ano_yaw_control |
| [core/rtl/pid_divide_signed64.v](source_cn/core/rtl/pid_divide_signed64.v) | 自写源码 | 9 | pid_divide_signed64 |
| [core/rtl/quad_mixer_feedback.v](source_cn/core/rtl/quad_mixer_feedback.v) | 自写源码 | 7 | quad_mixer_feedback |
| [core/spi_uart_modules.v](source_cn/core/spi_uart_modules.v) | 自写源码 | 15 | spi_mode3_master_1mhz、uart_tx_115200 |
| [gw5_snapshot_bram.v](source_cn/gw5_snapshot_bram.v) | 自写源码 | 6 | gw5_snapshot_bram |
| [level_calibration.vh](source_cn/level_calibration.vh) | 自写源码 | 3 | — |
| [mtf_navigation_shadow.v](source_cn/mtf_navigation_shadow.v) | 自写源码 | 13 | mtf_navigation_shadow |
| [mtf_xyz_navigation_control.v](source_cn/mtf_xyz_navigation_control.v) | 自写源码 | 82 | mtf_xyz_navigation_control |
| [nav_math_service.v](source_cn/nav_math_service.v) | 自写源码 | 12 | nav_math_service |
| [position/ano_flow_fusion.v](source_cn/position/ano_flow_fusion.v) | 自写源码 | 24 | ano_flow_fusion |
| [position/ano_height_fusion.v](source_cn/position/ano_height_fusion.v) | 自写源码 | 42 | ano_height_fusion |
| [position/ano_hold_control.v](source_cn/position/ano_hold_control.v) | 自写源码 | 43 | ano_hold_control |
| [position/ano_xy_divide36.v](source_cn/position/ano_xy_divide36.v) | 自写源码 | 6 | ano_xy_divide36 |
| [position/ano_xy_stick.v](source_cn/position/ano_xy_stick.v) | 自写源码 | 11 | ano_xy_stick |
| [position/ano_z_stick.v](source_cn/position/ano_z_stick.v) | 自写源码 | 12 | ano_z_stick |
| [position/mtf_position_integrator.v](source_cn/position/mtf_position_integrator.v) | 自写源码 | 26 | mtf_position_integrator、mtf_position_divide_constant |
| [position/mtf_shared_flow_fusion.v](source_cn/position/mtf_shared_flow_fusion.v) | 自写源码 | 25 | mtf_shared_flow_fusion |
| [position/mtf_shared_height_fusion.v](source_cn/position/mtf_shared_height_fusion.v) | 自写源码 | 47 | mtf_shared_height_fusion |
| [position/mtf_shared_hold_control.v](source_cn/position/mtf_shared_hold_control.v) | 自写源码 | 45 | mtf_shared_hold_control |
| [position/mtf_xyz_hold_control.v](source_cn/position/mtf_xyz_hold_control.v) | 自写源码 | 90 | mtf_xyz_hold_control |
| [position/pose_time_adapter.v](source_cn/position/pose_time_adapter.v) | 自写源码 | 7 | pose_time_adapter |
| [position/position_math.v](source_cn/position/position_math.v) | 自写源码 | 21 | position_multiply、position_gyro_increment、position_divide、position_sincos |
| [position/relative_position.v](source_cn/position/relative_position.v) | 自写源码 | 36 | relative_position |
| [sensor/flow_reader.v](source_cn/sensor/flow_reader.v) | 自写源码 | 28 | flow_reader、pmw3901_spi_mode3 |
| [sensor/mtf01p_reader.v](source_cn/sensor/mtf01p_reader.v) | 自写源码 | 57 | mtf_uart_rx、micolink_parser、mtf_metric_observer、mtf01p_reader |
| [sensor/mtf_native_geometry.v](source_cn/sensor/mtf_native_geometry.v) | 自写源码 | 38 | mtf_native_geometry、mtf_divide100 |
| [sensor/mtf_shared_geometry.v](source_cn/sensor/mtf_shared_geometry.v) | 自写源码 | 43 | mtf_shared_geometry |
| [sensor/pmw3901_init.vh](source_cn/sensor/pmw3901_init.vh) | 自写源码 | 7 | — |
| [sensor/range_height_estimate.v](source_cn/sensor/range_height_estimate.v) | 自写源码 | 19 | range_height_estimate |
| [sensor/range_reader.v](source_cn/sensor/range_reader.v) | 自写源码 | 26 | range_reader、range_frame_parser、range_uart_rx_115200 |
| [sik_imu_diagnostic.v](source_cn/sik_imu_diagnostic.v) | 自写源码 | 9 | sik_imu_diagnostic |
| [telemetry_tx.v](source_cn/telemetry_tx.v) | 自写源码 | 19 | telemetry_tx |
| [water_drive_control.v](source_cn/water_drive_control.v) | 自写源码 | 33 | water_drive_control |
| [water_pwm_pair.v](source_cn/water_pwm_pair.v) | 自写源码 | 23 | water_pwm_pair |
| [xy_pi_parameters.v](source_cn/xy_pi_parameters.v) | 自写源码 | 28 | xy_pi_parameters、xy_pi_uart_rx |

参数工具 [tools/xy_pi_cli.py](xy_pi_cli_cn.py) 的模块说明与算法注释使用中文；命令参数名称保持兼容。

完整性与注释逻辑核对结果见 [COMMENT_AUDIT.json](COMMENT_AUDIT_CN.json)。
