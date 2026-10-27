# compact_aw_v2：map1综合资源画像

**真实full-top elaboration及SYN均正常p.wait()=0，mapped gates全部通过；与同源码map2相比没有资源节省。** 本profile没有执行PNR或STA，不是50MHz物理资格。root随后单独授权的新物理尝试在另一个fixture，结果独立记录。

输入来自`out/z_aw_fix_20261026/compact_aw_v2/canonical/source`全部55项，hold SHA `afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3`。副本`map1_synthesis_01/source`与canonical55逐SHA相同，前后不变。源`build.tcl`仍map2且字节不改，只有新`map1_synthesis_01/synth_only.tcl`将map2覆盖为map1、run all改run syn并以EOF返回；UserCode B4、replicate0、global_freq50、原SDC20ns及唯一radio_rx pad false-path保持。

| 实际compiler mapped资源 | map2 v2 | map1 v2 | 差值 |
|---|---:|---:|---:|
| 全top FF | 27786 | 27786 | 0 |
| 全top ALU | 9592 | 9592 | 0 |
| 全top LUT | 36369 | 36370 | +1 |
| controller FF/ALU/LUT | 3298/1609/4985 | 3298/1609/4986 | 0/0/+1 |
| parameter bank FF/ALU/LUT | 290/79/437 | 290/79/437 | 0/0/0 |
| MULTALU27X18 / MULT12X12 / MULT27X36 / BSRAM | 30/7/13/2 | 30/7/13/2 | 均0 |

完整compiler层级资源树见`verification/map1_vs_map2_resources.json`，不是只比较选中行。新map1 VG SHA256 `3b90c12efcd48a1ce9b778194f4be6c7985e0fa99e3d3f456a3a06c593900d49`；不同网表不等于已证明路由更好。

实际新VG重新flatten审计：27786个FF全部clock来自clk50；包含DSP/RAM的27888个clock pins仅clk50或允许的常量GND。radio pad仅到第一同步级D，meta-Q仅到第二同步级D；没有放宽同步后时序。top实际18个scalar ports与冻结CST一致；P/I各16个live FF，逐bit INIT重构为1000/350。详见`mapped_audit.json`、`ff_clock_detail.json`、`gain_port_audit.json`。没有重跑功能RTL，因为输入55项与map2 v2完全相同；不把此前功能结果称为本profile重跑。

真实命令及过程PID、工具/runner/Tcl/source55 SHA、EOF sentinel和actual p.wait回执见`verification/{build_input,synthesis_input,elaboration_exit,synthesis_exit}.json`与原始日志。运行入口为本目录`run_synthesis.py`，仅写独立profile目录。其原样只读导入的gate provider与v2 gain/port audit代码均单独SHA绑定，输出globals指向新profile，未修改旧helper或旧fixture。

最终SYN冻结清单`map1_synthesis_01/synthesis_freeze_manifest_final.json` SHA `1926bf61976b67a15325301cca8fbb37d0df8d7464de0337d96144a44ca5d1f6`，79件；它保留并绑定添加FF精确时钟细分前的interim快照`5548e2dbd5ccf16907692615f5253f09ae8177da39c317df59affd9d8408c6d5`，没有重写此前记录。`RESULTS.json`保存门禁及资源JSON SHA。

root另授权的物理fixture为`out/z_aw_fix_20261026/compact_aw_v2/map1_physical_p3r0_01`，入口`run_physical_p3r0.py`，精确复用上述VG及最终SYN清单，source Tcl map2保留、执行Tcl明确map1/P3R0；不重综合。必须等其真实normal wait0、full route/FS、20ns下Fmax≥50及五类slack非负、18pins/B4身份/CDC约束绑定全部通过，才能谈物理交付；本文件不提前宣称该结果。
