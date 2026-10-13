"""No paid API calls. Check sequencing, exact evidence, scope and failure durability."""
import json,sys,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import server,rag
from http.server import ThreadingHTTPServer

class DebugTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.log=Path(self.tmp.name)/'events.jsonl'
  self.lp=patch.object(server,'LOG_PATH',self.log);self.lp.start()
  self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
  self.base='http://127.0.0.1:'+str(self.http.server_port)
 def tearDown(self):
  self.http.shutdown();self.http.server_close();self.lp.stop();self.tmp.cleanup()
 def post(self,path,data):
  req=urllib.request.Request(self.base+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req) as r:return json.load(r)
 def events(self):return [json.loads(x) for x in self.log.read_text().splitlines()]
 def test_single_company_overrides_stale_selection_and_panorama(self):
  r=self.post('/api/search',dict(question='华夏航空的客座率是多少？',companies=['中国国航'],panorama=True))
  self.assertEqual(r['companies'],['华夏航空']);self.assertFalse(r['panorama']);self.assertEqual({h['company'] for h in r['hits']},{'华夏航空'})
 def test_retrieval_is_saved_before_llm_and_same_hits_are_used(self):
  hits=server.engine.search('华夏航空的客座率是多少？',['华夏航空'])
  with patch.object(server.engine,'search',return_value=hits) as search,patch.object(server.engine,'answer') as answer:
   r=self.post('/api/retrieve',dict(question='华夏航空的客座率是多少？'))
   answer.assert_not_called();self.assertEqual(self.events()[0]['event'],'retrieval');self.assertEqual(self.events()[0]['retrieved_chunks'],r['hits'])
   def reply(*a,**kw):
    self.assertEqual(self.events()[0]['event'],'retrieval');self.assertEqual(kw['hits'],r['hits']);return dict(answer='test',hits=kw['hits'],mode='hybrid')
   answer.side_effect=reply;self.post('/api/generate',dict(request_id=r['request_id']));self.assertEqual(search.call_count,1)
   self.assertEqual([x['event'] for x in self.events()],['retrieval','answer'])
 def test_generation_failure_preserves_full_chunks(self):
  hits=server.engine.search('华夏航空的客座率是多少？',['华夏航空'])
  with patch.object(server.engine,'search',return_value=hits),patch.object(server.engine,'answer',side_effect=RuntimeError('test API failure')):
   r=self.post('/api/retrieve',dict(question='华夏航空的客座率是多少？'))
   with self.assertRaises(urllib.error.HTTPError):self.post('/api/generate',dict(request_id=r['request_id']))
   events=self.events();self.assertEqual(events[0]['retrieved_chunks'],hits);self.assertTrue(events[1]['retrieval_saved'])
 def test_exact_original_full_text_and_required_fields(self):
  raw={c['id']:c for c in server.engine.chunks}
  r=self.post('/api/search',dict(question='华夏航空的客座率是多少？'))
  for rank,h in enumerate(r['hits'],1):
   self.assertEqual(h['rank'],rank);self.assertEqual(h['text'],raw[h['chunk_id']]['text'])
   for k in ['company','report_name','report_year','chapter','pdf_page','retrieval_score','retrieval_source']:self.assertIn(k,h)
 def test_invalid_company_is_rejected(self):
  with self.assertRaises(urllib.error.HTTPError):self.post('/api/search',dict(question='营业收入',companies=['中信海直']))

if __name__=='__main__':unittest.main()
