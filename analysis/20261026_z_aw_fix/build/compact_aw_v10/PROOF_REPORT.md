# v10 诊断快照等价与综合

v10只改v9导航文件中的Z诊断打包。原始Z delta/collective/target与已有z_active标志一起快照，输出按同一快照标志归零；物理控制表达式、所有控制/融合状态机、参数、Q16及周期保持逐字节不变。原v6真实晚路径到diagnostic_q[63]/RESET是此项的依据。

直接执行两份源码完整diagnostic_next/寄存器/diagnostic_body块，shadow_flags[4]按实际源码保证等于同拍z_active。两个复位模式各比较720位，共160001拍；active33118、inactive33116、X/Z标志66237、hold22622、reset2255。包含原始Z字段X/Z、复位/保持X及输入变更不泄露当前值的断言。无私有force；这是提取块在精确接口契约下的证明，不冒称完整导航/飞机仿真。数学恒等式及hold/reset归纳说明见source_review.md。

实际顶层13项保护门也通过；compile/simulation/top及最终proof runner均真实exit0。控制器六个依赖、生产者、真实高度融合与共享数学服务未改变，按哈希复用v9/v8已通过证明。

首轮抽取夹具缺z_reason及显式mask位宽声明，compile实际4/root1，无仿真。原件保留；retry02在新目录补全声明、启用default_nettype none/-Wall并加强原始Z字段X/Z刺激。候选RTL未因夹具修正而改变。见FIXTURE_CORRECTION.json。

一次新SYN及全部时钟/同步器/默认增益/18端口审计通过，vendor/runner真实0。精确VG为607efaa6573e13c53802c7db227bc831a34778a6358de6da6b79962a413dc680；FF27751/ALU9544/LUT36198，相对v9为0/0/−25。资源变化不构成物理时序资格，mask后移可能影响后级遥测数据路径，必须实际PNR复核。

完整布线、50MHz五类slack非负及setup/hold0等物理门和独立raw复核未完成前，没有下载资格；实体状态、SRAM地面读回、Flash与完全断电另验。未增加着陆等待指令或改变低空掉高行为。
