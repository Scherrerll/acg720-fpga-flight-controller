from pathlib import Path
import hashlib,json,shutil,datetime
R=Path(__file__).resolve().parent;F=R/'fixture';D=R/'variants/reset_global';DF=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());assert q['offline_tests_passed']
for n,h in q['sources_sha256'].items():assert sha(F/n)==h,('qualification not current',n)
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h,('proof changed',n)
D.mkdir(parents=True,exist_ok=False)
files=set(q['evidence_sha256'])|{'qualification.json','baseline.json','说明.txt','实物验收要点.txt','DO_NOT_PROGRAM'}
files|={str(p.relative_to(R)).replace('\\','/') for p in R.glob('*.py')}
files|={'fixture/'+n for n in q['sources_sha256']}
files|={'fixture/'+n for n in json.loads((R/'baseline.json').read_text())['baseline_sources']}
files|={'fixture/build_project.py'}
for n in sorted(files):
 p=R/n
 if p.is_file():
  dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
cst=DF/'acg720_ano_port.cst';s=cst.read_text();assert 'CLOCK_LOC' not in s
line='CLOCK_LOC "n13_16" BUFG = SR;'
cst.write_text(s.rstrip()+'\n'+line+'\n',encoding='utf8')
contract=D/'control_contract.py';s=contract.read_text()
assert s.count("'acg720_ano_port.gprj','build.tcl','build_project.py'}")==1
s=s.replace("'acg720_ano_port.gprj','build.tcl','build_project.py'}","'acg720_ano_port.gprj','acg720_ano_port.cst','build.tcl','build_project.py'}")
old=" parent=Path(b['parent'])\n";assert s.count(old)==1
new=" parent=Path(b['parent'])\n clock_line='CLOCK_LOC \\\"n13_16\\\" BUFG = SR;'\n cst=(FIX/'acg720_ano_port.cst').read_text()\n original=(parent/'fixture/acg720_ano_port.cst').read_text()\n if cst!=original.rstrip()+'\\n'+clock_line+'\\n':raise ValueError('Only the single reset clock-resource constraint may differ; all IO unchanged')\n"
# Quotes are ordinary Python string delimiters in the generated validator.
new=new.replace('\\"','"')
s=s.replace(old,new);contract.write_text(s,encoding='utf8')
driver=DF/'build_project.py';s=driver.read_text();needle="    if re.search(r'ERROR\\s*\\(',resources)"
assert s.count(needle)==1
s=s.replace(needle,"    if not re.search(r'^\\s*n13_16\\s*\\|\\s*PRIMARY',resources,re.M):raise ValueError('Reset resource constraint was not implemented')\n"+needle)
driver.write_text(s,encoding='utf8')
for n,h in q['sources_sha256'].items():assert n=='acg720_ano_port.cst' or sha(DF/n)==h
q['sources_sha256']['acg720_ano_port.cst']=sha(cst)
q['evidence_sha256']['control_contract.py']=sha(contract)
q['build_configuration_requalification']=dict(parent_qualification_sha256=sha(R/'qualification.json'),
 change=line,rtl_changed=False,io_constraints_unchanged=True,existing_proofs_revalidated=True,
 vendor_reference='SUG1541-1.0E section2.8 CLOCK_LOC BUFG=SR',
 created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(D/'qualification.json').write_text(json.dumps(q,indent=2),encoding='utf8')
(D/'status.json').write_text(json.dumps(dict(phase='reset_global_resource_comparison',hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print(str(D),flush=True)
