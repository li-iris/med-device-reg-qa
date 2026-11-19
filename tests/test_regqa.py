import json, unittest
from pathlib import Path
from regqa.parse import cn2int
from regqa.qa import Engine, rewrite

ROOT = Path(__file__).resolve().parents[1]
E = Engine()


class TestParse(unittest.TestCase):
    def test_cn2int(self):
        for s, n in [("一", 1), ("十", 10), ("十二", 12), ("二十", 20), ("三十八", 38), ("一百零七", 107), ("一百二十", 120)]:
            self.assertEqual(cn2int(s), n)

    def test_article_counts_and_no_gaps(self):
        A = [json.loads(l) for l in open(ROOT / "data/clean/articles.jsonl", encoding="utf-8")]
        for k, n in [("reg2017", 80), ("reg2021", 107), ("ae2018", 80)]:
            nos = [a["no"] for a in A if a["key"] == k]
            self.assertEqual(nos, list(range(1, n + 1)), k)


class TestEngine(unittest.TestCase):
    def test_version_trap(self):
        r = E.ask("第三类医疗器械经营许可，药监部门要在多少个工作日内作出决定？")
        self.assertEqual(r["cites"], ["reg2021-042"]); self.assertIn("20个工作日", r["answer"])
        self.assertEqual(r["change"]["kind"], "2021 修订有修改")

    def test_history_question_uses_old_version(self):
        r = E.ask("2017年版条例里，第三类经营许可的审查时限是多少？")
        self.assertEqual(r["cites"], ["reg2017-031"]); self.assertIn("30个工作日", r["answer"])

    def test_article_lookup_and_missing_article(self):
        self.assertEqual(E.ask("条例第三十八条")["cites"], ["reg2021-038"])
        self.assertEqual(E.ask("条例第一百二十条是什么内容？")["status"], "NOT_FOUND")

    def test_refuses_out_of_scope(self):
        self.assertEqual(E.ask("洁净室的悬浮粒子标准是多少？")["status"], "NOT_FOUND")

    def test_colloquial_rewrite(self):
        self.assertIn("委托生产", rewrite("找代工厂生产谁负责"))
        self.assertEqual(E.ask("找代工厂生产，出了质量问题谁担责？")["cites"], ["reg2021-034"])


class TestEval(unittest.TestCase):
    def test_full_pipeline_beats_baseline_and_no_stale(self):
        ev = json.load(open(ROOT / "results/eval.json", encoding="utf-8"))
        for s in ev:
            self.assertGreaterEqual(ev[s]["full"]["metrics"]["acc"], ev[s]["baseline"]["metrics"]["acc"])
            self.assertEqual(ev[s]["full"]["metrics"]["stale"], 0)


if __name__ == "__main__":
    unittest.main()
