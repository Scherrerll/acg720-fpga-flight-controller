# ZI sign-step lemma：复位可达范围下可成立

只读审查冻结B0B4 `source/position/mtf_xyz_hold_control.v`（SHA256 `5a928e0a68db70974049a4debb0b841ca06fa00598a4ffb4cb506997cfed657c`）、`position/ano_z_stick.v`、`position/position_math.v`及`nav_math_service.v`。**未发现复位可达合法接口反例。** 在下面限定的状态/量化语义下，state66的两个candidate-vs-old-I动态比较，可以改为state22捕获I步长符号及taking_off=false的归零方向；这只是可实施性证明，未改RTL、未跑新测试或新综合/PNR。现有03继续等待原构建。

## 必须先修正的两个数值表述

实际`position_divide`（`position_math.v:61–64,131–137`）为**nearest，ties away from zero**，不是trunc。令Q=65536、RN为该整数除法舍入，所有下式均以Q16整数表示：

```
e = state53同一有效误差整数
d = RN(clip(e, -1000Q, +1000Q) * 11 / 10000)
P = RN(e / 5)
|d| <= RN(65536000 * 11 / 10000) = 72090
72090/Q = 1.100006103515625
```

因此raw候选的严谨闭区间是`[-350Q-72090, 850Q+72090]`，即`[-351.100006103515625, 851.100006103515625]`，不能把`[-351.1,851.1]`当严格界。这个修正不影响rail不触及或符号替代结论。

## 同e、位宽与bias界

1. Z误差链是state21先存`vsz-sample_vx-RN(afz/20)`，state53再加`RN(inner_alt_speed*3/5)`。state53向I计算提交的64位`exz+value`与同时写入31位`exz_store`的值相同；其后state23用该存储值求P，没有重新采样误差。合法Z输入vz为±10000mm/s，`vsz`为±1500；afz是从0开始、对±30000mm/s²输入作1/5松弛，因此`RN(afz/20)`在±1500。原Z stick被desired clamp及无越过目标的8mm/s slew约束在[-2500,3500]，`quantized_climb_q16`朝零到整cm/s不扩大界，auto速度在[0,800]，所以`inner_alt_speed`在[-2500,4300]，其3/5项在[-1500,2580]。
2. 故最终`e/Q`在**[-14500,15580]**，前一部分也在±13000。均严格落在signed31 Q16的[-16384,16384)内，没有因31位存储截断导致P与d符号不同的问题。31位存储与同一64位calc参数逐bit相同；FRAC_BITS=0或16两个支持模式均成立。P和d都用正分母的RN，故`d>0 => e>0 => P>=0`，`d<0 => e<0 => P<=0`；小量化值舍为0只会让方向标志为false，不会反向。
3. bias的唯一非零更新在state23：`b_new=b+RN((350Q-b)*6908/106908)`，taking_off=false则0。对整数剩差r≥0及0<6908/106908<1，有`0<=RN(r*6908/106908)<=r`，因此从0出发bias始终在**[0,350Q]**且不越过350Q。initial/reset/global cancel清0，未tracking进入时也清0；没有其他bias写。即使taking_off在任意时钟变化，该分支也仅执行区间内松弛或清0。

以上是合法输入被接纳、真实math服务正确返回的范围证明，不将任意伪造math_result或force私有寄存器值当作合法历史。外部故障/无效输入引发的全局cancel清0不破坏结论。

## ZI归纳及原rail不可达

令B=350Q=22937600、H=850Q=55705600，归纳假设每拍已提交`I`在[-B,H]。initial声明为0；reset及全局cancel/origin/blocked分支也为0。全源搜索只有这些路径及state67会写`iz_store`。

- **先证明rail不触，避免循环论证。** 旧I在[-B,H]，|d|≤72090，所以`I+d`在[-23009690,55777690]。state53捕获的旧bias在[0,B]，原rail幅度`2000Q-biasOld >=1650Q=108134400`；raw候选严格落在rail内部。state22 taking_off=true时candidate就是I+d，clip不会改变步长或方向；taking_off=false时candidate明确为0。
- taking_off=true at22且candidate>H：因I≤H，d必>0，从而P≥0；用于输出测试的更新bias≥0，所以`P+b_new+candidate>H`，原state67必拒绝向上的候选、保持旧I。
- taking_off=true at22且candidate<−B：d必<0，P≤0且b_new≤B，因此`P+b_new+candidate<0`，原state67必拒绝向下的候选、保持旧I。
- 候选在[-B,H]时，接受候选或拒绝保持旧I都在界内。state22 taking_off=false产生的candidate=0同样在界内，不需要假定此时d的符号。state67 taking_off=false无条件提交0。

因此`I∈[-350Q,850Q]`保持。此证明涵盖d=0、严格比较的边界相等、保持/清0、taking_off在22/23/66/67之间任意翻转；不依赖taking_off在一次callback内保持不变。biasOld用于rail，biasNew用于最终输出，两者各自有界即可，不要求二者相等。

## 精确的最小替代位置和条件

state22在同一个taking_off分支构造candidate时，同时捕获：

```verilog
candidate_i_up   <= taking_off ? (value > 0) : (iz < 0);
candidate_i_down <= taking_off ? (value < 0) : (iz > 0);
```

这里`value`是本次实际d；`iz`是旧已提交I。taking_off=false时不能无条件使用d符号，也不能全部写false：candidate=0，因此其相对旧I的方向必须由旧I<0或>0取得。等于0时两flag均false。

删除state66对这两个flag的动态candidate-vs-iz写入；其余66加法、67拒绝条件/输出选择、原rail、所有声明宽度及两额外时钟均保持。**不要到state66再按当时taking_off推断方向**，因为与22的candidate选择可能已经不同。

从22到66，IZ没有其他提交路径：只有67能写非零I，XY rollback只写IX/IY/XY滤波；新增高度输入只排队或触发blocked。reset/cancel/origin/blocked会先清flag/I并把state退0，不会继续走旧66/67。math错误置blocked后下一拍清0；合法服务不把已取消旧响应提交到新事务。故22捕获的方向与现有66的`candidate_iz>iz`/`<iz`逐次相同，任意后来taking_off变化由67现有强制清0继续处理。

**证明范围**：冻结B4控制器从复位/initial出发、两个支持速度格式、合法接纳输入及真实math服务；不宣称私有I被force到rail外时仍等价。**收益范围**：可去掉两个33bit动态方向比较的源码运算；实际ALU/LUT/控制集及route收益未测量，不能按比较器位数直接承诺物理节省。
