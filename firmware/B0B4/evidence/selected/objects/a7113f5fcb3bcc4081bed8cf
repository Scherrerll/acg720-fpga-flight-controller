# B0B0 只读接收端

复制自 10-24 验收时使用的 23 个接收文件。适配便携 `support/` 导入路径、测试夹具路径/输出位置，并将启动包装改为显式命令行入口；测试断言未改；数据解码、单位、标志及硬件控制边界未改。原字节与导出字节哈希见 `docs/WORK_ARCHIVE_20261023_24.json`。

```sh
python -m pip install -r ground/requirements.txt
python -B ground/B0B0/launch.py --port COM17 --baud 115200 --source SiK --logs ground/runtime --http-port 8765
```

USB 示例用 `--port COM23 --source USB --http-port 8767`。端口号须按实际设备选择；同一串口只能由一个接收程序打开。已存在的 8765 接收器保持运行时，不要在 8767 再选择同一 COM17。

公网 `gmflylog.com` 另外依赖 HTTP 旁路 8766 的显式实时分享；旁路只读取 8765，不再打开串口。见 [分享启动说明](../../web/flight-console/local/README.md)。本目录的启动命令不会自动开启公网分享，也不向飞控发送命令。

离线测试在本目录运行：`python -B -m unittest discover -p "test_*.py" -v`。旧 `ground/` 保留 10-22 的 B0AE 归档，未覆盖其哈希绑定文件。
