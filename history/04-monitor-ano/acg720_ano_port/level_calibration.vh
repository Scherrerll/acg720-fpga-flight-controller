`ifndef ANO_LEVEL_CALIBRATION_VH
`define ANO_LEVEL_CALIBRATION_VH
// Proper sensor-frame mounting rotation, Q24. Identity until a measured,
// stopped-aircraft calibration is compiled, installed and verified.
`define LEVEL_TRIM_ENABLE 0
`define LEVEL_R00_Q24 16777216
`define LEVEL_R01_Q24 0
`define LEVEL_R02_Q24 0
`define LEVEL_R10_Q24 0
`define LEVEL_R11_Q24 16777216
`define LEVEL_R12_Q24 0
`define LEVEL_R20_Q24 0
`define LEVEL_R21_Q24 0
`define LEVEL_R22_Q24 16777216
`endif
