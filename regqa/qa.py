"""法规问答引擎：版本感知检索 + 条号精确定位 + 可答性门槛 + 新旧版变化提示。

和前端 web/app.js 是同一套算法（前端为了在浏览器里实时运行，用 JS 重写了一遍；tests 里有一致性检查用的样例）。

流程
1. 条号直达：问题里写了「条例第三十八条」「办法第25条」→ 直接取该条（默认现行版，写了 2017 / 旧版则取旧版）
2. 版本过滤：默认只检索「现行有效」的文件；问题里出现 旧版 / 2017 / 修订前 / 原来 等词，才放开已废止版本
3. 检索：字符 2-gram BM25（中文法规用字面匹配很稳，数字、时限、机构名都要精确）
4. 可答性门槛：问题里的关键字在命中条款中的覆盖率不够、或分数太低 → 拒答，不让模型硬编
5. 回答：抽取最相关的句子 + 引用（文件、版本、条号）；若该条在 2021 修订中有变化，附上旧版原文对照
"""
import json, math, re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = re.compile(r"旧版|老版|2017|二〇一七|修订前|修改前|原来|以前|过去|曾经|原条例|上一版")
STOP = set("的了和与及或在是对于为以由向按其之等中上下个各有无请问一下什么哪些怎么如何多少几时候规定要求条例办法医疗器械应当")
CN = "零一二三四五六七八九"

# 口语 / 行业说法 → 法规用语（第一次留出集暴露的问题：用户不会说「未取得许可证」「委托生产」）
SYNONYMS = [
    (r"外包|代工|找.{0,4}工厂生产|OEM", "委托生产 受托生产企业"),
    (r"UDI|追溯码", "唯一标识 可追溯"),
    (r"无证|没拿到|没有.{0,3}(许可证|注册证)|未经许可", "未取得 许可证 注册证"),
    (r"停产|停止生产", "暂停生产"),
    (r"多久|多长时间|几天|多少天", "日内 工作日"),
    (r"外包装|标签上", "标签"),
    (r"上市后监测|售后安全", "不良事件监测"),
]
DEFN = re.compile(r"什么是|是指|定义|含义|怎么界定")


def rewrite(q):
    extra = [rep for pat, rep in SYNONYMS if re.search(pat, q, re.I)]
    return q + (" " + " ".join(extra) if extra else "")


def norm(t): return re.sub(r"\s", "", t)


def bigrams(t):
    t = norm(t)
    return [t[i:i + 2] for i in range(len(t) - 1)]


def content_chars(q):
    q = re.sub(r"第[一二三四五六七八九十百零\d]+条", "", norm(q))
    q = HISTORY.sub("", q)
    return {c for c in q if c not in STOP and not re.match(r"[，。？！、：；（）()?]", c)}


def cn2int(s):
    if s.isdigit(): return int(s)
    n = cur = 0
    for ch in s:
        if ch in CN: cur = CN.index(ch)
        elif ch == "十": n += (cur or 1) * 10; cur = 0
        elif ch == "百": n += (cur or 1) * 100; cur = 0
    return n + cur


class Engine:
    def __init__(self, articles=None, alignment=None, k1=1.4, b=0.6, min_cov=0.55, min_score=6.0):
        self.A = articles or [json.loads(l) for l in open(ROOT / "data/clean/articles.jsonl", encoding="utf-8")]
        al = alignment or json.load(open(ROOT / "data/clean/alignment.json", encoding="utf-8"))
        self.new2old = {r["new"]: r for r in al["rows"] if r["new"]}
        self.old2new = {r["old"]: r for r in al["rows"] if r["old"]}
        self.by = {a["id"]: a for a in self.A}
        self.tf = {a["id"]: collections.Counter(bigrams(a["text"])) for a in self.A}
        self.len = {i: sum(c.values()) for i, c in self.tf.items()}
        self.avg = sum(self.len.values()) / len(self.len)
        df = collections.Counter(g for c in self.tf.values() for g in c)
        N = len(self.A)
        self.idf = {g: math.log(1 + (N - n + 0.5) / (n + 0.5)) for g, n in df.items()}
        self.k1, self.b, self.min_cov, self.min_score = k1, b, min_cov, min_score

    def bm25(self, q, ids):
        qg = collections.Counter(bigrams(q))
        out = []
        for i in ids:
            tf, L, s = self.tf[i], self.len[i], 0.0
            for g, qn in qg.items():
                f = tf.get(g)
                if f: s += self.idf.get(g, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * L / self.avg))
            out.append((s, i))
        return sorted(out, reverse=True)

    def pool(self, q, use_version_filter=True):
        hist = bool(HISTORY.search(q))
        want_ae = "不良事件" in q and ("办法" in q or "监测机构" in q or "持有人" in q or "群体" in q or "定期风险" in q or "再评价" in q)
        ids = []
        for a in self.A:
            if use_version_filter and not hist and a["status"] != "现行有效": continue
            if use_version_filter and hist and a["key"] == "reg2021": continue    # 问旧版：条例只看 2017 版
            ids.append(a["id"])
        return ids, hist

    def lookup(self, q, hist):
        m = re.search(r"第([一二三四五六七八九十百零\d]+)条", q)
        if not m: return None
        no = cn2int(m.group(1))
        key = "ae2018" if "办法" in q or "不良事件" in q else ("reg2017" if hist else "reg2021")
        a = self.by.get(f"{key}-{no:03d}")
        return a or "NOT_FOUND"

    def best_sentences(self, q, text, n=2):
        cs = content_chars(q)
        sents = [s for s in re.split(r"(?<=[。；])", norm(text)) if s]
        scored = sorted(((len(cs & set(s)) + 0.5 * len(set(bigrams(q)) & set(bigrams(s))), i, s) for i, s in enumerate(sents)), reverse=True)[:n]
        return "".join(s for _, i, s in sorted(scored, key=lambda x: x[1]))

    def change_note(self, a):
        if a["key"] == "reg2021":
            r = self.new2old.get(a["id"])
            if r and r["kind"] == "新增": return {"kind": "2021 修订新增", "old": None}
            if r and r["kind"] == "有修改": return {"kind": "2021 修订有修改", "old": self.by[r["old"]]}
        if a["key"] == "reg2017":
            r = self.old2new.get(a["id"])
            if r is None or r["kind"] == "删除或并入": return {"kind": "2021 修订已删除", "new": None}
            return {"kind": "已被 2021 修订版取代", "new": self.by[r["new"]]}
        return None

    def ask(self, q, use_version_filter=True, use_gate=True, use_rewrite=True):
        q0 = q
        if use_rewrite: q = rewrite(q)
        ids, hist = self.pool(q, use_version_filter)
        hit = self.lookup(q, hist)
        if hit == "NOT_FOUND":
            return dict(status="NOT_FOUND", reason="该条号在资料库里不存在", cites=[])
        if hit:
            return dict(status="OK", answer=norm(hit["text"])[:400], cites=[hit["id"]], top=[hit["id"]], route="条号直达", change=self.change_note(hit))
        ranked = self.bm25(q, ids)
        if use_rewrite and DEFN.search(q0):   # 问定义：「用语的含义」条款加权
            ranked = sorted(((sc * (1.6 if "含义" in self.by[i]["text"][:20] else 1), i) for sc, i in ranked), reverse=True)
        ranked = ranked[:5]
        if not ranked or ranked[0][0] <= 0:
            return dict(status="NOT_FOUND", reason="没有检索到相关条款", cites=[], top=[])
        s, top = ranked[0]
        a = self.by[top]
        cs = content_chars(q)
        cov = len(cs & set(norm(a["text"]))) / max(1, len(cs))
        if use_gate and (cov < self.min_cov or s < self.min_score):
            return dict(status="NOT_FOUND", reason=f"资料库里没有足够依据（关键字覆盖 {cov:.0%}）", cites=[], top=[i for _, i in ranked], cov=cov, score=s)
        return dict(status="OK", answer=self.best_sentences(q, a["text"]), cites=[top], top=[i for _, i in ranked], route="检索",
                    cov=round(cov, 2), score=round(s, 1), change=self.change_note(a))


if __name__ == "__main__":
    import sys
    e = Engine()
    r = e.ask(" ".join(sys.argv[1:]) or "第三类医疗器械经营许可多久作出决定？")
    print(json.dumps({k: v for k, v in r.items() if k != "change"}, ensure_ascii=False, indent=1))
    if r.get("change"): print("变化提示：", r["change"]["kind"])


def _ask_baseline(self, q):
    """对照组：所有版本混在一起检索，没有条号直达、没有门槛。"""
    ranked = self.bm25(q, [a["id"] for a in self.A])[:5]
    s, top = ranked[0]
    return dict(status="OK", answer=self.best_sentences(q, self.by[top]["text"]), cites=[top], top=[i for _, i in ranked])


Engine.ask_baseline = _ask_baseline
