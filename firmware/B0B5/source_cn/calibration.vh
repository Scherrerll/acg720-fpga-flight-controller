// 编译期标定配置：掩码控制各项物理标定资格，Q20 常量保存光流与旋转补偿系数。
// 标定掩码保持为 0，只有记录实物测量结果后才按事实启用对应位；不猜测标定系数。
// 位 0～5 依次表示光流比例、光流轴向、旋转补偿、距离单位、
// 安装几何和相对航向对齐；位 6～7 表示控制增益和集合油门映射。
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
