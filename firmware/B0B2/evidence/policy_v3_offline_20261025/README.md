当前策略版已零未布通，但最佳 Fmax 为 39.234MHz；19.5ns 约束下有 1,194 个 setup 违例，因此没有物理合格版本。没有下载、刷 Flash、串口或电机操作。本目录不包含位流。

完整结论见 FINAL_RESULT.md；source_snapshot 为实际保留源码。best/fixture 包含成功布通的精确网表和输入；trials 中保留全部 8 组结论及已有完整时序报告。原始绝对路径属于执行时的工作目录，manifest.json 将其与本快照的相对路径及哈希对应。

只读检查快照完整性：`python verify_archive.py`。此检查不会把未通过时序的结果改为合格。

如需复现物理试验，可先复制整个目录到一个新的工作目录，再使用相同 Gowin V1.9.12.04：`python physical_trial.py rerun_p4r0 --donor best/fixture --place 4 --route 0`。该脚本只运行布局布线，不调用下载器。source_snapshot/build.tcl 是保留的历史元数据；实际物理命令为 best/fixture/build.tcl。新综合使用 synthesis 的输入凭据与源码快照，精确网表哈希见 receipts/synthesis_final_binding.json。
