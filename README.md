# 第三课作业 A：航空财报问答知识库

使用 **9 家纯航空公司**的 2026 年半年报全文，1,430 个物理 PDF 页、3,758 个 chunks。已经建立真实向量 + BM25 索引，网页可提问、显示原始召回并生成带块 ID 出处的答案。2026-10-13 重新运行并逐题核对 10 道题：**5 题通过、3 题部分正确、2 题不通过**。失败记录和模型原始回答完整保留。

按用户约定不补直升机、机场或制造企业。这 9 家样本**未满足课程“10 家以上”数量要求**；本项目不宣称完全满足所有硬性条件。财报均来自巨潮资讯披露平台，不将券商研报冒充公司财报。

## 样本与来源

| 公司 | 代码 | PDF 页 | chunks |
|---|---|---:|---:|
| 中国国航 | 601111 | 183 | 280 |
| 中国东航 | 600115 | 199 | 313 |
| 南方航空 | 600029 | 211 | 366 |
| 海航控股 | 600221 | 173 | 517 |
| 春秋航空 | 601021 | 181 | 522 |
| 吉祥航空 | 603885 | 205 | 593 |
| 华夏航空 | 002928 | 144 | 559 |
| 国货航 | 001391 | 78 | 486 |
| 国泰航空 | 00293 | 56 | 122 |

来源链接、文件路径与 SHA-256 见 `sources_2026H1.json`。9 个原 PDF 已做哈希校验。索引仅含这 9 家；本机历史缓存可能有旧报告，未纳入本次聚合索引。

## 快速运行

已配置且已建索引的本机可双击 `启动问答网页.command`，或：

```sh
python3 src/server.py
```

浏览器打开 http://127.0.0.1:8765/ 。若服务已经运行，直接打开网页，不必重建向量或重复评测。要载入代码改动，关闭本项目旧终端进程后重新启动；不要终止其他应用。

从代码仓库恢复完整系统：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 在本机 .env 填写密钥和对应业务空间的 OpenAI 兼容 Base URL
python3 src/download.py
python3 src/prepare.py
python3 src/build.py
python3 src/build.py --vectors
python3 src/server.py
```

`.env` 不进入代码仓库或提交包。向量模型为 `text-embedding-v4`、1,024 维，每批 10 段，缓存支持续跑。生成模型由 `.env` 配置，本次为 `qwen-plus`。API 调用会消耗所配置服务额度。本机 macOS 使用系统 CA 补充 Python 证书链，保持 TLS 验证。

## 原始检索可视化

页面“混合检索并回答”分两步执行：

1. `/api/retrieve` 执行真实检索，先追加落盘 `retrieval` 事件，返回原始 Top-k 与 `request_id`。
2. 浏览器把完整 chunks 渲染到页面，随后请求 `/api/generate`。服务端根据该 ID 使用同一批已保存的 chunks，**不会再次检索或由 LLM 挑选块**。

每块显示 rank、chunk_id、公司名、报告名称/年份、章节、PDF 页码、retrieval score、完整文本，以及 `BM25`、`vector retrieval` 或 `fusion`。全文在可滚动文本框内完整保留，可导出 JSON。

普通检索最多返回 8 块；全景检索按公司分组每家最多 3 块，9 家最多 27 块。rank 表示检索器最终返回顺序；全景顺序为公司分组顺序，**不是全球分数从高到低**。现有去重可能使实际数少于上限。

BM25 分数保留现有财务摘要加权；向量分数为归一化向量内积（余弦相似度）；混合最终分数为 RRF，各自量纲不同。`retrieval_contributions` 记录实际参与评分的全局/逐公司候选池、方法、候选排名和 RRF 贡献。`fusion` 表示两路均贡献；如果仅一路贡献则标记对应方法。源数据 chunks 的正文和已有筛选/排序公式不因日志而改变。

问题中明确出现唯一公司名时，以该公司为筛选范围，覆盖旧勾选/全景状态；问题出现多家则按实际选择或问题中的公司范围处理。实际筛选在页面显示，并保存日志。

`evaluation/retrieval_logs.jsonl` 为页面事件日志，`retrieval_test_runs.jsonl` 为批量测试事件日志。用同一个 request_id 联结 `retrieval`、`answer`、`error` 和 `review`；模型失败时仍保留已经落盘的原始召回。新日志带 event；没有 event 的行属于历史旧版格式。

## 评测与核对

```sh
python3 src/evaluate.py             # BM25 基线，不调用模型
python3 src/evaluate.py --answers   # 真实混合检索与模型回答，逐题增量保存
python3 -m unittest discover -s tests -v  # 调试时序/过滤/失败保留测试，无付费 API 调用
```

最新已核对文件：

- `evaluation/reviewed_results.jsonl`：10 题，每题含实际召回全文、模型原始回答、是否正确、参考答案来源与错误环节。
- `evaluation/review_summary.csv`：10 行逐题结论与原始模型答案。
- `evaluation/retrieval_chunks.csv`：118 行召回 chunks，所有要求字段。
- `evaluation/reviewed_results.json`：网页点击 10 道测试题时读取的完整记录。
- `deliverables/10题逐题核对.md`：核对解释、九家营收参考表、九家风险证据表。

判定由 Codex 阅读原 PDF 后逐项审查，仍建议提交者自行复核关键页；不冒充教师评分。完整“通过”要求主要答案正确且解释/引用没有实质错误。“部分正确”仍设置 answer_correct=false，另用 core_correct 标记主要要点正确。50% 为这次固定 10 题的完整通过比例，不能代表系统一般准确率。

主要失败包括母公司/合并口径混淆、表头年份和币种误读、无证据行业推断、全景营收漏召回国货航、亿元换算错误、把未召回误称全文未披露、未知引用及输出长度截断。未为提升分数而改写模型原始回答。

## 交付与限制

`deliverables/一页结论.pdf` 为正式一页结论；截图见 `deliverables/screenshots/`。本地 Git 仓库及提交压缩包可用于后续上传。线上仓库目标：https://github.com/lucaswzz843/airline-report-rag-homework（发布状态以远端实际文件为准）。

表格保留提取出的二维行列，表格块重复两行表头；无边框、多层表头、数值跨行和跨页续表不能保证全部自动正确。国货航双页版左右分开保存，普通横向宽表保持整页。物理 PDF 页码与印刷页码可能不同，引用按 PDF 物理页定位。章节使用规则识别，已发现部分章节元数据误标；未全量人工审计 1,430 页。没有 OCR，图片文字可能漏失。日志增强未重写召回公式、去重策略或全景候选配额，因此已记录的召回问题仍是本次评测结果的一部分。
