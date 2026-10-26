# B0B3 本地地面站：共享 XY 速度 P/I

沿用 B0B2 v3 遥测、监控和自动日志，在同一个串口所有者中增加参数查询及停机成对写入。原 `ground/B0B0`、B0B2 生成器和已验收固件均未修改。本目录的 `provenance/` 记录生成种子，描述准备时的字节，不冒充修改后文件清单。

机载须先按独立授权安装 [B0B3 固件](../../firmware/B0B3/README.md)。新地面站不会自动烧录。2026-10-26 首次实机联调已在当次拆桨、CH5低位及用户授权后下载 SRAM，并通过默认 P/I 的无线 SET ACK 和独立 GET 核对；未写 Flash。详细记录与首笔无响应的边界见[验证报告](../../validation/20261026_xy_pi_ground/README.md)。

## 启动

在仓库根目录，使用 Python 3.10+、pyserial：

```powershell
$env:PYTHONUTF8='1'
python -m pip install -r ground/requirements.txt
python -B ground/B0B3/launch.py --port COM实际电台串口 --source SiK --baud 115200 --enable-xy-pi
```

访问 `http://127.0.0.1:8765/`。请替换实际 COM 号；不得选择 FPGA 下载器或猜测历史 COM17。已有接收器占用时先在维护窗口释放它，不启动第二个串口所有者。日志默认在忽略目录 `ground/runtime/B0B3`。

不接硬件的页面预览：

```powershell
python -B ground/B0B3/launch.py --no-serial --enable-xy-pi --http-port 8873
```

预览显示未连接，不枚举/打开串口，不允许从预览切换到真实设备。没有 `--enable-xy-pi` 时保持只读接收。USB 镜像为只读，参数接口仅支持 SiK 115200。

完整操作见 [操作说明](../../docs/XY_PI_GROUND_STATION.md)，运行中的页面有“操作说明”链接。

## 收发与验收边界

- 独立 GET 确认参数功能；旧遥测 B0B2 标签不是能力证明。
- P/I 为十进制字符串，0～1、步长.0001；同一对用于两个水平轴。
- 接收请求及真正发送前均做新鲜停机预检，实际提交仍由 FPGA 裁决。
- 一笔 SET 保持忙碌，直到 ACK 后的独立 GET 验证相同 P/I 和 generation。无自动 SET 重试。
- 断线、换端口、接收异常或检测到重启会使旧会话失效；已经尝试的写入结果不明时只先查询。
- 本地 HTTP 只允许固定参数操作，严格同源及会话 token 校验。token 不进入 `/api/state`、遥测、日志或公开分享；未给网站旁路增加写接口。
- A591 注册到现有统一分包器，响应单独分发，不能刷新普通遥测的姿态/解锁状态。
- 仅本次上电有效，不保存 Flash。通过软件测试不代表已完成实机或飞行验收。

## 离线测试

```powershell
python -B -m unittest discover -s ground/B0B3 -p 'test_xy_pi_*.py' -v
```

测试使用内存、假串口和自有临时 loopback 服务，不连接真实电台或既有服务。UI 的 Node 测试不需要第三方包（若已安装 Node，见 `test_xy_pi_ui.cjs`）。
