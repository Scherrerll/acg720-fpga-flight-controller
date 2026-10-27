"""Strict read-only audit of actual mapped28 SP snapshot cells after SYN_ONLY."""
import re

def expand_primitive_bits(bits):
    # The shared scalar cone reader leaves escaped-vector slices as one item.
    # Expand only those primitive-pin ranges here; do not change the helper.
    result=[]
    for value in bits:
        match=re.fullmatch(r'(.+?)\s*\[(\d+):(\d+)\]',value)
        if match:
            name=match[1].rstrip();hi,lo=int(match[2]),int(match[3]);step=1 if lo>hi else -1
            result.extend(name+'['+str(i)+']' for i in range(hi,lo+step,step))
        else:result.append(value)
    return result

def audit_sp(graph,vg):
    clk=[c['pins']['O'][0] for c in graph.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
    assert len(clk)==1
    ground={graph.find(n) for c in graph.cells.values() if c['type']=='GND' for n in c['pins']['G']}
    high={graph.find(n) for c in graph.cells.values() if c['type']=='VCC' for n in c['pins']['V']}
    cells={n:c for n,c in graph.cells.items() if c['type']=='SP'}
    assert len(cells)==28,('Expected28 actual SP cells',len(cells))
    text=vg.read_text(encoding='utf8',errors='strict');params={}
    for inst,key,value in re.findall(r'defparam\s+(\S+)\s*\.(\w+)\s*=\s*([^;]+);',text):params.setdefault(inst,{})[key]=value.strip()
    def number(v):
        v=v.strip()
        if re.fullmatch(r'\d+',v):return int(v)
        m=re.fullmatch(r"\d+'([bhd])([0-9a-fA-F_]+)",v);assert m,('Unrecognized exact primitive value',v)
        return int(m[2].replace('_',''),{'b':2,'h':16,'d':10}[m[1]])
    ce=set();banks={};records=[]
    for name,c in cells.items():
        pins={k:expand_primitive_bits(v) for k,v in c['pins'].items()};assert len(pins.get('CLK',[]))==1 and graph.find(pins['CLK'][0])==graph.find(clk[0]),('SP is not CLK50',name,pins.get('CLK'))
        assert 'extension_storage' in name,('Unexpected SP domain',name)
        match=re.search(r'banks\[(\d+)\]\.memory',name);assert match,name
        bank=int(match[1]);assert bank not in banks;banks[bank]=name
        leaf=name.rsplit('/',1)[-1];p=params[leaf]
        assert number(p['BIT_WIDTH'])==32 and number(p['READ_MODE'])==0 and number(p['WRITE_MODE'])==1 and number(p['BLK_SEL'])==0 and p['RESET_MODE']=='"SYNC"',(name,p)
        assert all(number(v)==0 for k,v in p.items() if k.startswith('INIT_RAM_'))
        for pin in ['OCE','WRE']:assert len(pins[pin])==1 and graph.find(pins[pin][0]) in high,(name,pin,pins[pin])
        assert len(pins['RESET'])==1 and graph.find(pins['RESET'][0]) in ground,(name,'RESET',pins['RESET'])
        assert len(pins['BLKSEL'])==3 and all(graph.find(n) in ground for n in pins['BLKSEL'])
        assert len(pins['AD'])==14 and all(graph.find(n) in ground for n in pins['AD'][:10]) and all(graph.find(n) in high for n in pins['AD'][10:]),(name,'AD',pins['AD'])
        assert len(pins['DI'])==len(pins['DO'])==32
        if bank==27:assert all(graph.find(n) in ground for n in pins['DI'][:8]),('Last bank padding differs',name,pins['DI'][:8])
        assert len(pins['CE'])==1;ce.add(graph.find(pins['CE'][0]));records.append(dict(cell=name,bank=bank,CLK=pins['CLK'],CE=pins['CE'],parameters=p))
    assert set(banks)==set(range(28)) and len(ce)==1
    common_ce=next(iter(ce));assert common_ce not in ground|high
    core_snapshot_ce=[n for name,p in graph.regs.items() if 'staged_telemetry.core_q' in name for n in p.get('CE',[]) if graph.find(n)==common_ce]
    assert core_snapshot_ce,'SP CE does not match any remaining common-edge core snapshot FF CE'
    remaining=[name for name in graph.regs if 'staged_telemetry.extension_q' in name]
    assert not remaining,('Extension FF storage unexpectedly remains',remaining)
    return dict(passed=True,actual_SP_count=28,bank_indices=sorted(banks),all_SP_CLK50=True,common_CE_matches_remaining_core_snapshot=True,
        READ_MODE=0,WRITE_MODE=1,BIT_WIDTH=32,byte_enable_address='000f',reset_constant_zero=True,all_declared_INIT_RAM_zero=True,
        last_bank_padding_zero=True,remaining_extension_FF=[],cells=records,
        scope='Actual mapped primitive pins and modes only. Does not claim routed timing, hardware or full mapped sequential equivalence.')
