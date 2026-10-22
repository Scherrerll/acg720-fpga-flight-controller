# GM-FLY 免费托管候选：EdgeOne Makers

这是独立部署副本，免费测试域名 `https://test.gmflylog.com` 已启用 HTTPS。用户已确认中国大陆关闭 VPN 可以打开测试站并看到有效遥测；这是一项实际网络验收结果，不代表所有地区与运营商的长期可用性。主域名 `gmflylog.com` 的 CNAME 已改为平台提供的 `gmflylog.com.pages.dnsoe6.com`，公网 DNS 已确认生效；旧两条 A 记录暂停并保留，验证 TXT 保留。主域名 HTTPS 已正常验证，完整合成 API 冒烟与清理通过；公网实时数据连续3次 fresh=true、最大估计源龄1150ms且序号递增。用户在手机新标签页、关闭VPN，打开准确地址 `https://gmflylog.com/?check=20261022` 后确认“GM-FLY 页面和实时数值正常”，主域名大陆实际使用验收完成。先前截图来自旧 chatgpt.site 入口或缓存；已核对8765接收页面、8766桥接页面与主站HTML无旧托管域名链接。验收截图保存于部署目录旁的 `gmflylog-live-verified.png`。

项目 `makers-pgx1ueruoas8`（gmfly-flight-console-test）；最终部署 `dpuiqjnbrjkm`；全球可用区（不含中国内地），Node 香港区域。默认域名 `gmfly-flight-console-test-yhasagv5.edgeone.dev` 在中国内地需控制台提供的短期访问链接，不能用裸域名的401判断应用失败；正式访问使用自有域名。

当前唯一 bridge 在本地 `http://127.0.0.1:8766/`（PID 19860）运行，转发至 `https://gmflylog.com`，实时分享已明确开启。旧 bridge PID 63588 与测试 bridge PID 33764 已停止；原串口接收器（PID 45828）未修改。每次新启动仍默认关闭实时分享：打开本地 `http://127.0.0.1:8766/` 后，明确点击“开始实时分享”才会自动转发，关闭按钮不影响本地接收和记录。日志分享永不自动执行，只上传用户选定的日志；旧云端历史日志未自动迁移。当前状态为 `complete_apex_mainland_no_vpn_live_confirmed`。

## 已实现

- `public/` 静态前端，保留图例、缩放、拖动和日志分析。
- `cloud-functions/api/[[default]].js` 复用原分享 API，Node 云函数配合 Blob 存储；实时读取明确使用 strong consistency，避免跨节点缓存旧快照。
- 匿名只读、带独立发布令牌才能写入；令牌仅放平台环境变量 `PUBLISH_TOKEN`，至少32个字符。不要放仓库、网页或URL，也不要复用旧平台令牌。
- 本地 bridge 的实时分享默认关闭，在本地网页点击“开始实时分享”后才自动上传。停止分享不影响本地数传接收和日志记录；日志分享仍须逐条主动选择。
- 浏览器隐藏时停止实时轮询；前台有连接时约1秒，断线时约10秒。过期状态仍按真实数据年龄判断。
- 日志 gzip 上传：原始JSON最多8 MiB、压缩后最多5 MiB；超过明确拒绝，不截断。源码保留公网GET大日志的gzip协商，但外部实测即使接受gzip也未出现 Content-Encoding，网关如何处理响应压缩尚未确认；不能声称线上的响应压缩已经验证。服务端按返回正文设置5 MiB上限，超限明确报错，不静默截断。原导出已有20000样本上限及完整性标记仍保留，分享副本不等于本地完整原始日志。

## 构建与验证

本地验证：20项 Node 测试、16项 Python 测试全部通过。Node 20.18+；`npm ci`、`npm run build`、`npm test`。Python检查：进入 `local/` 后执行 `python -B -m unittest test_bridge.py`。后端本地测试使用内存存储，不连接云平台。

云存储初始为空时的 fresh=false 检查已在开启实时转发前通过。冒烟脚本目前仅允许准确的 `https://test.gmflylog.com` 与 `https://gmflylog.com` 两个来源，日志写入只使用合成样本；对当前公开实时状态只读并检查 schema/share 模式及布尔 freshness，不覆盖正在更新的遥测。主域名证书已就绪，完整冒烟与清理已执行通过。另用12000样本合成日志验证了上传200、读取样本数及首尾值、CSV 12000行和删除后404。

完整合成 API 冒烟已在同一运行时修复的先前部署 `dpsnx…` 通过；移除临时鉴权探针后的最终部署 `dpuiqjnbrjkm` 已再次确认 health 200 与有效 fresh live 200。临时诊断接口不包含于最终代码。

EdgeOne 会将原生 Request 的 `.body` 遮蔽成解析后的数据，并将 `.signal` 遮蔽为 undefined；云函数适配层通过 `Request.prototype.body` 原生 getter 取得真实流，再用 URL、method、headers 和 body 重建标准 Request，避免复制这些运行时遮蔽属性导致 JSON/gzip 请求错误。此兼容处理已有测试覆盖。

平台 `/api/health` 已实测返回 `storage_ready:true`。前端源码模块仍为 `.mjs`；构建时发布为 `.js` 副本并重写发布引用，已确认平台以正确 JavaScript MIME 返回，避免浏览器拒绝模块加载。

构建产物 `public/` 只含静态文件。平台云函数源码、`platform/`、`worker/` 和依赖也需要部署，不能只上传 public 文件夹作为纯静态站。

## 开通和部署

1. 用户本人登录腾讯 EdgeOne Makers，按页面要求完成账号实名与服务条款；选择当前免费版，不开通付费模式或自动升级。注册、条款和任何付费变更需用户本人确认。
2. 建立独立测试项目，通过私有代码仓库或官方CLI部署本目录。只提交代码与资源，不提交 `node_modules`、`.env`、本地日志和密钥。
3. 项目构建命令 `npm run build`，输出 `public`；`edgeone.json` 已配置 Node 云函数及境外香港区域。未备案域名先使用“全球（不含中国内地）”区域，能否从目标网络访问必须实测；香港区域不构成国内可达性保证。中国内地节点需先满足ICP备案要求。
4. 平台环境变量配置新 `PUBLISH_TOKEN`，Blob命名空间 `gmfly-flight` 由SDK首次使用创建。先检查临时域名 `/api/health` 和 `/api/live`。首次没有数据时应显示未连接，不能伪造在线。
5. 新候选 bridge 使用新域名和对应新令牌，通过已有隐藏标准输入启动流程配置；默认保持分享关闭。需要并存测试 bridge 时使用不同本地端口；当前正式 relay 仅保留8766。不能停止串口接收器，也不能同时占用同一端口。
6. 临时域名验收：页面与全部图标加载正常；无令牌POST返回401；只读访问无飞机控制功能；启动实时分享后时间和状态更新，停止后按真实时间过期；选定日志上传、样本数和CSV一致，重载后仍可读。分别用关闭VPN的手机蜂窝和Wi-Fi验证。合成 API、云函数存储与 gzip 日志请求已进行平台实测；响应线路压缩未验证；实际日志仍由用户逐条选择分享，避免把测试结果当作任意真实日志完整性承诺。
7. 实测通过后才把 `gmflylog.com` 切到平台实际提供的新CNAME/验证记录；不要猜记录值，也不要提前删除旧Sites绑定。记录旧DNS方便回退；旧站与本地原始日志保留。

## 免费额度和回退

当前官方文档：Node云函数100万次/月、50万GB-s/月；Blob账号存储1GB；云函数请求/响应6MB。按1Hz发布加3个1Hz观看页、每天2小时、30天，主接口约86.4万请求，另需预留对时、日志、重试。多人或全天常挂不适合沿用该预算；实测CPU/内存耗时和平台面板为准，不依赖试运行超限宽限。

实时快照只覆盖一个键，不累计存储；日志只分享选定记录，接近容量时先下载备份，由用户选择撤销分享释放空间。免费额度变化或新计费须重新确认，不能静默转付费。

回退时将 bridge 地址/令牌和已改的DNS恢复原值，保留新平台数据便于核对。此候选未自动迁移旧云日志；可从本地重新选择分享，避免遗漏来源完整性标记。

## 官方参考

- https://edgeone.ai/document/211893332490612736
- https://pages.edgeone.ai/document/node-functions
- https://pages.edgeone.ai/document/blob-storage
- https://pages.edgeone.ai/document/custom-domain
- https://pages.edgeone.ai/document/edgeone-json

此副本源自用户已有私有工程，未授予额外开源许可。前端资源与原工程保持原权利归属。
