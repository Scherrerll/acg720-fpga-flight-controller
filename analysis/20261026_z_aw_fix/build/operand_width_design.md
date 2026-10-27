# v3乘法操作数34/28位范围审计

只读基线：`out/z_aw_fix_20261026/compact_aw_v3/canonical/source/position/mtf_xyz_hold_control.v`，SHA256 **`9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa`**。本审计未执行仿真或构建。

**结论：没有发现实际服务消费路径反例。正常可消费乘法请求的a可用signed34保存，b可用signed28保存，随后仍须显式sign-extend为signed64参与原运算。** 不能宣称每次`calc`捕获或全部模块端口无条件逐拍相同：一拍非法az可在取消窗口产生超34位a，且ma/mb原本在reset/cancel不清零，算口差异可一直保留到下一次calc。该请求在服务消费前已被取消；控制/安全发布逐拍相等与实际消费操作数相等是所需验证契约。

## 1. 精确位宽与闭合调用表

记Q=65536，S_n=`[-2^(n-1),2^(n-1)-1]`，U16=`[0,65535]`。signed34原始整数范围为`[-8589934592,8589934591]`，相当于Q16的`[-131072,131072)`；signed28为`[-134217728,134217727]`。表中位数是安全保存位数，不是建议改变运算表达式宽度。

源码静态枚举共**34个calc调用**，全部列于下表。未列的state没有calc；state100/101只传递乘积/除法与返回状态，不另构造乘法请求。

| 调用state →返回state | a及范围依据 | b及范围依据 |
|---|---|---|
| 0(Z)→20 | `pending_az*Q-afz`：合法az±30000、afz为S32，绝对值≤62768Q，S33足够；非法窗口见后文 | 1 |
| 43→44 | pending_nx，S18 | horizontal_speed_limit：任何ph先经signed64乘98304，再clip到[500Q,1500Q]=[32768000,98304000]，fits S28 |
| 44→45 | pending_ny，S18 | 同上 |
| 45→1 | dt*314，dt∈[1000,100000]，范围[314000,31400000]，S26 | 65536，S18 |
| 2→3 | hy−afy：两个S33之差，范围[-(2^33−1),2^33−1]，**须S34** | alpha，S17 |
| 3→4 | afx，S33 | 3 |
| 4→5 | afy，S33 | 3 |
| 5→6 | clip(fixx,±500Q)，绝对值≤32768000，S26 | dt∈[1000,100000]，S18 |
| 6→64 | 上一步RN(clip(fixx)*dt/1e6)，绝对值≤50Q=3276800，S23 | zero-extended work_i，U16，fits S17 |
| 64→7 | clip(fixy,±500Q)，S26 | dt，S18 |
| 7→65 | 上一步RN(clip(fixy)*dt/1e6)，绝对值≤50Q，S23 | zero-extended work_i，U16 |
| 65→8 | ex，S32 | zero-extended work_p，U16 |
| 8→9 | ey，S32 | zero-extended work_p，U16 |
| 9→10 | sx，S29 | 1 |
| 10→11 | sy，S29 | 1 |
| 30→35 | −sample_vx：sample为S31，取负最多+2^30，S32 | cs，S18 |
| 31→32 | world_sy，S28；**31无正常入口**，仍满足宽度 | sn，S18 |
| 32→33 | world_sx，S28；仅从31链进入 | sn，S18 |
| 33→34 | world_sy，S28；仅从31链进入 | cs，S18 |
| 34→35 | world_sx−sample_vx：S28−S31，绝对值≤2^27+2^30−1，S32；仅从31链进入 | cs，S18 |
| 35→36 | world_sy−sample_vy，同上，S32 | sn，S18 |
| 36→37 | world_sx−sample_vx，同上，S32 | sn，S18 |
| 37→38 | world_sy−sample_vy，同上，S32 | cs，S18 |
| 38→39 | world_ax，S32 | cs，S18 |
| 39→40 | world_ay，S32 | sn，S18 |
| 40→41 | world_ax，S32 | sn，S18 |
| 41→42 | world_ay，S32 | cs，S18 |
| 42→2 | hx−afx：两个S33之差，**S34** | alpha，S17 |
| 20→21 | afz+value，value是同事务RN((azQ−old_afz)/5)，与old_afz相加位于两个整数端点之间；两端均S32，所以结果S32 | 1 |
| 21→53 | inner_alt_speed：Z state0先从signed32 alt_speed重写，再在21使用，S32；66的sum31复用不会越过下一次Z0定义 | 3 |
| 53→22 | clip(exz+value,±1000Q)，绝对值≤65536000，S27 | 11 |
| 22→23 | 350Q−bias，bias即使取整个S33类型界，范围[-4272029695,4317904896]，**S34** | 6908 |
| 23→24 | exz，S31；在24复用为P+bias前即已送入calc | 1 |
| 62→54 | alt_speed，S32 | 11 |

最大b为1500Q=98304000，严格小于2^27。表中gain按任意16位直接模块输入的U16处理，**没有借用bank的0..10000限制**，也不缩work_p/work_i。sin/cos按整个signed18类型界处理，不借用理想±1假设。

dt初始20000，实际用于XY的dt仅在接纳position_update且1000≤position_dt_us≤100000时更新；非法dt走blocked分支，不写pending pdt，也不能建立一个使用非法dt的新position_due。cancel保留或清状态不扩大该dt界。RN为真实divider的nearest/ties-away，50Q最大值是精确整数端点，单调RN不会把它扩大。

`afz+value`不是把任意48位value相加：可达state20的value必须是当前Z0请求的匹配除法返回，且afz在该请求到20之间没有其他非取消写。对整数D，RN(D/5)位于0与D之间，故滤波加和不越过原afz和合法azQ。若重置/取消则退出到0，不继续消费旧20。不能用私有force/伪造math_done/result破坏这一服务契约后再套范围证明。

## 2. 大位置信号及泛型

`position_px_store/py_store`有49或64位，qx/qy有41或64位，但这四个名称及其64位alias**没有任何运算读取、calc实参或公开发布使用**；POSITION_KP_Q16只出现在这些声明的宽度条件。position_ex/ey只在XY接纳时写，未连到calc。state31没有入口（正常30直接返回35），31–34残留链也已在表中按类型界覆盖，并未靠删除它们取得34/28结论。

所以当前闭合调用表对任意POSITION_KP_Q16整数均成立，不需要按该泛型把ma回退49/64。**不应顺便删除泛型/位置信号，也不能把本证明推广到将来恢复位置外环后**；一旦新增position_px等calc输入，必须重做范围审计及条件宽度适配。VELOCITY_FRAC_BITS只覆盖源码明确支持的0和16；其余值已有原始$error，不为未支持配置新增承诺。MAX_ANGLE/MAX_DELTA只作用于发布夹紧，不扩大乘法实参；CAL_MASK/CLK_HZ/ENTRY_TICKS不增加本表的乘法来源。

## 3. 非法一拍az：不能宣称无条件算口相等

考虑tracking中、state0空闲，数值检查此前有效，z_stick不忙、sample_update=0；C0在height_update同时给一拍az=INT32_MAX，随后恢复合法值。下面是源码时序推导，**尚未新跑该定向波形**。

| 时钟边沿 | 控制器与数值检查 | 服务观察 |
|---|---|---|
| C0 | 捕获pending_az=INT32_MAX并置height_due；check_az同沿捕获非法值；hbounds仍取前一拍有效check，cancel仍0 | 新mul_start还未出现 |
| C1 | hbounds对C0非法check变0；pending height stick最早本拍完成捕获；cancel仍采旧ready | 仍没有本次乘法请求 |
| C2 | state0最早接纳此pending tuple，calc捕获a≈2^47，旧ma50和新ma34可不同，mul_start变1；**同沿cancel采到此前hbounds=0而变1** | 服务在C2采的是旧mul_start=0；C2后request=1与cancel=1同时出现 |
| C3 | cancel优先于case，退0、清due/发布历史及积分，mul_start默认0 | `cancel[i]`优先清pending/更新epoch，不接受该request；found也排除cancel client，不能grant/捕获该a |

若stick仍忙、服务排队或控制器先前工作未完成，接纳只会更晚，cancel会先退0/清due；不会让非法a更早被消费。非法tuple如遇height_due已满，会直接blocked并清事务，不覆写新的待处理合法参数。恢复后必须重新height_update建立due并经Z0重写操作数。

ma_store/mb_store在原reset/cancel路径**没有清零**。因此旧/新ma差异不仅可出现在C2取消瞬间，还可保持整个取消后空闲期，直到下一次calc；math_mul_a在这期间也可不同。不能加reset来掩盖差异，那会增加原本没有的语义/控制树变化。此例是“每次calc都小于34位”的反例，但不是新控制发布的反例。

## 4. 每个请求到实际消费的取消隔离

控制器的calc在边沿t写操作数寄存器并置mul_start，服务最早在t+1见到该request。`nav_math_service.v:70–90`对同一client先检查cancel：cancel=1清pending；否则request且非busy才入队。真正捕获held_a/held_b在IDLE选择pending且**当前cancel=0**的client时发生，不在无条件总线上采数。

非法C2请求的cancel在request首次可被采样的C3已经为1，故没有新的pending/grant/held_a消费。若其他合法client当时拥有服务，其held_a/b独立、不会读取该client操作数；只有owner自己的cancel/epoch变化能中止其事务。若该client有旧事务，cancel使pending清零，owner_cancel及generation/response_epoch拒绝旧完成，done还受live cancel遮罩。取消释放后，已清pending且无新request时，保留的闲置算口差异不能凭空被grant。

所有**实际合法request/实际grant**则来自表中范围：34/28存储再sign-extend还原原64位a/b，产品、den、divider返回、return_state与周期数相同。这里不改变数值checker、hbounds/xybounds、cancel/xy_cancel注册级、service pending/epoch/owner逻辑或公开mask，因此取消保护时刻不因存储位宽改变。

## 5. 已有验证范围与明确剩余点

已只读检查当前v3 `shared_add_regression/aw_tb.v`及pair_harness：五场景包含上下饱和、恢复、22/23/24/66/67及RC/height_valid/origin取消、TO=false；但harness把az固定为0，取消通常保持8拍。它们**没有覆盖上述state0同沿height_update+一拍INT32_MAX az的最早消费窗口**。已有top13侧重真实停机/arm/commit边界；不能把这些PASS或历史毫秒级30001注入当作本次一拍算口缩位已验证。此审计未运行新验证。

若实施，应保留所有控制/安全公开输出和start/cancel侧带的逐拍比较；实际合法request/grant上的a/b必须严格相等，非法窗口另外断言service该client无新pending/grant/operand消费、无新控制发布、旧epoch响应不可被提交，并测试恢复后下一完整回调。**不要对闲置/取消math_mul_a/b作无条件相等断言，也不要放宽真实有效工作断言。** 最小定向覆盖还应包括C0/C1/C2相位、owner空闲/其他client占用/本client旧响应、az正负极值及30001、vz/XY/非法dt边界、FRAC_BITS 0/16和POSITION_KP非默认。

允许的实现仅为ma50→34、mb34→28及对应64位符号扩展（ma补30个符号位，mb补36个）；任务接口/表达式/数值检查/取消时序/数学服务/结果与分母宽度均保持。资源收益尚未测量，共享乘法器还服务其他宽操作数client，**不能承诺DSP一定减少或按22个源码位直接承诺映射FF节省**。

书面结论可支持建立独立宽度候选并进行新定向仿真/一次资源综合；它本身不等于该新候选已通过仿真、SYN或PNR。没有未解决的服务消费路径反例；明确待测的是上述一拍非法输入时序及取消后闲置算口不相等的比较契约。
