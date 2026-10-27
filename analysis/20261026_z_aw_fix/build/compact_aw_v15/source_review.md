# v15：着陆阈值比较分配到油门选择器之前

依据 v4 实际最差路径 output_az_3 到 flight_state/flying_ms_3：垂直可用性经过 fallback active，再选择16位 collective，随后比较 collective<1250，最后着陆状态分支可清零 flying_ms。这里仅把同一比较分配到两个数值分支，再选择1位结果，不添加寄存器、周期或保护延迟。

严格等价依据：active 为1时 fallback_collective 等于 fallback_unmasked_collective；active 为0时 selected_throttle 等于 hold_collective_us。因此对硬件二值输入，(active ? (active ? unmasked : 1000) : automatic)<1250 等于 active ? (unmasked<1250) : (automatic<1250)。阈值与所有着陆条件/优先级保持。两个纯组合分支比较使用 syn_keep 防止工具把阈值重新吸收到宽选择器之后；实际映射效果必须看新网表与 STA。

ano_flight_state 新增默认0参数 PRECHECKED_COLLECTIVE 和一位输入；默认仍逐字使用原 collective_us<1250，core 显式启用并传入同拍谓词。各 always 块内仅替换该条件名字；所有状态、更新式、复位、初值与输出不变。新增接口不用于其他调用者。对于无效 X 输入的仿真四态传播不作通用代数等价声明；自然初始化和二值功能输入须严格逐拍对比。

只改 core/flight_core.v 与 core/ano_flight_state.v；53文件字节不变，包括 v4 反积分控制器、XY1000/350默认、时基/时钟/约束。修改文件的 CRLF→LF 若存在会单独记录。候选先跑阈值全值覆盖、旧新完整飞行状态逐拍比较和原 top13，再绑定原六依赖五场景/FRAC/争用与43地面输入。新综合/物理资格另验；不得从这个数学依据宣称已通过时序或安装。
