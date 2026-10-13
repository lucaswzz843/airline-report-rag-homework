"""第一阶段教学脚本：提取指定原文页，保留页码；尚不切块或建立检索。"""
from pathlib import Path
import json
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/raw/春秋航空_2025年年度报告.pdf'
TARGET = ROOT / 'data/processed/春秋航空_2025_样本页.json'

with pdfplumber.open(SOURCE) as pdf:
    records = [
        {
            'source_id': 'spring_601021_2025_annual',
            'company': '春秋航空股份有限公司',
            'report_title': '2025年年度报告',
            'pdf_page': number,
            'printed_page': str(number),
            'page_number_note': '本次指定样本页已人工目视核对，PDF页序与印刷页码一致；不推广到其他页或其他文件。',
            'text': pdf.pages[number-1].extract_text() or '',
        }
        for number in [1, 6, 8, 31]
    ]
TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'共 {len(pdf.pages)} 页；已保存 {len(records)} 个样本页到 {TARGET}')
print('注意：这是初步文本提取；正式财报切块前仍需还原表格行列、表头、单位及脚注。')
