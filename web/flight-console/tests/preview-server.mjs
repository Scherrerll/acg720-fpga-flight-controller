// Loopback-only, in-memory preview. No device, cloud storage or real credentials.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import worker from '../worker/flight.mjs';
const data=new Map();
const bucket={async get(k){const v=data.get(k);return v?{json:async()=>JSON.parse(v)}:null;},async put(k,v){data.set(k,v);},async list(){return {objects:[],truncated:false};},async delete(k){data.delete(k);}};
const fixture=process.argv.includes('--test-fixture');
const env={BUCKET:bucket,...(fixture?{CONTROL_TOKEN:'test-operator-'+ 'a'.repeat(32),PUBLISH_TOKEN:'test-publisher-'+ 'b'.repeat(32)}:{})};
const port=Number(process.env.GMFLY_PREVIEW_PORT||0);
const server=http.createServer(async(req,res)=>{
 try{
 const origin=`http://127.0.0.1:${server.address().port}`,url=new URL(req.url,origin);
 if(!url.pathname.startsWith('/api/')){
  const name=url.pathname==='/'?'index.html':url.pathname==='/parameters'?'parameters.html':url.pathname.slice(1);
  if(!/^[a-zA-Z0-9_.-]+$/.test(name))throw Error();
  const body=await readFile(new URL('../frontend/'+name,import.meta.url));
  const type=name.endsWith('.css')?'text/css':/\.(mjs|js)$/.test(name)?'text/javascript':name.endsWith('.svg')?'image/svg+xml':name.endsWith('.png')?'image/png':'text/html';
  res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store'});res.end(body);return;
 }
 const chunks=[];let size=0;
 for await(const chunk of req){size+=chunk.length;if(size>65536){res.writeHead(413);res.end();return;}chunks.push(chunk);}
 const body=Buffer.concat(chunks);
 const r=await worker.fetch(new Request(url,{method:req.method,headers:req.headers,...(body.length?{body,duplex:'half'}:{})}),env);
 res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));
 }catch{res.writeHead(404);res.end('Not found');}
});
server.listen(port,'127.0.0.1',()=>console.log(JSON.stringify({url:`http://127.0.0.1:${server.address().port}`,fixture})));
