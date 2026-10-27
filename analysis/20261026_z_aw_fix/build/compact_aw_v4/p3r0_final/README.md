# v4 P3/R0：完整布线，STA失败，不可下载

此试验真实wait返回0，完整placement/routing、bitstream、EOF均完成；原ABB gate仍准确拒绝该结果。真实clk50 Period=20.000ns、Actual Fmax=49.456MHz，setup最差−0.220ns且32个setup violated endpoints，hold endpoints0。五类slack分别为setup−0.220、hold+0.122、recovery+11.288、removal+3.092、pulse+7.387ns。

最差setup原路径为`acc_time/output_az_3_s0/Q`→`core/flight_state/flying_ms_3_s0/D`。route、18pins、B4 FS/CFG身份和精确VG均通过，不抵消负setup或低于50MHz。它与旧试验的unrouted失败不同：本次是**完整route后STA失败**。没有放宽时钟/false_path、没有下载、没有取消别人的job。

源hold `ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642`；VG `e67bcab6336757e08645756258d39dd13726b452c392d470de4c900a159aaa8f`；P3/R0/map2/replicate0/TD1。原B4、v3及v4 canonical/快照各55文件在结束后仍匹配。

原始TR路径：`out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_01/source/impl/pnr/acg720_ano_port.tr`，SHA `c62307f8f84c2a0b742e1b5ba09211ad17158d9b6e6807e0c59146775ba80b82`。原FS虽已生成（SHA `2309283e832badccfb0d73b445d5b3998526b0a11c131c5fe1679f3ba97a6b93`），仅作失败诊断，不是release image。

`FINAL_STATUS.json`绑定实际exit、完整audit、TR/RPT/FS/PR/CFG、源55及执行脚本/日志原始哈希。`seal.py`只读原输出；本目录为最终封存，不继续追加monitor。其MANIFEST只绑定本目录文件，外部大文件按FINAL_STATUS路径/哈希引用，不隐含已复制到此目录。
