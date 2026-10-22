# 第三方来源与许可状态

本工程包含自主适配代码和从其他飞控/传感器实现派生的部分。仓库设为私有；私有归档不代表已取得对所有上游代码的公开再分发许可。本次不为整个仓库套用新的 MIT、GPL 或其他统一许可证。

| 来源 | 导出范围 | 处理 |
|---|---|---|
| 用户提供的匿名/拓空者参考源码 | 有限参考 C 函数、RTL 派生模块 | 保留版权头与来源；未找到可覆盖全部代码的明确宽松许可，公开前需核清 |
| Bitcraze PMW3901 初始化 | 历史光流 reader/init | 随相关源码保留 `sensor/UPSTREAM_LICENSE.txt` 的 MIT 文本 |
| PX4 派生控制/参考实现 | 相关模块 | 保留 `core/NOTICE_PX4.txt`，历史参考模块适用时保留原 LICENSE |
| Gowin 构建报告 | 有限 PNR/时序/资源文字证据 | 保留报告原版权声明，不含编译器二进制/安装包 |

完整 `reference_ano`、TI MCU 库、Bosch API 参考包、第三方资料压缩包和手册不在本次上传范围。特别是原资料树含仅允许面向 TI MCU 使用的文件，不能将整个资料树都标成项目自有开源代码。

来源/字节清单：`history/early_manifest.json`、`history/late_manifest.json`、`firmware/B0AE/source_export.json`、`ground/export_manifest.json`。地面站便携化修改在其清单中逐项列出；其修改不改变上游各自许可。

原始飞行日志和实物照片没有上传。少量历史证明保留原工作区路径及 USB 设备标识；转公开前还需复核第三方权限与这些记录的公开范围。是否转公开由仓库所有者后续决定，本次保持私有。
