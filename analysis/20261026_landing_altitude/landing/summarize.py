from pathlib import Path
import csv,hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
trace=list(csv.DictReader((O/'z_trace.csv').open(newline='')))
low=[r for r in trace if int(r['ch3'])==1002]
start=int(low[0]['logical_ms'])
early=[r for r in low if int(r['logical_ms'])-start<=4600]
def elapsed(predicate):return next(int(r['logical_ms'])-start for r in low if predicate(r))
log=R/'analysis/20261026_landing_altitude/logs/joined_rows.csv'
logged=[r for r in csv.DictReader(log.open(newline='',encoding='utf-8-sig')) if int(r['epoch'])==8 and 4259<=int(r['sequence'])<=4282]
cols=['epoch','sequence','utc','ch3','ch5','target_height_mm','fused_height_mm','fused_vz_mmps','world_az_up_mmps2','z_collective_us','taking_off','auto_takeoff','fallback','vertical_active','z_reason']
with (O/'low_stick_excerpt.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:r[k] for k in cols} for r in logged)
summary={'scope':'Actual RTL directed witness and finite observed telemetry, not plant simulation or exact flight replay. No measured private Z integral in the historical trace.',
 'telemetry':{'source':str(log.relative_to(R)).replace('\\','/'),'sha256':sha(log),'count':len(logged),'sequences':[4259,4282],
    'ch3_values':sorted({r['ch3'] for r in logged}),'collective_values':sorted({r['z_collective_us'] for r in logged}),
    'target_first_last_mm':[int(logged[0]['target_height_mm']),int(logged[-1]['target_height_mm'])],
    'fused_height_min_max_mm':[min(int(r['fused_height_mm']) for r in logged),max(int(r['fused_height_mm']) for r in logged)]},
 'rtl':{'trace_rows':len(trace),'low_stick_first_logical_ms':start,'early_4600ms_callbacks':len(early),
    'early_4600ms_collective_values':sorted({int(r['collective_us']) for r in early}),
    'negative_target_elapsed_ms':elapsed(lambda r:int(r['target_mm'])<0),
    'below1850_elapsed_ms':elapsed(lambda r:int(r['collective_us'])<1850),
    'below1250_elapsed_ms':elapsed(lambda r:int(r['collective_us'])<1250),
    'first_low':low[0],'last_low':low[-1],
    'timing_warning':'These logical elapsed times belong only to this fixed-sensor accelerated-callback witness; they are not aircraft flight waiting times or operating advice.'}}
assert summary['rtl']['early_4600ms_collective_values']==[1850] and len(early)==419
assert len(logged)==24 and summary['telemetry']['collective_values']==['1850']
(O/'evidence_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
H=Path(r'C:\Users\ScherrerL\Desktop\apple\handoff_xy_pi_runtime_20261026')
base=H/'workspace_snapshot/reference_ano/quadrotor_tm_v1_20261012/Quadrotor_TM_V1'
files=[base/p for p in ['SRC/fc_specific/Ano_AltCtrl.c','SRC/fc_specific/Ano_FlightCtrl.c','SRC/fc_specific/Ano_MotorCtrl.c','SRC/fc_specific/config.h','SRC/fc_general/Ano_Pid.c','Application/Ano_Parameter.c','Application/Ano_RC.c']]
refs={'external_p2_sources_not_redistributed':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],
      'sibling_log_evidence':[{'path':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [log,log.parent/'log_summary.json']],
      'source_files_unchanged':json.loads((O/'inputs.json').read_text())['source55']}
(O/'source_references.json').write_text(json.dumps(refs,indent=2)+'\n')
