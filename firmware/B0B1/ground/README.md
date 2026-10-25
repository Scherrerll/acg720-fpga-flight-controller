# B0B1 只读诊断接收器

本目录独立解析 M15 USB 诊断 UART 的 `A5 84` v1 帧，精确格式见
[DIAGNOSTIC_PROTOCOL.md](../DIAGNOSTIC_PROTOCOL.md)。不导入飞控、烧录或电机控制模块。
离线解码只依赖 Python 3.10+ 标准库；串口采集额外需要 `pyserial`。

## 离线复核

在仓库根目录执行，输出目录必须尚不存在：

```powershell
python firmware/B0B1/ground/capture.py --input C:\captures\trial1\raw.bin --output C:\captures\trial1_decode
python -m unittest discover -s firmware/B0B1/tests -p test_protocol.py -v
```

`--input` 模式不会导入 pyserial、打开串口或修改输入文件。它流式读取文件并在新输出
目录中复制原始字节、重新分帧和生成摘要；不会加载整份日志。

## 获得操作者当次确认后的串口采集

采集命令需要显式指定端口，不能从旧会话或当前接入设备猜测端口。硬件接线、拆桨、
供电、烧录与操作者当次确认流程由上层操作文档负责；执行本命令只表示启动接收。

```powershell
python firmware/B0B1/ground/capture.py --port COM_DIAGNOSTIC --baud 921600 --duration 60 --output C:\captures\new_trial
```

将 `COM_DIAGNOSTIC` 替换为已确认的 M15 USB 诊断串口。默认921600，8N1；
`--duration` 可省略，此时用 Ctrl+C结束并保存摘要。115200的SiK是另一条流。
接收器不发送任何字节、不清空串口缓冲，不调用烧录器。创建串口对象时暂不打开端口，
先将DTR/RTS置为false并禁用软/硬件流控，再打开。USB驱动在open时仍可能短暂改变
modem线，软件无法保证没有电气毛刺；不能依赖串口线作为电机/供电安全措施。

## 输出与判读

- `raw.bin`：本次从输入读到的全部字节，先保存再解码。
- `decoded.jsonl`：CRC正确且类型/长度合法的frame；另有精确匹配的`pose_raw_join`记录。
  每帧保留原始字节偏移、原始capture_tick、sequence、payload与epoch。
- `summary.json`：CRC、未知版本/类型、残缺尾帧、发送序号缺口、重复/逆序、
  各类型生产者drop counter、匹配/未匹配数量、首个故障分类、读错误及其他采集错误。
  `error_phase`指明错误发生在打开、读取还是写入/解码阶段；错误退出码为2。

CRC失败后从下一个字节重新寻找header；未知版本/类型没有已知长度，同样重新扫描。
四种payload严格按固定长度解码，CRC覆盖version到payload尾部。程序不会插值补齐缺帧。
正常EOF/时限结束时会再扫描不完整候选后的CRC合法尾帧，避免损坏的长type头遮住
较短尾帧；`eof_recovered_frames`和`truncated_frames`保留此过程。Ctrl+C或读错误仍原样
保留raw.bin，若恰在处理半帧时结束，可用离线模式完整复核。
`producer_drop_cumulative`是板上该boot内的累计值，可能包含接收开始以前的丢弃；
`producer_drop_observed_delta`仅是首末status之间的差值，不覆盖status外的尾段。
`0xFFFFFFFF`表示饱和下界。发送seq缺口和板上drop counter属于不同边界，不能相加当作
唯一的“总丢包数”；CRC错误也可能与seq缺口描述同一受损帧。

`fault_captures`保存每个收到的冻结fault窗口，`first_fault`只是本次捕获/boot中
最早收到的一个；后续窗口不能只看first_fault。`first_cause_name`是固件自最后一次姿态发布后锁存的诊断首因标签，
不等于已证实的机械/物理根因。全部同时触发位保留在fault记录中。
raw在`reader_valid && config_ok`时才是新物理观察；无效记录中的旧值仍原样保留，
不能据此推断传感器瞬时值。pose角度保持传感器符号，世界坐标保持X前/Y左/Z上，
不会自动改成已安装机体坐标。

## 跨raw/pose及SiK对齐

`source_id`标识原始决策，`accepted_count`标识guard接受事件。只有相同epoch内、
raw的accepted位和reader/config有效、且`raw.accepted_count == pose.consumed_accepted_id`
才产生`pose_raw_join`；不能把source_id与consumed_accepted_id直接比较。
pose先到时等待匹配raw；未见raw、队列丢弃或超过8192条匹配缓存时保持“未匹配”，
不会借用相邻样本。匹配记录保存两端capture tick及该次pose精确held_dt_ticks。

seq按16位解缠，tick按32位解缠。status的64位uptime锚定多次tick回绕；
status uptime回退、raw source/acceptance两个计数同时复位、或发送seq和capture tick
同时重启会开启新epoch并清空匹配缓存。单独tick回绕/计数回绕不会当成重启。
没有status或重启证据时，boot归属可能仍不确定；不能跨这种边界强行匹配。
初次status以前的tick扩展标为未锚定，不会伪装成确定的绝对uptime。
使用最近status延伸tick假设排队小于半个32位tick周期（42.95秒），原始tick始终保留。

对齐SiK时先确认两份数据对应同一boot/epoch和B0B1身份，再以SiK A580的板上
`uptime_ms`及USB status的`uptime_ms`建立锚，使用USB raw/pose capture tick定位。
A579本身没有uptime，应以同boot的A580源序号/板上uptime关联其帧。
主机`host_chunk_received_utc`只记录一次read完成时间，离线模式则只是解码时间；
不得用它推断两条UART中样本的同步或因果先后，更不能对5Hz SiK补成1kHz。
板上uptime只有毫秒量化，USB行中的估算标明±1ms量化限制；精确整数形式为
`onboard_uptime_ms_floor`加`onboard_sub_ms_ticks/50000`，避免极大u64测试值转float失精。
不同UART的发送排队延迟
也不能用主机时间消除。没有同boot锚的数据应保留为不可确定匹配。

此目录不修改冻结B0B0接收器。旧A580解码器若仅允许B0AF/B0B0身份，需使用单独的
B0B1身份适配后才能提供上述SiK锚；不能把旧解码器没有显示A580当作板上无status。

## 生成独立SiK兼容副本

```powershell
python firmware/B0B1/tools/prepare_sik_receiver.py
```

此命令只复制冻结`ground/B0B0`到新`out/B0B1/sik_receiver`，扩充B0B1身份白名单和
身份文字，并修正副本相对support/测试输出位置；字段、单位、原始B0B0目录不变。
已有目标目录一律拒绝覆盖。可用`--output`指定`out/B0B1`下另一个新子目录。
输出内`B0B1_PREPARATION_RECEIPT.json`记录源/输出逐文件与整树SHA256、完整补丁和补丁SHA256；
receipt自身及后续运行/测试新输出不包含在准备时的output hash范围内。
它不启动接收器；上层包装器后续可把`--receiver-dir`指向该目录。
