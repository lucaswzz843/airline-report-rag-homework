"""Real retrieval and answers, persisted before generation; no automatic correctness grading."""
import argparse,json,datetime
from rag import ROOT,Engine
from retrieval_log import new_id,record_retrieval,append_event
from coverage import retrieval_coverage

def main():
    p=argparse.ArgumentParser();p.add_argument('--answers',action='store_true');args=p.parse_args();e=Engine();rows=[];run_id=new_id()
    log=ROOT/'evaluation/retrieval_test_runs.jsonl'
    questions=json.loads((ROOT/'evaluation/questions_2026H1.json').read_text())
    mode='hybrid' if args.answers else 'bm25'
    name='answers_pending_review.json' if args.answers else 'bm25_baseline.json'
    for q in questions:
        request_id=new_id();hits=[]
        try:
            hits=e.search(q['question'],q.get('companies'),hybrid=args.answers,panorama=q.get('panorama',False))
            record_retrieval(log,request_id,q['question'],q.get('companies'),q.get('panorama',False),hits,mode,test_id=q['id'],run_id=run_id)
            r=e.answer(q['question'],q.get('companies'),q.get('panorama',False),hits=hits) if args.answers else dict(hits=hits,answer=None,mode=mode)
            append_event(log,request_id,'answer' if args.answers else 'complete',run_id=run_id,test_id=q['id'],system_answer=r['answer'],usage=r.get('usage'),finish_reason=r.get('finish_reason'),answer_correct=None,error_analysis='待核对')
            row=dict(**q,request_id=request_id,run_mode=mode,retrieved_blocks=hits,retrieval_coverage=retrieval_coverage(hits,q.get('companies') or e.companies),system_answer=r['answer'],answer_correct=None,error_analysis='待核对',usage=r.get('usage'),citation_warning=r.get('citation_warning'),finish_reason=r.get('finish_reason'),generation_parameters=r.get('generation_parameters'))
        except Exception as err:
            append_event(log,request_id,'error',run_id=run_id,test_id=q['id'],error=str(err),retrieval_saved=bool(hits))
            row=dict(**q,request_id=request_id,run_mode=mode,retrieved_blocks=hits,system_answer=None,answer_correct=False,error_analysis=str(err))
        rows.append(row)
        (ROOT/'evaluation'/name).write_text(json.dumps(dict(run_id=run_id,run_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),dataset_fingerprint=e.bm['fingerprint'],company_count=len(e.companies),results=rows),ensure_ascii=False,indent=2))
        print(q['id'],len(hits),'块',flush=True)
if __name__=='__main__':main()
