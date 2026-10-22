# MTF-01P 台架功能验证（独立测试，不接飞控）

目的：在**不改 FPGA、不接飞控**的前提下，先确认 MTF-01P 功能是否好用——测距是否跟手、
光流是否有响应、质量/状态是否正常、丢帧/校验错多少。验证通过后再讨论是否开新候选接入。

## 一、必备条件

- MTF-01P 模块（激光测距 0.02–12m，光流 42°，UART 3.3V 115200 100Hz，**5V/100mA**）
- 独立稳压 **5V**（不要用 P7-11 板载 5V，也不要接 3.3V 光流电源）
- USB-TTL 适配器（3.3V 电平；COM23 被飞控遥测占用，请用另一个口，如 COM24）
- 电脑 + 微空助手（MicoAssistant）软件

## 二、接线（只读测试，3 根线）

| MTF-01P | 接到 |
|---|---|
| 5V | 独立 5V 正极 |
| GND | 5V 负极 + USB-TTL 的 GND（**必须共地**） |
| Tx | USB-TTL 的 Rx |
| Rx | 可不接（只读测试不需要向模块发数据） |

⚠️ 不要把 5V 接到任何 FPGA/UART 信号脚；模块信号是 3.3V LVTTL。

## 三、操作步骤

1. 先只接 5V 与 GND，确认模块指示灯/电流正常（约 100mA）。
2. 接 Tx → USB-TTL Rx，插电脑，记下串口号（设备管理器或
   `python -m serial.tools.list_ports`）。
3. **打开微空助手，把模块协议切到 `Micolink`**（出厂默认 AUTO；AUTO 模式下可能等飞控
   握手而不输出 Micolink 帧）。保存后重新上电。
4. 运行监控脚本：

```
python micolink_monitor.py --port COM24 --csv mtf01p_bench.csv
```

5. 测试动作（一次只改一个条件）：
   - 静止 10s（看底噪：distance 抖动、flow 是否为 0、quality）
   - 纸板在镜头下 20cm → 50cm → 100cm → 150cm 逐级移动（看 distance 是否跟手、单位 mm）
   - 纸板水平左右/前后各移动 10–20cm（看 flow_vel_x/y 符号与幅度是否跟手）
   - 遮挡镜头 / 关灯（看 tof_status、flow_quality、distance=0 无效语义）
6. 结束 Ctrl+C，把 CSV 和观察记录发回。

## 四、判定标准（初筛）

| 项 | 期望 |
|---|---|
| 帧率 | 稳定 ~100Hz（脚本 frames/s） |
| 校验错 | 0（持续 >0 说明电平/波特率/接线问题） |
| 测距 | 20–150cm 范围内跟手，误差约 4cm（<2m 规格），单位 mm；0=无效、最小 10 |
| 光流 | 静止时≈0；移动时符号一致、幅度随速度增大；quality 稳定非 0 |
| 状态位 | tof_status/flow_status 不异常翻转 |

## 五、数据含义（厂家定义）

- `distance`：**mm**，0 表示不可用，最小值 10。
- `flow_vel_x/y`：**cm/s @1m 高度**（高度归一化速度）；
  实际速度(cm/s) = flow_vel × 高度(m)。例如 0.5m 高度、flow_vel=100 → 实际 50cm/s。
- `flow_quality`：光流质量（越大越好）；`flow_status`/`tof_status`：状态字节，
  具体位定义厂家未公开，先按"是否异常翻转"观察。
- 校验：`sum(前 len+6 字节) & 0xFF == checksum`。

## 六、脚本自测（无硬件可先跑）

```
python micolink_monitor.py --self-test
```

应输出 `SELF_TEST PASS`（5 帧解码 + 校验错拒绝）。

## 七、下一步（验证通过后）

1. 若功能正常：开新候选（如 B08C）——空闲 GPIO（D14/D15 等，Bank16 3.3V）做第二路
   UART，新增 Micolink 解析；光流观测用 `flow_vel × height_mm / 100` 得到 mm/s 接入
   `ano_flow_fusion` 观测速度入口；距离 mm→cm 边界转换。
2. 仍要重新标定（轴向/符号/比例/旋转/安装偏移），验收后才有资格谈 CAL 位。
3. 与 B08A（高度融合修复）互不冲突：高度链路不变。
