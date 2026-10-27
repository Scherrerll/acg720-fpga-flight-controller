# v15：着陆阈值比较分配到油门选择器之前

依据 v4 实际最差路径 output_az_3 到 flight_state/flying_ms_3：垂直可用性经过 fallback active，再选择16位 collective，随后比较 collective<1250，最后着陆状态分支可清零 flying_ms。这里仅把同一比较分配到两个数值分支，再选择1位结果，不添加寄存器、周期或保护延迟。

严格等价依据：active 为1时 fallback_collective 等于 fallback_unmasked_collective；active 为0时 selected_throttle 等于 hold_collective_us。因此对硬件二值输入，(active ? (active ? unmasked : 1000) : automatic)<1250 等于 active ? (unmasked<1250) : (automatic<1250)。阈值与所有着陆条件/优先级保持。两个纯组合分支比较使用 syn_keep 防止工具把阈值重新吸收到宽选择器之后；实际映射效果必须看新网表与 STA。

ano_flight_state 新增默认0参数 PRECHECKED_COLLECTIVE 和一位输入；默认仍逐字使用原 collective_us<1250，core 显式启用并传入同拍谓词。各 always 块内仅替换该条件名字；所有状态、更新式、复位、初值与输出不变。新增接口不用于其他调用者。对于无效 X 输入的仿真四态传播不作通用代数等价声明；自然初始化和二值功能输入须严格逐拍对比。

只改 core/flight_core.v 与 core/ano_flight_state.v；53文件字节不变，包括 v4 反积分控制器、XY1000/350默认、时基/时钟/约束。修改文件的 CRLF→LF 若存在会单独记录。候选先跑阈值全值覆盖、旧新完整飞行状态逐拍比较和原 top13，再绑定原六依赖五场景/FRAC/争用与43地面输入。新综合/物理资格另验；不得从这个数学依据宣称已通过时序或安装。


# v16：只给实际187负载的fallback组合数据驱动施加局部syn_maxfan50

v15实际SYN/严格时钟和增益审计已通过，AZ→flying_ms组合锥体19→14级，但fallback active实际合并到187负载。此候选在准确v15源上仅对原active表达式经同值普通wire施加局部syn_maxfan50，不给previous_pose_valid加属性，不全局改SYN fanout，不新加状态、周期或时钟。原厂SUG550支持内部wire/reg综合扇出约束；先前v14此属性确实拆分驱动，但v14物理未布通，不是v16成功依据。v16必须新测完整原/新/default FSM、实际fallback关系和原top13，新综合/物理另验。相对v4共3文件变化、52文件字节相同，B3相对6文件。上方v15叙述仅说明父候选；本候选不宣称只改2文件。


# v17：previous_pose_valid 数据寄存器的局部 syn_maxfan10

从实际已证明/综合通过的v16只新增一个综合注释，RTL时钟、FF定义/状态与表达式不变。依据旧v4原始TR，previous_pose_valid→共享乘法 held_a38/42 为setup−0.140ns，首网布线6.920ns；v16实际映射仍有19个引脚负载。此前v14同属性真实产生9/8负载副本，但v14原19级主路径未布通，因此不能作为v17物理成功依据。此候选保留v16已缩至12级的主路径与active扇出50，只对第二条旧关键数据网请求局部复制；不约束clock/CE/reset，不新增状态或周期，不改全局扇出。必须以新SYN实测是否复制并保留严格50MHz物理门。相对v4共4文件变化，B3相对7文件。上方各段分别为父候选沿革，本段给出最终新增范围。


# v18：同拍缓存输入速度范围，保持原数据与公开时序

在精确v17上仅新增四文件的MTF速度范围谓词。metric observer由明确signed32 next_vx/next_vy表达原先条件选择的同一32位字，在每个sample_valid（包括重复时间戳）同拍发布这两字及范围谓词；初始化/复位为零速度及true，未发布时一起保持。未修改解析器、metric_commit、积分/定点算术、有效性/年龄或任何时基。真实增加一位同元组谓词状态，不能声称RTL无新状态；不增加旧输出的周期延迟。nav/shared geometry的参数默认0，原调用者保持原signed32比较，顶层仅对正确连接的新元组显式启用。

独立组件证明包含真实旧/新metric全signed16扫值及signed64参考、两种完整UART模式的全部旧公开位比较、正负999999/1000000/1000001边界与异常/重复/失联恢复、旧/prechecked/default三映射几何模块和9份真实数学服务。实际9份成功compile/vvp/父supervisor等待回执经主会话重新核验，原回执字段仅通过有原SHA的适配记录统一命名。组件证明不等于物理通过，也不能替代新的完整top13及50MHz布线。

相对v4共7文件，48文件字节相同；相对B3共10文件。P/I1000/350gen0、原反积分控制器、50MHz/20ns、18引脚及原唯一radio_rx例外保持。上方各段为父候选沿革；本段说明最终新增范围。
