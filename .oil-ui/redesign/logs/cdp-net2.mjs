const targets = await (await fetch('http://127.0.0.1:9223/json')).json();
const page = targets.find(t => t.type==='page' && t.url.includes('5176'));
if(!page){console.log('no page');process.exit(1)}
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id=0;const pending=new Map();
const send=(m,p={})=>new Promise((res,rej)=>{const i=++id;pending.set(i,{res,rej});ws.send(JSON.stringify({id:i,method:m,params:p}))});
ws.onmessage=(ev)=>{const m=JSON.parse(ev.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.rej(m.error):p.res(m.result)}else if(m.method==='Network.responseReceived'&&m.params.response.status>=400){console.log('HTTP',m.params.response.status,m.params.response.url)}else if(m.method==='Runtime.exceptionThrown'){console.log('EXC',m.params.exceptionDetails.text,m.params.exceptionDetails.exception?.description||'')}else if(m.method==='Runtime.consoleAPICalled'){console.log('CONSOLE',m.params.type,m.params.args.map(a=>a.value??a.description).join(' '))}};
await new Promise(r=>ws.onopen=r);
await send('Runtime.enable');await send('Network.enable');await send('Page.enable');
await send('Page.reload',{ignoreCache:true});
await new Promise(r=>setTimeout(r,6000));
const r=await send('Runtime.evaluate',{expression:'({text:document.body.innerText,app:document.querySelector("#app")?.innerHTML?.slice(0,300)})',returnByValue:true});
console.log(JSON.stringify(r.result.value)); ws.close();
