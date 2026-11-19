"""导出前端数据：条款、对照（含逐字差异）、评测结果。"""
import json, difflib, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    A = [json.loads(l) for l in open(ROOT / "data/clean/articles.jsonl", encoding="utf-8")]
    by = {a["id"]: a for a in A}
    al = json.load(open(ROOT / "data/clean/alignment.json", encoding="utf-8"))
    for r in al["rows"]:
        if r["kind"] in ("有修改", "基本未变") and r["old"] and r["new"]:
            o, n = re.sub(r"\s", "", by[r["old"]]["text"]), re.sub(r"\s", "", by[r["new"]]["text"])
            r["diff"] = [[t, o[i1:i2], n[j1:j2]] for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, o, n, autojunk=False).get_opcodes()]
    arts = [{k: a[k] for k in ("id", "key", "doc", "short", "version", "status", "effective", "repealed", "order", "url", "chapter", "no", "label", "text")} for a in A]
    ev = json.load(open(ROOT / "results/eval.json", encoding="utf-8"))
    d = ROOT / "web"; d.mkdir(exist_ok=True)
    json.dump(dict(articles=arts, alignment=al), open(d / "data.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(ev, open(d / "eval.json", "w", encoding="utf-8"), ensure_ascii=False)
    print((d / "data.json").stat().st_size, (d / "eval.json").stat().st_size)

if __name__ == "__main__":
    main()
