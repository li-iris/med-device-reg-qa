"""三条管线对比：
  baseline   纯检索（不分版本、无门槛）
  +version   加版本过滤和条号直达
  full       再加可答性门槛
指标：答对率（引用了 gold 条款，或无答案题正确拒答）、答成旧版数（引用了 trap 条款）、无答案题拒答率、Top-3 命中率。
"""
import json
from pathlib import Path
from regqa.qa import Engine
from regqa.evalset import DEV, HOLDOUT, HOLDOUT2

ROOT = Path(__file__).resolve().parents[1]
PIPES = {"baseline": dict(use_version_filter=False, use_gate=False), "+version": dict(use_version_filter=True, use_gate=False, use_rewrite=False), "+gate": dict(use_version_filter=True, use_gate=True, use_rewrite=False), "full": dict(use_version_filter=True, use_gate=True, use_rewrite=True)}


def judge(r, item):
    if item["type"] == "none":
        return r["status"] == "NOT_FOUND"
    return r["status"] == "OK" and bool(set(r["cites"]) & set(item["gold"]))


def run(e, items, pipe):
    rows = []
    for it in items:
        if pipe == "baseline":
            r = e.ask_baseline(it["q"])
        else:
            r = e.ask(it["q"], **PIPES[pipe])
        rows.append(dict(q=it["q"], type=it["type"], ok=judge(r, it), stale=bool(set(r.get("cites", [])) & set(it["trap"])),
                         top3=bool(set(r.get("top", [])[:3]) & set(it["gold"])) if it["gold"] else None,
                         cites=r.get("cites"), status=r["status"]))
    n = len(rows); none = [x for x in rows if x["type"] == "none"]; ans = [x for x in rows if x["type"] != "none"]
    trap = [x for it, x in zip(items, rows) if it["trap"]]
    return dict(acc=sum(x["ok"] for x in rows) / n, stale=sum(x["stale"] for x in trap), trap_n=len(trap),
                refuse=(sum(x["ok"] for x in none) / len(none)) if none else None,
                top3=sum(bool(x["top3"]) for x in ans) / len(ans)), rows


def main():
    e = Engine()
    res = {}
    for name, items in (("dev", DEV), ("holdout", HOLDOUT), ("holdout2", HOLDOUT2)):
        res[name] = {}
        for p in PIPES:
            m, rows = run(e, items, p)
            res[name][p] = dict(metrics=m, rows=rows)
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    json.dump(res, open(out / "eval.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    lines = ["| 题集 | 管线 | 答对率 | 答成旧版 | 无答案题拒答 | Top-3 命中 |", "|---|---|---|---|---|---|"]
    for name in res:
        for p, v in res[name].items():
            m = v["metrics"]
            lines.append(f"| {name} | {p} | {m['acc']:.0%} | {m['stale']}/{m['trap_n']} | {m['refuse']:.0%} | {m['top3']:.0%} |")
    open(out / "report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    for name in res:
        for x in res[name]["full"]["rows"]:
            if not x["ok"]: print("MISS", name, x["type"], x["q"], x["cites"], x["status"])
    return res


if __name__ == "__main__":
    main()
