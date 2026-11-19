"""把中国政府网上的法规网页全文切成「章 → 条」结构，并标注版本与效力状态。

输入：data/raw/regs.json（浏览器从 gov.cn 抓取的页面正文，见 README「数据来源」）
输出：data/clean/articles.jsonl，每行一条：文件、版本、效力、章、条号、正文
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CN = {c: i for i, c in enumerate("零一二三四五六七八九")}

DOCS = {
    "reg2017": dict(doc="医疗器械监督管理条例", short="条例", version="2017 修订版", order="国务院令第 680 号",
                    effective="2017-05-04", repealed="2021-06-01", status="已废止", url="https://www.gov.cn/gongbao/content/2017/content_5197006.htm"),
    "reg2021": dict(doc="医疗器械监督管理条例", short="条例", version="2021 修订版", order="国务院令第 739 号",
                    effective="2021-06-01", repealed=None, status="现行有效", url="https://www.gov.cn/gongbao/content/2021/content_5595920.htm"),
    "ae2018": dict(doc="医疗器械不良事件监测和再评价管理办法", short="不良事件办法", version="2018 版", order="市场监管总局、国家卫健委令第 1 号",
                   effective="2019-01-01", repealed=None, status="现行有效", url="https://www.gov.cn/zhengce/2021-06/24/content_5728115.htm"),
}


def cn2int(s):
    """一百零三 → 103；二十 → 20；十二 → 12"""
    n, cur = 0, 0
    for ch in s:
        if ch in CN: cur = CN[ch]
        elif ch == "十": n += (cur or 1) * 10; cur = 0
        elif ch == "百": n += (cur or 1) * 100; cur = 0
    return n + cur


ART = re.compile(r"^\s*第([一二三四五六七八九十百零]+)条[\s　]*")
CHAP = re.compile(r"^\s*第([一二三四五六七八九十]+)章[\s　]*(.+)$")
END = re.compile(r"\n链接：|扫一扫|【我要纠错】|相关稿件|网站纠错|责任编辑|主办单位")


def parse(key, text):
    first = text.find("第一条")
    start = text.rfind("第一章", 0, first)
    body = text[start if start >= 0 else first:]
    m = END.search(body)
    if m: body = body[:m.start()]
    out, chap, cur = [], "", None
    for line in [l.strip().replace("　", " ").strip() for l in body.split("\n")]:
        if not line: continue
        c = CHAP.match(line)
        if c and not ART.match(line):
            chap = f"第{c.group(1)}章 {re.sub(r'[ ]+', '', c.group(2))}"; continue
        a = ART.match(line)
        if a:
            if cur: out.append(cur)
            no = cn2int(a.group(1))
            cur = dict(key=key, **DOCS[key], chapter=chap, no=no, label=f"第{a.group(1)}条", text=line[a.end():].strip())
        elif cur:
            cur["text"] += "\n" + line
    if cur: out.append(cur)
    for i, x in enumerate(out):
        x["id"] = f"{key}-{x['no']:03d}"
    return out


def main():
    raw = json.load(open(ROOT / "data/raw/regs.json", encoding="utf-8"))
    arts = []
    for k in DOCS:
        a = parse(k, raw[k])
        nos = [x["no"] for x in a]
        assert nos == list(range(1, len(nos) + 1)), (k, [n for i, n in enumerate(nos, 1) if n != i][:5])
        arts += a
        print(k, len(a), "条，", len({x['chapter'] for x in a}), "章")
    p = ROOT / "data/clean/articles.jsonl"; p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for x in arts: f.write(json.dumps(x, ensure_ascii=False) + "\n")
    return arts


if __name__ == "__main__":
    main()
