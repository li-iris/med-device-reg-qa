"""新旧版条款对照：2017 版条例 ↔ 2021 版条例。

条号整体重排（80 条 → 107 条），不能按条号对。做法：
1. 字符 2-gram TF-IDF 余弦相似度算候选；
2. 匈牙利式贪心一对一匹配（相似度从高到低取，阈值 0.30）；
3. 对匹配上的条款用 difflib 算编辑相似度，分「基本未变 / 有修改」；未匹配的为「新增」或「删除」。
输出 data/clean/alignment.json，前端「新旧对照」页使用。
"""
import json, re, difflib, math, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def grams(t):
    t = re.sub(r"\s", "", t)
    return collections.Counter(t[i:i + 2] for i in range(len(t) - 1))


def main(th=0.30, same=0.92):
    A = [json.loads(l) for l in open(ROOT / "data/clean/articles.jsonl", encoding="utf-8")]
    old = [a for a in A if a["key"] == "reg2017"]; new = [a for a in A if a["key"] == "reg2021"]
    G = {a["id"]: grams(a["text"]) for a in old + new}
    df = collections.Counter(g for a in old + new for g in G[a["id"]])
    N = len(old) + len(new)
    def vec(i):
        v = {g: c * math.log(N / df[g]) for g, c in G[i].items()}
        n = math.sqrt(sum(x * x for x in v.values())) or 1
        return {g: x / n for g, x in v.items()}
    V = {i: vec(i) for i in G}
    cos = lambda a, b: sum(x * V[b].get(g, 0) for g, x in V[a].items())
    pairs = sorted(((cos(n["id"], o["id"]), n["id"], o["id"]) for n in new for o in old), reverse=True)
    used_n, used_o, match = set(), set(), {}
    for s, n, o in pairs:
        if s < th: break
        if n in used_n or o in used_o: continue
        used_n.add(n); used_o.add(o); match[n] = (o, s)
    byid = {a["id"]: a for a in A}
    rows = []
    for n in new:
        if n["id"] in match:
            o, s = match[n["id"]]
            r = difflib.SequenceMatcher(None, byid[o]["text"], n["text"]).ratio()
            rows.append(dict(new=n["id"], old=o, sim=round(s, 3), edit=round(r, 3), kind="基本未变" if r >= same else "有修改"))
        else:
            rows.append(dict(new=n["id"], old=None, sim=None, edit=None, kind="新增"))
    for o in old:
        if o["id"] not in used_o:
            rows.append(dict(new=None, old=o["id"], sim=None, edit=None, kind="删除或并入"))
    c = collections.Counter(r["kind"] for r in rows)
    json.dump(dict(rows=rows, summary=dict(c)), open(ROOT / "data/clean/alignment.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return rows, c


if __name__ == "__main__":
    rows, c = main()
    print(dict(c))
