"""按已核验清单下载；来源和 SHA-256 校验可复现。"""
import json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for source in json.loads((ROOT/'sources_2026H1.json').read_text()):
    path=ROOT/source['file'];path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']:
        print(source['company'],'已存在且校验通过');continue
    tmp=path.with_suffix('.download')
    subprocess.run(['curl','--fail','--location','--retry','2','--max-time','90',source['url'],'-o',str(tmp)],check=True)
    data=tmp.read_bytes()
    if not data.startswith(b'%PDF') or hashlib.sha256(data).hexdigest()!=source['sha256']:raise ValueError(f'{source["company"]} 文件校验失败；保留 .download 供核查，未覆盖原报告')
    tmp.replace(path);print(source['company'],'下载校验通过')
