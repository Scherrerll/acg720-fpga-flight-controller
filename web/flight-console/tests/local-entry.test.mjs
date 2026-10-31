import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../frontend/local-entry.js',import.meta.url),'utf8');
const html=await readFile(new URL('../frontend/index.html',import.meta.url),'utf8');
function boot(protocol,readyState='loading'){
 const classes=[],scripts=[],listeners=[],help={hidden:true};
 const document={readyState,documentElement:{classList:{add:v=>classes.push(v)}},
  getElementById:id=>id==='local-file-help'?help:null,
  addEventListener:(type,fn,options)=>listeners.push({type,fn,options}),
  createElement:tag=>({tag}),head:{appendChild:node=>scripts.push(node)}};
 vm.runInNewContext(source,{document,location:{protocol}});
 return {classes,scripts,listeners,help,ready(){for(const l of listeners)l.fn();}};
}
test('file entry explains the launcher and never starts the HTTP-dependent telemetry module',()=>{
 const view=boot('file:');
 assert.deepEqual(view.classes,['local-file-entry']);assert.equal(view.scripts.length,0);
 view.ready();assert.equal(view.help.hidden,false);assert.equal(view.scripts.length,0);
 assert.match(html,/启动本地监控\.cmd/);assert.match(html,/http:\/\/127\.0\.0\.1:8766\//);
});
test('HTTP and HTTPS preserve module startup after the parsed DOM, without showing file help',()=>{
 for(const protocol of ['http:','https:']){
  const view=boot(protocol);assert.equal(view.scripts.length,0);assert.deepEqual(view.classes,[]);
  assert.equal(view.listeners[0].type,'DOMContentLoaded');assert.equal(view.listeners[0].options.once,true);
  view.ready();assert.equal(view.help.hidden,true);assert.equal(view.scripts.length,1);
  assert.equal(view.scripts[0].type,'module');assert.equal(view.scripts[0].src,'./app.js');
 }
});
test('already parsed DOM starts immediately and entry help assets resolve beside the real HTML',()=>{
 assert.equal(boot('http:','complete').scripts.length,1);
 assert.equal(boot('file:','complete').help.hidden,false);
 assert.match(html,/<script src="\.\/local-entry\.js"><\/script>/);
 assert.doesNotMatch(html,/<script type="module" src="\/app\.js"/);
 for(const name of ['styles.css','local-entry.css','gm-fly-mark.svg','gm-fly-wordmark.svg'])assert.ok(html.includes(`"./${name}"`));
});
