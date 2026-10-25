# 冗余字段复用前的源码与结果

此目录保留初始 B0B2 SiK 汇总模块，SHA256 `8bff3d129b80875c4bced236238952ccdee43f8107947ff13489d2c52945dfcc`，以及当时全部 53 个源文件的哈希和相关审查/测试结果。后续仅复用 tap 已保持的五个字段，其他 52 文件不变；变换及逐拍证明见上级 `copy99_integration.json` 与 `copy99_proof/`。

初始网表的完整默认布线剩余 292 条网络；强制已证明的复位全局网后，p2/r2/rep1、p3/r2/rep1、p2/r2/rep0 分别剩余 266、340、210 条，均未生成位流或有效时序结论。原始结果分别保留在 `../../failed_default_route/` 和 `../../failed_global_routes/`。

旧 B0B0 胜出物理脚本采用 replicate=0，源码快照默认采用 replicate=1。前几轮候选沿用了后者，随后已纠正并明确记录。以上失败版本均未安装到 FPGA，未写 Flash。
