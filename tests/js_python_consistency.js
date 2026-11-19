const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const P=process.argv[2]||'./';  // 先运行 python 导出 py_out.json，再 node tests/js_python_consistency.js <目录>
const py=JSON.parse(fs.readFileSync(P+'py_out.json'));
const p=await b.newPage({viewport:{width:1280,height:900}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('http://localhost:8766/t.html');await p.waitForTimeout(2000);
let mism=0;for(const [q,st,c] of py){const r=await p.evaluate(q=>{const r=window.__ask(q);return [r.status,r.cites||[]]},q);if(r[0]!==st||JSON.stringify(r[1])!==JSON.stringify(c)){mism++;console.log('DIFF',q,st,c,r)}}
console.log('checked',py.length,'mismatch',mism,'errors',errs);
await p.screenshot({path:P+'s_ask.png'});
await p.goto('http://localhost:8766/t.html#compare');await p.waitForTimeout(800);await p.screenshot({path:P+'s_cmp.png'});
await p.goto('http://localhost:8766/t.html#eval');await p.waitForTimeout(800);await p.screenshot({path:P+'s_eval.png',fullPage:true});
const m=await b.newPage({viewport:{width:400,height:860},colorScheme:'dark'});await m.goto('http://localhost:8766/t.html');await m.waitForTimeout(1500);
console.log('mobile sw',await m.evaluate(()=>document.documentElement.scrollWidth));await m.screenshot({path:P+'s_m.png'});
await b.close()})();
