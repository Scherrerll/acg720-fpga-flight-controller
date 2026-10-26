"""Hash and bound existing evidence; no hardware, network or source mutations."""
from pathlib import Path
from datetime import datetime,timezone
import collections
import hashlib
import json

REPO=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PRIOR=REPO/'firmware/B0B3/analysis'
CURRENT=REPO/'ground/runtime/B0B3/20261026T002929Z_9ccb8279/telemetry.jsonl'

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb')as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def save(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def current_prefix():
    limit=CURRENT.stat().st_size;digest=hashlib.sha256();counts=collections.Counter();epochs={};responses=[]
    read_bytes=0;first=None;last=None;partial=0
    with CURRENT.open('rb')as stream:
        while read_bytes<limit:
            line=stream.readline(limit-read_bytes)
            if not line:break
            digest.update(line);read_bytes+=len(line)
            if not line.endswith(b'\n'):partial+=1;continue
            if not any(pattern in line for pattern in (b'"_protocol": "a579"',b'"_protocol": "a580"',b'"_protocol": "a591"')):continue
            item=json.loads(line);row=item.get('row')or{};protocol=row.get('_protocol')
            if protocol not in ('a579','a580','a591'):continue
            counts[protocol]+=1;first=first or item.get('utc');last=item.get('utc')
            epoch=item.get('epoch');entry=epochs.setdefault(str(epoch),dict(primary=0,armed=0,controller_enabled=0,taking_off=0,first_utc=item.get('utc'),last_utc=None,first_sequence=row.get('sequence'),last_sequence=None))
            entry['last_utc']=item.get('utc');entry['last_sequence']=row.get('sequence')
            if protocol=='a579':
                flags=row.get('flags',0);entry['primary']+=1
                entry['armed']+=bool(flags&0x10);entry['controller_enabled']+=bool(flags&0x20)
            elif protocol=='a580':entry['taking_off']+=row.get('taking_off')is True
            else:responses.append(dict(utc=item.get('utc'),epoch=epoch,opcode=row.get('opcode'),sequence=row.get('sequence'),status=row.get('status'),p_wire=row.get('p_wire'),i_wire=row.get('i_wire'),generation=row.get('generation'),build=row.get('build')))
    return dict(path=str(CURRENT),captured_bytes=read_bytes,initial_size=limit,prefix_sha256=digest.hexdigest(),
                partial_final_lines_not_parsed=partial,protocol_counts=dict(counts),first_utc=first,last_utc=last,epochs=epochs,
                parameter_responses=responses,interpretation='Only this fixed prefix. Protocol semantics checked via normalized a579 flags and a580 taking_off; current source telemetry is not a flight truth sensor.')

def main():
    prior=json.loads((PRIOR/'evidence_summary.json').read_text(encoding='utf-8'))
    sources=[]
    for name,record in prior.items():
        path=Path(record['source']);actual=sha(path)
        sources.append(dict(dataset=name,path=str(path),bytes=path.stat().st_size,sha256=actual,
                            matches_previous_summary=actual==record['sha256']))
    assert all(value['matches_previous_summary']for value in sources),'Original limited evidence changed'
    product={p.relative_to(REPO/'firmware/B0B3/source').as_posix():sha(p)for p in sorted((REPO/'firmware/B0B3/source').rglob('*'))if p.is_file()}
    assert len(product)==55
    save('input_ledger.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),historical_sources=sources,
         original_findings_sha256=sha(PRIOR/'FINDINGS.md'),original_reader_sha256=sha(PRIOR/'analyze_evidence.py'),
         current_b0b3_source_sha256=product,scope='New read-only follow-up; original R/H/source/evidence are preserved; no claim that prior reports were complete.'))
    current=current_prefix();save('current_session_summary.json',current)
    print(json.dumps(dict(historical_sources=len(sources),all_hashes_match=True,current_source_files=len(product),
                         current_log_prefix_bytes=current['captured_bytes'],current_log_last_utc=current['last_utc'],
                         epochs=current['epochs']),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
