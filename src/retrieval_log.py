"""Persist retriever outputs before generation; later events share the same request_id."""
import datetime,json,os,threading,uuid
from rag import ROOT
_LOCK=threading.Lock()

def new_id():return uuid.uuid4().hex

def append_event(path,request_id,event,**fields):
    record=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),request_id=request_id,event=event,**fields)
    path.parent.mkdir(parents=True,exist_ok=True)
    with _LOCK,path.open('a',encoding='utf8') as f:
        f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    return record

def record_retrieval(path,request_id,question,companies,panorama,hits,mode,**extra):
    return append_event(path,request_id,'retrieval',question=question,companies=companies or [],panorama=panorama,run_mode=mode,top_k=len(hits),retrieved_chunks=hits,system_answer=None,answer_correct=None,error_analysis='待核对',**extra)
