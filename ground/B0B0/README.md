# B0B0 只读接收端

本目录复制了 10 月 24 日验收时使用的 23 个接收文件，并适配了便携 `support/` 导入路径、测试夹具路径和输出位置。启动包装改为显式命令行入口；测试断言、数据解码、单位、标志和硬件控制边界均未修改。原文件与导出文件的哈希见 `docs/WORK_ARCHIVE_20261023_24.json`。

在仓库根目录安装依赖，并启动 SiK 接收：

```sh
python -m pip install -r ground/requirements.txt
python -B ground/B0B0/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

使用 USB 时，可参考 `--port COM23 --source USB --http-port 8767`。串口号需要根据实际设备修改，同一串口只能由一个接收程序打开。如果 8765 接收器已经在使用 COM17，不要再让 8767 的接收器使用同一个串口。

公网网站 `gmflylog.com` 还需要通过 8766 HTTP 旁路显式开启实时分享。旁路只读取 8765，不会再次打开串口，具体见[分享启动说明](../../web/flight-console/local/README.md)。本目录的启动命令不会自动开启公网分享，也不会向飞控发送命令。

在本目录运行离线测试：

```sh
python -B -m unittest discover -p "test_*.py" -v
```

旧 `ground/` 目录保留了 10 月 22 日的 B0AE 归档，本次没有覆盖其中的哈希绑定文件。
