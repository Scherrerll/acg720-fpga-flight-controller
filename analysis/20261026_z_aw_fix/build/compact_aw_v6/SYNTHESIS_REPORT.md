# v6 SYN_ONLY

2026-10-26 单次独立hidden后台执行完成：elaboration、vendor SYN、supervisor等待runner的真实 `p.wait()` 均为0。仅两模块7处±30000布尔guard改为upper符号扩展检查和S16边界；其余53源同v5，hold仍04e75ada…；旧v5/helper/main B4源未变。

VG SHA256：`6b169818d5029c45e0a778d74d8d3e90e129caa430e93eb3778661f18fa7cb99`。

mapped审计通过：27725 FF全部clk50；radio pad/同步链与唯一false path不变；P1000/I350各16活位；18标量ports。相对v5 map2：top LUT36163（+13）、ALU9525（+64）、FF27725（0），DSP/BSRAM不变；height fusion LUT+16，controller_proof LUT-9。资源变化不证明时序改善。

证据：`out/z_aw_fix_20261026/compact_aw_v6/build_attempt_01/verification/` 中 `synthesis_exit.json`、`synthesis_summary.json`、`mapped_audit.json`、`gain_port_audit.json`、`strict_ff_clock_audit.json`、`resource_comparison.json`；本目录 `runner_exit.json` 为独立监督进程真实退出凭据。本SYN阶段无50MHz/STA结论；之后root授权两PNR启动另见 `PHYSICAL_START_MANIFEST.json`。二态等价及四态X差异见上级 `numeric_guard_design.md`；功能验证由root另行负责。
