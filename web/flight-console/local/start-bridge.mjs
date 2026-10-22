// Receive publisher configuration without terminal echo or command-line secrets.
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const [python] = process.argv.slice(2);
if (!python) throw Error('Pass the Python executable path');
const raw = await new Promise((resolve,reject)=>{
 let value='';const tty=process.stdin.isTTY;
 const finish=error=>{process.stdin.removeListener('data',data);process.stdin.removeListener('end',end);if(tty)process.stdin.setRawMode(false);process.stdin.pause();error?reject(Error('Configuration cancelled')):resolve(value);};
 const data=chunk=>{value+=chunk;if(value.includes('\u0003')||value.length>16384)finish(true);else if(/[\r\n]/.test(value))finish(false);};
 const end=()=>finish(false);
 if(tty)process.stdin.setRawMode(true);
 process.stdin.setEncoding('utf8');process.stdin.on('data',data);process.stdin.once('end',end);process.stdin.resume();
 process.stderr.write('Ready for bridge configuration on stdin (input is hidden).\n');
});
let settings;try{settings=JSON.parse(raw);}catch{throw Error('Invalid configuration');}
const child=spawn(python,['-B',fileURLToPath(new URL('bridge.py',import.meta.url)),'--stdin-config'],{detached:true,windowsHide:true,stdio:['pipe','ignore','ignore']});
let failed=false;child.once('error',()=>{failed=true;});child.once('exit',()=>{failed=true;});
child.stdin.on('error',()=>{failed=true;});child.stdin.end(JSON.stringify(settings)+'\n');
let ready=false;
for(let i=0;i<20&&!failed;i++){
 try{const r=await fetch(`http://127.0.0.1:${settings.listen_port||8766}/api/capabilities`);if(r.ok){ready=true;break;}}catch{}
 await new Promise(r=>setTimeout(r,200));
}
if(!ready||failed)throw Error('Bridge did not start');
child.unref();console.log(JSON.stringify({pid:child.pid,url:`http://127.0.0.1:${settings.listen_port||8766}/`,started:true}));
