// 编译期安装微调配置：旋转矩阵各项使用 Q24，启用位与矩阵常量保持原值。
`ifndef ANO_LEVEL_CALIBRATION_VH
`define ANO_LEVEL_CALIBRATION_VH
// 传感器安装微调旋转矩阵采用 Q24；下方保存当前已编译的矩阵常量，
// 矩阵并非全单位阵，是否参与估计由 LEVEL_TRIM_ENABLE 等配置决定。
`define LEVEL_TRIM_ENABLE 1
`define LEVEL_R00_Q24 16777216
`define LEVEL_R01_Q24 43
`define LEVEL_R02_Q24 -3825
`define LEVEL_R10_Q24 0
`define LEVEL_R11_Q24 16776151
`define LEVEL_R12_Q24 189005
`define LEVEL_R20_Q24 3826
`define LEVEL_R21_Q24 -189005
`define LEVEL_R22_Q24 16776151
`endif
