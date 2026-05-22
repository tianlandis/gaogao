const http=require('http'),fs=require('fs'),path=require('path');
const t={'.html':'text/html','.js':'text/javascript','.json':'application/json','.csv':'text/csv'};
http.createServer((req,res)=>{
  let p='.'+req.url.split('?')[0]; if(p==='./')p='./index.html';
  try{const d=fs.readFileSync(p);res.writeHead(200,{'Content-Type':t[path.extname(p)]||'text/plain'});res.end(d)}
  catch(e){res.writeHead(404);res.end('404')}
}).listen(8080,()=>console.log('Ready: http://127.0.0.1:8080'));
