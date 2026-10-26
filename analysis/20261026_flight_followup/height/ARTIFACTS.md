# 高度调查证据边界

`HEIGHT_FINDINGS.md` 是最终报告；`packet_evidence.json`、`boundary_packets.csv` 是从冻结有限窗口派生的真实包分析。`analyze_height.py` 不插值、不补缺包。H原始16MB窗口和旧源码仍是外部只读依赖，没有复制进本目录；路径与SHA记录于 `INPUTS.json`。

真实 RTL 的权威成功回执只有 **`rtl_attempt_03/rtl_results.json`**，其中编译和三个 vvp 进程的实际 returncode 都为0。场景0是有限正常调用，场景1/2是构造注入，不是高频飞行输入重放。每场景80ms，共12,000,000拍；已经完成，不再增加测试循环。

根目录 `compile.log` / `rtl_results.json` 是第一份TMP目录配置失败；`rtl_attempt_02/` 是第二份缺少include路径的编译失败。两者没有执行任何有效产品RTL仿真。原日志、命令和失败回执保留，不能当作成功证据或产品缺陷。`rtl_runner*_process.json` 仅记录本任务隐藏离线进程，不代表硬件会话。

`run_height_rtl.py` 是实际执行03时的字节，命令、源/TB/驱动SHA写入成功回执。它拒绝覆盖已有 `rtl_attempt_03`。若复现，在独立工作副本将OUT改为未使用目录，并使用本机外部 Icarus（`.tools/iverilog/app/bin`）；不运行冻结目录内的旧验证入口，不覆盖这些历史回执。完整B3源码55文件在仓库 `firmware/B0B3/source`，不是本目录副本。

`MANIFEST.json` 绑定本目录保留文件，并记录显式排除项。**所有 `*.vvp`、临时目录、Python缓存不属于上传或必需验证文件**；已生成的本地vvp仅以 `omitted_local_compiled` 保存大小/SHA供本机核对，缺少它不使归档不完整。清单与sidecar不自包含。不要用“所有目录文件均已上传/均须存在”解释清单。

本任务未访问HTTP、串口、下载器或飞机，没有改动固件/旧证据/其他分析目录，也没有Git操作。表格中seq375的主帧/CH3保持缺失；P005历史记录不冒充B3飞行。
