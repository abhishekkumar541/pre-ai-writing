#!/usr/bin/env python3
"""blind_pack.py: build a blind odd-one-out review pack (pre-ai-writing skill, high-stakes tier).

Copies the draft and the baseline answers into OUT as Doc_A.md, Doc_B.md, ... in random order,
after stripping anything that could tell the reviewer which is which:
  - HTML comments (capture notes), vendor or model self-references, coaching tails ("Want me to...")
  - the author's name (--redact) and AI-use disclosure lines
  - every first heading becomes "# Doc X"; with --drop-sources the Sources list and [n] markers go too
Then it searches OUT for leftovers and exits 1 if any remain. The key is written OUTSIDE OUT.
It prints counts only, never the key.

Usage:
  python3 blind_pack.py --draft draft.md --baselines baselines --out blind --key ../blind_KEY.txt \
      [--redact "Your Name"]... [--drop-sources] [--brief brief.md] [--seed N]
Exit 0 = pack clean, 1 = leak found (pack kept for inspection), 2 = usage error.
"""
import argparse
import subprocess
import random
import re
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_doc  # noqa: E402

VENDOR = r"(?:chat\s?gpt|openai|gpt-?\d[\w.-]*|gemini|bard|google ai studio|claude|anthropic|sonnet|opus|haiku|fable|llama|mistral|copilot|perplexity|deepseek|grok)"
SELF_REF = re.compile(r"\b(?:as an ai\b|i'?m (?:an ai|chatgpt|claude|gemini)|(?:chatgpt|claude|gemini) (?:here|answer|response|output)\b|"
                      r"generated (?:by|with|using) " + VENDOR + r")", re.I)
COACHING = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?\s*(?:why this (?:works|stands out|answer works)|want me to|would you like me to|"
                      r"if you(?:'d| would) like|let me know if|i can also|next,? i can|should i |shall i |"
                      r"tips? for (?:the|your) interview|how to present this)", re.I)
AI_USE = re.compile(r"\b(?:AI tools?|ChatGPT|Claude|Gemini|an LLM|LLMs|large language models?|generative AI)\b[^.\n]{0,40}"
                    r"\b(?:helped|assisted|was used|were used|drafted|wrote)\b|\bwith (?:the )?help of AI\b|\bAI-assisted\b", re.I)


def strip_sources(text):
    lines = text.split("\n")
    out, skip_lvl = [], None
    for l in lines:
        m = lint_doc.HEADING_RE.match(l)
        if m:
            lvl, title = len(m.group(1)), re.sub(r"[*_]", "", m.group(2)).strip()
            if skip_lvl is not None and lvl <= skip_lvl:
                skip_lvl = None
            if lint_doc.SOURCES_HEAD_RE.match(title):
                skip_lvl = lvl
                continue
        if skip_lvl is None:
            out.append(l)
    text = "\n".join(out)
    return re.sub(r"\s?\[\d{1,3}(?:\s*[,-]\s*\d{1,3})*\](?!\()", "", text)


def clean(text, letter, redact, drop_sources):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines = text.split("\n")
    # cut coaching tails: everything from the first coaching line in the last third of the doc
    cut = None
    for i, l in enumerate(lines):
        if i > len(lines) * 0.6 and COACHING.search(l):
            cut = i
            break
    if cut is not None:
        lines = lines[:cut]
    out, seen_h1 = [], False
    for i, l in enumerate(lines):
        if SELF_REF.search(l) or AI_USE.search(l):
            continue
        h = lint_doc.HEADING_RE.match(l)
        if h and not seen_h1:
            out.append(f"# Doc {letter}")
            seen_h1 = True
            continue
        if not seen_h1 and re.search(VENDOR, l, re.I):
            continue
        if any(r.lower() in l.lower() for r in redact):
            if len(l.split()) < 15:
                continue
            for r in redact:
                l = re.sub(re.escape(r), "", l, flags=re.I)
        out.append(l)
    if not seen_h1:
        out.insert(0, f"# Doc {letter}\n")
    text = "\n".join(out)
    if drop_sources:
        text = strip_sources(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def leaks(out_dir, redact, names):
    found = []
    for f in sorted(out_dir.glob("Doc_*.md")):
        lines = f.read_text(encoding="utf-8").split("\n")
        heads = [l for l in lines if lint_doc.HEADING_RE.match(l)]
        for l in heads + lines[:4]:
            if re.search(VENDOR, l, re.I):
                found.append(f"{f.name}: vendor name in heading or opening: {l[:80]}")
        for n, l in enumerate(lines, 1):
            if SELF_REF.search(l):
                found.append(f"{f.name}:{n}: self-reference")
            if AI_USE.search(l):
                found.append(f"{f.name}:{n}: AI-use line")
            if COACHING.search(l) and n > len(lines) * 0.6:
                found.append(f"{f.name}:{n}: coaching tail")
            for r in redact:
                if r.lower() in l.lower():
                    found.append(f"{f.name}:{n}: redacted text remains")
            for nm in names:
                if len(nm) >= 4 and re.search(r"(?<![\w-])" + re.escape(nm) + r"(?![\w-])", l, re.I):
                    found.append(f"{f.name}:{n}: source file name '{nm}'")
    if any(p.name.lower().startswith("key") for p in out_dir.iterdir()):
        found.append("a KEY file sits inside the review folder")
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a blind odd-one-out review pack.")
    ap.add_argument("--draft", required=True)
    ap.add_argument("--baselines", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", required=True, help="where to write the key; must be outside --out")
    ap.add_argument("--redact", action="append", default=[], help="text to remove, e.g. the author's name (repeatable)")
    ap.add_argument("--drop-sources", action="store_true")
    ap.add_argument("--brief", default=None, help="brief text to put in BRIEF.md")
    ap.add_argument("--seed", type=int, default=None)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    out_dir, key = Path(a.out).resolve(), Path(a.key).resolve()
    if out_dir == key.parent or out_dir in key.parents:
        print("blind_pack: --key must sit outside --out, or the reviewer can read it", file=sys.stderr)
        return 2
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"blind_pack: {out_dir} is not empty; pick a new folder (nothing overwritten)", file=sys.stderr)
        return 2
    draft = Path(a.draft)
    bases = sorted(Path(a.baselines).glob("*.md"))
    if not draft.is_file() or len(bases) < 2:
        print("blind_pack: need a draft file and at least two baseline .md files", file=sys.stderr)
        return 2
    files = bases + [draft]
    if len(files) > 26:
        print("blind_pack: at most 26 documents", file=sys.stderr)
        return 2
    brief = "(paste the brief here)"
    if a.brief:
        bp = Path(a.brief)
        try:
            if bp.suffix.lower() == ".pdf":

                brief = subprocess.run(["pdftotext", "-layout", str(bp), "-"], capture_output=True, text=True, check=True).stdout
            else:
                brief = bp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, subprocess.CalledProcessError) as e:
            print(f"blind_pack: cannot read the brief {bp}: {e}", file=sys.stderr)
            return 2
    rng = random.Random(a.seed)
    rng.shuffle(files)
    out_dir.mkdir(parents=True, exist_ok=True)
    key_lines = []
    for letter, f in zip(string.ascii_uppercase, files):
        text = clean(f.read_text(encoding="utf-8"), letter, a.redact, a.drop_sources)
        (out_dir / f"Doc_{letter}.md").write_text(text, encoding="utf-8")
        key_lines.append(f"Doc_{letter} = {f.name}")
    key.parent.mkdir(parents=True, exist_ok=True)
    key.write_text("\n".join(key_lines) + "\n", encoding="utf-8")
    prompt = (Path(__file__).resolve().parent.parent / "templates" / "blind_review_prompt.md").read_text(encoding="utf-8")
    body = prompt.split("---", 2)[1].strip() if prompt.count("---") >= 2 else prompt
    (out_dir / "BRIEF.md").write_text("# Brief\n\n" + brief.strip() + "\n\n# Your task\n\n" + body + "\n", encoding="utf-8")
    found = leaks(out_dir, a.redact, [p.stem for p in files])
    print(f"blind_pack: wrote {len(files)} documents and BRIEF.md to {out_dir}; key at {key}")
    if found:
        print(f"blind_pack: {len(found)} possible leaks, fix before sending:")
        for x in found[:30]:
            print("  " + x)
        return 1
    print("blind_pack: leak check clean. Fill {reader_role} and {brief_summary} in BRIEF.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
