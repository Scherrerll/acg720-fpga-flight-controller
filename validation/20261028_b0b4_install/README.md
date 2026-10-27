# B0B4 50 MHz 上板安装记录 — 2026-10-28

本次已完成 SRAM 下载验收、Flash 写入、独立校验和物理断电冷启动验收。新启动实际读回 B0B4、P=0.1000 / I=0.0350、generation0，飞行验收未完成。冻结离线发布包及其资格文件不回写；本目录单独记录硬件阶段，最终状态见 `final_status.json`。

用户本次明确确认桨叶全部拆除、CH3/CH5/CH7 低位、正确的 FPGA 板及下载器已连接，并授权开始烧录。实际预检为 COM17 电台、COM22 下载器，唯一 serial6 下载线的新鲜枚举位置 292；JTAG 为 GW5AT-60B、ID 0001481B，原 UserCode 0000B0B3。每个后续设备操作重新核对下载器和位置，未沿用旧会话的连接事实。

使用已通过真实 50 MHz 离线验收的 `firmware/B0B4/release/acg720_ano_port.fs`，SHA256 为 `199bc466f8a8fe18e891600d18161babcea9c2495eee8d307dac62ac8646c610`。没有重新综合、改动源代码、降低时钟或增加时序例外。

## 实际结果

- SRAM 只下载一次。原脚本在下载、健康采样和 JTAG B0B4 身份检查通过后，参数查询轮询恰遇主帧与附加帧尚未同组，实际顶层退出 1。原失败报告、7 个正常退出 0 的子进程收据及日志均原样保留，未改成成功记录。
- 独立 completion 仅重读 JTAG 身份、健康遥测和一笔新的参数 GET，不再次下载 SRAM。它只对精确的同组拼帧等待做 3 秒有界重读，最终仍要求严格同组；实际根进程正常退出 0。新 A591 响应为 B0B4、wire P1000/I350、generation0。
- Flash 阶段实际执行 `0 → 54 → 1 → 0 → 66 → 1 → 0`。操作 54 明确报告 Program and Verify Flash successfully，操作 66 明确报告 Verify Flash successfully；全部真实子进程及根进程正常退出 0。两次重载后的停机、姿态/IMU 连续计数及 B0B4 身份均通过。
- 最终独立 GET 为 epoch4、operation5、B0B4、P=0.1000 / I=0.0350、generation0。没有 SET、解锁、试转电机或飞行命令；P/I 仍只在本次上电有效。

`evidence/ARCHIVE_INDEX.json` 绑定本轮原始路径、归档文件及哈希；先前 partial 索引另行保留。大日志采用确定性 gzip，并同时绑定压缩和解压内容。原 root1 是工具真实完成结果的观测记录，明确没有直接捕获的根 stdout 文件；completion/Flash/cold 使用真实 Popen/wait 收据和直接捕获的 stdout/stderr。

## 物理断电冷启动

冷启动观察器先取得新鲜基线并发出 BASELINE_READY，然后由用户断开电池、板 USB 和下载器与板端连接，灯全灭至少 5 秒，再仅用电池上电。用户直接确认已完整完成。真实观察器和根进程正常退出 0，记录断流及 uptime 从 204200ms 降至 399ms，随后 10 个新启动严格停机健康样本的 uptime 为 4199～6199ms，IMU raw/accepted/pose 计数持续推进。新的 B0B4 默认参数 GET 为 epoch5、operation6、wire1000/350、generation0。

`completion.json` 将人工完整断电事实与不可变观察证据合并，物理冷启动验收通过。原观察器自身的 physical=false 标记保留原字节，因为软件单独不能证明板灯全灭等实体事实；未将软件重载当作物理冷启动。

冷启动后曾出现遥测接收空窗，后续 40 次只读采样均为 live，uptime 无回退。用户随后补充“当时应该是断电了，不用管”，故按用户要求停止追查；此补充按用户回忆记录，不作为软件测得的断电原因。先前报告与派生记录保留，最终跟进状态见 `user_followup.json` 和 `final_status.json`。

当前停机运行和 IMU 数据正常；测距与光流尚无有效数据。安装与基本启动通过不构成飞行资格。
