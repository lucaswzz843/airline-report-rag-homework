import json,argparse,urllib.parse,time,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from rag import ROOT,Engine,config
from retrieval_log import new_id,record_retrieval,append_event
engine=Engine()
LOG_PATH=ROOT/'evaluation/retrieval_logs.jsonl'
PENDING={};LOCK=threading.Lock();TTL=1200

def scope(question,companies,panorama):
    if not isinstance(companies,(list,type(None))):raise ValueError('公司筛选必须为列表')
    chosen=companies or []
    if any(co not in engine.companies for co in chosen):raise ValueError('筛选包含知识库之外的公司，请刷新页面')
    mentioned=[co for co in engine.companies if co in question]
    # A question naming one company takes precedence over stale UI selections.
    if len(mentioned)==1:return mentioned,False
    if len(mentioned)>1 and not chosen:return mentioned,panorama
    return chosen or None,panorama

class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,ctype='application/json; charset=utf-8'):
        if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urllib.parse.urlparse(self.path).path
        if path=='/':return self.send(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
        if path=='/api/status':return self.send(200,dict(companies=engine.companies,chunks=len(engine.chunks),vectors_ready=engine.matrix is not None,key_configured=bool(config().get('DASHSCOPE_API_KEY')),sources=json.loads((ROOT/'sources_2026H1.json').read_text()),version='retrieval-debug-v2'))
        if path=='/api/evaluation':
            p=ROOT/'evaluation/reviewed_results.json'
            return self.send(200,json.loads(p.read_text()) if p.exists() else {'results':[]})
        if path.startswith('/report/'):
            code=path.rsplit('/',1)[-1];source=next((s for s in json.loads((ROOT/'sources_2026H1.json').read_text()) if s['code']==code),None)
            if source:return self.send(200,(ROOT/source['file']).read_bytes(),'application/pdf')
        return self.send(404,{'error':'未找到'})
    def do_POST(self):
        request_id=new_id();retrieved=False
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>12000:return self.send(413,{'error':'问题太长'})
            obj=json.loads(self.rfile.read(length))
            if self.path=='/api/generate':
                request_id=str(obj.get('request_id',''))
                with LOCK:item=PENDING.pop(request_id,None)
                if item is None or time.monotonic()-item['created']>TTL:raise ValueError('检索记录已过期或已使用，请重新检索')
                q,companies,panorama,hits=item['question'],item['companies'],item['panorama'],item['hits'];retrieved=True
                result=engine.answer(q,companies,panorama,hits=hits)
                append_event(LOG_PATH,request_id,'answer',system_answer=result['answer'],usage=result.get('usage'),finish_reason=result.get('finish_reason'),answer_correct=None,error_analysis='待核对')
                return self.send(200,dict(result,request_id=request_id,companies=companies or [],panorama=panorama))
            if self.path not in ('/api/search','/api/retrieve','/api/ask'):return self.send(404,{'error':'未找到'})
            q=str(obj.get('question','')).strip()
            if not q or len(q)>1500:raise ValueError('请输入不超过1500字的问题')
            companies,panorama=scope(q,obj.get('companies'),bool(obj.get('panorama')))
            hybrid=self.path!='/api/search';mode='hybrid' if hybrid else 'bm25'
            hits=engine.search(q,companies,hybrid=hybrid,panorama=panorama)
            record_retrieval(LOG_PATH,request_id,q,companies,panorama,hits,mode);retrieved=True
            if self.path=='/api/retrieve':
                with LOCK:
                    for ident in [i for i,v in PENDING.items() if time.monotonic()-v['created']>TTL]:PENDING.pop(ident)
                    if len(PENDING)>=100:raise ValueError('待回答检索过多，请稍后重试')
                    PENDING[request_id]=dict(created=time.monotonic(),question=q,companies=companies,panorama=panorama,hits=hits)
                return self.send(200,dict(hits=hits,mode=mode,answer='',request_id=request_id,companies=companies or [],panorama=panorama))
            result=engine.answer(q,companies,panorama,hits=hits) if hybrid else dict(hits=hits,mode=mode,answer='')
            append_event(LOG_PATH,request_id,'answer' if hybrid else 'complete',system_answer=result['answer'],usage=result.get('usage'),finish_reason=result.get('finish_reason'),answer_correct=None,error_analysis='待核对')
            return self.send(200,dict(result,request_id=request_id,companies=companies or [],panorama=panorama))
        except Exception as e:
            error=str(e) if isinstance(e,(ValueError,RuntimeError)) else '处理失败，请查看本地终端。'
            append_event(LOG_PATH,request_id,'error',error=error,retrieval_saved=retrieved)
            return self.send(400,{'error':error,'request_id':request_id,'retrieval_saved':retrieved})
    def log_message(self,*args):pass
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    print(f'打开 http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
