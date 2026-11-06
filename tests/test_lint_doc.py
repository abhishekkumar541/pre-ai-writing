#!/usr/bin/env python3
"""Tests for lint_doc.py and blind_pack.py. Run: python3 -I tests/test_lint_doc.py

Each rule gets a fixture that should fire and a clean document that should not. The real-document
tests are not shipped: they used private documents.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import lint_doc as L  # noqa: E402


CLEAN = """# Growth plan for Acme

Jane Doe, March 2021

Acme asked how to double paid sign-ups this year. I think the answer is to fix the trial before buying more traffic, because most paid visitors leave before they see the product working. Everything below uses the public site as it stood in March 2021.

## Assumptions

- I had no internal data, so the conversion rates are examples.
- A sign-up counts when the person finishes setup.

## 1. Channels

I'd keep search ads and add partner referrals. Search already brings most trials [1], and partners reach teams that never search for the category. Events can wait until the trial converts better.

Partners need a page they can send people to and a simple payout. I'd start with five agencies we already know, and judge the test on finished setups. A code to confirm the email stays.

## 2. The trial

The trial asks for a card before anyone sees a report. I'd move the card to day seven and show a sample report on the first screen. If that lifts finished setups by a fifth, the paid budget can grow.

| Step | Today | Target |
|---|---|---|
| Visit to start | 4% | 6% |
| Start to setup | 30% | 45% |

## What could go wrong

Partners may send small teams that churn. I'd watch the first two months before paying more.

## Next steps

In the first week I'd pull the funnel by source and ask sales which partners already refer work.

## Sources

1. Acme pricing page, read in March 2021: https://example.com/streamline-pricing
"""


def run(text, dtype="memo"):
    doc = L.Doc(text, "")
    rep = L.Report()
    L.lint(doc, dtype, rep)
    return {i["rule"]: i["level"] for i in rep.items}


def para(n=1):
    return ("This is a plain sentence about the plan and what it would change for the team. " * 3 + "\n\n") * n


class CleanDoc(unittest.TestCase):
    def test_clean_memo_has_no_fail(self):
        r = run(CLEAN, "memo")
        self.assertNotIn("FAIL", r.values(), r)

    def test_near_misses(self):
        r = run(CLEAN, "memo")
        for rule in ("placeholders", "jargon", "stock_words", "urls_in_body", "colon_headings", "not_x_but_y",
                     "counter_sections", "no_next_step", "no_assumptions", "late_assumptions", "investor_verbs"):
            self.assertNotIn(rule, r, rule)


class Fires(unittest.TestCase):
    def check(self, text, rule, level, dtype="memo"):
        r = run(text, dtype)
        self.assertEqual(r.get(rule), level, f"{rule}: {r}")

    def test_dash(self):
        self.check("# T\n\nA plan \u2014 with a dash.\n", "dash", "FAIL")

    def test_ellipsis_and_arrow(self):
        self.check("# T\n\nWait… then go.\n", "ellipsis_char", "WARN")
        self.check("# T\n\nVisit -> sign-up -> post.\n", "arrows", "WARN")

    def test_stock_words(self):
        self.check("# T\n\nWe delve into a robust plan.\n", "stock_words", "FAIL")
        self.check("# T\n\nA robust plan.\n", "stock_words", "WARN")

    def test_stock_word_in_quote_or_url_ignored(self):
        r = run('# T\n\nThe page says "a robust and pivotal platform". See https://x.com/streamline-robust\n')
        self.assertNotIn("stock_words", r)

    def test_jargon_is_warn(self):
        self.check("# T\n\nWe will leverage partners and showcase results.\n", "jargon", "WARN")

    def test_investor_verbs_is_warn(self):
        self.check("# T\n\nThe three channels I'd fund, and the one to double down on.\n", "investor_verbs", "WARN")

    def test_investor_verbs_near_miss(self):
        r = run("# T\n\nThe three channels I'd invest in. We found the fundamentals weak.\n")
        self.assertNotIn("investor_verbs", r)

    def test_staged_and_residue(self):
        self.check("# T\n\nHere's the thing: churn is high. I hope this helps!\n", "staged_or_residue", "FAIL")

    def test_meta_labels(self):
        self.check("# T\n\n**The answer in one line.** Fix the trial.\n\n" + para(2), "meta_labels", "FAIL")
        self.check("# T\n\nReasoning: search has intent.\n\n" + para(2), "meta_labels", "FAIL")

    def test_repeated_labels(self):
        block = "**Cost.** Low.\n\n**Impact.** High.\n\n**Owner.** Growth.\n\n"
        self.check("# T\n\n" + block * 2 + para(3), "repeated_labels", "FAIL")
        self.check("# T\n\nDescription: one.\n\nDescription: two.\n\n" + para(3), "repeated_labels", "WARN")

    def test_bullet_bold_leads(self):
        t = "# T\n\n- **Speed:** faster pages.\n- **Trust:** reviews.\n- **Price:** clear plans.\n\n" + para(4)
        self.check(t, "bullet_bold_leads", "FAIL")

    def test_question_bullets_are_fine(self):
        t = "# T\n\n1. **Is the drop real?** Check the tag.\n2. **Did traffic change?** Check terms.\n3. **Did the page change?** Check deploys.\n\n" + para(4)
        self.assertNotIn("bullet_bold_leads", run(t))

    def test_reading_guide(self):
        self.check("# T\n\nHow to read it: each section opens with its answer.\n", "reading_guide", "FAIL")

    def test_coverage_table(self):
        t = "# T\n\n| The brief asks | Section |\n|---|---|\n| Channels | 1 |\n\n" + para(3)
        self.check(t, "coverage_table", "FAIL")

    def test_status_words(self):
        self.check("# T\n\nFees are $20k (Confirmed). Reply time is 2 days (Unconfirmed).\n", "status_words", "FAIL")

    def test_counter_sections(self):
        t = "# T\n\n## A\n\n" + para() + "## The strongest argument against\n\n" + para() + "## B\n\n" + para() + "## Counterargument\n\n" + para()
        self.check(t, "counter_sections", "FAIL")

    def test_colon_and_decimal_headings(self):
        t = "# Plan: my answers\n\n## 01.1 Channels: search wins\n\n" + para() + "## 01.2 Funnel\n\n" + para() + "## 01.3 Drip\n\n" + para()
        r = run(t)
        self.assertEqual(r.get("colon_headings"), "FAIL")
        self.assertEqual(r.get("decimal_numbering"), "FAIL")

    def test_enumerator_colon_is_fine(self):
        t = "# Plan\n\n## Part 1: Channels\n\n" + para() + "## Part 2: Funnel\n\n" + para()
        self.assertNotIn("colon_headings", run(t))

    def test_title_case_and_rules(self):
        t = "# Plan\n\n## Channel Overview Today\n\n---\n\n## Funnel Design Choices\n\n---\n\n## Drip Email Plan\n\n---\n\n" + para()
        r = run(t)
        self.assertEqual(r.get("title_case_headings"), "WARN")
        self.assertEqual(r.get("horizontal_rules"), "WARN")

    def test_process_slide(self):
        self.check("## Limits, and how I made this\n\nSome text.\n", "process_slide", "FAIL", "deck")

    def test_date_stamps(self):
        t = "# T\n\nA (Confirmed, 2 Nov 2026). B (read 3 Nov 2026). C (checked 4 Nov 2026).\n"
        self.check(t, "date_stamps", "FAIL")

    def test_urls_and_refs(self):
        t = "# T\n\nSee https://a.com and [2].\n\n## Sources\n\n1. A: https://a.com\n3. C, no link\n"
        r = run(t)
        self.assertEqual(r.get("urls_in_body"), "FAIL")
        self.assertEqual(r.get("ref_without_source"), "FAIL")
        self.assertEqual(r.get("source_without_raw_url"), "FAIL")

    def test_table_and_prose_share(self):
        rows = "| " + " | ".join(["word word word word"] * 4) + " |\n"
        t = "# T\n\n| a | b | c | d |\n|---|---|---|---|\n" + rows * 12 + "\n" + para(1)
        r = run(t)
        self.assertEqual(r.get("table_share"), "FAIL")
        self.assertEqual(r.get("prose_share"), "FAIL")

    def test_markdown_in_email(self):
        self.check("Hi Sam,\n\n**Quick ask:** can we talk Thursday?\n\nAlex\n", "markdown_in_plain_text", "FAIL", "email")

    def test_recap_and_takeaways(self):
        r = run("# T\n\n" + para(2) + "## Key takeaways\n\nIn summary, fix the trial.\n")
        self.assertEqual(r.get("recap_ending"), "FAIL")
        self.assertEqual(r.get("takeaways_block"), "FAIL")

    def test_missing_next_step_and_assumptions(self):
        r = run("# T\n\n" + para(4), "memo")
        self.assertEqual(r.get("no_next_step"), "WARN")
        self.assertEqual(r.get("no_assumptions"), "WARN")

    def test_self_narration_and_contrast(self):
        r = run("# T\n\nThe table below shows the costs. It's not about price, it's about trust.\n")
        self.assertEqual(r.get("self_narration"), "WARN")
        self.assertEqual(r.get("not_x_but_y"), "WARN")

    def test_placeholders(self):
        self.check("# T\n\nPrice: TBD. Owner: [Name].\n", "placeholders", "WARN")

    def test_length(self):
        self.check("Hi Sam,\n\n" + "word " * 400 + "\n", "length", "WARN", "email")


class Cli(unittest.TestCase):
    def test_exit_codes_and_fixer(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.md"
            bad.write_text("# T\n\nA plan \u2014 here “quoted”.\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "lint_doc.py"), str(bad)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            out = Path(d) / "fixed.md"
            r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "lint_doc.py"), str(bad), "--fix-typography", str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertNotRegex(out.read_text(encoding="utf-8"), "[\u2014\u2013“”]")
            self.assertIn("\u2014", bad.read_text(encoding="utf-8"))  # never edits in place
            r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "lint_doc.py"), str(Path(d) / "missing.md")], capture_output=True)
            self.assertEqual(r.returncode, 2)

    def test_blind_pack_refuses_key_inside(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "b").mkdir()
            for n in ("x", "y"):
                (p / "b" / f"{n}.md").write_text("# Gemini answer\n\nText.\n", encoding="utf-8")
            (p / "draft.md").write_text("# Mine\n\nText.\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "blind_pack.py"), "--draft", str(p / "draft.md"),
                                "--baselines", str(p / "b"), "--out", str(p / "out"), "--key", str(p / "out" / "KEY.txt")],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "blind_pack.py"), "--draft", str(p / "draft.md"),
                                "--baselines", str(p / "b"), "--out", str(p / "out"), "--key", str(p / "KEY.txt")],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            heads = [f.read_text().splitlines()[0] for f in sorted((p / "out").glob("Doc_*.md"))]
            self.assertTrue(all(h.startswith("# Doc ") for h in heads), heads)


if __name__ == "__main__":
    unittest.main(verbosity=1)
