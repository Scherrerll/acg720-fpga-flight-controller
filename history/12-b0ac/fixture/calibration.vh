// Keep mask0 until physical measurements are recorded. Never infer coefficients.
// bits0..5: optical scale, optical axes, rotation compensation, range units,
// mounting geometry, relative-yaw alignment. bits6..7: control gains and collective mapping.
`define FLIGHT_CAL_MASK 8'h00
`define FLOW_XX_Q20 0
`define FLOW_XY_Q20 0
`define FLOW_YX_Q20 0
`define FLOW_YY_Q20 0
`define ROT_XX_Q20 0
`define ROT_XY_Q20 0
`define ROT_XZ_Q20 0
`define ROT_YX_Q20 0
`define ROT_YY_Q20 0
`define ROT_YZ_Q20 0
