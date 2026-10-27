"""Correct only preparation regex: exclude the distinct inner_alt_speed identifier."""
from pathlib import Path
import hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent;old=O/'prepare_alias.py';new=O/'prepare_alias_retry02_resolved.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=old.read_text();assert s.count("r'alt_speed<=([^;]+);'")==2
s=s.replace("r'alt_speed<=([^;]+);'","r'(?<![a-z_])alt_speed<=([^;]+);'")
s=s.replace("D.mkdir()","assert D.is_dir() and not any(D.iterdir())")
assert not new.exists();new.write_text(s,encoding='utf8')
(O/'ALIAS_PREPARATION_CORRECTION_02.json').write_text(json.dumps({'scope':'Preparation-only correction; original script preserved. Initial inline preparation returned AssertionError because alt_speed<= regex also matched inner_alt_speed<=. No RTL or assertion/stimulus change.','original_script_sha256':sha(old),'resolved_retry_script_sha256':sha(new),'correction':'Identifier boundary before alt_speed excludes inner_alt_speed; permit the already-created empty fixture directory.','original_failure_receipt_available':False,'original_failure_observation':'Initial exec_command output contained AssertionError at prepare_alias.py line14 before writing any fixture; suite had already started independently.'},indent=2)+'\n')
command=[sys.executable,'-B','-X','utf8',str(new)]
with (O/'alias_preparation_retry02.stdout.log').open('wb') as out,(O/'alias_preparation_retry02.stderr.log').open('wb') as err:
 p=subprocess.Popen(command,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);code=p.wait()
(O/'alias_preparation_retry02_exit.json').write_text(json.dumps({'command':command,'normal_wait_return':True,'actual_p_wait':code,'runner_sha256':sha(new),'stdout_sha256':sha(O/'alias_preparation_retry02.stdout.log'),'stderr_sha256':sha(O/'alias_preparation_retry02.stderr.log')},indent=2)+'\n');raise SystemExit(code)
