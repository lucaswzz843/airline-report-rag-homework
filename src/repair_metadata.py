"""修复空格排版的章节标题，不改写财报正文。"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/processed/2026H1'
TITLES={'財務及營業撮要','主席致函','業務回顧','財務評述','審閱報告','簡明財務報表','按上市規則所需提供的資料','免責聲明'}
def repair():
    all_chunks=[]
    for s in json.loads((ROOT/'sources_2026H1.json').read_text()):
        p=DATA/f'{s["code"]}_pages.json';c=DATA/f'{s["code"]}_chunks.json';pages=json.loads(p.read_text());chunks=json.loads(c.read_text())
        if s['company']=='国泰航空':
            chapter='封面、目录及公司简介';mapping={}
            for page in pages:
                if page['pdf_page']>3:
                    for line in page['text'].splitlines()[:3]:
                        t=re.sub(r'\s+','',line)
                        if t in TITLES:chapter=t;break
                page['chapter']=chapter;mapping[page['pdf_page']]=chapter
            for chunk in chunks:chunk['chapter']=mapping[chunk['pdf_page']]
        for chunk in chunks:
            chunk.update(source_url=s['url'],report_title=s.get('report_title'),currency=s.get('currency'),full_report_verified=s.get('full_report_verified',False))
        p.write_text(json.dumps(pages,ensure_ascii=False));c.write_text(json.dumps(chunks,ensure_ascii=False));all_chunks.extend(chunks)
    (DATA/'chunks.json').write_text(json.dumps(all_chunks,ensure_ascii=False))
if __name__=='__main__':repair()
