"""Prepare one source-only age predicate experiment; never start vendor tools."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil

O = Path(__file__).resolve().parent
R = O.parents[2]
OLD = R / 'out/z_aw_fix_20261026/compact_aw_v12/canonical/source'
NEW = R / 'out/z_aw_fix_20261026/compact_aw_v13/canonical/source'
M = O / 'compact_aw_v13'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not NEW.exists() and not M.exists()
prior = json.loads((O / 'compact_aw_v12/source_freeze.json').read_text())['source55']
assert len(prior) == 55 and {n: sha(OLD / n) for n in prior} == prior
shutil.copytree(OLD, NEW)
name = 'sensor/mtf01p_reader.v'
text = (NEW / name).read_text()
before = """ reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 always @(posedge clk)begin
  if(!rst_n)begin age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;end
  else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)age_ms<=age_ms+1'b1;
 end
 // P2 module offline indication is separate from metric/control freshness.
 wire module_online=samples!=0 && age_ms<1000;
 wire link_fresh=samples!=0 && age_ms<200;"""
after = """ reg [31:0] age_ms=32'hffffffff,age_previous_time=0;reg age_seen=0;
 // Exact predicates of this same 32-bit age, including expiry and publication clocks.
 reg age_below_1000=0,age_below_200=0;
 always @(posedge clk)begin
  if(!rst_n)begin
   age_ms<=32'hffffffff;age_previous_time<=0;age_seen<=0;
   age_below_1000<=0;age_below_200<=0;
  end else if(sample_valid && (!age_seen || time_ms!=age_previous_time))begin
   age_ms<=0;age_previous_time<=time_ms;age_seen<=1;
   age_below_1000<=1;age_below_200<=1;
  end else if(tick_ms && age_ms!=32'hffffffff)begin
   age_ms<=age_ms+1'b1;
   age_below_1000<=age_ms<32'd999;age_below_200<=age_ms<32'd199;
  end
 end
 // P2 module offline indication is separate from metric/control freshness.
 wire module_online=samples!=0 && age_below_1000;
 wire link_fresh=samples!=0 && age_below_200;"""
assert text.count(before) == 1
(NEW / name).write_text(text.replace(before, after), encoding='utf8', newline='\n')
current = {n: sha(NEW / n) for n in prior}
assert [n for n in current if current[n] != prior[n]] == [name]
M.mkdir()
review = M / 'source_review.md'
review.write_text('''# v13：MTF同拍年龄谓词

仅改v12的sensor/mtf01p_reader.v年龄块与两个内部比较。原全32位age_ms、重复时间戳不刷新、样本计数、解析器/度量算术、UART、诊断hold/reset、外部接口全部保留。新增两位始终等于(age_ms<1000)/(age_ms<200)。初始化和reset的FFFFFFFF两位均0；真正新时间戳与age=0同拍置1；非饱和tick分支下一年龄不溢出，分别按旧age<999/199计算下一谓词；饱和与非tick分支保持。分支优先级原样，公开模块在线/新鲜度撤销和恢复均不增加周期。

依据实际v4 clockbuf1完整raw TR Path6：mtf/age_ms_21_s1至staged_telemetry.extension_q_814_s0，setup -0.242ns，18级，数据路由13.026ns，占64.536%。前两级为mtf/module_online_s13/s4，随后经过metric有效性、geometry、nav_xy_ready和xy_active。该名称可由综合共享比较产生，不能仅据名称断言是1000ms而非200ms比较；本候选精确缓存这两个既有谓词。v12未修改此生产者文件，因此这是有独立raw依据的局部后续尝试，不从拓扑推断STA通过。

将用两份实际完整源通过真实UART帧比较所有公开输出与内部年龄/两个新鲜度条件，覆盖两个诊断reset模式、hold、有效/重复/损坏帧、199/200和999/1000超时及同拍恢复。独立提取实际年龄逻辑检查全32位边界/随机转移和不变量，再重做top13。其他控制/融合/算术文件按哈希复用v12及其依赖证明。已初始化可达年龄为已知值，不声称任意强制破坏内部不变量后的四态年龄等价。共享水平默认与Z抗饱和不改，低空前飞掉高仍不处理。当前只是未验证的源候选，不具综合/布线/下载资格。
''', encoding='utf8')
raw = R / 'out/z_aw_fix_20261026/compact_aw_v4/physical_p3r0_clkbuf1_01/source/impl/pnr/acg720_ano_port.tr'
core = raw.read_text(errors='replace').split('Note:Core Timing Report', 1)[1]
part = core.split('3.3.1 Setup Analysis', 1)[1]
match = re.search(r'\bPath6\b', part)
end = re.search(r'\bPath7\b', part[match.end():])
path = part[match.start():match.end() + end.start()]
assert 'mtf/age_ms_21_s1' in path and 'staged_telemetry.extension_q_814_s0' in path
(M / 'RAW_PATH_BASIS.txt').write_text(path, encoding='utf8')
(M / 'source_freeze.json').write_text(json.dumps({
    'prepared_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source55': current, 'baseline_source55': prior, 'changed_files': [name],
    'source_review_sha256': sha(review), 'raw_TR_sha256': sha(raw),
    'raw_path_extract_sha256': sha(M / 'RAW_PATH_BASIS.txt'),
    'scope': 'Unverified source candidate only; v12 physical jobs untouched.'
}, indent=2) + '\n', encoding='utf8')
print(json.dumps({'prepared_source_only': True, 'changed_files': [name], 'source_files': 55,
                  'hardware_operation': False, 'vendor_started': False}))
