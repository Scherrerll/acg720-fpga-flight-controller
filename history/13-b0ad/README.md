# 13-b0ad

日期：2026-10-20 至 2026-10-21。

B0AD 局部取消，Fmax 50.067 MHz；历史 SRAM 测试，默认 Flash 保持 B0AC。SWA/保持与手动拾起台架观察通过；旋转/飞行验收未完成。status 的 installed_build=B0AD 是历史 SRAM 状态，不是当前板上声明。

历史来源：`routing_rescue_20261015/mtf01p_b0ad_local_cancel/fixture`。

入口：Gowin IDE 打开 `fixture/acg720_ano_port.gprj`；在 fixture 目录用已安装的 Gowin `gw_sh build.tcl` 重新编译。这些命令只编译；不提供硬件下载入口。

导出保留原 GPRJ 的全部本地文件引用、递归 Verilog include、约束和 Tcl，以及少量历史验证摘要；未附 bitstream、impl、仿真可执行文件、大型日志、硬件快照或旧 ground。

证据 JSON 内个人机器绝对路径仅为原机器的历史 provenance；本副本不承诺完整证据重放。重新编译可能因工具版本、布局布线及环境不同产生不同结果，不能替代原 bitstream/hash 绑定的历史证明。验证状态仅限各报告明确的范围；重新编译或自测不等于硬件或飞行验收。

每个导出文件的原相对路径及 SHA-256 见 `../late_manifest.json`。
