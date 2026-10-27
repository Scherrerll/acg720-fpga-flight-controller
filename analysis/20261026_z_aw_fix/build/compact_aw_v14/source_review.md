# v14：只约束两个原始关键网络的综合扇出

从准确冻结v4源55出发，仅改两个文件。顶层previous_pose_valid原reg增加syn_maxfan=10；fallback的原组合active表达式逐字不改，通过一个普通wire同值连接输出，对该驱动wire施加syn_maxfan=50。没有添加寄存器、always块、状态或周期，普通四态连线语义相同。每处替换均有精确反向文本校验，撤去局部属性和同值wire连接后，两个文件文本逐字等于v4。

依据实际v4原始TR：Path1最差setup−0.220ns，fallback active末级fanout115且到selected_throttle布线1.569ns；Path8 previous_pose_valid到共享乘法器数据端点setup−0.140ns，首网布线6.920ns。此前max_fanout100实际新综合把fallback115拆为58/57，但全芯片同时增加81FF/83LUT，其完整物理结果尚未返回。本候选只请求这两个网络的复制，避免全局改变；实际工具是否应用及资源影响必须等新SYN审计，不能从属性字面推断。

官方SUG550-2.4E PDF65-66支持wire/reg的syn_maxfan，可复制寄存器或逻辑；不适用于clock/CE/reset信号，子模块输入端口应约束驱动端。本轮直接约束原数据reg及内部组合驱动wire，不新建或修改clock/CE/reset定义。若工具忽略某个属性，应按真实新网表如实记录。

控制器、PID/Q16精度、全部保护/降级/着陆条件、已批准的抗饱和行为、wire1000/350默认、50MHz/20ns及唯一radio_rx原例外均不改。53文件逐字不变，五场景/FRAC边界/四客户端按原完全相同控制依赖复用；新准确顶层13项门需重新运行。功能复用证明不是新的综合或物理通过。本候选目前只准备，禁止下载；firmware/B0B4/source原型保持。
