"""提取全文、表格和可溯源分块；不调用模型。"""
import json,re,hashlib,concurrent.futures,sys
from pathlib import Path
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/2026H1'

def split_lines(text,limit=900):
    buf=[];size=0
    for line in text.splitlines():
        for start in range(0,max(len(line),1),limit):
            part=line[start:start+limit]
            if size+len(part)>limit and buf:
                yield '\n'.join(buf);buf=buf[-2:];size=sum(map(len,buf))
            buf.append(part);size+=len(part)
    if buf:yield '\n'.join(buf)

def extract(source):
    company=source['company'];chunks=[];pages=[];chapter='封面及前言';table_count=0
    def chunk(text,pg,side,kind,printed,table_id=None):
        if len(text.strip())<20:return
        ident=f"{source['code']}-p{pg:03d}{side}-{len(chunks):05d}"
        chunks.append(dict(id=ident,company=company,code=source['code'],period='2026H1',chapter=chapter,pdf_page=pg,side=side,printed_page=printed,type=kind,table_id=table_id,text=text,source_url=source['url'],source_file=source['file']))
    with pdfplumber.open(ROOT/source['file']) as pdf:
        source['pages']=len(pdf.pages)
        for n,p in enumerate(pdf.pages,1):
            # 国货航原文是双页跨页版，必须左右分别提取。
            regions=[('L',p.crop((0,0,p.width/2,p.height))),('R',p.crop((p.width/2,0,p.width,p.height)))] if company=='国货航' and p.width>p.height*1.3 else [('',p)]
            for side,pg in regions:
                text=pg.extract_text(x_tolerance=2,y_tolerance=3) or ''
                lines=text.splitlines();printed=None
                for l in lines[-3:]+lines[:2]:
                    m=re.fullmatch(r'\s*(\d{1,3})(?:\s*/\s*\d{1,3})?\s*',l)
                    if m:printed=m.group(1)
                if '目录' not in ''.join(lines[:4]) and not any('......' in x for x in lines[:10]):
                    for l in lines[:10]:
                        if re.match(r'^第[一二三四五六七八九十0-9]+[章节]\s*\S',l) and len(l)<55:chapter=l.strip();break
                        if l.strip() in ['管理层讨论与分析','財務報表','財務報表附註','財務摘要','主席報告','業務回顧','财务报告','公司简介和主要财务指标']:chapter=l.strip();break
                tables=[]
                try:
                    for t in pg.find_tables():
                        grid=t.extract();grid=[[re.sub(r'\s+',' ',c or '').strip() for c in row] for row in grid]
                        if len(grid)<2 or max(map(len,grid),default=0)<2:continue
                        if sum(bool(c) for row in grid for c in row)<4:continue
                        tid=f'{source["code"]}-p{n}{side}-t{len(tables)+1}'
                        tables.append(dict(id=tid,bbox=list(t.bbox),rows=grid));table_count+=1
                        # 重复前两行以保留多层表头，保存原始行列不猜测空白单元格含义。
                        header='\n'.join(' | '.join(row) for row in grid[:2]);body=grid[2:]
                        pre='\n'.join(l for l in lines if any(x in l for x in ['单位','單位','币种','幣種']))[:180]
                        groups=[];buf=[];length=0
                        for row in body:
                            r=' | '.join(row)
                            if length+len(r)>750 and buf:groups.append(buf);buf=[];length=0
                            buf.append(r);length+=len(r)
                        if buf:groups.append(buf)
                        if not groups:groups=[[]]
                        for group in groups:chunk(pre+'\n'+header+'\n'+'\n'.join(group),n,side,'table',printed,tid)
                except Exception as e:tables=[{'extraction_error':type(e).__name__}]
                # 全页文字保留，避免无边框表格或跨页表格漏失；与表格块重复在召回时去重。
                cleaned='\n'.join(l for l in lines if not re.fullmatch(r'\d{1,3}(?:/\d{1,3})?',l.strip()) and not ('半年度报告' in l and len(l)<45))
                for part in split_lines(cleaned):chunk(part,n,side,'text',printed)
                pages.append(dict(company=company,pdf_page=n,side=side,printed_page=printed,chapter=chapter,text=text,tables=tables))
            p.close()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f'{source["code"]}_pages.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
    (OUT/f'{source["code"]}_chunks.json').write_text(json.dumps(chunks,ensure_ascii=False),encoding='utf8')
    print(f'{company}: {source["pages"]} PDF页，{len(chunks)}块，{table_count}张表',flush=True)
    source.update(chunk_count=len(chunks),table_count=table_count)
    return source,chunks

def main():
    sources=json.loads((ROOT/'sources_2026H1.json').read_text());all_chunks=[];verified=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for source,chunks in pool.map(extract,sources):verified.append(source);all_chunks.extend(chunks)
    (OUT/'chunks.json').write_text(json.dumps(all_chunks,ensure_ascii=False),encoding='utf8')
    (ROOT/'sources_2026H1.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2),encoding='utf8')
    print('合计',len(all_chunks),'块',flush=True)
if __name__=='__main__':
    main()
    from repair_metadata import repair
    repair()
