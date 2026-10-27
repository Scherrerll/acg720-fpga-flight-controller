"""Exact actual-LUT CE function proof over shared mapped FF-Q boundaries."""
import hashlib,json,re
from escaped_port_adapter import _modules

class BDD:
    def __init__(self,names):self.names=names;self.nodes={};self.unique={};self.cache={};self.next=2
    def make(self,v,lo,hi):
        if lo==hi:return lo
        key=(v,lo,hi)
        if key not in self.unique:self.unique[key]=self.next;self.nodes[self.next]=key;self.next+=1
        return self.unique[key]
    def ite(self,c,t,e):
        if c==0:return e
        if c==1:return t
        if t==e:return t
        key=(c,t,e)
        if key in self.cache:return self.cache[key]
        level=min(self.nodes[n][0] for n in key if n>=2)
        def co(n,high):return self.nodes[n][2 if high else 1] if n>=2 and self.nodes[n][0]==level else n
        lo=self.ite(co(c,False),co(t,False),co(e,False));hi=self.ite(co(c,True),co(t,True),co(e,True))
        result=self.make(level,lo,hi);self.cache[key]=result;return result

def prove_shared_ce(graph,vg):
    sp={n:c for n,c in graph.cells.items() if c['type']=='SP'};assert len(sp)==28
    sp_roots={graph.find(c['pins']['CE'][0]) for c in sp.values()};assert len(sp_roots)==1
    core={n:p for n,p in graph.regs.items() if 'staged_telemetry.core_q' in n and p.get('CE')};assert len(core)==627
    core_roots={graph.find(p['CE'][0]) for p in core.values()}
    assert core_roots==sp_roots,'Actual CE nets differ after explicit port aliases'
    root=next(iter(sp_roots));text=vg.read_text(encoding='utf8',errors='strict');raw=_modules(text)
    params={typ:{inst:int(value.replace('_',''),{'h':16,'b':2,'d':10}[base]) for inst,width,base,value in re.findall(r"defparam\s+(\S+)\s*\.INIT\s*=\s*(\d+)'([hbd])([0-9a-fA-F_]+)\s*;",body)} for typ,body in raw.items()}
    context={}
    def hierarchy(typ,prefix=''):
        for child,instance,pins in graph.modules[typ][1]:
            name=prefix+instance
            if child in graph.modules:hierarchy(child,name+'/')
            else:context[name]=(typ,instance)
    hierarchy('acg720_ano_port')
    drivers={}
    for name,cell in graph.cells.items():
        typ=cell['type']
        pin='Q' if typ.startswith('DFF') else 'F' if typ.startswith('LUT') else 'O' if typ in {'INV','BUF','BUFG'} or typ.startswith('MUX2') else 'G' if typ=='GND' else 'V' if typ=='VCC' else None
        if pin:
            assert len(cell['pins'][pin])==1
            drivers.setdefault(graph.find(cell['pins'][pin][0]),[]).append((name,cell))
    nodes={};leaves={};visiting=set();clock=[c['pins']['O'][0] for c in graph.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']];assert len(clock)==1
    def collect(net):
        net=graph.find(net)
        if net in nodes:return
        assert net not in visiting,('Combinational cycle in CE cone',net);visiting.add(net)
        ds=drivers.get(net,[]);assert len(ds)==1,('Missing/conflicting CE driver',net,[n for n,c in ds])
        name,cell=ds[0];typ=cell['type'];pins=cell['pins']
        if typ.startswith('DFF'):
            assert len(pins['CLK'])==1 and graph.find(pins['CLK'][0])==graph.find(clock[0])
            leaves[net]=dict(cell=name,type=typ,Q_net=net,CLK=pins['CLK'][0]);nodes[net]=dict(kind='FF',cell=name)
        elif typ in {'GND','VCC'}:nodes[net]=dict(kind='constant',value=int(typ=='VCC'),cell=name)
        elif re.fullmatch(r'LUT[1-8]',typ):
            width=int(typ[3:]);inputs=[graph.find(pins['I'+str(i)][0]) for i in range(width)]
            assert all(len(pins['I'+str(i)])==1 for i in range(width))
            parent,instance=context[name];init=params[parent][instance];assert 0<=init<(1<<(1<<width))
            nodes[net]=dict(kind='LUT',cell=name,type=typ,input_order=['I'+str(i) for i in range(width)],inputs=inputs,INIT=init,INIT_hex=hex(init))
            for value in inputs:collect(value)
        elif typ in {'INV','BUF','BUFG'}:
            assert len(pins['I'])==1;value=graph.find(pins['I'][0]);nodes[net]=dict(kind=typ,cell=name,inputs=[value]);collect(value)
        elif typ.startswith('MUX2'):
            inputs=[graph.find(pins[k][0]) for k in ['I0','I1','S0']];assert all(len(pins[k])==1 for k in ['I0','I1','S0'])
            nodes[net]=dict(kind='MUX2',cell=name,inputs=inputs)
            for value in inputs:collect(value)
        else:raise AssertionError(('Unsupported CE cone primitive',typ,name))
        visiting.remove(net)
    collect(root);assert leaves
    order=sorted(leaves);bdd=BDD(order);memo={}
    def build(net):
        if net in memo:return memo[net]
        node=nodes[net];kind=node['kind']
        if kind=='FF':value=bdd.make(order.index(net),0,1)
        elif kind=='constant':value=node['value']
        elif kind=='LUT':
            inputs=[build(x) for x in node['inputs']];init=node['INIT']
            def lut(i,offset):
                if i==len(inputs):return (init>>offset)&1
                return bdd.ite(inputs[i],lut(i+1,offset|(1<<i)),lut(i+1,offset))
            value=lut(0,0)
        elif kind in {'BUF','BUFG'}:value=build(node['inputs'][0])
        elif kind=='INV':value=bdd.ite(build(node['inputs'][0]),0,1)
        elif kind=='MUX2':a,b,s=[build(x) for x in node['inputs']];value=bdd.ite(s,b,a)
        else:raise AssertionError(kind)
        memo[net]=value;return value
    sp_value=build(next(iter(sp_roots)));core_value=build(next(iter(core_roots)))
    assert sp_value==core_value and sp_value>=2
    serial=dict(variable_order=order,root=sp_value,nodes={str(k):v for k,v in sorted(bdd.nodes.items())})
    return dict(passed=True,actual_SP_count=28,remaining_core_snapshot_FF_count=len(core),same_canonical_CE_net=root,
        strict_same_net_after_explicit_alias=True,actual_LUT_cone_nodes=nodes,shared_FF_roots=leaves,FF_root_count=len(leaves),
        exact_BDD_root=sp_value,BDD_allocated_nodes=len(bdd.nodes),BDD_sha256=hashlib.sha256(json.dumps(serial,sort_keys=True).encode()).hexdigest(),
        symbolic_all_shared_FF_assignments=True,BDD=serial,
        scope='Actual parsed LUT INIT bit I0=least-significant address bit, exact BUF/INV/MUX logic and actual shared CLK50 FF-Q roots. Structural CE identity remains mandatory; Boolean proof does not waive it.')
