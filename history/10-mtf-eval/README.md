# 10-mtf-eval

日期：2026-10-18。

MTF-01P 独立 USB-TTL/Micolink 功能工具，不接 FPGA，无 FPGA build ID；工具自测不代表实物或飞行验收。

历史来源：`routing_rescue_20261015/mtf01p_eval_20261018`。

入口：`python micolink_monitor.py --self-test`（无需硬件）；接线和只读串口使用说明见 `ORIGINAL_README.md`。

本阶段仅导出独立工具和原使用说明，无 GPRJ、FPGA 工程或硬件快照。SELF_TEST.json 记录导出副本的无硬件自测。

证据 JSON 内个人机器绝对路径仅为原机器的历史 provenance；本副本不承诺完整证据重放。重新编译可能因工具版本、布局布线及环境不同产生不同结果，不能替代原 bitstream/hash 绑定的历史证明。验证状态仅限各报告明确的范围；重新编译或自测不等于硬件或飞行验收。

每个导出文件的原相对路径及 SHA-256 见 `../late_manifest.json`。
