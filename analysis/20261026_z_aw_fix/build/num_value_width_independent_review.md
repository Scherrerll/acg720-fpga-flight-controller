# num50 / value39 独立只读审计

实际读取并核对：

* v4 hold：`ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642`。
* v5 hold：`04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873`。
* `num_value_width_design.md`：`e41101a0b8732177ac28769dd5475c12deede0eea01725fcbe04fa0768ffa47a`。

**未发现真实合法消费路径反例，同意signed50 num和signed39 value的方案。** 此结论仅为独立源码审计；没有由本审阅者运行新的v5仿真、综合或改代码。根任务报告的测试结果不写成我本人执行的证明。

实际diff只把num64改为num_store50并按bit49补14个符号位、value_store48改39并按bit38补25个符号位，以及state100写目标改名；表达式、分母、状态和控制顺序未改。

独立复核的关键点：

1. **乘积不能仅凭MA34×MB28的全类型范围论证。** 我逐类追了calc配对。最大者是两个S33的hx/afx或hy/afy之差（绝对值≤2^33−1）乘S17 alpha（绝对值≤65536）：`2^49−65536`，严格落在S50。世界加速度S32×trig S18最多2^48；norm S18×限幅speed、dt314×65536、clip500Q×dt100000及其他常数乘法均更小。state20的`afz+value`是在AFZ写回截断前求值，需使用真实1/5松弛的有界性，不能仅因目标寄存器S32就宣称右式S32；即使用更宽的S32+S34/5保守界，该组仍远小于全局乘积/商最大值。
2. **商必须按原分母及前驱配对。** 不能把num50除最小分母5来证明S39。最大商来自S32负端点ex/ey乘U16增益65535，再除1000：`RN(140735340871680/1000)=140735340872`。它大于2^37而小于2^38，S39够用，S38不够。这里使用真实nearest/ties-away，不用trunc替代。
3. state6/7的`calc(value,gain,1000)`不能拿任意value39来盲乘；该value的前驱是`clip(fix,±500Q)*dt/1000000`，dt已硬检查1000..100000，因此绝对值≤50Q。这个调用关联是闭合商界的重要条件，源码中的return_state路径满足。
4. 分母均为正literal或`10000000+314dt`；后者在[10314000,41400000]且无uint32溢出。闲置den初始1不等于一个新calc请求。POSITION_KP_Q16只影响未参与calc的旧位置暂存声明，不引入新大乘积；支持的速度格式为F0/F16。
5. num只在state100且md有效时接收本client product；value只在state101且dd有效、derr为0时接收quotient。真实service的owner/epoch/live-cancel拒绝其他client及已取消旧响应；全局取消或XY取消分支先退0。不能用伪造md/dd与任意64位result替代该服务契约。异常/取消没有新的无界写入。
6. 初始值均0；reset/cancel本来保留num/value，保留的旧值仍在上述范围。对原v4先证明每种写入有界，再按首个差异归纳证明新sign-alias逐bit还原；没有先假设v5正确再反推界。与MA/MB不同，本次num/value可以在idle和取消拍也要求64位别名严格相等。

范围结论适用于原控制/返回路径、真实math服务及其接纳条件；不是任意force私有状态或恶意math响应的全模块形式验证。若恢复位置外环、增加calc、扩大dt或改变分母/return_state，需重审。此次没有建议降低时序要求、削减保护或新增构建；物理结果仍由原完整20ns gate决定。
