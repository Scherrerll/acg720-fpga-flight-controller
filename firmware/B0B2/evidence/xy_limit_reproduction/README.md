# XY 25° target versus 15° optical qualification: offline evidence

Both simulations completed normally with VVP exit code 0. They compile the frozen B0B2 RTL without modifying source, tools or committed tests. `result.json` and `controller_result.json` bind all 53 source-file hashes, bench hashes and logs; before/after source maps match. No device, serial, state API or programmer access occurred.

## Actual asserted results

| Test | Actual result |
| --- | --- |
| Controller input −1200 mm/s Q16, centered sticks, yaw/acceleration zero, real 50MHz and 20ms XY callbacks | roll target 0, pitch target −1810 cdeg, ix=655360 Q16 (=10 cdeg); XY/Z active |
| Next controller callback at −2000 mm/s | pitch target −2500 cdeg, ix=1310720 Q16 (=20 cdeg); XY/Z active |
| Full navigation with measured roll/pitch zero | target pitch −1848 cdeg while geometry and XY/Z remain eligible |
| Live roll 1500 → 1501 cdeg | 1500 remains eligible; 1501 immediately withdraws XY with reason4 while Z and height remain active |
| Loss held for 20ms | velocity-fusion integrals/output reset; completed controller ix/iy and acceleration LPF state remain unchanged (ix=2203189 Q16, approximately33.618 cdeg) |
| Roll returns to1499 but no new MTF sample | geometry flow and XY stay invalid; Z remains active |
| Fresh MTF callbacks resume, CH7 continuously high | XY/Z recover without switch acknowledgement; saved controller ix equals the pre-loss value at the first recovery callback; recovered target pitch−308 cdeg |
| origin_reset | controller XY integrals clear and XY/Z withdraw |

The first two cases directly supply controller-input velocity. They are not raw MTF readings and do not model aircraft dynamics. The full-navigation test uses a deliberately large synthetic native velocity of −9000mm/s only to excite the chain quickly. It does not quantify either flight's velocity or required correction. This lies within the geometry's ±10000mm/s numeric eligibility and its `geometry_flow_ready` assertion proves those bounds passed. Reader quality scores are outside the bench: upstream range_valid and flow_valid are synthetic true inputs. No forces or weakened qualification are used.

The full-navigation log's `t_ns` label is misleading: Verilog `%t` prints at the 1ps precision. Thus100129461000 corresponds to100.129461ms and160129461000 to160.129461ms. These are simulation-relative times, not flight timestamps.

## Frozen RTL references

All paths below are under firmware/B0B2/source.

- acg720_ano_port.v:280 enables the actual native controller with PROOF_CONTROLLER=1. mtf_xyz_navigation_control.v:67 selects height4500/flow1500 cdeg; :246 does not override the controller's MAX_ANGLE2500 default.
- position/mtf_xyz_hold_control.v:10 sets2500; :347–350 clips only the completed XY PI output. core/flight_core.v:151–154 and :208–211 bound that consumed target to2500 again. There is no prior1500 target clamp.
- sensor/mtf_shared_geometry.v:43–50 qualifies each measured roll/pitch independently in the inclusive interval[−1500,1500]. This is not a combined tilt norm. :73 masks flow_ready immediately; :173–175 destroys flow_seen/flow_epoch even for a brief invalid excursion. :222–229 requires a new eligible publication.
- mtf_xyz_navigation_control.v:127 ties velocity authority to geometry flow; :270–284 masks public XY separately from Z. position/mtf_shared_flow_fusion.v:75–109 clears its v/iq/aq state on lost flow and :124–129 reestablishes continuity through new callbacks. The20ms position timer is at navigation:189–201.
- The display position epoch clears through position/mtf_position_integrator.v:79–99. It is distinct from XY controller integral state.
- position/mtf_xyz_hold_control.v:303 clears command_seen for XY cancellation; :311–323 rolls an in-progress callback back to saved ix/iy/afx/afy. Completed XY state survives a pure flow-only loss while height/IMU/enable remain healthy. Reset/global cancel/blocked paths at :263–278 clear all those states. The XY integral clip at :337–338 is±1000 cdeg (=±10°), so a retained integral alone does not prove a new target over15°.
- Static-only additional transition detail: core/rtl/ano_manual_angles.v:89–100 shares the last completed OF Loc cache until the next20ms manual Loc callback, then :75–87 publishes through the6ms attitude task. core/flight_core.v:198–211 and :260–267 consume it. Therefore public navigation target zero on withdrawal does not prove every internal target instantaneously zero. This full-core/manual transition was not simulated here.

There is no angular hysteresis or switch-reselection requirement in the demonstrated pure-flow recovery. A returned angle alone is insufficient: fresh geometry/fusion continuity and another XY callback are necessary. This is a conditional source mechanism, not evidence of a sustained physical oscillation.

## Flight and history boundaries

The critical navigation/geometry/fusion/hold/position/manual modules are byte-identical to the frozen B0B0 versions used in the two flights; B0B2 top/core contain added diagnostics, so whole-top equivalence is not claimed here.

`flight_review_20261025_two_trials/timeline_agent/epoch3_primary_joined.csv` lines300–302 (seq465–467) show the second flight:

- seq465 uptime93200ms, sticksCH1/CH2=1500/1500, measured6.89°/−4.82°, target18.37°/−17.14°, XY active/reason0.
- seq466 uptime93400ms, measured19.32°/−15.84°, target0/0, XY inactive/reason4; Z remains active, native flow/range flags valid, source age3ms, quality99, fusion velocity/display position are zero. Controller/yaw faults are still zero.
- seq467 later reports IMU/controller faults and an armed-health revoke. Those are a subsequent failure path; the angle/flow mechanism does not establish their physical root cause.
- seq470 (line305) restores velocity/position numerical readiness, but XY remains inactive/reason2 because the aircraft is no longer enabled. There is no logged airborne automatic XY re-entry proof.

The first trial's measured/target angles remain below15°. Neither flight sampled an actual±25° saturation. The200ms snapshots do not expose controller integrals or the6/20ms target-cache transition. The log supports a second-flight target>15° followed by measured-bound exit; it does not establish a complete autonomous oscillation, integral reset, or the primary reason for physical drift/IMU failure.

`firmware/B0B1/evidence/b0ac_to_b0b0.json` lines174–175 records MAX_ANGLE changing from1200 to2500. The older B0AC geometry at routing_rescue_20261015/mtf01p_b0ac_preserve_fsm/fixture/sensor/mtf_shared_geometry.v:37 already used±1500. The later target increase removed that prior target-versus-qualification margin; it is historical parameter evidence, not proof of flight causation.

Relevant logs: simulation.log, controller_simulation.log. Benches: xy_limit_tb.v, controller_limits_tb.v. The existing B0AE navigation_control.v/control_races.v supplied their interfaces and callback schedule. Any future fix should first choose an explicit target-versus-observer eligibility policy and test the exact boundary/recovery transitions above; this investigation changes no gains, geometry limits or architecture.
