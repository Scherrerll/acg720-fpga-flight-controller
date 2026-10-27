# B0B4 候选地面站：共享 XY 速度 P/I

本目录来自冻结B0B3地面站的新副本，保留B0B2 v3遥测接收、自动日志及同一个串口所有者。参数能力仅接受A591中的B0B4标识；旧A580遥测继续显示B0B2，不能据此认定参数能力。B0B3原地面站、固件及历史验收记录未修改，provenance/仅描述复制种子，不是本目录修改后的验收清单。

新候选的开机默认值为 **共享水平XY速度 P=0.1000 / I=0.0350**（wire1000/350），generation从0开始。这不是高度Z增益，也不是落地控制修复本身。参数只在本次上电有效；重启恢复这对新默认值，网页不会自动写参数或保存Flash。该目录不自动安装固件，B0B4的构建、物理实现和安装资格另由对应固件交付记录确认；本目录的离线软件测试不构成硬件或飞行验收。

## 启动与操作

仓库根目录，Python3.10+与pyserial：

```powershell
python -B ground/B0B4/launch.py --port COM实际电台串口 --source SiK --baud 115200 --enable-xy-pi
```

页面为http://127.0.0.1:8765/，运行记录默认写入忽略目录ground/runtime/B0B4。自行核对实际串口；已有接收器占用时在停机维护窗口释放，不启动第二个所有者争用同一端口。新地面站不会关闭或替换旧服务。

仅预览页面、不接串口：

```powershell
python -B ground/B0B4/launch.py --no-serial --enable-xy-pi --http-port 8874
```

预览没有演示遥测，不枚举/打开串口，也不能通过页面切换到真实设备。未显式启用--enable-xy-pi时仅接收；USB镜像始终只读。在线参数通路仅支持SiK115200。操作说明在页面/pi-help中。

- 查询取得本次B0B4设备的实际P/I及generation；初始输入框只是草稿，旧B3响应不能取得B4写入资格。
- 默认值按钮仅把0.1000/0.0350填入输入框，不发送POST/SET；草稿不会被状态轮询覆盖。
- 范围各0～1、步长0.0001；没有自动舍入。编码范围不是全范围飞行资格。
- 写入前确认拆桨、停机、未解锁且CH5低/中位；后端发送前再次检查，FPGA在实际原子提交边沿最终裁决。
- SET保持忙碌直到ACK后的独立GET验证完整P/I和generation。超时、断线或不匹配先显式查询；不自动重发SET，也不把默认值当成失败回退写入。
- 一次仅一个在途操作；换连接/检测重启后旧会话失效。token仅本地会话接口使用，不进入公开遥测、日志或分享。

## 离线验证

```powershell
python -X utf8 -B -m unittest discover -s ground/B0B4 -p 'test_xy_pi_*.py' -v
node ground/B0B4/test_xy_pi_ui.cjs
```

Python使用内存、假串口和自有临时loopback服务，Node使用实际HTML/JS与内存DOM/API替身；均不连接真实设备、8765或既有服务。回执在test_results/，不代表B4位流已经安装或完成实飞。
