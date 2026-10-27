# v11：同拍发布年龄谓词

原v4局部位置方案完整布通但45.460MHz/setup−1.997ns/255端点，原始最差路径从height_fusion/publication_age_10穿过高度可用性及fallback到manual_angles使能。该报告仅作为定位证据，不宣称原v9具有相同物理延迟。

v11从v9冻结源出发，只改高度融合一文件。32位publication_age、所有数值运算/状态机/输出/数学服务请求保持；新增一位publication_fresh，在每一个年龄赋值的同一always分支、同一优先级计算赋值后年龄的原谓词age<AGE_LIMIT，并在两个原组合使用点引用它。初始化/cleanup为f(FFFFFFFF)，普通自增为f(age+32d1)，发布覆盖为f(0)，饱和值保持；最后非阻塞赋值优先级与原年龄完全相同。

归纳不变量publication_fresh === (publication_age<AGE_LIMIT)：初始和reset成立；三种赋值/保持逐一保持。因此到达AGE_LIMIT的那个边沿立即撤销，发布置0的同一边沿立即恢复，不增加一拍宽限或收紧窗口；原qualified_ready/valid自身一拍延迟不变。加一为原32位无符号表达式，AGE_LIMIT仍原integer类型，零/边界值按同一Verilog规则比较。没有改原范围输入的即时撤销、cleanup、epoch、fault、数学端口或PID。

不声称任意强制破坏内部年龄/新增位之间不变量后的状态等价。验证必须实际比较完整融合模块的全部公开位、请求/服务和年龄每拍一致，并覆盖正常发布、重入、实时坏输入、复位/取消，以及小阈值/16位进位附近的同拍超时。控制器六依赖完全相同，复用已通过的五场景/边界/争用；生产者范围标志代码未改，复用原444003拍证明。新top13、一次新SYN及精确新VG物理门另行执行。

这是待验证候选；没有下载或50MHz资格。
