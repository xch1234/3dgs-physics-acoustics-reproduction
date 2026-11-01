"""Record actual public links and local benchmark gaps; do not infer missing releases."""
from common import ROOT,AUDIT,save,digest
from html.parser import HTMLParser
from urllib.parse import urljoin
import requests,json
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   for k,v in attrs:
    if k=='href' and v:self.links.append(v)
rows=[]
for name,base in [('ABC','https://deep-geometry.github.io/abc-dataset/'),('PhysGaussian','https://xpandora.github.io/PhysGaussian/'),('NeuralSound','https://hellojxt.github.io/NeuralSound/')]:
 parser=Links();parser.feed((AUDIT/'remote'/f'{name}.html').read_text(encoding='utf8'))
 links=sorted(set(urljoin(base,u) for u in parser.links if not u.startswith(('#','mailto:','javascript:'))))
 rows.append(dict(name=name,source=base,links=links))
targets=[]
for row in rows:
 if row['name']=='ABC':
  targets=[u for u in row['links'] if any(s in u.lower() for s in ['download','archive','chunk','abc_','zenodo','drive','figshare'])][:12]
checks=[]
for url in targets:
 try:
  r=requests.get(url,timeout=45,stream=True)
  content=r.raw.read(65536,decode_content=True)
  checks.append(dict(url=url,final_url=r.url,status=r.status_code,content_type=r.headers.get('Content-Type'),content_length=r.headers.get('Content-Length'),sample_bytes=len(content),scope='at most first 64 KiB fetched, not dataset download'))
  r.close()
 except requests.RequestException as e:checks.append(dict(url=url,error=str(e)))
save('checks/V29-public-resource-inventory.json',dict(pages=rows,access_samples=checks,scope='Current linked resources, not an exhaustive internet search or proof that unpublished paper artifacts do not exist.'))
lines=['# 论文级要求与尚缺的证据','','本文件记录补做期间的资源复核。网页可访问、代码可训练、演示可播放，都不能代替论文数据和评测协议。','','## PhysGaussian','','公开 README 提供预训练模型与场景配置。本轮重新取得六份模型并核对了内容。现有静态 Ficus 的 100 个训练视图、200 个测试视图，不是论文 Table 1 的 Wolf/Stool/Plant 变形真值数据。本次尚未取得并完成那个基准的全部训练与变形真值评测；新默认 SH 修正也不等于该基准通过。','','## PAT','','本地 ModalSound 是 2016 教学模块，不是 2006 全部作者工具。已跑通局部 FEM、BEM、多极子拟合与音频。均匀法向导数球体的网格误差不完全单调；精确制造解案例提供了另一组收敛证据。NeoAcoustics 原流程、原论文复杂几何、薄壳/高频完整测试、原硬件 7000 倍基准和受试者实验没有在这里实际完成，继续标为未验证。','','## NeuralSound','','公开 README 明说辐射网络比论文架构更紧凑。原论文训练涉及约 100K ABC 模型及随机材质/模态，本地只使用 24 个程序化几何，且固定几何划分。增加 epoch 不能填补数据和架构差距。独立评估继续报告真实测试误差，不将完成训练作为高精度证据。','','本机为 RTX 2050 4 GB，作者 3080 Ti/3090 测速不能由本机壁钟时间替代。没有组织受试者实验，也没有对此作通过结论。完整 ABC 训练、原架构/全部参考标签和论文 Table 5 评测仍未完成。未把公开页面可访问说成已下载完整训练数据。','','## 环境与统一系统','','空 Conda 前缀安装、源码重新编译和实际运行是本轮可验证的环境恢复范围；同一机器的系统库、驱动与 WSL 不变，因此仍不能叫全新机器验证。远端重新下载证明记录来源的内容一致，没有作者数字签名或独立原始校验清单时，不称为真实性认证。','','同梁高斯表面与相位声学演示是一项新增局部原型。它不包含照片训练高斯到体积材料的自动绑定、MPM 接触到高频振动的耦合，以及同一对象上的 NeuralSound 学习泛化验证。这些研究环节保留为未验证。','','## 实际查到的页面与入口','']
for row in rows:
 lines += [f'### {row["name"]}',f'来源：{row["source"]}','']+[f'- {u}' for u in row['links']]+['']
lines+=['访问记录与限制见 `checks/V29-public-resource-inventory.json`。本文件不声称穷尽了互联网资源，也不推断作者一定没有提供其他版本。']
(AUDIT/'未能完成的论文级要求.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps(dict(pages=len(rows),sampled_links=checks),ensure_ascii=False,indent=2))
