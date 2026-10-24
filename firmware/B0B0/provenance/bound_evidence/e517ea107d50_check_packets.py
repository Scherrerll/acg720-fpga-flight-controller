from pathlib import Path
import json
D=Path(__file__).resolve().parent
report_path=D/'full_top.proof.json'
report=json.loads(report_path.read_text())
rows=[line.split() for line in (D/'full_top_acceptance.log').read_text().splitlines()]
assert len(rows)==1136
cycles=[int(r[0]) for r in rows]
assert all(b>a for a,b in zip(cycles,cycles[1:]))
assert [int(r[1]) for r in rows]==list(range(1136))
data=bytes(int(r[2],16) for r in rows)
layout=[('A579',224),('A57A',32),('A580',40),('A581',128),('A582',96),('A583',48)]
packets=[];offset=0;nav=[]
for frame in range(2):
 for kind,length in layout:
  packet=data[offset:offset+length]
  assert packet[:2].hex().upper()==kind
  assert int.from_bytes(packet[2:4],'big')==frame
  if kind in ('A579','A57A'):
   checksum=0
   for b in packet[2:-1]:checksum^=b
   assert checksum==packet[-1]
  else:
   crc=0xffff
   for b in packet[2:-2]:
    crc^=b<<8
    for _ in range(8):crc=((crc<<1)^0x1021 if crc&0x8000 else crc<<1)&0xffff
   assert crc==int.from_bytes(packet[-2:],'big')
  if kind=='A582':nav.append(packet[4:-2])
  packets.append({'frame':frame,'type':kind,'length':length,'first_accept_cycle':cycles[offset],'last_accept_cycle':cycles[offset+length-1]})
  offset+=length
assert nav[0]!=nav[1], 'Subsequent navigation snapshot must change'
report.update(packet_counts={kind:2 for kind,_ in layout},accepted_bytes=len(data),packets=packets,navigation_payload_changed=True,checksums_verified=True)
report_path.write_text(json.dumps(report,indent=2))
print('PASS: two each A579 A57A A580 A581 A582 A583; 1136 bytes; sequences0/1; XOR/CRC; changed navigation payload')
