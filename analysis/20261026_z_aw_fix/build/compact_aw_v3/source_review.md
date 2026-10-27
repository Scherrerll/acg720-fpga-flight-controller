# compact_aw_v3 共享Z加法器只读语义审查

已检查真实v2→v3差异；v2 hold为 `afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3`，v3 hold为 `9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa`。差异仅新增signed64 `z_add_rhs`/`z_shared_sum`和state22/23/24的三处表达式替换，未见阻塞性语义反例。

* state22选择iz，所以shared为`value+iz`，原式`iz+value`；两操作数均为原signed64别名。state23/24选择bias，分别等于原`bias+value`和`value+bias`。
* 相同64位二进制加法的交换律在溢出截断mod2^64下仍逐bit成立；新声明没有增加窄化、无符号拼接、不同宽度或提前截断。不需要假设“不溢出”或依赖ZI范围lemma才能证明这三处相等。
* sequential case在同一posedge按旧state和旧寄存值求RHS；NBA后的state/iz/bias变化不会反过来改变已采样RHS。state23仍使用当拍更新前bias，24仍使用经过原P数学事务之后的新bias，时刻与v2相同。
* z_shared_sum仅被这三个case消费，其他状态的值不属于接口。reset/cancel分支、taking_off三元门、candidate flags、原rails、66 sums和67提交均未改；没有新增FF、状态或数学请求。

这只是RTL位语义审查，不是映射资源/时序结论。显式共享可能增加输入mux或关键路径，实际综合与完整20ns物理gate仍必须测量；不得以源码少一个加号推断物理节省或放宽时序。
