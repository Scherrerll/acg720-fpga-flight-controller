"""Plot recorded snapshots only; no interpolation or hidden controller states."""
from pathlib import Path
import csv,hashlib,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent

def records(path):
    with path.open(encoding='utf-8-sig',newline='')as stream:return list(csv.DictReader(stream))
def number(row,key,scale=1):
    try:return float(row[key])/scale
    except (ValueError,KeyError,TypeError):return math.nan
def boolean(row,key):
    value=row.get(key,'')
    return 1.0 if value=='True'else 0.0 if value=='False'else math.nan
def broken(rows,key,scale=1,gate=None):
    xs=[];ys=[];last=None
    for row in rows:
        seq=int(row['sequence'])
        if last is not None and seq!=last+1:xs.append(seq-.5);ys.append(math.nan)
        xs.append(seq);ys.append(number(row,key,scale)if gate is None or row.get(gate)=='True'else math.nan);last=seq
    return xs,ys

def main():
    response_path=HERE/'response/response_rows.csv';height_path=HERE/'height/boundary_packets.csv'
    response=records(response_path);height=records(height_path)
    plt.rcParams.update({'font.size':9,'axes.titlesize':11,'axes.labelsize':9})
    fig,axes=plt.subplots(2,2,figsize=(13,8.4))
    windows=[]
    for ax,axis,lo,hi,center_lo,center_hi,drop in [
        (axes[0,0],'pitch',280,295,285,292,293),
        (axes[0,1],'roll',482,502,487,494,500)]:
        data=[row for row in response if row['epoch']=='12'and lo<=int(row['sequence'])<=hi]
        assert len(data)>5
        x,y=broken(data,'target_'+axis+'_cdeg',100,'qualified_visible_xy')
        ax.plot(x,y,'o-',color='#1677b8',lw=1.2,ms=4,label='Selected angle target (XY active)')
        x,y=broken(data,axis+'_cdeg',100)
        ax.plot(x,y,'s--',color='#d37718',lw=1,ms=3,label='Reported attitude')
        ax.axvspan(center_lo,center_hi,color='#54b889',alpha=.15,label='Sampled sticks incl. throttle/yaw centered')
        ax.axvline(drop,color='#b33143',ls=':',label='First visible XY qualification withdrawal')
        ax.set(title=f'V15 epoch12: {axis} after stick return',xlabel='Telemetry sequence (about 5 Hz)',ylabel='Degrees')
        ax.grid(alpha=.2);ax.legend(fontsize=7,loc='best')
        windows.append(dict(kind='response',epoch=12,axis=axis,sequences=[lo,hi],points=len(data),centered=[center_lo,center_hi],withdrawal=drop))
    for ax,lo,hi,last_active,first_fallback in [
        (axes[1,0],225,234,230,231),(axes[1,1],369,378,374,375)]:
        data=[row for row in height if row['epoch']=='22'and lo<=int(row['sequence'])<=hi]
        assert len(data)>5
        x=[int(row['sequence'])for row in data]
        ax.plot(x,[boolean(row,'a582.native_height_ready')for row in data],'o--',color='#1677b8',ms=6,label='Native height ready at snapshot')
        ax.plot(x,[boolean(row,'a582.height_fusion_ready')for row in data],'x:',color='#309b68',ms=6,label='Height fusion ready at snapshot')
        ax.plot(x,[boolean(row,'a580.height_loss_fallback_active')for row in data],'s-',color='#c04745',ms=4,label='Fallback latched')
        ax.axvspan(last_active,first_fallback,color='#c04745',alpha=.10,label='First trigger lies between snapshots')
        ax.set(title=f'P005 epoch22: fallback first visible at seq{first_fallback}',xlabel='Telemetry sequence (about 5 Hz)',ylabel='Reported flag',ylim=(-.15,1.5),yticks=[0,1])
        twin=ax.twinx();twin.plot(x,[number(row,'a579.ch3')for row in data],'d--',ms=3,lw=1,color='#7b5aa5',label='CH3 (missing primary stays blank)')
        twin.set(ylabel='CH3 / us',ylim=(950,1550));twin.tick_params(colors='#7b5aa5')
        ax.grid(alpha=.2);ax.legend(fontsize=7,loc='upper left');twin.legend(fontsize=7,loc='lower left')
        windows.append(dict(kind='height',epoch=22,sequences=[lo,hi],points=len(data),trigger_bracket=[last_active,first_fallback]))
    fig.suptitle('Recorded evidence: stick return oscillation and short height-qualification loss',fontsize=14,y=.985)
    fig.text(.5,.015,'Markers are sparse recorded snapshots; lines are guides. Gaps/unknown values are not filled.\nA sampled ready=True cannot exclude an earlier millisecond dropout; low CH3 is not a direct fallback trigger.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,.96));fig.savefig(HERE/'evidence_overview.png',dpi=150);plt.close(fig)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (HERE/'plot_provenance.json').write_text(json.dumps(dict(inputs={str(p.relative_to(HERE)):sha(p)for p in [response_path,height_path]},windows=windows,
        scope='Actual recorded telemetry snapshots only; no reconstructed P/I components, exposure alignment, interpolation or flight acceptance'),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,output='evidence_overview.png',sha256=sha(HERE/'evidence_overview.png'),windows=windows),indent=2))

if __name__=='__main__':main()
