#!/usr/bin/env python3
"""
LLM-sameness check (pre-ai-writing skill, high-stakes tier).

Question it answers: if a reader pasted the brief into Claude, ChatGPT or
Gemini, would this draft look like one more of those answers?
Generalised from a checker built for one growth take-home.

How: compare the draft against a folder of baseline LLM answers to the same
assignment. Baseline-vs-baseline similarity sets the "LLMs agree with each other
this much" reference. The draft should sit clearly below that reference, carry
more subject-specific evidence, and show fewer AI writing tells. The tell rate
comes from lint_doc.py so there is one source for the rules.

Pure standard library. Usage:
  python3 sameness_check.py --draft draft.md --baselines baselines \
      [--ideas ideas.json] [--terms terms.txt] [--out report.md]
Exit 0 = PASS, 1 = NOT YET, 2 = usage error.
"""
import argparse, json, math, re, statistics, sys
from collections import Counter
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_doc  # noqa: E402

STOP = set("""a an the and or but if then so of to in on at by for with from as is are was
were be been being it its this that these those there their they them we our you your i
me my he she his her not no do does did done have has had having can could will would
shall should may might must into over under about than more most such each per via
which who whom what when where why how all any both few other some own same too very
just also only up out off again further once here s t don now new also etc vs e g eg ie""".split())

# Humanizer section 12 word list plus common 2024-26 LLM favourites.
STOCK_WORDS = """additionally align aligns aligned bolster bolstered crucial delve delves
enduring enhance enhances enhanced garner garners interplay intricate landscape meticulous
pivotal robust showcase showcases tapestry testament underscore underscores vibrant
leverage leveraging seamless seamlessly streamline streamlined unlock unlocks elevate
holistic synergy synergies empower empowers navigate navigating realm foster fostering
comprehensive cutting-edge game-changer game-changing paramount nuanced""".split()

TELL_PATTERNS = {
    "em_or_en_dash": "[\u2014\u2013]",
    "not_x_but_y": r"\bnot (?:just |only |merely )?[\w\s,'-]{1,40}?\bbut\b|\bisn't about\b|\bit's not\b[^.]{0,40}\bit's\b|\brather than\b",
    "staged_opener": r"\b(here's the thing|let's dive|here's what|real talk|honestly\?|the bottom line|in today's)\b",
    "deep_saying": r"\b(the real question|at its core|what really matters|the heart of)\b",
    "bold_lead_in": r"^\s*[-*\d.]+\s*\*\*[^*]{1,40}:\*\*",
    "heading_with_colon": r"^#+ [^\n]*:\s*\S",
    "triad_x_y_and_z": r"\b\w+, \w+(?: \w+)?, and \w+\b",
    "chatbot_residue": r"\b(i hope this helps|great question|certainly!|absolutely!|happy to help|feel free to)\b",
}

WORD = re.compile(r"[a-z0-9][a-z0-9'%$.-]*[a-z0-9%]|[a-z0-9]")


def strip_md(t: str) -> str:
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*_|]", " ", t)
    return t


def tokens(t: str):
    return WORD.findall(strip_md(t).lower())


def content_tokens(t: str):
    return [w for w in tokens(t) if w not in STOP and len(w) > 1]


def shingles(toks, n):
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def tfidf_vectors(docs):
    feats = []
    for d in docs:
        feats.append(Counter(content_tokens(d)))
    df = Counter()
    for f in feats:
        df.update(f.keys())
    n = len(docs)
    vecs = []
    for f in feats:
        v = {k: (1 + math.log(c)) * math.log((1 + n) / (1 + df[k])) + 1e-9 for k, c in f.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({k: x / norm for k, x in v.items()})
    return vecs


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(k, 0.0) for k, x in a.items())


def sentences(t):
    t = strip_md(t)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", t) if len(s.split()) >= 3]


def tells(raw: str):
    low = raw.lower()
    words = max(len(tokens(raw)), 1)
    out = {}
    for k, p in TELL_PATTERNS.items():
        flags = re.M | re.I
        out[k] = len(re.findall(p, raw if k in ("bold_lead_in", "heading_with_colon") else low, flags))
    stock = Counter(w for w in tokens(raw) if w in STOCK_WORDS)
    out["stock_words"] = sum(stock.values())
    out["stock_words_list"] = ", ".join(f"{w}x{c}" for w, c in stock.most_common(8))
    # Present-participle clauses after a comma (", making it..."): GPT-4o uses them at 5.3x the human rate
    # (Reinhart et al., PNAS 2025). Reported separately, not added to the tell total.
    out["participle_clauses_per_1k"] = round(len(re.findall(r",\s+\w+ing\b", strip_md(raw))) * 1000 / words, 1)
    lens = [len(s.split()) for s in sentences(raw)]
    out["sentence_len_mean"] = round(statistics.mean(lens), 1) if lens else 0
    out["burstiness_cv"] = round(statistics.pstdev(lens) / statistics.mean(lens), 2) if len(lens) > 1 else 0
    out["tells_per_1k_words"] = lint_doc.tells_per_1k(raw)[0]
    return out


def specificity(raw: str, terms):
    words = max(len(tokens(raw)), 1)
    plain = strip_md(raw)
    nums = re.findall(r"(?<![\w])[$]?\d[\d,.]*\s?(?:%|k|m|x|days?|hours?|weeks?)?", plain)
    urls = re.findall(r"https?://\S+", raw)
    low = raw.lower()
    def hits(t):
        t = t.lower()
        pat = (r"\b" if t[0].isalnum() else "") + re.escape(t) + (r"\b" if t[-1].isalnum() else "")
        return len(re.findall(pat, low))
    term_hits = {t: hits(t) for t in terms if hits(t)}
    # Without a terms file, specificity = numbers plus mid-sentence proper names per 1,000 words.
    proper = re.findall(r"(?<=[a-z0-9,;:)] )[A-Z][A-Za-z0-9&'.-]+", plain)
    spec = sum(term_hits.values()) if terms else len(nums) + len(proper)
    return {
        "numbers_per_1k": round(len(nums) * 1000 / words, 1),
        "urls": len(urls),
        "subject_specific": spec,
        "subject_specific_per_1k": round(spec * 1000 / words, 1),
        "terms_found": ", ".join(sorted(term_hits)[:20]) if terms else f"{len(proper)} proper names, {len(nums)} numbers",
    }


def idea_hits(raw: str, ideas):
    low = strip_md(raw).lower()
    return {i["id"] for i in ideas if any(re.search(p, low) for p in i["patterns"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", required=True)
    ap.add_argument("--baselines", required=True)
    ap.add_argument("--ideas", default=None, help="consensus_ideas.json")
    ap.add_argument("--terms", default=None, help="terms only first-hand work would contain, one per line")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    draft_raw = Path(a.draft).read_text(encoding="utf-8")
    base_files = sorted(p for p in Path(a.baselines).glob("*.md"))
    if len(base_files) < 2:
        print("sameness_check: need at least two baseline .md files", file=sys.stderr)
        return 2
    base_raw = [p.read_text(encoding="utf-8") for p in base_files]
    names = [p.stem for p in base_files]
    ideas = json.loads(Path(a.ideas).read_text()) if a.ideas else []
    terms = [l.strip() for l in Path(a.terms).read_text().splitlines() if l.strip() and not l.startswith("#")] if a.terms else []

    L = []
    w = L.append
    w("# LLM-sameness check\n")
    w(f"Draft: `{a.draft}` ({len(tokens(draft_raw))} words). Baselines: {len(base_files)} ({', '.join(names)}).\n")

    # 1. Wording overlap: 5-word shingles
    dsh = shingles(tokens(draft_raw), 5)
    bsh = [shingles(tokens(r), 5) for r in base_raw]
    bb_j = [jaccard(x, y) for x, y in combinations(bsh, 2)]
    db_j = [jaccard(dsh, b) for b in bsh]
    union_b = set().union(*bsh)
    contain = len(dsh & union_b) / len(dsh) if dsh else 0
    # 2. Topic and phrasing overlap: TF-IDF cosine on content words and bigrams
    vecs = tfidf_vectors(base_raw + [draft_raw])
    bv, dv = vecs[:-1], vecs[-1]
    bb_c = [cosine(x, y) for x, y in combinations(bv, 2)]
    db_c = [cosine(dv, b) for b in bv]

    # Leave-one-out: each LLM answer's mean similarity to the other LLM answers.
    nb = len(base_raw)
    def loo(sim_pairs):
        m = {}
        for (i, j), s in zip(combinations(range(nb), 2), sim_pairs):
            m.setdefault(i, []).append(s)
            m.setdefault(j, []).append(s)
        return [statistics.mean(m[i]) for i in range(nb)]
    loo_c, loo_j = loo(bb_c), loo(bb_j)
    loo_contain = []
    for i in range(nb):
        others = set().union(*[bsh[k] for k in range(nb) if k != i])
        loo_contain.append(len(bsh[i] & others) / len(bsh[i]) if bsh[i] else 0)

    w("## 1. How close is the draft to what LLMs write?\n")
    w("Each LLM answer is compared with the other LLM answers (leave-one-out); the draft is compared with all of them. "
      "The draft passes a row when it is less similar than the least typical LLM answer.\n")
    w("| Measure | LLM answers vs the rest (min / median / max) | Draft vs all LLM answers | Pass rule | Result |")
    w("|---|---|---|---|---|")
    def mm(x):
        return f"{min(x):.3f} / {statistics.median(x):.3f} / {max(x):.3f}"
    c_pass = statistics.mean(db_c) < min(loo_c)
    j_pass = statistics.mean(db_j) < min(loo_j)
    k_pass = contain < min(loo_contain)
    w(f"| Topic overlap (TF-IDF cosine, content words) | {mm(loo_c)} | {statistics.mean(db_c):.3f} | below LLM min | {'PASS' if c_pass else 'FAIL'} |")
    w(f"| Wording overlap (5-word phrase Jaccard) | {mm(loo_j)} | {statistics.mean(db_j):.4f} | below LLM min | {'PASS' if j_pass else 'FAIL'} |")
    w(f"| Reused wording (share of 5-word phrases found in another answer) | {mm(loo_contain)} | {contain:.3f} | below LLM min | {'PASS' if k_pass else 'FAIL'} |\n")
    w("Per baseline cosine to draft: " + "; ".join(f"{n} {c:.3f}" for n, c in zip(names, db_c)) + "\n")
    w("Caution: LLM answers converge on ideas more than on exact sentences, so wording rows are weak evidence on their own. "
      "Sections 3 and 5 and the blind review carry more weight.\n")

    # 1b. Section by section: which parts of the draft sit inside the LLM band?
    parts = [p for p in re.split(r"\n(?=#{1,3} )", draft_raw) if len(tokens(p)) >= 60]
    if len(parts) > 1:
        svecs = tfidf_vectors(base_raw + parts)
        sb, sd = svecs[:nb], svecs[nb:]
        w("### Section by section\n")
        w(f"A section reads as consensus when its mean topic overlap with the LLM answers is at or above "
          f"{min(loo_c):.3f} (the least typical LLM answer).\n")
        w("| Section | Words | Topic overlap (mean) | Reused 5-word phrases | Reads as |\n|---|---|---|---|---|")
        for p, v in zip(parts, sd):
            title = p.strip().splitlines()[0].lstrip("# ").strip()[:60]
            ps = shingles(tokens(p), 5)
            pc = len(ps & union_b) / len(ps) if ps else 0
            m = statistics.mean(cosine(v, b) for b in sb)
            w(f"| {title} | {len(tokens(p))} | {m:.3f} | {pc:.1%} | {'consensus' if m >= min(loo_c) else 'own'} |")
        w("")

    # 3. Consensus phrases reused in the draft
    d4 = tokens(draft_raw)
    d4s = {" ".join(d4[i:i + 4]) for i in range(len(d4) - 3)}
    cnt = Counter()
    for r in base_raw:
        t = tokens(r)
        cnt.update({" ".join(t[i:i + 4]) for i in range(len(t) - 3)})
    shared = sorted(
        [(p, cnt[p]) for p in d4s if cnt[p] >= max(2, len(base_raw) // 2) and sum(x not in STOP for x in p.split()) >= 2],
        key=lambda x: -x[1])
    w("## 2. Phrases the draft shares with half or more of the baselines\n")
    w("Rewrite these unless they are the assignment's own words or plain terms of art.\n")
    if shared:
        w("| Phrase | Baselines using it |\n|---|---|")
        for p, c in shared[:40]:
            w(f"| {p} | {c}/{len(base_raw)} |")
    else:
        w("None.")
    w("")

    # 4. Consensus ideas
    if ideas:
        w("## 3. Consensus ideas (what most LLM answers say)\n")
        base_hits = [idea_hits(r, ideas) for r in base_raw]
        dh = idea_hits(draft_raw, ideas)
        w("| Idea | Baselines saying it | In draft | What to do |\n|---|---|---|---|")
        for i in ideas:
            k = sum(i["id"] in h for h in base_hits)
            todo = i.get("action", "")
            w(f"| {i['label']} | {k}/{len(base_raw)} | {'yes' if i['id'] in dh else 'no'} | {todo if i['id'] in dh else ''} |")
        share_base = statistics.mean(len(h) / len(ideas) for h in base_hits)
        w(f"\nBaselines cover {share_base:.0%} of the consensus list on average; the draft covers {len(dh)/len(ideas):.0%}. "
          "Covering a consensus idea is fine when it is correct; the draft must add what the baselines cannot (section 5).\n")

    # 5. AI writing tells
    w("## 4. AI writing tells (per Humanizer / 'Signs of AI writing')\n")
    keys = list(TELL_PATTERNS) + ["stock_words", "participle_clauses_per_1k", "sentence_len_mean", "burstiness_cv",
                                  "tells_per_1k_words"]
    bt = [tells(r) for r in base_raw]
    dt = tells(draft_raw)
    w("| Tell | Baseline median | Draft | Target |\n|---|---|---|---|")
    targets = {"burstiness_cv": "higher is more human (vary sentence length)", "sentence_len_mean": "12-20",
               "tells_per_1k_words": "under 3", "participle_clauses_per_1k": "below baseline median"}
    for k in keys:
        med = statistics.median(b[k] for b in bt)
        w(f"| {k} | {med} | {dt[k]} | {targets.get(k, '0')} |")
    if dt["stock_words_list"]:
        w(f"\nStock words in draft: {dt['stock_words_list']}\n")

    # 6. Specificity
    w("## 5. Evidence only first-hand work can have\n")
    bs = [specificity(r, terms) for r in base_raw]
    ds = specificity(draft_raw, terms)
    w("| Measure | Baseline median | Draft | Target |\n|---|---|---|---|")
    for k, tgt in [("numbers_per_1k", "above baseline, every number sourced"), ("urls", "every factual claim linked"),
                   ("subject_specific_per_1k", "well above baseline")]:
        w(f"| {k} | {statistics.median(b[k] for b in bs)} | {ds[k]} | {tgt} |")
    w(f"\nSubject-specific evidence in draft: {ds['terms_found'] or 'none'}\n")

    spec_pass = ds["subject_specific_per_1k"] > 2 * max(1, statistics.median(b["subject_specific_per_1k"] for b in bs))
    tell_pass = dt["tells_per_1k_words"] < 3
    verdict = c_pass and k_pass and tell_pass and spec_pass
    w(f"## Verdict: {'PASS' if verdict else 'NOT YET'}\n")
    w(f"- Topic overlap below every LLM answer: {'yes' if c_pass else 'no'}")
    w(f"- Reused wording below every LLM answer: {'yes' if k_pass else 'no'}")
    w(f"- Under 3 AI tells per 1,000 words: {'yes' if tell_pass else 'no'}")
    w(f"- Subject-specific evidence at least double the LLM median: {'yes' if spec_pass else 'no'}\n")
    w("The consensus-idea table (section 3) and the blind odd-one-out review (blind_pack.py) are judged "
      "by reading, not by this score.")

    report = "\n".join(L)
    if a.out:
        Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
