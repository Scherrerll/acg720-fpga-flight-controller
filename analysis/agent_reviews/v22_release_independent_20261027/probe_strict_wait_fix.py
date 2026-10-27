"""Focused strict-wait closure, current producer read-only and in-memory stubs only."""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2]
verify=R/'firmware/B0B4/verify_release.py';export=R/'analysis/20261026_z_aw_fix/build/export_qualified_v4.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected={str(verify):'0ba2c0cdca20b7bcf60b34c4d7f2c059762e7f1723f78fa977b0ad4884353cbf',str(export):'c52c889b913f9b5d1d0bfcd8d15bd50475b3550175c9245767efbff4dd26e3d2'}
assert {p:sha(p) for p in expected}==expected
spec=importlib.util.spec_from_file_location('current_wait_fix_readonly',verify);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Stub:
    origins={'repo':'c:/review'}
    def __init__(self,j):self.j=j
    def read(self,*args):return self.j
    def check(self,*args):pass
    def blob(self,*args):return b''
missing=object();values=[('int0',0),('boolFalse',False),('float0',0.0),('str0','0'),('null',None),('missing',missing),('int1',1),('boolTrue',True),('float1',1.0)]
normals=[('true',True),('false',False),('numeric1',1),('null',None),('missing',missing)]
interfaces=[('check_receipt_Popen','actual_p_wait','normal_wait_return',0),('check_receipt_CompletedProcess','actual_completedprocess_returncode','normal_return',0),('raw_success_Popen','actual_p_wait','normal_wait_return',0),('raw_success_child_Popen','actual_child_p_wait','normal_wait_return',0),('raw_success_CompletedProcess','actual_completedprocess_returncode','normal_return',0),('check_failed_receipt','actual_p_wait','normal_wait_return',1)]
rows=[]
for name,field,normal,success_code in interfaces:
    for label,value in values:
        for normal_label,flag in normals:
            j={'stdout_sha256':'a'*64,'stderr_sha256':'b'*64}
            if value is not missing:j[field]=value
            if flag is not missing:j[normal]=flag
            try:
                if name.startswith('check_receipt_'):m.check_receipt(Stub(j),'c:/review/x_exit.json')
                elif name.startswith('raw_success_'):m.raw_success_receipt(Stub(j),'c:/review/x_exit.json',None,field)
                else:m.check_failed_receipt(Stub(j),'c:/review/x_exit.json',None)
                accepted=True
            except SystemExit:accepted=False
            wanted=type(value) is int and value==success_code and flag is True
            assert accepted is wanted,(name,label,normal_label,accepted,wanted)
            rows.append({'interface':name,'wait_value':label,'normal_flag':normal_label,'accepted':accepted,'expected':wanted})
assert len(rows)==270 and sum(x['accepted'] for x in rows)==6
# Physical receipt validation uses real bytes and their original script/log hashes.
STD=R/'analysis/20261026_z_aw_fix/build/compact_aw_v22';A=R/'out/z_aw_fix_20261026/compact_aw_v22/physical_p3r0_01'
class Real:
    origins={k:m.evidence_key(v) for k,v in {'repo':R,'metadata':STD,'physical_metadata':STD,'report':STD/'physical_p3r0_01'}.items()}
    def blob(self,path,expected=None):
        p=m.safe_local(Path(path),R);data=p.read_bytes()
        if expected is not None:assert hashlib.sha256(data).hexdigest()==expected
        return data
    def read(self,path,expected=None):return json.loads(self.blob(path,expected))
    def check(self,path,expected):self.blob(path,expected)
real=Real();physical=[]
for label,path in [('vendor',A/'verification/physical_exit.json'),('runner',STD/'physical_p3r0_01/runner_exit.json')]:
    j=real.read(path);assert type(j['actual_p_wait']) is int and j['actual_p_wait']==0 and j['normal_wait_return'] is True
    assert m.check_receipt(real,str(path),sha(path))==j
    physical.append({'role':label,'path':str(path),'sha256':sha(path),'actual_p_wait':j['actual_p_wait'],'actual_p_wait_python_type':type(j['actual_p_wait']).__name__,'normal_wait_return':j['normal_wait_return'],'pid':j['pid']})
assert json.loads((A/'verification/physical_exit.json').read_text())['parent_pid']==physical[1]['pid']
# Scope review of the change: preserve a diff, never mutate the old42 review.
diff=''
for name,path in [('verify_release.py',verify),('export_qualified_v4.py',export)]:
    old=O/'reviewed_production_42'/name
    diff+=''.join(difflib.unified_diff(old.read_text().splitlines(True),path.read_text().splitlines(True),fromfile='old42/'+name,tofile='strict_wait_fix/'+name))
diff_path=O/'STRICT_WAIT_FIX.diff';assert not diff_path.exists();diff_path.write_text(diff,encoding='utf8')
assert {p:sha(p) for p in expected}==expected
report={'passed_focused_fix_closure':True,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'production_script_hashes':expected,'old_review_path':str(O/'REVIEW_OLD42.json'),'old_review_sha256':sha(O/'REVIEW_OLD42.json'),'old_review_unchanged':True,'closed_finding':'Exact integer success0/failure1 codes with normal flag isTrue; bool/float/string/missing/null are rejected at both common receipt interfaces and raw-success/preserved-failure helpers.','stub_cases':len(rows),'expected_acceptances':6,'per_interface_summary':{name:{'cases':sum(x['interface']==name for x in rows),'accepted':sum(x['interface']==name and x['accepted'] for x in rows)} for name,*_ in interfaces},'all_cases':rows,'real_standard22_physical_receipts':physical,'real_physical_receipt_script_log_hashes_validated':True,'minimal_diff_sha256':sha(diff_path),'scope':'Only focused read-only/memory-stub fix verification. No full42 suite rerun by this reviewer; owner new suite/seal is independent and is not claimed here. No physical timing re-audit, qualified file, export, promotion or hardware operation.','qualified_file_created':False,'production_files_edited_by_reviewer':False,'vendor_or_DUT_tests_executed':False,'probe_script_sha256':sha(Path(__file__))}
dest=O/'STRICT_WAIT_FIX_CLOSURE.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['all_cases']}))
