# compact_aw_v2 direction flags：只读审阅通过

对照v1/v2 canonical的55项文件，**唯一差异是hold控制器**；其余54项逐字节相同。v1 hold SHA `479f757149a57ac0b5f9e0334dab80cae475a5345b834fde9c5130c701057ac3`，v2 SHA `afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3`，与root冻结值一致。未编辑这两个源或任何构建fixture，未运行测试/综合/PNR。

**未发现阻塞问题；该代码准确实现已证明的sign-step替代。** 结论限于从复位可达、合法接纳输入、真实数学服务返回的执行，不把force私有I/状态值纳入等价范围。lemma见上一层`sign_step_bound.md`，SHA `cf2a9de051973862c68cd2d462678cf6436756c3a65cc4ef2c4f16f933de9c0d`。

- **state22分支正确**：candidate写入原`iz_lower_q`别名时，同沿NBA捕获`candidate_i_up <= taking_off ? value>0 : iz<0`及down的`value<0 : iz>0`。此处value仍是实际I步长d；RHS的iz仍是旧已提交I。taking_off=false明确提出candidate0，所以按旧I负/正来确定向上/向下，未误用d符号，也没有把flags一概清false。
- **state66确实只删除两动态比较的写入**，两个候选/旧输出和的加法与压位/符号扩展、state转移没有改。22到66没有其他IZ提交；普通XY撤销只处理XY状态，Z回调的work_xy为0。全局cancel/reset/origin/blocked清I/flags并退state0，不能继续提交旧67。因此在能到达67的执行中，22新flags与v1原66的candidate>oldI、candidate<oldI相同。
- **TO任意变动已覆盖**：flags跟随22构造candidate时的TO，而非后来66的TO；23的bias松弛/清0仍在[0,350]。67仍以当拍taking_off选择提交或强制I/collective为0。故22/23/66/67间任意TO翻转不构成反例。
- **量化前提正确**：注释写最大步长72090 Q16，吻合实际RN/ties-away除法；并非错误的“恰1.1”或trunc。旧I归纳[-350Q,850Q]给出raw candidate[-23009690,55777690]，严格落在最紧±1650Q rail内，故clip不改方向。state53 I步与state23 P使用同一不溢出31位的误差，d的正/负蕴含P非负/非正，维持该归纳。
- **rails及输出未变**：state53原上下rail计算、state22原clip表达式、state23 bias、state24 P+bias、66的两输出和、reject_z_i两条件、selected_z_i/selected_z_collective选择、67的提交/0..850夹紧均与v1相同；仍为原+2时钟。raw diff仅新增22的两个赋值/解释注释，并把66赋值改为注释。
- flags只是在私有生命周期中更早更新；它们唯一决定提交的使用在67。此审阅不要求22..65私有flags逐拍相同，不宣称全私有状态等价。

因此可进行root已安排的真实原B4v1逐cycle公共输出等价、主动区间I界断言及新资源测量。此报告本身是源级审阅，不冒充这些测试已通过，也不承诺ALU、LUT或布线收益。03旧P3R1物理任务继续独立等待实际终态。
