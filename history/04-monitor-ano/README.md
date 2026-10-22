# 综合监控与FPGA控制算法工程化（2026-10-12至13）

flight_monitor验证完成UTC 2026-10-11T18:32:05.155709+00:00，即北京时间10月12日02:32。ANO全局验证最新记录UTC 2026-10-13T13:03:57.030792+00:00。dashboard原README第59行记录10月13日A701/AFSR发布，第65行仍记录线加速度尖峰。此处不打包网页或位流，也不据这些历史报告宣称当前归档源码飞行合格。

本目录为2026-10-22从工作区当前文件导出的源码归档，按历史功能出现顺序分组，并非从Git恢复的当日快照。历史报告、UserCode、频率或硬件结果不自动适用于这份源码。

构建：用Gowin FPGA Designer打开对应子目录GPRJ，工作目录设为该工程目录，核对GW5AT-60B目标和本机工具版本，再运行综合与布局布线。有build.tcl时也可在工程目录用gw_sh执行。这里只检查了GPRJ引用与递归include完整性，没有在归档目录重新编译。

不包含生成器、下载脚本、FS、impl、raw日志或硬件快照。历史README提到的跨工程生成/恢复步骤不在本归档提供；不要在本目录运行旧生成流程。源码头原样保留，未授予新的统一许可证。

来源证据（均指原工作区路径；未随归档完整复制）：
- `acg720_flight_monitor_bench/validation.json`
- `acg720_ano_port/validation.json`
- `acg720_ano_port/PORT_NOTES.txt`
- `acg720_dashboard/README.md`

ANO公式/执行顺序/默认参数派生自用户提供的Quadrotor_TM_V1.7z。原工程PORT_NOTES明确保留匿名原作者归属，具体上游版本仅由本地哈希标识。ANO授权未完成核查，本归档不附带无明确许可的完整上游库或资料，不代表已获公开再分发许可。PX4与Bitcraze许可文本保存在适用工程的core/NOTICE_PX4.txt和sensor/UPSTREAM_LICENSE.txt；其中提到的上游reference快照不随本档分发。
