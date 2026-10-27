# XY开机默认值定位与B0B4地面站同步

用户指定新默认为共享XY速度P=0.1000、I=0.0350，对应wire1000/350；它们**不是Z高度增益**。generation重启为0，每次成功SET仍递增。下列出处行号以冻结B3及本次B4副本定位为准，不建议修改旧B3树、原receipts、旧报告或旧测试结果。实现落在新`ground/B0B4`；bank/控制器/固件构建由主线负责。

仓库根：`C:/Users/ScherrerL/Desktop/apple/github_publish/acg720-fpga-flight-controller`。

## 1. 需要同步的语义位置

| 精确出处path:line | 新候选要求与本轮状态 |
|---|---|
| `firmware/B0B3/source/xy_pi_parameters.v:12`、`:34` | INIT与reset原为500/0；主线在B4副本改为1000/350。两处generation=0保留，不把历史gen8当新上电代际。 |
| `firmware/B0B3/source/xy_pi_parameters.v:83` | SET成对提交并generation+1；默认变更不改这条语义。 |
| `firmware/B0B3/source/position/mtf_xyz_hold_control.v:207`、`:209` | work快照INIT与bank一致1000/350；state0同时采样完整pair保留。主线负责B4，不能删快照改为运算中读取live系数。 |
| `ground/B0B4/dashboard.html:19` | 初始编辑草稿已同步0.1000/0.0350；不是设备读回值。 |
| `ground/B0B4/xy-pi-ui.js:186` | 默认按钮同步新值，仅填草稿，不发POST。 |
| `ground/B0B4/xy_pi_service.py:46` | 状态API persistence说明同步重启恢复新XY默认；不改变can_set/停机判据。 |
| `ground/B0B4/pi-help.html:4`、`:5` | 默认示例、重启、generation0和XY/Z区别已同步。 |
| `ground/B0B4/README.md:5` | 新候选说明、B4能力、默认值、易失性、只填草稿和测试边界；没有把旧B3实机结果改名为B4通过。 |
| `ground/B0B4/ground_server.py:309` | 默认日志目录改为`ground/runtime/B0B4`，避免旧B3运行记录混入；旧B3服务未关闭或重启。 |

新固件文档由主线在B4交付中同步以下旧版出处的对应段落，不覆写B3原文：

- `firmware/B0B3/PROTOCOL.md:47`：上电500/0改为新版本1000/350；generation0和SET序号/拒绝规则不变。
- `firmware/B0B3/PROTOCOL.md:61`：新默认P内部系数为1000/1000=1；“500/1000对应原1/2”只能作为显式旧参数回归，不能仍称新默认。
- `firmware/B0B3/PROTOCOL.md:64`、`:68`：旧默认数值等价证明是历史范围，新默认非零I需要自己的实际RTL证据；不能把旧I0结论换标题。
- `firmware/B0B3/README.md:13`及`export_package.py:84`：若复用模板，新版描述需同步，不能复制“default .05/I0”。旧导出模板及原manifest保留。
- `docs/XY_PI_GROUND_STATION.md:3`、`:35`、`:59`：主线更新现行B4操作说明时改默认及示例；`:5`等有日期的旧B3安装记录不改写。

## 2. B4能力标识与codec

冻结`firmware/B0B3/xy_pi_cli.py:13`严格拒绝非B3，不能当作无build限制的generic decoder接收B4。主线已另建B4 codec；本轮`ground/B0B4/xy_pi_control.py:11–12`直接只读导入`firmware/B0B4/xy_pi_cli.py`，没有重复decoder、修改旧codec或伪装build/CRC。

能力检查已在`ground/B0B4/xy_pi_control.py:223`、`xy-pi-ui.js:29`与后端提示中同步B4。A591必须返回`0000B0B4`；legacy A580/B0B2标签及接收profile保留。旧B3 A591在测试中明确拒绝。CRC、长度、version、range和status检查沿用，线格式与单位未变。

## 3. 测试定位与保留事项

| 新副本测试出处 | 本轮处理 |
|---|---|
| `ground/B0B4/test_xy_pi_control.py:11`、`:38`、`:90` | 默认字节帧fixture改为B4、1000/350/gen0；断言格式化0.1000/0.0350和wire值；加入旧B3正确CRC帧被拒绝的断言。仍为原53项中的原case。 |
| `ground/B0B4/test_xy_pi_http.py:23` | 响应fixture为新pair，保留故意采用generation5的并发/陈旧代际用例；这不是boot代际测试，不改成0以削弱冲突检查。 |
| `ground/B0B4/test_xy_pi_transport.py:54`、`:128` | 假设备初态1000/350/gen0，响应B4；真实Host/Recorder单一所有者、丢ACK/回读、重连及USB边界测试保留。 |
| `ground/B0B4/test_xy_pi_ui.cjs:33`、`:113–114`、`:150–152` | B4初始草稿、读回fixture、默认按钮断言同步；同时检查I和默认按钮不增加POST。新增B3能力不能授权B4的断言。 |
| `runtime_xy_pi_20261026/verify_protocol.py:21`、`:24`、`:45–46` | 主线复用到新候选的RTL协议测试需同步boot/reset预期1000/350/gen0；原脚本和结果不改。显式SET到500/0及其拒绝预期不应全局替换。 |
| `runtime_xy_pi_20261026/verify_link.py:55` | 新候选真实UART首GET预期应为1000/350/gen0；字节数/仲裁/独立SET预期不改。 |
| `runtime_xy_pi_20261026/verify_control.py:41`、`:71`、`:88`、`:110` | 500/0是旧P005精确回归/I0清理用例，作为显式输入保留，并另增新默认非零I的真实回调见证；不全局替换`I=0`断言。 |

53项Python与Node实际执行回执保存在新`ground/B0B4/test_results/`。CRC正确的响应字节fixture通过实际codec不等于FPGA硬件响应或新位流安装验收；主线另负责实际RTL reset/GET及物理构建资格。

## 4. 不应随默认值改变的内容

- `firmware/B0B3/xy_pi_cli.py:6`及新codec对应GET零负载；GET中的P/I=0不是开机默认。
- SET两值仍必填，不增加“缺字段就用新默认”或NACK/超时自动写默认的路径。
- `xy_pi_control.py:93–103`的未知结果/失效语义、`xy_pi_service.py:35–45,84–98`的停机/epoch/generation门，`xy-pi-ui.js:153–178`的单次提交与无重试边界保留。
- 每次SET仍是同一边沿完整pair提交，ACK后独立GET验证；上电generation0，不能沿用旧gen8或旧会话token。
- 旧P005/I0、V15、B3默认500/0的飞行记录、proofs、source hash、Flash/SRAM回执与归档manifest均为历史证据，不覆写成新默认。
- Z抗饱和修复属于另一个控制路径；改变XY默认不应顺带修改Z系数、着陆判据、SET保护或失联策略。

冻结B3地面站39文件及固件55源的审计前哈希在`defaults_baseline.json`，本轮结束再次核对。没有启动真实接收服务、操作硬件、HTTP机载事务、Git或旧runtime。

## 5. 最终离线回执

复跑命令：`python -X utf8 -B analysis/20261026_z_aw_fix/defaults_verify.py`。脚本约束输出仅在新B4地面站的`test_results/`，绑定测试输入及新B4 codec；测试前后核对原B3的39+55个文件哈希均未变。

- Python原53项测试实际退出0；包含CRC完整的B4、1000/350、generation0响应字节经过实际B4 codec及控制器后的断言，正确CRC的B2/B3响应拒绝。HTTP测试使用自行创建的临时loopback测试夹具；串口为mock。
- Node实际退出0；加载真实HTML/JS与模拟DOM/API，确认初始草稿、默认按钮均为0.1000/0.0350，默认按钮不发POST，严格B4能力、unknown后仅查询恢复、无POST自动重试等边界通过。
- `ground/B0B4/test_results/verification.json` SHA256：`770fa8e15ca39ce511f21e5b5b470e08edd34f358a3038d961ed9a08c4a633ea`。
- 测试绑定的`firmware/B0B4/xy_pi_cli.py` SHA256：`b2f25c0f78343b0d7f6a5fbbaacb08a7b11c8ff857de83a88208b7da6c7ea968`。

逐项diff复核：控制器仅codec路径/模块名及严格build值变更；服务仅B4提示/易失默认说明变更；SET停机门、token/epoch/generation、超时/未知、ACK后独立GET及单串口所有者语义均未改。该回执是地面软件证明，不是实际FPGA响应、B4位流安装或飞行验收。
