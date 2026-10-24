from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent;FIX=ROOT/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 b=json.loads((ROOT/'baseline.json').read_text())
 allowed={'acg720_ano_port.v','core/flight_core.v','core/rtl/ano_rate_control.v',
 'position/ano_z_stick.v','position/mtf_xyz_hold_control.v','mtf_xyz_navigation_control.v','sensor/mtf_shared_geometry.v',
 'core/motor_pwm.v','acg720_ano_port.gprj','build.tcl','build_project.py'}
 for n,h in b['baseline_sources'].items():
  if n not in allowed and sha(FIX/n)!=h:raise ValueError('Protected hardware/math source changed: '+n)
 for n,h in b['original_sources'].items():
  if sha(ROOT/'reference'/Path(n).name)!=h:raise ValueError('Original ANO source changed: '+n)
 parent=Path(b['parent'])
 if sha(parent/'offline_release.json')!=b['parent_offline_release_sha256'] or sha(parent/'fixture/impl/pnr/acg720_ano_port.fs')!=b['parent_bitstream_sha256']:raise ValueError('Rollback baseline changed')
 s=(FIX/'core/motor_pwm.v').read_text()
 if s.count('ticks4<=EXTERNAL_TICKS ?pre_ticks4:(clamp(m4_us)*TICKS_PER_US);')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('ticks4<=EXTERNAL_TICKS ?pre_ticks4:(clamp(m4_us)*TICKS_PER_US);','ticks4<=clamp(m4_us)*TICKS_PER_US;')
 if s.count('ticks3<=EXTERNAL_TICKS ?pre_ticks3:(clamp(m3_us)*TICKS_PER_US);')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('ticks3<=EXTERNAL_TICKS ?pre_ticks3:(clamp(m3_us)*TICKS_PER_US);','ticks3<=clamp(m3_us)*TICKS_PER_US;')
 if s.count('ticks2<=EXTERNAL_TICKS ?pre_ticks2:(clamp(m2_us)*TICKS_PER_US);')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('ticks2<=EXTERNAL_TICKS ?pre_ticks2:(clamp(m2_us)*TICKS_PER_US);','ticks2<=clamp(m2_us)*TICKS_PER_US;')
 if s.count('ticks1<=EXTERNAL_TICKS ?pre_ticks1:(clamp(m1_us)*TICKS_PER_US);')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('ticks1<=EXTERNAL_TICKS ?pre_ticks1:(clamp(m1_us)*TICKS_PER_US);','ticks1<=clamp(m1_us)*TICKS_PER_US;')
 if s.count('    input wire [15:0] m1_us,m2_us,m3_us,m4_us,\n    input wire [31:0] pre_ticks1,pre_ticks2,pre_ticks3,pre_ticks4,')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('    input wire [15:0] m1_us,m2_us,m3_us,m4_us,\n    input wire [31:0] pre_ticks1,pre_ticks2,pre_ticks3,pre_ticks4,','    input wire [15:0] m1_us,m2_us,m3_us,m4_us,')
 if s.count('parameter integer MAX_US=1150,\n    parameter integer EXTERNAL_TICKS=0')!=1:raise ValueError("Unexpected PWM conversion wrapper")
 s=s.replace('parameter integer MAX_US=1150,\n    parameter integer EXTERNAL_TICKS=0','parameter integer MAX_US=1150')
 if s!=(parent/'fixture/core/motor_pwm.v').read_text():raise ValueError('PWM frame/stop math changed')
 # Exact reversible edits prove Q12/Q24/rate arithmetic wasn't rewritten.
 s=(FIX/'core/rtl/ano_rate_control.v').read_text()
 s=s.replace('input wire clk,rst_n,sample_update,enabled,auto_takeoff,','input wire clk,rst_n,sample_update,enabled,').replace('reg history_seeded=0;reg held_auto_takeoff=0;','reg history_seeded=0;').replace('held_auto_takeoff<=auto_takeoff;held_dt<=dt_ticks;','held_dt<=dt_ticks;').replace('ki<=held_auto_takeoff ?0:ROLL_KI_MILLI;','ki<=ROLL_KI_MILLI;').replace('ki<=held_auto_takeoff ?0:PITCH_KI_MILLI;','ki<=PITCH_KI_MILLI;')
 if s!=(parent/'fixture/core/rtl/ano_rate_control.v').read_text():raise ValueError('Unexpected rate arithmetic delta')
 # Geometry math/cancellation remain exact; only separate qualified tilt
 # bounds are configurable to avoid dropping Z at the old XY15deg boundary.
 s=(FIX/'sensor/mtf_shared_geometry.v').read_text()
 s=s.replace(' parameter integer HEIGHT_TILT_LIMIT_CDEG=1500,FLOW_TILT_LIMIT_CDEG=1500,\n','')
 s=s.replace('roll_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && roll_cdeg<=HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg>=-HEIGHT_TILT_LIMIT_CDEG && pitch_cdeg<=HEIGHT_TILT_LIMIT_CDEG &&','roll_cdeg>=-1500 && roll_cdeg<=1500 && pitch_cdeg>=-1500 && pitch_cdeg<=1500 &&')
 s=s.replace(' wire flow_pose_ok=roll_cdeg>=-FLOW_TILT_LIMIT_CDEG && roll_cdeg<=FLOW_TILT_LIMIT_CDEG &&\n  pitch_cdeg>=-FLOW_TILT_LIMIT_CDEG && pitch_cdeg<=FLOW_TILT_LIMIT_CDEG;\n','')
 s=s.replace('flow_valid && flow_pose_ok && range_ok','flow_valid && range_ok')
 s=s.replace('   HEIGHT_TILT_LIMIT_CDEG<1 || HEIGHT_TILT_LIMIT_CDEG>4500 || FLOW_TILT_LIMIT_CDEG<1 || FLOW_TILT_LIMIT_CDEG>HEIGHT_TILT_LIMIT_CDEG ||\n','')
 if s!=(parent/'fixture/sensor/mtf_shared_geometry.v').read_text():raise ValueError('Unexpected geometry arithmetic delta')
 top=(FIX/'acg720_ano_port.v').read_text();core=(FIX/'core/flight_core.v').read_text();hold=(FIX/'position/mtf_xyz_hold_control.v').read_text()
 for token in ['.hold_active(xyz_joint_active),.altitude_active(z_handoff_active)', '.enabled(armed),.taking_off(taking_off)',"32'h0000B0AE"]:
  if token not in top:raise ValueError('Missing control path: '+token)
 for forbidden in ['throttle_takeover #','function [15:0] throttle_target','mapped_throttle=']:
  if forbidden in core:raise ValueError('Obsolete manual-PWM policy: '+forbidden)
 for forbidden in ['throttle_centered','!centered','position_ex*POSITION_KP_Q16']:
  if forbidden in hold:raise ValueError('Obsolete mode/position gate: '+forbidden)
 if 'auto_phase' not in hold or 'bias+value' not in hold:raise ValueError('Missing original takeoff/bias path')
 if 'ano_manual_angles manual_angles' not in core or 'ano_rc_angle_targets manual_angles' in core:raise ValueError('Manual branch must reuse Flight_State_Task stick pair')
 if top.count('.pilot_norm_x(pilot_norm_x)')!=2:raise ValueError('Shared pilot stick pair must connect navigation and core')
 if not (ROOT/'DO_NOT_PROGRAM').is_file():raise ValueError('Offline hardware lock marker missing')
 return True
if __name__=='__main__':print('Control source contract',verify())
