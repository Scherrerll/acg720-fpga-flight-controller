# 前飞掉高：倾角、Z比例与执行余量核查

**用户已暂缓掉高调查，判断可能与低空地效有关；地效不是本次已证实的原因。本文件只收尾停止前已完成的证据，不再新增分析或试验。**

当前可见证据是Z总距长时间保持1850上限；尚不能把掉高归因为缺少倾角补偿。B3确实没有总推力的倾角前馈，P2参考代码也没有。新日志主要前飞窗口倾角很小，17帧四PWM平均值均等于1850，因而该窗口既未证明明显倾角升力损失，也未观察到混控裁剪降低平均PWM。Z为何长期请求高端，属于另一条低杆不下降调查的P/I/前馈/反馈链；本分支不把缺失的内部项补成观测事实。

## 1. 已确定的代码行为

以下路径均为冻结文件，只读核查；B3根目录为`firmware/B0B3/source`，P2为本机handoff内`reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1`。精确SHA见`log_projection_results.json/source_inputs`。

| 核查项 | 源码位置与结论 |
|---|---|
| B3 Z输出 | `position/mtf_xyz_hold_control.v:387–402,447–449`：Z速度误差产生P项、I项及向350松弛的bias；输出裁剪0..850，最后加1000成为1000..1850us。Z模块没有roll/pitch输入，没有除以cos或其他倾角增推步骤。 |
| 从Z到电机 | `core/flight_core.v:437,507–514`选择正常Z总距或fallback，直接保持到`pending_throttle`；`core/rtl/quad_mixer_feedback.v:18–35`加姿态差动，各电机独立裁剪1200..2000。没有保持总距的重新分配/去饱和。1850基准上仅余150us正差动空间。 |
| 抗积分饱和范围 | `core/rtl/ano_rate_control.v:219–250`按混控方向反馈抑制rate I继续积向无余量方向；Z I没有该混控/总距饱和反馈接口。由此可提出Z windup机制核查，不能直接由本分支日志读出当时I值。 |
| 实测角与目标角 | `core/flight_core.v:120–125`的body roll/pitch来自姿态观测（pitch符号映射）；Z推力路径两者都未使用。下面测距cos使用实测姿态，不是目标姿态。 |
| 斜距到垂直高度 | `sensor/mtf_shared_geometry.v:183–205`捕获distance_mm及实测roll/pitch（cdeg），转换为Q20弧度、求Q16 cos，得到`distance*cos(roll)*cos(pitch)`并舍入到mm。这是**测距几何校正，不是总推力补偿**。 |
| 实际Z反馈 | `mtf_xyz_navigation_control.v:120–126,216–218,326`：上述垂直参考与earth-up加速度进入native height fusion，再以其fused height/vz给实际Z控制。顶层旧laser/display路径不是该控制反馈源。Z目标/高度是mm，速度内部mm/s Q16；高度反馈先按整cm量化。 |
| 模式/降级 | `mtf_xyz_navigation_control.v:75–80`允许height几何到45°、flow/XY到15°，XY退出不能单独推定Z降级；`core/flight_core.v:372,429–438`的height fallback锁存会撤销navigation许可并用fallback集体量。新选窗fallback均false，不能套用以前降级首因。 |

**FINAL_P核查：没有发现B3遗漏或重复Z末端0.35。** P2 `config.h:39,74–80`给FINAL_P=.35、THR_INTE_LIM=70/FINAL_P；故I允许幅度为2000减bias。`Ano_Pid.c:44–57`直接输出P+I+D；`Ano_AltCtrl.c:186–211`加bias、裁剪0..850并直接赋`mc.ct_val_thr`。`Ano_MotorCtrl.c:86–97,123`直接混控再送驱动。只有`Ano_AttCtrl.c:316–318`对roll/pitch/yaw末端乘FINAL_P；B3也只在`ano_rate_control.v:260–261`乘350/1000。

P2 `Driver/Drv_PwmOut.c:80–86`以`1.25*value+1250`变定时器ticks，tick为0.8us，因此等于1000us+value，而不是再乘0.35。P2默认Alt1 P=2/(cm/s)、I=1/(cm/s*s)、KD=.05s；B3用mm/s后的P=1/5、I每11ms乘11/10000、加速度反馈1/20，系数量级一致。P2的2000积分界大于850总输出界，是参考本身的行为，不据此推定所有状态/传感器/数值实现均完全相同。这里是源码/单位核查，未编译执行P2 C。

## 2. 通用倾角关系与本机实测分开

在各旋翼推力沿机体Z轴、忽略其他气动力、Euler旋转为Rz(yaw)Ry(pitch)Rx(roll)的假设下，旋转矩阵R33=cos(roll)cos(pitch)，因此竖直推力为`T*cos(roll)*cos(pitch)`。理想定高需总推力按其倒数增加。俯仰10°/15°时固定T的竖直分量分别少1.52%/3.41%；双轴各15°少6.70%。这些是**力的比例**，不是PWM补偿律，不能直接把1000..2000us除以cos。

官方原始控制文档[ArduPilot Stabilize Mode](https://ardupilot.org/copter/docs/stabilize-mode.html)说明其按倾角增加电机油门、减少姿态变化时所需的人为补偿。这支持倾斜需增推的一般控制考虑；不证明本机此次掉高的唯一原因，也不把ArduPilot参数/实现移植为本机修复。几何推导和七个参考数例保存在`force_geometry_reference.csv`。

在平地、正确安装和时间对齐条件下，真实垂直高度不变时斜距应随倾角增大，乘cos会还原高度；“固定斜距乘cos变小”不是本机真实下降的证明。原始斜距、融合高度均不是外部高度真值；曝光/pose对齐、传感器安装、加速度偏置及推进系统实际推力仍未识别。

## 3. 新实飞同key结果改变了优先级

只读取日志支线冻结`joined_rows.csv`，按同一epoch8/sequence配对A579/A580/A582/A57A/A581/A585；原始固定窗口SHA256为`c46a8f81344b5af33060c216fd0446383a6b65c477680b73e0668d7df18b469c`。派生表的PWM均值明确取`physical_m1_us..physical_m4_us`锁存字段，不是RPM/推力测量，不声称与导航总距属于同一次mixer执行。停止前已抽查3579–3595的command四路均值也每帧1850、也无触2000；但3588和3594的command/physical四元组不同，证明不同锁存时刻不能混同。现有派生列保持原样，不追加复算。每行姿态独立计算投影，绝不把不同帧的角极值组合。

| 窗口 | 直接日志及派生边界 |
|---|---|
| **3579–3595**，UTC02:43:04.909–08.199，17/17六类包齐全 | CH2=1552..1594、CH3=1488..1498；target恒1400mm，fused1214→941、raw1154→873。roll−0.70..+0.67°、pitch−1.06..+3.95°；逐帧理想投影损失仅**0.0011%..0.2378%**。Z全1850；17帧PWM平均都恰1850，无帧触2000。vz全负−106.79..−34.46mm/s；az−686..837mm/s²。此窗口支持掉高描述，尚不支持把主要原因归于明显倾角或已观测的混控裁剪。 |
| **3602–3610**，9/9齐全 | target仍1400；Z全1850，3帧触2000；平均PWM相对总距请求最多低13.75us。存在有限混控余量问题，但不能由PWM均值换算物理升力亏损。 |
| **4041–4282**，UTC02:44:37.287–02:45:25.492 | **242/242导航包连续全1850，48.2s**，不是仅最后低杆才顶限。237组六类包齐全，其余不补缺；齐全组5次触2000、平均最多低8.5us、fallback无true。首个1850前4038/39/40分别1812/1828/1841（该邻域见日志支线表）。 |
| **4259–4282**，24/24齐全、4.6s | CH3恒1002，目标+1284→−1740mm，fused260..318、raw354..412，Z全1850，无fallback，XY/Z/taking_off/flying均真。逐帧投影损失**0.0335%..0.2098%**；平均PWM最多低2.75us，一次触2000。这不是“目标没下降”或“仅卡1200运行下限”的窗口；没有Z内部I/P/限幅前项，不能单凭日志定I值。 |

参数成功SET及独立GET为P=.1000/I=.0350、gen8，但这是共享XY外环参数，不应继续用XY PI来掩盖Z高端保持。前后不同飞行状态不构成XY I导致Z异常的因果实验。取样约5Hz，不能排除帧间更大倾角/裁剪，也不能把同key接收组称为所有传感器曝光完全同步。

## 4. 已执行的最小离线证据及后续范围

`analyze_tilt.py`用真实冻结`quad_mixer_feedback.v`实例做8个混控输入和disabled检查：iverilog exit0、vvp实际wait0，共9个PASS。例：t=1850/p=300输出2000/2000/1550/1550，平均1775；t=1850/p=150恰触2000，严格clip标志仍0，但方向反馈已置位。故仅flags严格clip=0不足以保证有正向余量。此测试只执行真实mixer，不是整架飞机/推进系统、Z闭环或P2 C测试。

`analyze_log_projection.py`实际exit0，复核22个来源文件前后SHA相同（20个B3/P2源码与原始/派生日志），断言242个连续导航高限及关键窗口齐全数量。逐组数值在`log_projection_samples.csv`，完整范围及来源hash在`log_projection_results.json`。`tilt_math_results.json`保留实际编译/仿真命令、wait回执及15个原始源码hash。脚本旧docstring称TILT_FINDINGS.md，权威报告名称是本文件FINDINGS.md。

若后续重新授权调查，最小范围应留在**Z误差/积分/总输出饱和及其执行反馈**，而非凭XY PI弥补Z问题。倾角前馈/混控去饱和属于独立设计项，需实际推力标定、上下限与状态交接验收，不能先套PWM倒cos或提高1850上限。本分支现已停止，不执行这些后续事项。没有授权或执行任何产品源码修改、综合、PNR、服务、硬件或Git动作。
