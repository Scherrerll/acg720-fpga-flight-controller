# 11-b0ab

日期：2026-10-19。

B0AB 最终选中的 publication_yaw_study；Fmax 50.001 MHz；资源、布线和 50 MHz 离线证明通过，物理安装/旋转及飞行未验收。

历史来源：`routing_rescue_20261015/mtf01p_b0ab_control/publication_yaw_study/fixture`。

入口：Gowin IDE 打开 `fixture/acg720_ano_port.gprj`；在 fixture 目录用已安装的 Gowin `gw_sh build.tcl` 重新编译。这些命令只编译；不提供硬件下载入口。

导出保留原 GPRJ 的全部本地文件引用、递归 Verilog include、约束和 Tcl，以及少量历史验证摘要；未附 bitstream、impl、仿真可执行文件、大型日志、硬件快照或旧 ground。

证据 JSON 内个人机器绝对路径仅为原机器的历史 provenance；本副本不承诺完整证据重放。重新编译可能因工具版本、布局布线及环境不同产生不同结果，不能替代原 bitstream/hash 绑定的历史证明。验证状态仅限各报告明确的范围；重新编译或自测不等于硬件或飞行验收。

每个导出文件的原相对路径及 SHA-256 见 `../late_manifest.json`。
