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
('材料与方法','使用 9 家纯航空公司（8 家客运航司/集团、1 家货运航司）的 2026 年半年报全文，来源为巨潮资讯。共 1,430 个物理 PDF 页、3,758 个片段；保留公司、章节、页码与原文。正文切块约 900 字，表格保存行列；使用 1,024 维 text-embedding-v4 向量、BM25 和 RRF 融合。普通问题召回 8 块，全景问题逐公司 3 块，共 27 块。'),
('评测结果与判定','2026-10-13 重新运行 10 道题，其中 2 道为跨公司全景题；逐题回查原 PDF，区分完整正确与仅主要要点正确。通过 5 题、部分正确 3 题、不通过 2 题，完整答案通过率 50%。这是单次固定 10 题测试结果，不能代表一般问题准确率。'),
('哪些题答得好','Q01 春秋合并营收、Q02 华夏客座率、Q03 国泰收益与币种、Q06 华夏经营模式、Q08 国航客座率定义通过。公司、指标和期间明确的局部事实通常能召回直接证据。国泰未命中摘要参考页，却从其他财务页获得同一指标，说明参考页命中率不能替代答案核对。'),
('哪些题翻车、为什么','Q04 主要现金流数值正确，但把母公司数据误称异常；Q05 风险敏感性正确，额外敞口表错读年份、单位；Q07 三板块正确，却补写无证据的行业及股权断言。Q09 漏召回国货航营收（原文为 12,538,900,409 元），且模型部分亿元换算少 10 倍。Q10 缺少南航、华夏需求风险页，模型误称全文未披露，并在第 8 家中途截断。错误分别来自切块/表头上下文、召回缺失、生成推断和长度限制。'),
('检索调试与结论','网页先落盘并展示检索器实际 Top-k 原始片段，再以相同片段生成答案；记录排名、ID、公司、报告、章节、页码、分数、全文和召回来源。JSONL 可按 request_id 联结召回、答案、错误与核对事件。财报数字、定义与可追溯事实适合建库；已有召回不保证生成正确。应优先检查证据与口径，再考虑改进表头传递、全景召回与输出长度。'),
('范围与限制','按用户约定保留 9 家，未达到课程“10 家以上”的数量要求。章节规则及复杂/跨页表格未全量人工审计；本次逐题核对相关财报页面，另对 4 页表格进行图像核验。不将未召回视为未披露，不混加人民币/港币或有关联的集团营收。')]
story=[P('航空财报问答知识库 · 一页结论','title'),P('第三课作业 A | 9 家航空公司 | 2026H1 | 核对日期：2026-10-13','sub')]
for title,text in sections:story.extend([P(title,'head'),P(text)])
story.append(Spacer(1,6));story.append(P('证据文件：evaluation/reviewed_results.jsonl（10 题全文）｜review_summary.csv（逐题判定）｜retrieval_chunks.csv（118 块）','small'))
def footer(c,d):
 c.setFont(FONT,8);c.setFillColor(colors.HexColor('#64748b'));c.drawString(34,22,'结论来自实际评测与原文核对；失败记录保留，未改写模型输出。');c.drawRightString(A4[0]-34,22,str(d.page))
doc=SimpleDocTemplate(str(OUT/'一页结论.pdf'),pagesize=A4,rightMargin=34,leftMargin=34,topMargin=30,bottomMargin=34);doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'一页结论.md').write_text('# 航空财报问答知识库：一页结论\n\n'+'\n\n'.join('## '+t+'\n\n'+v for t,v in sections)+'\n')
# Keep stale stage draft out of the active hand-in list, while retaining it in history.
stale=OUT/'一页结论_阶段稿.md'
if stale.exists():
 archive=ROOT/'evaluation/archive';archive.mkdir(exist_ok=True);stale.rename(archive/'一页结论_旧阶段稿.md')
print('Created',OUT/'一页结论.pdf')
