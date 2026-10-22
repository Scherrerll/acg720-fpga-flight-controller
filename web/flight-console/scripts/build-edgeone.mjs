import {cp,mkdir,readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../',import.meta.url),out=new URL('public/',root);
await mkdir(out,{recursive:true});
await cp(new URL('frontend/',root),out,{recursive:true});
// Makers serves .mjs as octet-stream. Keep source modules for Node tests,
// and publish browser imports with its supported JavaScript extension.
for(const name of ['live-state','polling'])await cp(new URL(`frontend/${name}.mjs`,root),new URL(`${name}.js`,out));
const app=new URL('app.js',out);
await writeFile(app,(await readFile(app,'utf8')).replace('./live-state.mjs','./live-state.js').replace('./polling.mjs','./polling.js'));
const index=new URL('index.html',out);
await writeFile(index,(await readFile(index,'utf8')).replace('https://acg720-flight-console.bloomybowl256.chatgpt.site/gm-fly.png','/gm-fly.png'));
console.log('Built static frontend:',fileURLToPath(out));
