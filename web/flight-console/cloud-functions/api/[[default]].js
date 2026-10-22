import {getStore} from '@edgeone/pages-blob';
import {gzip} from 'node:zlib';
import {promisify} from 'node:util';
import worker from '../../worker/flight.mjs';
import {BlobBucket} from '../../platform/blob-bucket.mjs';

const compress=promisify(gzip),MAX_RESPONSE=5*1024*1024;
let defaultStore;
const store=()=>defaultStore ||= getStore({name:'gmfly-flight',consistency:'strong'});
export function createHandler({storeFactory=store,handler=worker}={}){
  return async function onRequest({request,env={}}){
    try{
    const bucket=new BlobBucket(storeFactory());
    // EdgeOne shadows body with parsed data and signal with undefined. Restore
    // the native stream without cloning, touching either shadow, or teeing it.
    const rawBody=Object.getOwnPropertyDescriptor(Request.prototype,'body').get.call(request);
    const cleanRequest=new Request(request.url,{method:request.method,headers:request.headers,
      ...(rawBody?{body:rawBody,duplex:'half'}:{})});
    const response=await handler.fetch(cleanRequest,{BUCKET:bucket,PUBLISH_TOKEN:env.PUBLISH_TOKEN||process.env.PUBLISH_TOKEN});
    if(request.method==='HEAD'||!response.body)return new Response(null,response);
    let data=Buffer.from(await response.arrayBuffer());
    const headers=new Headers(response.headers);
    const gzipAllowed=/(?:^|,)\s*gzip\s*(?:;\s*q=(?!0(?:\.0*)?(?:\s|,|$))[0-9.]+)?\s*(?:,|$)/i.test(request.headers.get('Accept-Encoding')||'');
    if(data.byteLength>1024&&gzipAllowed){data=await compress(data);headers.set('Content-Encoding','gzip');headers.set('Vary','Accept-Encoding');}
    if(data.byteLength>MAX_RESPONSE)return new Response(JSON.stringify({error:'response_exceeds_platform_limit'}),{status:413,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
    headers.delete('Content-Length');
    return new Response(data,{status:response.status,headers});
    }catch{return new Response(JSON.stringify({error:'temporarily_unavailable'}),{status:503,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});}
  };
}
const defaultHandler=createHandler();
export default function onRequest(context){return defaultHandler(context);}
