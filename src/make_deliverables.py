"""Generate the one-page conclusion from the reviewed, unedited model run."""
import json,xml.sax.saxutils as xml
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';OUT.mkdir(exist_ok=True)
font='/Library/Fonts/Arial Unicode.ttf'
if Path(font).exists():pdfmetrics.registerFont(TTFont('CJK',font))
else:
 from reportlab.pdfbase.cidfonts import UnicodeCIDFont
 pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));font='STSong-Light'
FONT='CJK' if font!='STSong-Light' else font
r=json.loads((ROOT/'evaluation/reviewed_results.json').read_text());summary=r['summary']
styles={
 'title':ParagraphStyle('title',fontName=FONT,fontSize=21,leading=29,textColor=colors.HexColor('#102c45'),spaceAfter=8),
 'sub':ParagraphStyle('sub',fontName=FONT,fontSize=9,leading=14,textColor=colors.HexColor('#527080'),spaceAfter=12),
 'head':ParagraphStyle('head',fontName=FONT,fontSize=12,leading=18,textColor=colors.HexColor('#14657a'),spaceBefore=9,spaceAfter=5),
 'body':ParagraphStyle('body',fontName=FONT,fontSize=10,leading=16,spaceAfter=6),
 'cell':ParagraphStyle('cell',fontName=FONT,fontSize=9,leading=14),
 'small':ParagraphStyle('small',fontName=FONT,fontSize=8,leading=12,textColor=colors.HexColor('#64748b'))}
def P(text,style='body'):return Paragraph(xml.escape(text),styles[style])
sections=[
('材料与方法','11家纯航空公司（10家客运航司/集团、1家货运航司）的2026H1官方完整报告：8份巨潮、1份港交所、2份台湾证交所。共1,564个物理PDF页、4,014个片段；逐份核对目录、报表、附注和SHA-256。新增中华航空、长荣航空；国泰原文件与港交所全文哈希一致，“撮要”只是章节，已切换官方来源。'),
('索引与证据保存','正文约900字切块；表格保存行列，国货航双页左右分开。新增台湾财报保留日期行，取民国115年（2026年）1-6月列，不混用4-6月单季。重建1,024维text-embedding-v4向量、BM25及RRF融合。普通题8块，全景题每家3块；130个实际召回块均在生成前保存，网页展示排名、ID、公司、报告、章节、页码、分数、全文和来源。'),
('同套10题复评','2026-10-14实际调用qwen-plus，Q01-Q08原文不变，Q09-Q10仅由9家扩为11家。逐题回查PDF：5题通过、3题部分正确、2题不通过，完整通过率50%。旧版题目、原始输出、核对、截图及结论保留。全景输出预算3000增至5500 tokens，本轮未截断；样本与生成条件均改变，不能作单变量因果比较。'),
('哪些题答得好、哪些翻车','春秋营收、华夏客座率/经营模式、国泰集团收益、国航客座率定义通过。现金流题正确主数却误判母公司值为排版错误；海航题误读敞口年份、换算及升贬值方向；国货航题补写无证据行业比例。Q09缺南航/国货航营收，华夏国内收入误作合并总额；新增中华、长荣半年营收读对。Q10输出列齐11家，却把海航需求写给南航、长荣租赁数据写给中华，并错读新台币千元。'),
('公司覆盖、证据覆盖与答案评价','按第61-63及90-92页分别记录三层证据。Q09召回公司11/11，营收证据covered 8、partial 1、missing 2，答案8家营收正确。Q10召回/回答公司均11/11，33项风险证据为covered 27、partial 1、missing 5，完整答案仍不通过。JSONL联结召回与答案，CSV逐公司列证据义务、原页与错误环节；未召回不等于全文未披露。'),
('结论与限制','可追溯财报数字、定义适合建库；全景比较必须检查公司、期间、单位、合并/母公司口径及证据缺口。人民币、港元、新台币分列，不直接排名或相加。本次达到至少10家公司完整报告的数量要求；表头及章节仍有自动提取限制，未逐页人工审计全部1,564页。保持原检索逻辑，没有实现完整自主补查或GraphRAG；失败记录是作业分析的一部分，材料完成不代表课程评分通过。')]
story=[P('航空财报问答知识库 · 一页结论','title'),P('第三课作业 A | 11 家航空公司 | 2026H1 | 增量核对：2026-10-14','sub')]
for title,text in sections:story.extend([P(title,'head'),P(text)])
story.append(Spacer(1,6));story.append(P('证据文件：evaluation/reviewed_results.jsonl（10 题全文）｜review_summary.csv（逐题判定）｜retrieval_chunks.csv（130 块）','small'))
def footer(c,d):
 c.setFont(FONT,8);c.setFillColor(colors.HexColor('#64748b'));c.drawString(34,22,'结论来自实际评测与原文核对；失败记录保留，未改写模型输出。');c.drawRightString(A4[0]-34,22,str(d.page))
doc=SimpleDocTemplate(str(OUT/'一页结论.pdf'),pagesize=A4,rightMargin=34,leftMargin=34,topMargin=30,bottomMargin=34);doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'一页结论.md').write_text('# 航空财报问答知识库：一页结论\n\n'+'\n\n'.join('## '+t+'\n\n'+v for t,v in sections)+'\n')
# Keep stale stage draft out of the active hand-in list, while retaining it in history.
stale=OUT/'一页结论_阶段稿.md'
if stale.exists():
 archive=ROOT/'evaluation/archive';archive.mkdir(exist_ok=True);stale.rename(archive/'一页结论_旧阶段稿.md')
print('Created',OUT/'一页结论.pdf')
