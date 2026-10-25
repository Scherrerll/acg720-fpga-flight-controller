# 先综合，再运行派生物理工程

所有输出目录必须是新目录。以下命令从仓库根目录运行，不访问下载器或串口。

```powershell
python -B firmware/B0B2/tools/build.py --synthesis-only --output out/B0B2/NEW_SYN --place 2 --route 2 --replicate 0
python -B firmware/B0B2/tools/build.py --output out/B0B2/NEW_PNR --pnr-only-from out/B0B2/NEW_SYN --global-observer-reset --place 2 --route 2 --replicate 0
python -B firmware/B0B2/tools/verify_offline.py --build out/B0B2/NEW_PNR
python -B firmware/B0B2/tools/install_sram.py --build out/B0B2/NEW_PNR
```

第一条只运行 `run syn`。成功收据为 `synthesis_result.json`，明确不构成物理验收，不产生可用于安装的 `result.json`。独立综合工程即使被摆入额外的物理报告，也不能通过物理收集或安装器检查。

第二条验证综合成功收据、退出码、归档构建脚本、完整控制源码、日志及网表哈希。它创建只启用 VG/CST/SDC 的工程，避免重新综合；从实际 boot/pose LUT 结构唯一证明复位全局网。原引脚、电气配置及单一19.5ns时钟保持，不能任意传入额外网名或时序例外。

第三条仅在实际布线和时序通过后生成离线验收收据。它包含输入策略对照证据核验、真实 tap 的12万拍字段复用回归、被动观测审计、实际UART/CRC、接收器兼容及安装器拒绝路径测试。

最后一条默认只核验离线文件。实际 SRAM 写入仍须当次拆桨、机架放稳、低油门及SWA/SWC低档确认，并检查新鲜停机遥测与唯一下载器；不自动解锁、不写Flash。新生成或旧基准重放的位流均不能仅因完成综合而获得安装或飞行资格。
