# Conditional-Z-I 临时存储生命周期复用复核

审阅输入为B4-v1 hold SHA `5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c`。四项均可复用；未发现阻塞项。本结论不把资源增长认定为1416未布通的唯一原因，不构成物理通过。

| 原暂存→复用目标 | 完整生命周期证据（当前v1行号） |
|---|---|
| candidateI→iz_lower_q | 134声明/初始化，298/308原有reset/cancel清零；407 state53写动态下rail，411 state22是其最后读。state22右式使用旧rail完成clip后，可非阻塞覆盖为candidateI。下一Z回调必先走state53再22，重新生成rail。 |
| P+bias→exz_store | 157声明、201有符号扩展；405 state21写初误差，408 state53加入速度前馈，415 state23调用calc(exz,1,5,24)是最后误差用途。calc已把操作数锁进ma/mb，经过100/101完成乘除后才回24，因此24可写P+bias，66再读。无55/61后续读。 |
| candidateSum→inner_alt_speed | 108声明；349 Z入口0捕获上个alt_speed，405 state21调用calc(inner_alt_speed,3,5,53)后不再读原值。66可覆盖candidateSum，67消费。下个Z入口0先重捕获；XY不读取它。 |
| currentSum→sample_vx_store | 154声明/198有符号扩展；347 Z入口写vz，405 state21读后不再用于Z。XY仅356入口写vx及390/394/396读；每次XY入口一定先重捕获。66在work_xy=0的Z事务中覆盖currentSum，67消费；55/61不读。 |

单FSM使XY与Z的实际计算互斥；pending tuple可并行到达，但只更新p*/pending字段，不会在入口0前改写上述工作暂存。XY取消342–343只回滚ix/iy/afx/afy，不读取这四项；Z事务work_xy=0，不误走该分支。global cancel/reset返回0并丢弃待办，下一次必须经0→20→21→53→22→23→24→66→67重新刷新各项。没有新增状态、数学请求或提交时刻。

宽度：exz_store和sample_vx_store均为signed31 Q16（范围±16384单位）。即使仅按原exz_store的31位范围而不依赖精确传感器上界，P=exz/5约±3276.8；bias自然复位轨迹0..350、|I|≤2000，则P+bias及两个总和都保守落在±5627以内，适合31位。候选I仍用原64位clip与rail，接口alias保留33位。inner_alt_speed虽声明64，66右式应先明确取有符号31位总和再sign extend64，避免引入64个独立FF；入口0的alt_speed符号扩展仍保留原表达式。

四个原新增*_store名称可改为signed33 wire alias，供有效提交阶段观测。它们在无效/取消阶段不再保证与v1私有寄存器的清零值一致：例如inner_alt_speed/exz/sample_vx原本没有运行时reset。**不要因此盲加reset扩大原复位树。** 等价比较应要求全部module端口每cycle及已提交I/bias/目标/输出一致，并在22候选完成、24 PB完成、66总和完成后的有效阶段比较alias；不能对invalid临时别名作全cycle相等断言。原取消回归中临时reg清零检查需要用“无新发布、真实I/输出清零、下一完整回调不消费旧候选”取代并披露。

建议新候选pair测试用scoreboard记录每个67确实自本epoch经过22/24/66，取消时清scoreboard；不一定需要新增硬件valid FF。所有正常、饱和、反向恢复、taking_off=false、XY/Z交错和取消路径必须保留。新综合只报告真实FF/LUT/CLS/时钟/映射变化，不预先承诺节省数量或布线修复。
