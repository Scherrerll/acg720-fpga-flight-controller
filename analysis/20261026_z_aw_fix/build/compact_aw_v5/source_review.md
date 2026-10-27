# compact_aw_v5 num/value存储实现核对

v4 hold ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642，v5 hold04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873。只有4条原字节替换：num64声明换成num_store50+64位signalias、state100写目标改num_store；value_store48换39及其64alias补25符号位。其余54输入、全部表达式/状态/接口/分母/请求取消不变，无新reset。

源级数值证明见../num_value_width_design.md，SHAe41101a0b8732177ac28769dd5475c12deede0eea01725fcbe04fa0768ffa47a。关键界为乘积绝对值<=2^49-65536、RN商绝对值<=140735340872<2^38，分母/返回状态配对和真实owner/epoch契约保证不摄入其他client或取消旧响应。初始0及每次合法写入有界，所以num/value的64位别名可每拍对比，包括idle；不新增MA缩位那种允许差异。

root将并行原AW/边界/top/四client验证并额外检查num/value别名；本文不提前称这些新回归已通过。此runner仅一次map2 fulltop elaboration/SYN与原mapped/strictFFclk50/radio/gain/18port审计，实测资源对v4，禁止擅自PNR。
