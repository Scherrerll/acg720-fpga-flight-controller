"""Read selected original timing tables and first setup path; never writes reports."""
from pathlib import Path
import gzip, re, sys
p=Path(sys.argv[1]); raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
t=raw.decode('utf8',errors='replace')
for start,end in [('3.1.1 Setup Paths Table','3.1.2 Hold Paths Table'),('3.3.1 Setup Analysis','3.3.2 Hold Analysis')]:
    a=t.find(start,t.find(start)+len(start))
    if a<0:a=t.find(start)
    b=t.find(end,a+len(start))
    if a>=0:print(t[a:b if b>=0 else a+12000][:12000])
if '3.3.1 Setup Analysis' not in t:
    match=re.search(r'(?:Path 1\b|Path #1\b|1\. Setup)',t)
    if match:print(t[match.start():match.start()+10000])
