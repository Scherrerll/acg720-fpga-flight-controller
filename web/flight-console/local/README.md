# HTTP 旁路与本地预览

仅依赖 Python 3.10+ 标准库。这个进程从已运行的 `http://127.0.0.1:8765/api/state` 读取网页快照，不打开串口，不导入旧接收端模块，不发送 FPGA/电机/校准命令，也不停止原监控服务。源快照由独立线程每250毫秒最多抓取一次（4Hz）；浏览器读取的是内存缓存。日志目录和串口由原监控服务继续管理。

## 无发布密钥的本地预览

在本目录运行：

```sh
python -B bridge.py
```

新页面为 `http://127.0.0.1:8766/`，静态资源来自 `../frontend/`。可用 `--port 8767` 选择另一个空闲本地端口；不要停止现有 8765 服务或重启串口接收器。没有发布配置时，本地实时数据、只读日志和数值 CSV 仍可用，分享按钮由 capabilities 关闭。上游离线时页面显示未知/陈旧状态，不使用演示数据冒充遥测。

## 由主管进程通过 stdin 配置发布

```sh
python -B bridge.py --stdin-config
```

启动后必须通过 stdin 提供**一行** JSON，对象仅接受以下键：

- `upstream`：默认 `http://127.0.0.1:8765`，仅允许 `127.0.0.1`/`localhost` 的 HTTP origin，不接受路径、用户信息、查询参数或任意外部地址。
- `listen_port`：默认 `8766`；命令行 `--port` 可覆盖该非秘密参数。
- `site_url`：共享站点的 HTTPS origin，不含路径、查询参数或用户信息。HTTP 仅允许本机 mock 测试。
- `publish_token`：站点写 API 的发布密钥，主管进程在内存中组装并通过子进程 stdin 管道传入。

密钥不通过命令行、环境变量、配置文件、URL或 stdout 传递；不要将含密钥的 JSON 写入文件、Shell 命令或示例截图。bridge 不回显配置，HTTP响应与访问日志也不包含密钥。密钥仅用于向固定站点 `/api/publish/live` 和 `/api/publish/log` 发送 `X-Flight-Publish-Token` 请求头，值为密钥本身，不加 Bearer 前缀，不使用平台保留的 Authorization 头。请求保留 `User-Agent: ACG720-GroundStation/1.0`；密钥不随静态页面或浏览器代码返回，不接受重定向；本机接收请求不经过代理，外发 HTTPS 使用电脑已配置的系统代理。

配置成功也不会自动上传。每次启动实时分享默认关闭，不请求云端时钟或实时发布。仅在本地页面点击“开始实时分享”后，独立后台线程才最多每秒上传一次**脱敏实时摘要**（1Hz）。点击“停止实时分享”后不再自动请求云端；已在途的请求会先完成，公开快照按原有5秒/10秒规则自然过期。开关不影响4Hz本地接收、录制或手动日志分享，重启后仍默认关闭。上传期间不持有快照锁，不阻塞4Hz源轮询；两个线程只读取初始化后的配置/内存密钥，不并发修改它。慢网络不延长源TTL；源抓取自身超时仍会判陈旧。停止这个 bridge 只停止它自己的 HTTP 旁路与发布，不影响原接收服务和 FPGA。共享站点仍需正确配置自己的写权限和数据保留策略。

## API 与数据边界

- `GET /api/live`：schema 1 实时摘要，与共享站点契约一致。包含姿态、融合运动、RC、PWM命令、健康标记、记录计数与最多120个趋势点。无电池、电流或 RPM 虚构值；未知数为 null，健康标记为 bool/null。
- `GET /api/capabilities`：`{mode:'local', share_url, can_share_logs, sharing_enabled}`。
- `GET /api/logs`：最多200个已有会话的白名单元信息；不读取日志正文，不返回原始 meta、USB 标识、串口、本机路径或任意错误原文。列表中的 frames/duration 等源摘要未提供的数据保持 null，不为取得这些数字自动扫描日志。
- `GET /api/logs/:id`：用户选择某个合法会话后，向原服务请求该会话 CSV，转换成 `{log:{id,title,columns,samples,summary}}`。没有任意文件路径/URL参数，没有 ZIP、原始串口字节或设备元信息透传。
- `GET /api/logs/:id/download.csv`：仅导出固定列中的数字、布尔状态和相对时间。
- `POST /api/share/log`，JSON `{id}`：**仅显式点击后**将选中日志的脱敏 `log` 对象发送到共享站点。成功返回 `{ok,id,share_url}`。查看/下载日志本身不触发日志上传。

`POST /api/sharing` 只接受 `{ "enabled": true }` 或 `{ "enabled": false }`，用于实时分享开关；它复用同源 Host/Origin 校验。手动日志分享仍是独立显式操作，实时分享关闭也可手动分享日志。

本地 API 校验 Host 为实际 listener 的 `127.0.0.1`/`localhost`，跨 Origin 请求拒绝。分享 POST 必须带本地 same-origin Origin 和 `application/json`，日志分享正文只接受会话 ID；实时开关正文只接受布尔 enabled。不存在连接切换、标记、停服务、校准或硬件写 API；未知 `/api/*` 路径拒绝。前端不持有写密钥。

### 新鲜度与时间

源有效断言 `source_valid` 需要上游 connected/fresh/flight_info_fresh 均为 true、合法设备 build 与16位序号，且 `(primary_sequence-info_sequence)&65535` 为0或1：允许当前身份帧比主帧晚一个序号到达，远间隔或旧身份帧仍拒绝。输出 `source_ttl_ms` 保留上游TTL（最多1秒）。本地 `fresh` 继续严格使用源 frame_age_ms 加获取后经过的单调时间；超过源TTL即过期，没有延长实际500ms的源资格。源有效断言与本地呈现TTL分别处理：单纯跨过本地TTL不抹掉 poll 当时的源断言；上游获取失败、没有最近成功抓取或超过1秒未更新时，source_valid=false。

上游断开/清空陈旧 data 时，bridge 只保留此前已脱敏的数值，并明确 fresh=false、递增 age；不会把历史值变成新的实时测量。`received_at` 是本地成功取得快照时间。发布包保留 source_valid/source_ttl_ms，发布包 fresh 使用有效源断言、connected 与最多5000ms的呈现预算；它与本地严守源TTL的 fresh 不同，不能据此扩大设备控制资格。

仅在实时分享开启时，发布线程每60秒对固定站点 `GET /api/health` 同步一次云时钟；公共读请求带相同User-Agent，不带发布密钥，公网使用系统代理。响应必须含 server_time_ms；使用单调时钟测量 RTT，仅接受RTT≤4000ms，记录在响应结束时的服务器基准为 `server_time_ms+RTT/2`。随后 source_publish_at 从该基准与单调经过时间投影，不依赖可能相差数十秒的本机墙钟。包同时携带 `timing_version:2`、`timing_valid:true` 与 `clock_uncertainty_ms:RTT/2`。

旧同步基准最多有效120秒；续同步失败而旧基准仍有效时可继续。无有效基准时仍发布状态，但 timing_valid=false、fresh=false、source_publish_at=null，不能伪装实时。云端重记 received_at，并按 `age_ms += max(0, receive_now-projected_publish_time)+clock_uncertainty_ms` 继续计龄；5秒为远端呈现预算，10秒为远端断线界限，并非500ms源资格被延长。时钟握手和上传都在独立发布线程，不阻塞4Hz本地源获取。

发布包另带 `history_reference_time_ms`，始终是组包时的本机墙钟毫秒，与 history.t 使用同一时间基；它不是云端原采样时间，即使云同步无效也可提供。Worker 可在 timing_valid 时用 `history.t + (投影后的 source_publish_at - history_reference_time_ms)` 映射趋势到云时基；浏览器再以 API received_at 加单调经过时间作显示参考，避免本机与浏览器墙钟差造成轴偏移。

实时趋势由 bridge 自己在每次成功且源有效的抓取后，从当时已脱敏的 attitude/motion 数值最多每500毫秒追加一次，保留最近60秒、最多120点；同一固件/主帧序号不重复追加。点的 epoch 毫秒为本机接收时刻减源 frame_age_ms，不重设源龄。旧源 history 缺融合高度，因此不用于回填过去：刚启动只显示启动以后实际观察到的点，不制造过去曲线。该锚定是主机接收时间估计，非传感器曝光时间。日志样本 `t_s` 则严格来自源 CSV 的 `elapsed_s`（相对会话秒数），不使用 UTC 或 sequence 冒充横轴。

### 日志单位、稀疏值与限额

优先按现有 `analysis.export_csv` 列命名解析：

| 源列 | 导出字段 | 转换 |
|---|---|---|
| `roll_deg/pitch_deg/yaw_deg` | 同名 | 度，原值 |
| 主帧 `selected_height_cm` | `height_m` | 除以100 |
| 导航帧 `nav_fused_height_mm` | `height_m` | 除以1000 |
| 导航帧 `nav_fused_vx/vy/vz_mm_s` | `vx/vy/vz_mps` | 除以1000；融合局部坐标速度，不是机身前向/右向速度 |
| 主帧 `m1_us`…`m4_us`, `throttle_us` | 同名 | μs，命令遥测，非转速/物理波形实测 |
| 主帧 `armed` | `armed` | 真实主帧布尔状态；导航帧的占位 false 不沿用 |

不同协议行仍保持稀疏，不将相邻帧强行拼接、不补零、不填补缺口。MTF 原始斜距不能当垂直高度，模块坐标速度不能当融合局部速度；这类未转换字段与诊断帧不进入统一样本。`columns` 对应完整数值白名单，未上报字段为 null。

每个上游响应最多 **20 MiB**；超限返回413并明确未载入完整日志，不截断伪装成功。完整 CSV 中的相关样本超过 **20,000** 时，保留首尾均匀抽样到20,000，并在 summary 注明 source_rows、eligible_samples、exported_samples、downsampled、complete。summary 的 source_complete 仅表示全部 CSV 响应已读取；不代表无线记录无缺口，也不代表包含已排除的诊断/原始数据。downsampled=true 时 complete=false；CSV 仍是同一抽样结果。active 会话仅代表原服务生成导出时的前缀，不是未来完整记录。

短期日志缓存仅保留最近一次选择结果10秒；不创建新的原始日志文件。序号缺口/复位等日志统计没有可靠映射时保持 null，不编造0。

## 离线验证

```sh
python -B -m unittest -v test_bridge
```

测试只使用内存夹具及随机空闲 loopback 端口的 mock HTTP 服务；不连接8765、不连接真实站点、不接串口。覆盖契约、单位/时间、稀疏样本、超限/抽样、陈旧保留、隐私字段白名单、Host/Origin、固定接口和仅点击后日志发布。调度测试分别证明4Hz源抓取、1Hz发布，并验证发布被阻塞时仍可更新源快照。时钟测试覆盖35秒本机钟差、RTT补偿、不确定度、60秒续同步与120秒过期；另覆盖相邻/远间隔身份帧、本地480+30ms过期但不丢源断言、上游失败不恢复，以及无有效云时钟时保守状态。任何 POST 测试只发往本地 mock。



## 免费额度与传输

浏览器页面进入后台/隐藏时暂停实时轮询，回到前台立即请求一次。可见且连接正常时按请求起点维持最多每秒一次；请求耗时超过一秒时，完成后立即衔接下一次，不再额外空等一秒。短暂断开或请求失败后按1、2、4、8、10秒逐步重试，长期断线最多每10秒一次；恢复或页面重新显示时重置退避。恢复期间继续按单调经过时间计龄，不把旧数据标为新数据。请求全程往返时长只给出源龄上界；该上界跨过5秒、但云端仍确认近期有效时，保留可见读数并标注“延迟接收值”，fresh仍为false。云端已过期、源无效、时间未确认或本地经过时间证明确实过期时，仍灰显最后值。后台之前已在途的单次请求可能完成。日志页的手动刷新/分享仍由用户触发。

手动分享日志使用 `Content-Encoding: gzip`；原始 JSON 超过8 MiB或压缩后超过5 MiB会直接报413，不发送部分数据，也不因传输限制偷偷截断。既有日志脱敏和最多20000样本的公开导出规则保持原样，并继续标记抽样来源；这个抽样规则与传输限额分开。实时 JSON 不压缩。此版本针对支持 gzip 的 EdgeOne 后端，不能把 gzip 日志直接发给未升级的旧 Worker。

额度由云服务当前套餐和实际请求量决定，按需分享只是减少空闲流量，不保证永不超额。首次安装使用新的目录/端口，未修改或重启正在运行的 bridge。


## 2026-10-24：恢复官网实时分享

链路是接收器 8765 → HTTP-only 旁路 8766 → `https://gmflylog.com`。本地有数据而官网仍是旧版快照时，先检查 8766 是否运行及分享是否已明确开启；不要再启动一个串口接收器争用 COM17。

```sh
python local/start-live-share.py --token-env-file /path/to/private/.env --enable-sharing
```

凭证文件应是原有、未入库的 `PUBLISH_TOKEN=...` 配置；也可使用已配置的同名环境变量。参数只包含文件路径，凭证在内存和子进程 stdin 中传递，不回显。启动器复用已有正确的 8766，不停止接收器、不打开串口；同端口属于不同分享目标时拒绝复用。没有 `--enable-sharing` 则不主动打开分享，bridge 默认行为保持不变。

已经分享时不重复提交开关，避免等待发布线程的网络锁。关闭启动器的终端不等于停止旁路分享；通过 8766 网页“停止实时分享”显式关闭。退出/重启电脑后需重新启动；未添加自动启动或定时上传。

离线：`python -B -m unittest test_bridge test_start_live_share`。5 项启动器测试使用 mock，不连接真实网站、不接串口。没有自动分享历史日志。10-24 恢复样本见仓库 validation/20261024/web_relay_recovery。
