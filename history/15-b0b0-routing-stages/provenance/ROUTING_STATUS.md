# 最新结果：已布通，51.608 MHz 时序通过

已选择 routing_closure_20261024/B0B0_51_608MHz_verified。零未连通、19.5 ns 目标下 setup/hold 违例为零，三项增量验证已通过，SRAM 启动与正常测距四路输出回归通过。本轮测距失效接管、手动油门、恢复保持接管及SWA停机回归均已通过。Flash 未改，flight_ready=false。详情见相邻工作区 routing_closure_20261024/验收记录.md 与 WORK_STATE.json。

以下是历史记录，旧的“尚无通过版本”描述已被上述结果取代。

# B0B0 当前状态

**尚无通过50 MHz时序的发布候选，默认Flash仍为B0AC。**

0beP2actual56unrouted/noTRFS; no activebuild. SameVG targetedphysical CLOCK_LOC n3217_8 BUFG CE|SR|LOGIC CSTsingleline prepared pending officialsyntaxreview; primary/LW8of8 occupied so rebalance only, no success promise. Allsource/CSTbase andphysicaloverride separatelybound. No SYN/tests/launch.
Best complete unqualified candidate: variants/range_age_prechecked_multiply7_map2_feasibility_p2_r2_rep0_fan23,819VG,47.948MHz; below50MHz, no programming/release. Older chronology below is historical, not active state.

4c386年龄谓词分支两单均失败：p2为344条、p1为338条未布线，均无TR/FS；该分支退休，不执行其功能证明。

最后一个有界源码组合已独立源审通过：以完整8e320预检查基线，仅叠加相同NAV两行7位乘法/共享wire；原显式age<100与default-off RANGE_AGE_PRECHECKED/5m门限保留，没有4c386标志混入。唯一授权SYN已完成，VG819dece；实测LUT35857/ALU9296/FF27372/BSRAM2，相对8e320为+47LUT/-8FF，并非面积胜出。独立P2/r2/rep0/fan23/50 feasibility输入已准备且身份预检通过，root已启动独立PNR（session48243/PID41796），SkipSYN/placement1；不运行功能测试或全资格矩阵。当前295885输入及所有旧结果冻结。

已完成结果：
- 4c386 p1/r2/rep0/fan23 失败338条未布线，无TR/FS；该分支无活动进程。
- 4c386 p2/r2/rep0/fan23 失败344条未布线，无TR/FS；p1也已失败338，分支退役，尚无新发布候选。
- 1aee完整布线，Fmax41.761 MHz；9e4ea完整布线，Fmax41.571 MHz，均低于50 MHz，不能下载。
- 8e320 p2/p3/p4分别失败145/397/379条；旧66/208/223等记录保留且不采用。
- 增量布局参考匹配3.24低于80，被工具拒绝；已停止回退默认的重复计算，原.p及副本SHA不变。
- 19位mixer仅省2 LUT/3 ALU，拒绝且未PNR。4c386实际综合35918 LUT、27377 FF、9294 ALU，属于时序结构权衡，未声称面积下降。

按用户要求先布线，布通后只验证改动处并复用未改证据，不重复光流标定、遥控行程或历史整套矩阵。没有下载FPGA、改Flash、操作电机或切换接收器。

更新时间：2026-10-23T23:32:27.049477+00:00

Retired 4c386 P1 raw result: `variants/reader_age_predicate_map2_feasibility_p1_r2_rep0_fan23/feasibility_result.json`; SHA256 `45b04a749c01fb75fa20e05dd273daefa517a5810be64099c6dc854a904cdfed`; actual338unrouted, noTR/FS.

Completed295885P2: `variants/nav_age_multiply7_map2_feasibility_p2_r2_rep0_fan23/feasibility_result.json`; SHA256 `96f7f47c9600ee32d2f2825ef7e92c0872532cd05632737f6e41a49ce4b3c4e7`; VG `295885db6f57ad74359384ea6ee3a2bab2a6141eb4b4c7acdc38f72f21d43981`; resources35764LUT/9295ALU/27367FF/2BSRAM; actual252unrouted/noTR/FS. Source family:9e4ea-parent NAV-only low7/shared age (no8e320prechecked/no4cflags). No functional proof run. No additional SYN/trim/trials until819 actual result. Prior zero-route timing-fail1aee41.761MHz and9e4ea41.571MHz remain preserved.

819P2 actual result: `variants/range_age_prechecked_multiply7_map2_feasibility_p2_r2_rep0_fan23/feasibility_result.json`; SHA256 `2ac67a8e24d7119be09d1b3fc37ac195a388e7c5a75d5a0da360f7ed42ce5fb6`; FS SHA256 `62d98023464e5ffaa78c365df7a6e37fcff743aeaf9dc566820ade187c497262`. Qualification/programming/release remain false.

Focused proof: builder reported PASS; final metadata/hash pending. Initial bench GSR compile/extraction reset-vs-normal issues were corrected in bench only; initial logs preserved. No claim of first-run success or completed qualification.

Final focused proof bound: `hardware/range_age_prechecked_multiply7_plan/post_route_pending/proof.json`; SHA256 `ed51dfd5f48b5d0d4a3e05188a9191190bf6fc07f9d284576cdfa9eb362f4308`; reviewer ACK of actual7bindings/evidence/history.365 ages and6400 caller cases PASS, scoped source+isolated DSP only, not whole mapped. EXECUTED_RESULT.md records3 compilations/2 simulations and bench-only repairs with original logs. Same819VG P3 reuses proof without repetition. Qualification remains false/no release pending50MHz and reviewer changed-cone connection check. Only P3 session72110/PID19040 active.

No further preparation pending actual P3/P4 results. Root owns monitoring and may stop remaining owned PNR upon qualified50MHz winner. No hardware.

P4 result `variants/range_age_prechecked_multiply7_map2_feasibility_p4_r2_rep0_fan23/feasibility_result.json` SHA256 `77e990804a86d41bccf4010b1c85ccccef8d927572680898a873c2752e7108a8`; FS `cc82d012a2e18d42e689922341d63b354c2549e2ad190b400f55f1ec1104827e`; same819 scope, no new functional tests; q/program/release false.

Independent scoped offline proof/connectivity and packaging preparation ACCEPTED. Helper SHA256 `b1d972661023182ce9badc987e18b9ad6940ba69301ac851af9e76441fa9555e`; scope SHA256 `6a835c412f3e629db53d475d2e5e018df968d20414c2cbf7b35dbfa576de7a7e`; independent record SHA256 `7fbea7f2ca15c0c461cb4fe641c84f19bb93e214b2a336a01b9d4d95712bea1d`. Only50MHz physical timing winner remains before positivefreeze. P3/P1 remain active PID19040/61592; best47.948 unchanged. No positivefreeze executed; no flight/program authorization.

P3 raw result `variants/range_age_prechecked_multiply7_map2_feasibility_p3_r2_rep0_fan23/feasibility_result.json`; SHA256 `a211a1c7b1556da8f602f02f874ef1930087d1015f763b2486ec76a2d603ce01`; actual570unrouted/noTR/FS.

Root owns both PNRs and may stop remaining owned run on qualified50MHz winner. Qualification/programming/flight remain false until applicable gates; no hardware.

P1 result `variants/range_age_prechecked_multiply7_map2_feasibility_p1_r2_rep0_fan23/feasibility_result.json` SHA256 `787c28d310d364dbbefa3a85effb1061f69b0557e810c5fbfdaec523f693ab61`;311unrouted/noTRFS.

Rejected/aborted incremental result `variants/range_age_prechecked_multiply7_map2_incremental_p2_r2_rep1_fan23/feasibility_result.json`; SHA256 `ced5a9d0050995a49cc333b482bc54d731f1e2f7fabcd6ec0160309ff5d79cc1`. Reference input archive SHA4811cbbfaaa439b54cc3d7b8472104cf03f8d7bb1584751d612b55b79fb17c4a unchanged. Origins: {"variants\\range_age_prechecked_multiply7_map2_incremental_p2_r2_rep1_fan23\\fixture\\impl\\pnr\\acg720_ano_port.reference_input.p": "4811cbbfaaa439b54cc3d7b8472104cf03f8d7bb1584751d612b55b79fb17c4a", "variants\\range_age_prechecked_multiply7_map2_incremental_p2_r2_rep1_fan23\\fixture\\impl\\pnr\\acg720_ano_port.reference_evidence.json": "3648834dc610f3a9931131378ce8179db72aab6f939548edf6012d34638b5cd3"}.

Fresh819P2rep1 result `variants/range_age_prechecked_multiply7_map2_feasibility_p2_r2_rep1_fan23/feasibility_result.json`; SHA256 `58fb6d31fb3d306a0584c405a3b9ce654a1d36a175d8911a1633ec1cbf08cddb`; actual216unrouted/noTRFS. Physical replication attempt retired; no qualified winner.

Current pointers synchronized UTC: 2026-10-24T01:07:08.275738+00:00

f293 actual result `variants/published_tilt4500_map2_feasibility_p2_r2_rep0_fan23/feasibility_result.json`; SHA256 `37f68bf0e3eb8f37d8c30c8309daedd90afd4792379730811046fd1ef5e1faf2`; fullyrouted45.408MHz/setup-324.985ns/318ep/hold0, timingfailed. Sourceflag focusedproof remains pending; no new validation or packaging. UpdatedUTC 2026-10-24T01:12:18.790116+00:00

Active start records synchronized 2026-10-24T01:15:40.153753+00:00

Final f293 physical retry results:
- `variants/published_tilt4500_map2_feasibility_p2_r2_rep1_fan23/feasibility_result.json` SHA256 `c164c91f09a20cb61e493a724fc3d341082cd80b6d5ea741f373c917119c7ec1`; actual399unrouted/noTRFS.
- `variants/published_tilt4500_map2_feasibility_p1_r2_rep0_fan23/feasibility_result.json` SHA256 `1da3747f95e19eab9665a7dae03e05e2cdd755bba5932027141be7c72dd97d81`; actual405unrouted/noTRFS.

Factoring structure evidence SHA256: {"hardware\\control_ready_factoring_plan\\mapped_structure_inventory.json": "7de67e75ace82d50698c160a7e5ceb1d7a3ef0c6c27f20d805e9139892ca39ad", "hardware\\control_ready_factoring_plan\\inspect_structure.py": "9cc7ebf50654bba84d20cde34344257ad6609fd1d1dce62de8f9bdc67ffc3871"}. Current result pending at `variants/control_ready_factoring_map2_feasibility_p2_r2_rep0_fan23/feasibility_result.json`.

6ebb actual result `variants/control_ready_factoring_map2_feasibility_p2_r2_rep0_fan23/feasibility_result.json`; SHA256 `0cb2b3fbcf023648fb18a1ccd2a796155b41d1c136810d97391803d5cd954b13`; actualPR0004 139unrouted,noTR/FS,no measuredtiming. Pendingfocusedproofs remain unexecuted.

Finevelocity actual structure evidence SHA256: {"hardware\\control_fine_velocity_factoring_plan\\mapped_structure_inventory.json": "ae8aea312397900bf47e8940423f983f31af67771daf411ce6ffde6fc8d1777c", "hardware\\control_fine_velocity_factoring_plan\\mapped_range_Q_inventory.json": "e9576036e0bdca1f23bb2629d88067fefe264bb3e51e64875ab4186e9c3fe283", "hardware\\control_fine_velocity_factoring_plan\\inspect_structure.py": "00735fc28da0246bb88f617b4bce69943cadd050aa125ed85099035756048e36"}. Only source/structure ACK, functionalproof pending.

0be original result SHA256 `90f33dcdd878dc6119fd3de5b6b897cb65807011b8b0b0ae7ff44635f74272e0`;56unrouted/noTRFS.
