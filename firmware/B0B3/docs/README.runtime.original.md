# ACG720 60K 光流 XY 速度 P/I 在线参数

独立工作目录 `runtime_xy_pi_20261026`，来源为已逐文件验证的 parallel_p2_v4 交接包。只增加共享 XY P/I 运行时参数，不增加位置环或光流去旋转。默认 P=0.05/I=0；调参仅本次上电有效。当前目录的实现与构建不代表已安装或飞行通过。

接收 B16/P7-20 ← 机载 SiK TX，发送 B15/P7-19 → 机载 SiK RX，115200 8N1、3.3V TTL、共地。range_rx 不改用途。接线选择有历史双向实测依据，当前实物接线仍须在新镜像安装前核对。只允许停机时写入，飞行中只读。协议、合法范围、量化、积分与生效机制见 [PROTOCOL.md](PROTOCOL.md)。

## 电脑端

使用 Python 与 pyserial。`xy_pi_cli.py` 独占一次串口会话，不连接/关闭/替换现有接收器。当前接收器若占用端口，须由操作者在准备好的停机维护窗口释放串口，再运行；不要同时启动第二个串口所有者。COM 号须重新枚举，不照抄历史 COM17/COM22。

```powershell
python -B xy_pi_cli.py --port COM实际端口 get
python -B xy_pi_cli.py --port COM实际端口 set --p 0.05 --i 0
```

SET 同时写一对，打印 ACK 实际生效值，随后独立 GET 核对 generation 和完整 P/I。超时不自动重发 SET；先查询当前值。每次 SET 序号须严格增加；默认使用低32位 Unix 毫秒，可通过 `--seq` 显式设置。STALE_SEQUENCE 不改参数，详见协议。示例仅说明操作，不构成新飞行增益建议。

GET 响应必须报告 protocol=1、build=0000B0B3；原遥测 B0B2 字段为旧解析兼容而保留。需要以新位流 SHA256、JTAG UserCode 及 A591 响应一起识别镜像。

## 离线重现

```powershell
$env:PYTHONUTF8='1'
python -B verify_protocol.py
python -B verify_control.py
python -B verify_link.py
python -B verify_top_safety.py
python -B build.py --all --fixture builds/rebuild_001
```

工具链使用本机 Gowin 1.9.12.04 和 `.tools/iverilog/app/bin`。构建复制独立 `source` 到新命名的冻结 fixture，不覆盖已有 fixture，不操作硬件。测试记录保存在 `verification/`，厂商网表、布局布线、位流和报告在所选 `builds/<名字>/source/impl/`。最终构建路径与哈希绑定状态见 `DELIVERY_REPORT.md` 与 `delivery_manifest.json`（生成后）。耗时构建应使用隐藏独立后台进程，避免工具会话生命周期中止构建；当前执行 PID 与退出回执保存在对应 `verification/process*.json`。

`--all` 使用canonical `build.tcl`默认的P2/R0；最终选中的place/route以 `qualification.json` 的physical_options和 `DELIVERY_REPORT.md` 为准。最终报告提供先 `--synth`、再exact-netlist `physical_retry.py`的对应选项命令。复现须使用独立交付副本及未使用的新fixture名称，不覆盖canonical source或已有fixture；验证/audit命令会刷新该副本的verification记录。

只读并行飞行/P2 核查位于 `analysis_flights/FINDINGS.md`。其中的飞行资格结论与参数接口验收分开；新增接口不证明“回中刹停、稳定悬停”已经通过。

## 回退与上板边界

本任务不自动下载 SRAM 或写 Flash。历史拆桨/Flash 授权不沿用到新位流。新镜像上板前需当次确认 B15/B16 接法、电平/共地、拆桨/停机条件，以及本次具体 SRAM 或 Flash 操作。先 SRAM 查询/拒绝路径/生效回读核验，再决定 Flash；只运行新的、绑定本次文件哈希的安装步骤，不能直接运行旧安装器。

回退文件保存在 `rollback/`（交付打包时复制）：

- `current_P005_I0.fs`：当前已安装基线，SHA256 `a876c8ed073588e17b6289f8aac7573334a5d5e9c992d394d0d14f61ed17db7c`。
- `original_V15.fs`：原 P=0.15/I=0.10 V15，SHA256 `3b9920acc1abecf6e0ef50465f5bc408d9b74af2ac6d046cb151137a375b4306`。

若仅做新镜像 SRAM 测试且 Flash 未修改，完全断电后恢复现有 Flash 基线。若后续获当次授权替换 Flash，回退前先按清单校验镜像 SHA256，在拆桨停机维护条件下选正确 Gowin 器件/下载器写入对应 `.fs`，执行厂商 verify，再断电冷启动核对镜像身份和遥测；旧、新两份 UserCode 可能不足以区分旧镜像，必须结合位流哈希与安装回执。本文是回退步骤说明，不代替下载操作授权。
