const http=require('http'),fs=require('fs'),path=require('path'),zlib=require('zlib');
const t={
  '.html':'text/html; charset=utf-8',
  '.js':'text/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8',
  '.csv':'text/csv; charset=utf-8',
  '.css':'text/css; charset=utf-8',
  '.svg':'image/svg+xml',
  '.png':'image/png',
  '.jpg':'image/jpeg',
  '.webp':'image/webp',
  '.ico':'image/x-icon'
};
const cache={'.json':86400,'.html':300,'.js':3600,'.css':3600,'.svg':86400,'.png':86400,'.jpg':86400,'.webp':86400,'.ico':86400};

http.createServer((req,res)=>{
  let p='.'+req.url.split('?')[0];
  try{const st=fs.statSync(p);if(st.isDirectory()){if(!req.url.endsWith('/')){res.writeHead(301,{Location:req.url+'/'});res.end();return}p+='index.html'}}catch(e){}
  try{
    const ext=path.extname(p);
    const data=fs.readFileSync(p);
    const maxAge=cache[ext]||0;
    // gzip for text/json types if >1KB
    const ae=req.headers['accept-encoding']||'';
    const gzipOk=ae.includes('gzip')&&data.length>1024&&
      (ext==='.json'||ext==='.html'||ext==='.js'||ext==='.css'||ext==='.csv'||ext==='.svg');
    const headers={
      'Content-Type':t[ext]||'text/plain; charset=utf-8',
      'Cache-Control':maxAge?'public, max-age='+maxAge:'no-cache',
      'Access-Control-Allow-Origin':'*'
    };
    if(gzipOk) headers['Content-Encoding']='gzip';
    res.writeHead(200,headers);
    if(gzipOk){
      zlib.gzip(data,(_,z)=>res.end(z));
    }else{
      res.end(data);
    }
  }
  catch(e){res.writeHead(404);res.end('404')}
}).listen(8080,()=>console.log('Ready: http://127.0.0.1:8080  (gzip enabled)'));
