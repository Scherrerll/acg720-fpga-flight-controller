"""Strict local lexer completion for the actual snapshot wrapper's named ports.

The protected shared Graph reader is unchanged. Only explicitly declared and
connected escaped ports omitted by its no-whitespace regex may acquire aliases.
"""
import re

def _modules(text):
    return {m[1]:m[2] for m in re.finditer(r'^module\s+(\S+)\s*\(.*?\)\s*;(.*?)^endmodule',text,re.S|re.M)}

def _declarations(body,kinds):
    result={}
    pattern=r'^('+kinds+r')\s+(?:(?:wire|reg)\s+)?(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?(\\[^\s]+|[A-Za-z_$][A-Za-z0-9_$]*)\s*;'
    for match in re.finditer(pattern,body,re.M):
        direction,hi,lo,name=match.groups()
        # Escaped identifiers must have a real lexical whitespace terminator.
        if name.startswith('\\'):
            end=match.start(4)+len(name);assert body[end].isspace()
        item=dict(direction=direction,hi=None if hi is None else int(hi),lo=None if lo is None else int(lo))
        if name in result:assert result[name]['hi']==item['hi'] and result[name]['lo']==item['lo']
        else:result[name]=item
    return result

def _decl_bits(name,item):
    if item['hi'] is None:return [name]
    hi,lo=item['hi'],item['lo'];step=1 if lo>hi else -1
    return [name+'['+str(i)+']' for i in range(hi,lo+step,step)]

def _connection_bits(expression,declarations):
    text=expression.lstrip()
    if text.startswith('\\'):
        match=re.match(r'\\[^\s]+',text);assert match
        name=match[0];rest=text[len(name):]
        assert rest and rest[0].isspace(),('Escaped net lacks whitespace terminator',expression)
    else:
        match=re.match(r'[A-Za-z_$][A-Za-z0-9_$]*',text);assert match,expression
        name=match[0];rest=text[len(name):]
    assert name in declarations,('Undeclared parent connection',name)
    all_bits=_decl_bits(name,declarations[name]);rest=rest.strip()
    if not rest:return all_bits
    match=re.fullmatch(r'\[\s*(\d+)\s*(?::\s*(\d+)\s*)?\]',rest);assert match,expression
    hi=int(match[1]);lo=hi if match[2] is None else int(match[2]);step=1 if lo>hi else -1
    selected=[name+'['+str(i)+']' for i in range(hi,lo+step,step)]
    assert set(selected)<=set(all_bits),('Parent slice exceeds declaration',expression)
    return selected

def _pins(cons):
    pattern=re.compile(r'\.\s*(?:(?P<escaped>\\[^\s]+)(?P<terminator>\s+)|(?P<plain>[A-Za-z_$][A-Za-z0-9_$]*)\s*)\((?P<expression>[^()]*)\)')
    pins={};last=0
    for match in pattern.finditer(cons):
        gap=cons[last:match.start()].strip();assert gap in {'',','},('Unparsed connection syntax',gap)
        name=match['escaped'] or match['plain'];assert name not in pins,('Duplicate named port',name)
        pins[name]=match['expression'];last=match.end()
    assert cons[last:].strip() in {'',','}
    return pins

def _expand(bits):
    result=[]
    for value in bits:
        match=re.fullmatch(r'(.+?)\s*\[(\d+):(\d+)\]',value)
        if match:
            name=match[1].rstrip();hi,lo=int(match[2]),int(match[3]);step=1 if lo>hi else -1
            result.extend(name+'['+str(i)+']' for i in range(hi,lo+step,step))
        else:result.append(value)
    return result

def complete_snapshot_aliases(graph,vg):
    text=vg.read_text(encoding='utf8',errors='strict');modules=_modules(text)
    parent='acg720_ano_port';child='gw5_snapshot_bram';instance=r'\staged_telemetry.extension_storage'
    body=modules[parent];port_declarations=_declarations(modules[child],'input|output|inout')
    parent_declarations=_declarations(body,'input|output|inout|wire|reg')
    pattern=r'^  '+re.escape(child)+r'\s+'+re.escape(instance)+r'\s+\((.*?)\)\s*;'
    instances=list(re.finditer(pattern,body,re.S|re.M));assert len(instances)==1
    connections=_pins(instances[0][1]);assert set(connections)==set(port_declarations)
    parsed=[(t,n,p) for t,n,p in graph.modules[parent][1] if t==child and n==instance];assert len(parsed)==1
    old_pins=parsed[0][2];child_ports=graph.modules[child][0]
    assert set(child_ports)==set(port_declarations)
    missing=set(connections)-set(old_pins)
    expected={r'\staged_telemetry.core_q_453_20',r'\hardware_bram.padded_q'}
    assert missing==expected and all(name.startswith('\\') for name in missing),('Unexpected lexer omissions',missing)
    for name,expression in old_pins.items():assert expression.strip()==connections[name].strip()
    output_pins={'F','O','Q','G','V','DO'};drivers={}
    for name,cell in graph.cells.items():
        for pin in output_pins:
            for net in _expand(cell['pins'].get(pin,[])):drivers.setdefault(graph.find(net),[]).append((name,pin))
    evidence=[]
    for name in sorted(connections):
        declaration=port_declarations[name];assert declaration['direction'] in {'input','output'}
        declared_bits=_decl_bits(name,declaration);parent_bits=_connection_bits(connections[name],parent_declarations)
        assert declared_bits==child_ports[name] and len(declared_bits)==len(parent_bits),(name,len(declared_bits),len(parent_bits))
        if name not in missing:continue
        if name==r'\staged_telemetry.core_q_453_20':assert declaration['direction']=='input' and len(declared_bits)==1
        else:assert declaration['direction']=='output' and len(declared_bits)==888
        pairs=[]
        for local_bit,parent_bit in zip(declared_bits,parent_bits):
            local=instance+'/'+local_bit;old_local=graph.find(local);old_parent=graph.find(parent_bit)
            assert old_local!=old_parent,('Unexpected pre-existing alias',local,parent_bit)
            child_drivers=drivers.get(old_local,[]);parent_drivers=drivers.get(old_parent,[])
            if declaration['direction']=='input':assert not child_drivers and len(parent_drivers)==1,(local,child_drivers,parent_drivers)
            else:assert len(child_drivers)==1 and child_drivers[0][1]=='DO' and not parent_drivers,(local,child_drivers,parent_drivers)
            graph.union(local,parent_bit)
            assert graph.find(local)==graph.find(parent_bit)
            pairs.append(dict(child=local,parent=parent_bit,previous_child_root=old_local,previous_parent_root=old_parent,child_drivers=child_drivers,parent_drivers=parent_drivers))
        evidence.append(dict(port=name,direction=declaration['direction'],width=len(declared_bits),raw_parent_expression=connections[name],aliases=pairs))
    assert sum(x['width'] for x in evidence)==889
    return dict(passed=True,instance=instance,module=child,all_named_ports_checked=len(connections),only_explicit_escaped_ports_completed=True,
        missing_port_names=sorted(missing),aliases=evidence,alias_bit_count=889,shared_graph_source_unmodified=True,
        scope='Explicit actual-VG parent/child port aliases with strict identifier termination, declarations, direction, width, membership and driver-conflict checks. No name-based guessed aliases.')
