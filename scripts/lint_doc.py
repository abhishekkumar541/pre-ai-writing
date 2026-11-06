#!/usr/bin/env python3
"""lint_doc.py: structure and wording checks for documents someone else will read.

Part of the pre-ai-writing skill. Standard library only.

Usage:
  python3 lint_doc.py FILE_OR_DIR [--type TYPE] [--strict] [--json]
                      [--notes-marker REGEX] [--fix-typography OUT]

TYPE is one of: takehome memo email cover post resume deck landing doc (default doc).
A directory is read as a deck: every *.html in it, with <aside> treated as speaker notes.

Exit codes: 0 no FAIL (with --strict: no WARN either), 1 at least one FAIL, 2 usage or read error.

FAIL rules are patterns a rejected, AI-sounding take-home answer had and the pre-2022 human
take-homes did not. Everything with weaker evidence is a WARN. Some numbers are only
reported (INFO). A clean lint does not make a document read as human-written: the
read-through and, for high-stakes work, the blind review still decide.
"""
import argparse
import html as htmlmod
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

TYPES = ["takehome", "memo", "email", "cover", "post", "resume", "deck", "landing", "doc"]

# Body-word ranges per type. WARN outside. Sources are in references/structures.md.
LENGTHS = {
    "takehome": (1300, 2700),   # two real pre-2022 take-home answers ran about 1,300 and 2,700 words (a guide, not a rule)
    "memo": (250, 2500),
    "email": (20, 150),         # Hunter: 20-39 words had the highest reply rate on cold email
    "cover": (200, 450),        # 3 to 4 paragraphs, under one page
    "post": (40, 300),          # LinkedIn: about 1,200 to 1,600 characters
}

PROSE_TYPES = {"takehome", "memo", "doc", "cover"}       # prose/bullet/table share rules apply
SOURCED_TYPES = {"takehome", "memo", "doc", "cover"}     # numbered Sources list expected when citing
PLAIN_TYPES = {"email", "post"}                          # no markdown at all
NO_LABEL_TYPES = {"resume"}                              # bold labels are normal on a resume
NO_HEADING_STYLE_TYPES = {"resume", "deck", "landing", "email", "post"}

# ---------------------------------------------------------------- patterns
DASH_RE = re.compile("[\u2014\u2013]")
CURLY_RE = re.compile("[‘’“”]")
ELLIPSIS_RE = re.compile("…")
ARROW_RE = re.compile("→|(?<![-<])->(?!>)")
URL_RE = re.compile(r"https?://[^\s)>\]|]+|www\.[^\s)>\]|]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
HR_RE = re.compile(r"^\s*(?:-\s*){3,}$|^\s*(?:\*\s*){3,}$|^\s*(?:_\s*){3,}$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
LABEL_RE = re.compile(r"^\s*((?:[-*+]|\d+[.)])\s+)?\*\*([^*\n]{1,90}?)\*\*(.*)$")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’.,%&/-][A-Za-z0-9]+)*%?")
MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"

SOURCES_HEAD_RE = re.compile(
    r"^(?:\d+[.)]\s*)?(?:sources|references|bibliography|works cited|citations|endnotes|footnotes|"
    r"notes and sources|sources and notes|further reading)\s*$", re.I)
NOTES_HEAD_RE = re.compile(r"(?:speaker notes|presenter notes|notes for (?:me|myself|the presenter)|internal notes)", re.I)

# Stock words. STRONG: AI-era words (Humanizer 12 plus common LLM favourites) that the pre-2022 human
# take-homes never used. JARGON: business words people used long before AI ("leverage", "showcase"
# appear 15 times in the two human samples), so they are a plain-English WARN, not proof of AI.
# WEAK: common in human prose too, so only density matters.
STRONG_WORDS = """delve delves delved delving tapestry testament underscore underscores underscored
underscoring robust seamless seamlessly pivotal meticulous meticulously intricate intricacies interplay
garner garners garnered bolster bolsters bolstered vibrant paramount myriad realm foster fosters
fostered fostering enduring""".split()
STRONG_PHRASES = ["deep dive", "deep-dive", "ever-evolving", "ever-changing landscape", "rich tapestry"]
JARGON_WORDS = """leverage leverages leveraged leveraging utilize utilizes utilized utilizing utilise utilises
utilised utilising spearhead spearheads spearheaded spearheading harness harnessed harnessing streamline
streamlines streamlined streamlining showcase showcases showcased showcasing synergy synergies holistic
empower empowers empowered empowering elevate elevates elevated elevating orchestrate orchestrated
game-changer game-changing cutting-edge best-in-class world-class""".split()
JARGON_PHRASES = ["move the needle", "low-hanging fruit", "north star"]
# Rule 15: investor or boardroom decision verbs. WARN only, because the brief may use them.
INVESTOR_WORDS = ["fund", "funds", "funded", "deploy capital", "double down", "doubling down", "bet on",
                  "betting on", "allocate firepower", "firepower"]
WEAK_WORDS = """additionally crucial enhance enhances enhanced enhancing comprehensive landscape navigate
navigates navigating align aligns aligned valuable nuanced innovative unlock unlocks unlocked
furthermore moreover""".split()

STAGED = [r"\bhere'?s the thing\b", r"\blet'?s dive\b", r"\blet'?s (?:break|unpack) (?:it|this|that) down\b",
          r"\breal talk\b", r"\bin today'?s (?:world|fast-paced|digital|competitive|ever-changing|rapidly)",
          r"\bthe bottom line is\b", r"\bhere'?s (?:why|how) (?:it|this|that) (?:matters|works)\b",
          r"\bthe real question is\b", r"\bat its core\b", r"\bwhat really matters\b", r"\bat the heart of\b"]
RESIDUE = [r"\bi hope this helps\b", r"\bgreat question\b", r"\bcertainly!", r"\babsolutely!",
           r"\bwould you like me to\b", r"\bwant me to\b", r"\bshould i continue\b",
           r"\byou'?re absolutely right\b", r"\bas an ai\b", r"\bmy (?:last )?(?:training|knowledge) (?:data|cutoff|update)\b"]
CLICHE_CLOSERS = [r"\bfeel free to\b", r"\bhappy to help\b", r"\bdon'?t hesitate to\b"]
READING_GUIDE = [r"\bhow to read (?:this|it|the)\b", r"\beach (?:section|heading|slide|chapter|part) (?:opens|starts|begins|leads) with\b",
                 r"\bthe headings alone\b", r"\bread (?:only )?the headings\b", r"\bstatus words (?:show|tell|mark)\b",
                 r"\bwhere each part of the brief is (?:answered|covered)\b"]
SELF_NARRATION = [r"\bthe point (?:here )?is\b", r"\bthe key (?:insight|point|takeaway|thing) (?:here )?is\b",
                  r"\bit'?s worth noting\b", r"\bit is (?:important|worth) (?:to note|noting)\b", r"(?:^|\. )importantly,",
                  r"(?:^|\. )notably,", r"\bthe table below (?:shows|compares|lists|sets out)\b",
                  r"\bthis (?:section|document|doc|memo|deck) (?:is organi[sz]ed|covers|walks|outlines|explains)\b",
                  r"\bbelow,? (?:i|we)(?:'ll| will) (?:walk|cover|outline)\b",
                  r"\b(?:was|were) (?:compiled|generated|drafted) (?:from|using|with)\b", r"\bflagged rather than guessed\b"]
NOT_X_BUT_Y = [r"\bnot (?:just |only |merely |simply )?(?:about )?[^.;:!?\n]{1,50}?[,;]? but (?:also |rather )?\w",
               r"\bisn'?t (?:just |only )?(?:about )?[^.;\n]{1,40}[.;,] it'?s\b",
               r"\bit'?s not (?:just |only )?(?:about )?[^.;\n]{1,40}[.;,] it'?s\b",
               r"\bless about [^.;\n]{1,40} (?:and )?more about\b"]
COUNTER_RE = re.compile(
    r"(?:argument against|counter-?argument|counterpoint|devil'?s advocate|steel-?man|the case against|"
    r"what could go wrong|^risks?\b|limitations?|^caveats?|pushback|objections?|what would change my mind)", re.I)
META_LABEL_RE = re.compile(
    r"^(?:(?:my |the )?answer(?: in one line| in short)?|(?:my |the )?(?:short|one-line) (?:answer|version)|"
    r"tl;?dr|bottom line|key takeaways?|the takeaway|in short|why|why this(?: \w+)?|why (?:i'?d|i would|we should) invest|"
    r"why invest|reasoning|rationale|the reasoning|my reasoning|what i'?d do|how i'?d judge(?: it)?|"
    r"how to read(?: it| this)?|the brief|what counts|who owns what|the question i'?d ask.*|"
    r"why it reads this way|what i couldn'?t see|verdict|the ask)$", re.I)
PLAIN_LABEL_RE = re.compile(r"^\s*((?:[-*+]|\d+[.)])\s+)?([A-Z][A-Za-z'&/ ]{1,30}?):(?:\s+\S|\s*$)")
STATUS_RE = re.compile(r"\b(?:Confirmed|Unconfirmed|Supported|Disputed)\b|\bNot found in cited source\b")
STAMP_RE = re.compile(
    r"\([^()\n]{0,90}?(?:\b(?:Confirmed|Unconfirmed|Supported|Disputed|read|accessed|checked|seen|captured|"
    r"retrieved|visited|viewed)\b[^()\n]{0,40}?\b\d{1,2}\s+" + MONTH + r"|\b\d{1,2}\s+" + MONTH +
    r"(?:\s+\d{4})?[^()\n]{0,40}?\b(?:Confirmed|Unconfirmed|Supported|Disputed)\b)[^()\n]{0,90}\)"
    r"|\bas of \d{1,2}\s+" + MONTH, re.I)
PLACEHOLDER_RE = re.compile(
    r"\[(?:postal address|address|name|first name|company|link|url|date|placeholder|tbd|tbc|todo|to confirm|x+|insert[^\]]*)\]"
    r"|\bTODO\b|\bTBD\b|\bTBC\b|\((?:to confirm|tbc|tbd)\)|^\s*to confirm\b|\blorem ipsum\b|\bXX+\b|\?\?\?|\{\{[^}]+\}\}", re.I)
RECAP_RE = re.compile(r"^(?:in (?:summary|conclusion|short|sum)|to (?:sum up|summari[sz]e|conclude|wrap up)|"
                      r"overall,|ultimately,|all in all)\b", re.I)
TAKEAWAY_HEAD_RE = re.compile(r"^(?:tl;?dr|key takeaways?|takeaways|the takeaway)\b", re.I)
END_HEAD_RE = re.compile(r"^(?:summary|conclusion|in conclusion|final thoughts|wrapping up)$", re.I)
NEXT_RE = re.compile(r"\b(?:next steps?|first (?:week|two weeks|30 days|month|90 days)|week one|day one|"
                     r"i'?d (?:start|begin|want|ask|like to|need)|i would (?:start|begin|want|like|need)|happy to|"
                     r"let me know|would you|could we|can we|are you free|shall we|please (?:send|let|reply)|"
                     r"before (?:changing|spending|any)|what i'?d do first|follow up)\b|\?", re.I)
ASSUME_RE = re.compile(r"\bassum(?:e|es|ed|ing|ption|ptions)\b", re.I)
PROCESS_SLIDE_RE = re.compile(r"\b(?:how (?:i|we) (?:made|built|did|wrote|used ai)|method(?:ology)?\b|my process|"
                              r"about this (?:deck|document)|limits,? and how|ai use)\b", re.I)
SMALL_WORDS = set("a an the and or but nor of to in on for with by at from as vs via per into over is are be".split())


# ---------------------------------------------------------------- loading
def html_to_md(src):
    """Turn slide or page HTML into rough Markdown. <aside> blocks become speaker notes."""
    notes = re.findall(r"<aside\b[^>]*>(.*?)</aside>", src, re.S | re.I)
    src = re.sub(r"<(aside|script|style|head)\b.*?</\1>", "", src, flags=re.S | re.I)
    src = re.sub(r"<h([1-6])\b[^>]*>(.*?)</h\1>",
                 lambda m: "\n\n" + "#" * int(m.group(1)) + " " + re.sub(r"\s+", " ", m.group(2)) + "\n\n",
                 src, flags=re.S | re.I)
    src = re.sub(r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>", r"**\1**", src, flags=re.S | re.I)
    src = re.sub(r"<li\b[^>]*>", "\n- ", src, flags=re.I)
    src = re.sub(r"<(?:td|th)\b[^>]*>", " | ", src, flags=re.I)
    src = re.sub(r"<tr\b[^>]*>", "\n", src, flags=re.I)
    src = re.sub(r"<(?:p|div|section|br|ul|ol|table|blockquote)\b[^>]*>|</(?:p|div|section|ul|ol|table|blockquote)>",
                 "\n\n", src, flags=re.I)
    src = re.sub(r"<[^>]+>", "", src)
    src = htmlmod.unescape(src)
    src = re.sub(r"[ \t]+", " ", src)
    src = re.sub(r"\n\s*\n\s*\n+", "\n\n", src)
    notes_text = "\n\n".join(htmlmod.unescape(re.sub(r"<[^>]+>", "", n)) for n in notes)
    return src.strip() + "\n", notes_text


def load(path):
    p = Path(path)
    if p.is_dir():
        files = sorted(p.glob("*.html")) or sorted(p.glob("*.md"))
        if not files:
            raise FileNotFoundError(f"no .html or .md files in {p}")
        raw = "\n\n".join(f.read_text(encoding="utf-8") for f in files)
        is_html = files[0].suffix.lower() in (".html", ".htm")
    else:
        raw = p.read_text(encoding="utf-8")
        is_html = p.suffix.lower() in (".html", ".htm")
    if is_html:
        return (*html_to_md(raw), raw)
    return raw, "", raw


# ---------------------------------------------------------------- helpers
def words(text):
    return WORD_RE.findall(URL_RE.sub(" ", text))


def plain(line):
    line = URL_RE.sub(" ", line)
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", line)
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    return re.sub(r"[*_#>|]", " ", line)


def unquoted(line):
    """Drop short quoted passages: Humanizer leaves watched phrases alone inside quotations."""
    return re.sub(r"\"[^\"\n]{1,200}\"|“[^”\n]{1,200}”", " ", line)


def mention_free(line):
    """Drop `code` spans and short quotes, then markdown: a document that discusses a phrase is not using it."""
    return unquoted(plain(re.sub(r"`[^`\n]{1,200}`", " ", line)))


def show(s, n=110):
    s = s.strip().replace("\u2014", "<U+2014>").replace("\u2013", "<U+2013>")
    return s if len(s) <= n else s[: n - 3] + "..."


def syllables(word):
    w = word.lower()
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


class Doc:
    def __init__(self, raw, notes_text, notes_marker=None):
        self.raw = raw
        self.notes_text = notes_text

        def blank(m):
            return "\n" * m.group(0).count("\n")
        text = raw.replace("\r\n", "\n")
        text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
        text = re.sub(r"```.*?```", blank, text, flags=re.S)
        text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
        text = re.sub(r"<aside\b.*?</aside>", blank, text, flags=re.S | re.I)
        self.lines = text.split("\n")
        n = len(self.lines)
        heads = []
        for i, l in enumerate(self.lines):
            m = HEADING_RE.match(l)
            if m:
                heads.append((i, len(m.group(1)), m.group(2).strip()))
            else:
                b = re.match(r"^\s*\*\*([^*]{1,40})\*\*\s*:?\s*$", l)
                if b and SOURCES_HEAD_RE.match(b.group(1).strip()):
                    heads.append((i, 2, b.group(1).strip()))
        self.excluded = [False] * n
        self.sources = []          # (lineno, text)
        notes_re = re.compile(notes_marker, re.I) if notes_marker else NOTES_HEAD_RE
        self.has_sources = False
        for k, (i, lvl, title) in enumerate(heads):
            is_src = bool(SOURCES_HEAD_RE.match(re.sub(r"[*_]", "", title)))
            is_notes = bool(notes_re.search(title))
            if not (is_src or is_notes):
                continue
            end = n
            for j, lv2, _ in heads[k + 1:]:
                if lv2 <= lvl:
                    end = j
                    break
            for x in range(i, end):
                self.excluded[x] = True
                if is_src and x > i:
                    self.sources.append((x + 1, self.lines[x]))
            if is_notes:
                self.notes_text += "\n" + "\n".join(self.lines[i + 1:end])
            self.has_sources = self.has_sources or is_src
        self.heads = [(i, lvl, t) for i, lvl, t in heads if not self.excluded[i]]
        self.body = [(i + 1, l) for i, l in enumerate(self.lines) if not self.excluded[i]]
        self.body_text = "\n".join(l for _, l in self.body)
        self.n_lines = n

        # line classes for shares
        self.share = Counter()
        self.tables = []           # list of header strings
        prev = ""
        for ln, l in self.body:
            s = l.strip()
            if not s or HEADING_RE.match(l) or HR_RE.match(l):
                prev = s
                continue
            if TABLE_SEP_RE.match(l):
                if prev.startswith("|"):
                    self.tables.append(prev)
                prev = s
                continue
            w = len(words(plain(l)))
            if s.startswith("|"):
                self.share["table"] += w
            elif BULLET_RE.match(l):
                self.share["bullet"] += w
            else:
                self.share["prose"] += w
            prev = s
        self.words = sum(self.share.values()) + sum(len(words(plain(t))) for _, _, t in self.heads)

        # paragraphs (for ending checks): runs of non-empty, non-heading lines
        paras, cur = [], []
        for ln, l in self.body:
            if not l.strip() or HEADING_RE.match(l) or HR_RE.match(l):
                if cur:
                    paras.append(cur)
                cur = []
            else:
                cur.append((ln, l))
        if cur:
            paras.append(cur)
        self.paras = paras

    def sentences(self):
        t = "\n".join(plain(l) for _, l in self.body if not l.strip().startswith("|") and not HEADING_RE.match(l))
        out = []
        for s in re.split(r"(?<=[.!?])\s+|\n{2,}", t):
            s = " ".join(s.split())
            if len(s.split()) >= 3:
                out.append(s)
        return out


# ---------------------------------------------------------------- checks
class Report:
    def __init__(self):
        self.items = []

    def add(self, rid, level, count, msg, examples=()):
        self.items.append({"rule": rid, "level": level, "count": count, "message": msg,
                           "examples": [show(e) for e in list(examples)[:3]]})


def scan(body, patterns, flags=re.I, transform=None):
    hits = []
    for ln, l in body:
        s = transform(l) if transform else l
        for p in patterns:
            for m in re.finditer(p, s, flags):
                hits.append(f"L{ln}: {s[max(0, m.start() - 30):m.end() + 40]}")
    return hits


def lint(doc, dtype, rep):
    body = doc.body
    nw = max(doc.words, 1)
    per_k = 1000 / nw

    # 1. dashes, anywhere, quotes and sources included (a house rule: the author bans em and en dashes)
    hits = [f"L{i + 1}: {l}" for i, l in enumerate(doc.raw.split("\n")) if DASH_RE.search(l)]
    if doc.notes_text and DASH_RE.search(doc.notes_text):
        hits.append("speaker notes: " + doc.notes_text[max(0, DASH_RE.search(doc.notes_text).start() - 40):][:80])
    if hits:
        rep.add("dash", "FAIL", len(DASH_RE.findall(doc.raw)) + len(DASH_RE.findall(doc.notes_text)),
                "Em or en dash (U+2014/U+2013). Use a hyphen, comma, colon or full stop.", hits)

    # 2. typography
    c = len(CURLY_RE.findall(doc.raw))
    if c:
        rep.add("curly_quotes", "INFO", c, "Curly quotes. Fine if the target format curls quotes; --fix-typography straightens them.")
    e = scan(body, [ELLIPSIS_RE.pattern], 0)
    if e:
        rep.add("ellipsis_char", "WARN", len(e), "Ellipsis character. Write three dots or cut it.", e)
    a = scan(body, [ARROW_RE.pattern], 0, transform=lambda l: URL_RE.sub(" ", l))
    if a:
        rep.add("arrows", "WARN", len(a), "Arrow used as a connector (Humanizer 20). Write 'to' or rewrite.", a)

    # 3. stock words (URLs and short quotes removed)
    strong, jargon, weak = [], [], []
    sw = re.compile(r"\b(" + "|".join(map(re.escape, STRONG_WORDS + STRONG_PHRASES)) + r")\b", re.I)
    jw = re.compile(r"\b(" + "|".join(map(re.escape, JARGON_WORDS + JARGON_PHRASES)) + r")\b", re.I)
    ww = re.compile(r"\b(" + "|".join(map(re.escape, WEAK_WORDS)) + r")\b", re.I)
    for ln, l in body:
        s = mention_free(l)
        strong += [f"L{ln}: {m.group(0)} | {s[max(0, m.start() - 30):m.end() + 30]}" for m in sw.finditer(s)]
        jargon += [f"L{ln}: {m.group(0)} | {s[max(0, m.start() - 30):m.end() + 30]}" for m in jw.finditer(s)]
        weak += [f"L{ln}: {m.group(0)}" for m in ww.finditer(s)]
    if strong:
        rep.add("stock_words", "FAIL" if len(strong) >= 2 else "WARN", len(strong),
                "Stock AI words (Humanizer 12). Say the plain thing.", strong)
    if jargon:
        rep.add("jargon", "WARN", len(jargon), "Business jargon ('leverage', 'showcase'). Use the plain verb: use, show, lead.", jargon)
    iv = re.compile(r"\b(" + "|".join(map(re.escape, INVESTOR_WORDS)) + r")\b", re.I)
    inv = [f"L{ln}: {m.group(0)} | {mention_free(l)[max(0, m.start() - 30):m.end() + 30]}"
           for ln, l in body for m in iv.finditer(mention_free(l))]
    if inv:
        rep.add("investor_verbs", "WARN", len(inv),
                "Investor word for the decision (rule 15). Use the brief's own verb; keep it only if the brief uses it.", inv)
    if weak and len(weak) * per_k >= 3:
        rep.add("stock_words_weak", "WARN", len(weak), f"Common AI-favoured words at {len(weak) * per_k:.1f} per 1,000 words.", weak)

    # 4. staged openers, deep sayings, chatbot residue
    st = scan(body, STAGED + RESIDUE, transform=mention_free)
    if st:
        rep.add("staged_or_residue", "FAIL", len(st), "Staged opener, deep-sounding saying or chatbot residue (Humanizer 3, 4, 22). Cut it.", st)
    cc = scan(body, CLICHE_CLOSERS, transform=mention_free)
    if cc:
        rep.add("cliche_closer", "WARN", len(cc), "Stock closer. Ask for the specific thing instead.", cc)

    # 5. run-in labels, bold ("**Why.** ...") or plain ("Reasoning: ...")
    labels = []          # bold labels
    plain_labels = []    # plain "Label:" lines
    bullet_leads = []
    for ln, l in body:
        if HEADING_RE.match(l) or l.strip().startswith("|"):
            continue
        m = LABEL_RE.match(l)
        if not m:
            pm = PLAIN_LABEL_RE.match(l)
            if pm and len(pm.group(2).split()) <= 4:
                plain_labels.append((ln, pm.group(2).strip(), pm.group(2).strip().lower()))
            continue
        bullet, label, rest = m.group(1), m.group(2).strip(), m.group(3)
        norm = re.sub(r"^\d+[.)]\s*", "", label).strip().rstrip(".:?!").strip().lower()
        labels.append((ln, label, norm, rest))
        ends_stmt = label.endswith((".", ":")) or rest.lstrip().startswith((".", ":"))
        if bullet and ends_stmt and rest.strip(" .:"):
            bullet_leads.append(f"L{ln}: **{label}**{rest[:50]}")
    if dtype not in NO_LABEL_TYPES and (labels or plain_labels):
        every = [(ln, lab, norm) for ln, lab, norm, _ in labels] + plain_labels
        meta = [f"L{ln}: {lab}" for ln, lab, norm in every if META_LABEL_RE.match(norm)]
        cnt = Counter(norm for _, _, norm in every if len(norm) > 1)
        rep_labels = [f"'{k}' x{v}" for k, v in cnt.items() if v >= 2]
        lvl = "WARN" if dtype == "deck" else "FAIL"
        if meta:
            rep.add("meta_labels", lvl, len(meta), "Run-in labels that announce the answer or the reasoning ('The answer in one line.', "
                    "'Why.', 'Reasoning:'). Make the section's first sentence carry the point.", meta)
        # One repeated label can be a human per-item template (a pre-2022 sample repeats 'Description:');
        # three or more different labels repeating is the same template stamped on every section.
        if len(rep_labels) >= 3:
            rep.add("repeated_labels", lvl, len(rep_labels), "Several labels repeat in every section: a template, not writing.", rep_labels)
        elif rep_labels:
            rep.add("repeated_labels", "WARN", len(rep_labels), "A label repeats across sections. Fine for a list of like items; otherwise write it out.", rep_labels)
        dens = len(labels) * 400 / nw
        if dens > 1 and dtype not in ("deck", "landing"):
            rep.add("label_density", "WARN", len(labels), f"{len(labels)} bold run-in labels ({dens:.1f} per 400 words). Use paragraphs.",
                    [f"L{ln}: **{lab}**" for ln, lab, _, _ in labels])
        if len(bullet_leads) >= 3 and dtype not in ("deck", "landing"):
            rep.add("bullet_bold_leads", "FAIL", len(bullet_leads),
                    "Bullets that each open with a bold label and a colon or full stop (Humanizer 19).", bullet_leads)

    # 6. reading guide, coverage-map table
    rg = scan(body, READING_GUIDE, transform=mention_free)
    if rg:
        rep.add("reading_guide", "FAIL", len(rg), "Text that tells the reader how to read the document. Number the headings to the brief instead.", rg)
    for h in doc.tables:
        hl = h.lower()
        if re.search(r"brief|prompt|question|asks|requirement", hl) and re.search(r"section|where|answered|slide|page|covered", hl):
            rep.add("coverage_table", "FAIL", 1, "A table mapping the brief to sections. Keep it in your notes; headings numbered to the brief do this job.", [h])

    # 7. status words in the body
    sth = scan(body, [STATUS_RE.pattern], 0, transform=mention_free)
    if sth:
        rep.add("status_words", "FAIL" if len(sth) >= 2 else "WARN", len(sth),
                "Evidence-status labels in the body. They belong in notes or chat; in the document, name the source in the sentence.", sth)

    # 8. counterargument sections
    ch = [(i, t) for i, _, t in doc.heads if COUNTER_RE.search(t.strip())]
    cl = [(ln - 1, lab) for ln, lab, norm, _ in labels if re.search(r"argument against|counter-?argument", norm)]
    ct = ch + cl
    if len(ct) > 1:
        rep.add("counter_sections", "FAIL", len(ct), "More than one counterargument or risks section. Keep one 'What could go wrong' near the end.",
                [f"L{i + 1}: {t}" for i, t in ct])
    elif len(ct) == 1 and dtype in ("takehome", "memo") and ct[0][0] < 0.75 * doc.n_lines:
        rep.add("counter_position", "WARN", 1, "The risks section sits early. Put it after the answers.", [f"L{ct[0][0] + 1}: {ct[0][1]}"])

    # 9. heading style
    if dtype not in NO_HEADING_STYLE_TYPES:
        colon = [f"L{i + 1}: {t}" for i, _, t in doc.heads
                 if re.search(r":\s*\S", t) and not re.match(r"^(?:part|question|q|step|section|prompt|appendix|task|exercise|option|phase|week|day)\s*\d+\s*:", t, re.I)]
        if len(colon) >= 2:
            rep.add("colon_headings", "FAIL", len(colon), "Headings that state a claim after a colon. Use plain topic headings.", colon)
        dec = [f"L{i + 1}: {t}" for i, _, t in doc.heads if re.match(r"^\s*(?:\d+\.\d+|0\d)\b", t)]
        if len(dec) >= 3:
            rep.add("decimal_numbering", "FAIL", len(dec), "Decimal or zero-padded heading numbers (01.2). Number to the brief: 1, 2, 3.", dec)
        tc = []
        for i, _, t in doc.heads:
            ws = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", t)[1:] if w.lower() not in SMALL_WORDS and not w.isupper()]
            if len(ws) >= 2 and all(w[0].isupper() for w in ws):
                tc.append(f"L{i + 1}: {t}")
        if len(tc) >= 3 and len(tc) > 0.5 * max(len(doc.heads), 1):
            rep.add("title_case_headings", "WARN", len(tc), "Title Case headings (Humanizer 20). Use sentence case.", tc)
    hr = [f"L{ln}" for ln, l in body if HR_RE.match(l) and l.strip()]
    if len(hr) >= 3:
        rep.add("horizontal_rules", "WARN", len(hr), "A rule between every section (Humanizer 20). Headings already separate sections.", hr)
    if dtype == "deck":
        ps = [f"L{i + 1}: {t}" for i, _, t in doc.heads if PROCESS_SLIDE_RE.search(t)]
        if ps:
            rep.add("process_slide", "FAIL", len(ps), "A slide about method or how the deck was made. One line in the notes or on the sources slide is enough.", ps)

    # 10. per-claim date stamps
    stamps = scan(body, [STAMP_RE.pattern], re.I, transform=mention_free)
    if len(stamps) >= 3:
        rep.add("date_stamps", "FAIL", len(stamps), "Per-claim access dates or status stamps. Say once, in Assumptions, when the pages were checked.", stamps)
    elif stamps:
        rep.add("date_stamps", "WARN", len(stamps), "Access-date stamp in the body.", stamps)

    # 11. links and references
    body_urls = [f"L{ln}: {m.group(0)}" for ln, l in body for m in URL_RE.finditer(l)]
    if dtype in SOURCED_TYPES:
        if doc.has_sources and body_urls:
            rep.add("urls_in_body", "FAIL", len(body_urls), "URLs in the body while a Sources list exists. Use [n] and put the URL in Sources.", body_urls)
        elif not doc.has_sources and len(body_urls) > 3:
            rep.add("urls_in_body", "FAIL", len(body_urls), "Many inline URLs and no Sources list. Move them to a numbered Sources list at the end.", body_urls)
    elif dtype in PLAIN_TYPES and len(body_urls) > 1:
        rep.add("too_many_links", "WARN", len(body_urls), "More than one link. Emails and posts carry one link at most.", body_urls)

    refs = set()
    ref_lines = {}
    for ln, l in body:
        for m in re.finditer(r"(?<![\]\w])\[(\d{1,3}(?:\s*[,-]\s*\d{1,3})*)\](?![(\[:])", l):
            for part in re.split(r"\s*,\s*", m.group(1)):
                if "-" in part:
                    a_, b_ = part.split("-", 1)
                    nums = range(int(a_), int(b_) + 1) if int(b_) - int(a_) < 30 else [int(a_), int(b_)]
                else:
                    nums = [int(part)]
                for x in nums:
                    refs.add(x)
                    ref_lines.setdefault(x, ln)
    entries = {}
    for ln, l in doc.sources:
        m = re.match(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+(.*)", l)
        if m:
            entries[int(m.group(1) or m.group(2))] = (ln, m.group(3))
    if refs:
        missing = sorted(r for r in refs if r not in entries)
        if missing:
            rep.add("ref_without_source", "FAIL", len(missing), "[n] references with no matching Sources entry.",
                    [f"[{r}] first at L{ref_lines[r]}" for r in missing])
    no_url = [f"L{ln}: {t}" for n_, (ln, t) in entries.items() if not re.search(r"(?<!\]\()https?://", t)]
    if no_url:
        rep.add("source_without_raw_url", "FAIL", len(no_url), "Sources entries without a full raw URL.", no_url)
    if refs and entries:
        unused = sorted(set(entries) - refs)
        if unused:
            rep.add("source_not_cited", "WARN", len(unused), "Sources entries never cited in the body.", [f"[{u}]" for u in unused])

    # 12. format shares
    tot = max(sum(doc.share.values()), 1)
    tshare, pshare, bshare = doc.share["table"] / tot, doc.share["prose"] / tot, doc.share["bullet"] / tot
    if dtype in PROSE_TYPES:
        if tshare > 0.30:
            rep.add("table_share", "FAIL", round(tshare * 100), f"{tshare:.0%} of words sit in tables. Keep tables for scoring, KPIs and maths.")
        elif tshare > 0.20:
            rep.add("table_share", "WARN", round(tshare * 100), f"{tshare:.0%} of words sit in tables.")
        # Ten LLM answers to one growth take-home brief ran 22 to 43% prose (one outlier at 84%); two pre-2022
        # human take-homes ran 97 to 100%; the accepted human-edited answer ran 56%.
        if pshare < 0.45:
            rep.add("prose_share", "FAIL", round(pshare * 100), f"Only {pshare:.0%} of words are prose paragraphs. "
                    "Write the reasoning as paragraphs; keep bullets for parallel items.")
        elif pshare < 0.50:
            rep.add("prose_share", "WARN", round(pshare * 100), f"Only {pshare:.0%} of words are prose paragraphs.")
        if bshare > 0.35:
            rep.add("bullet_share", "WARN", round(bshare * 100), f"{bshare:.0%} of words are bullets.")
    if dtype in PLAIN_TYPES:
        md = [f"L{ln}: {l}" for ln, l in body if HEADING_RE.match(l) or "**" in l or l.strip().startswith("|")
              or re.search(r"\[[^\]]+\]\([^)]+\)", l)]
        if md:
            rep.add("markdown_in_plain_text", "FAIL", len(md), "Markdown (headings, bold, tables, [text](link)) in text that goes out as plain text.", md)
    if dtype == "cover":
        md = [f"L{ln}: {l}" for ln, l in body if HEADING_RE.match(l) or l.strip().startswith("|")]
        if md:
            rep.add("cover_structure", "WARN", len(md), "Headings or tables in a cover letter.", md)

    # 13. endings
    if doc.paras:
        tail = doc.paras[-2:]
        recap = [f"L{p[0][0]}: {p[0][1]}" for p in tail if RECAP_RE.match(plain(p[0][1]).strip())]
        if recap:
            rep.add("recap_ending", "FAIL", len(recap), "A recap at the end ('In summary'). End on the next step or the ask.", recap)
    tk = [f"L{i + 1}: {t}" for i, _, t in doc.heads if TAKEAWAY_HEAD_RE.match(t.strip())]
    tk += [f"L{ln}: **{lab}**" for ln, lab, norm, _ in labels if TAKEAWAY_HEAD_RE.match(norm)]
    if tk:
        rep.add("takeaways_block", "FAIL", len(tk), "A TL;DR or key-takeaways block.", tk)
    if doc.heads and END_HEAD_RE.match(doc.heads[-1][2].strip()):
        rep.add("summary_section_last", "WARN", 1, "The last section is a summary or conclusion. End on next steps.", [doc.heads[-1][2]])
    if dtype in ("takehome", "memo", "email", "cover") and doc.paras:
        last_head = doc.heads[-1][2] if doc.heads else ""
        tail_text = " ".join(plain(l) for p in doc.paras[-2:] for _, l in p)
        if not (NEXT_RE.search(last_head) or NEXT_RE.search(tail_text)):
            rep.add("no_next_step", "WARN", 1, "The ending has no next step or ask.")

    # 14. assumptions up front (take-homes and memos)
    if dtype in ("takehome", "memo"):
        pos = [i for i, _, t in doc.heads if ASSUME_RE.search(t)]
        if not pos:
            pos = [ln - 1 for ln, l in body if ASSUME_RE.search(l)][:1]
        if not pos:
            rep.add("no_assumptions", "WARN", 1, "No assumptions stated. Put them near the top.")
        elif pos[0] > 0.35 * doc.n_lines:
            rep.add("late_assumptions", "WARN", 1, f"Assumptions first appear at line {pos[0] + 1}. Move them near the top.")

    # 15. self-narration, not-X-but-Y, placeholders
    sn = scan(body, SELF_NARRATION, transform=mention_free)
    if sn:
        rep.add("self_narration", "WARN", len(sn), "Text about the document instead of its subject (Humanizer 25).", sn)
    nx = scan([(ln, l) for ln, l in body if not l.strip().startswith("|")], NOT_X_BUT_Y, transform=mention_free)
    if nx:
        rep.add("not_x_but_y", "WARN", len(nx), "'Not X but Y' contrast (Humanizer 1). Check each one adds a fact.", nx)
    ph = scan(body, [PLACEHOLDER_RE.pattern], 0, transform=lambda l: URL_RE.sub(" ", l))
    if ph:
        rep.add("placeholders", "WARN", len(ph), "Placeholder text left in.", ph)

    # 16. length
    if dtype in LENGTHS:
        lo, hi = LENGTHS[dtype]
        if not lo <= doc.words <= hi:
            rep.add("length", "WARN", doc.words, f"{doc.words} body words; a rough guide for a {dtype} is {lo:,} to {hi:,} "
                    "(see references/structures.md). A length or page limit in the brief always overrides this.")
    if dtype == "post":
        first = plain(doc.body_text.strip())[:210]
        tags = re.findall(r"(?<!\w)#\w+", doc.body_text)
        if len(tags) > 5:
            rep.add("hashtags", "WARN", len(tags), "More than five hashtags.")
        if not first.strip():
            rep.add("empty_hook", "WARN", 1, "Nothing before LinkedIn's 'see more' cut (about 210 characters).")

    # 17. reported only
    sents = doc.sentences()
    lens = [len(s.split()) for s in sents]
    wl = words(" ".join(sents))
    syl = sum(syllables(w) for w in wl)
    fk = 0.39 * (len(wl) / max(len(sents), 1)) + 11.8 * (syl / max(len(wl), 1)) - 15.59 if sents else 0
    part = len(re.findall(r",\s+\w+ing\b", "\n".join(plain(l) for _, l in body))) * per_k
    stats = {
        "body_words": doc.words,
        "prose_share": round(pshare, 2), "bullet_share": round(bshare, 2), "table_share": round(tshare, 2),
        "sentence_mean": round(statistics.mean(lens), 1) if lens else 0,
        "burstiness_cv": round(statistics.pstdev(lens) / statistics.mean(lens), 2) if len(lens) > 1 else 0,
        "participle_per_1k": round(part, 1),
        "reading_grade": round(fk, 1),
        "sources_entries": len(entries), "body_urls": len(body_urls), "bold_labels": len(labels),
    }
    if dtype == "landing" and fk > 9:
        rep.add("reading_grade", "WARN", round(fk, 1), f"Reading grade {fk:.1f}. Unbounce found grade 5 to 7 copy converts best.")
    return stats


def tells_per_1k(text, dtype="doc"):
    """Count of WARN and FAIL hits per 1,000 words, for sameness_check.py. Score a deck with dtype="deck"."""
    doc = Doc(text, "")
    rep = Report()
    lint(doc, dtype, rep)
    skip = {"length", "no_next_step", "no_assumptions", "late_assumptions", "prose_share", "bullet_share",
            "table_share", "source_not_cited", "curly_quotes"}
    n = sum(i["count"] for i in rep.items if i["level"] in ("FAIL", "WARN") and i["rule"] not in skip)
    return round(n * 1000 / max(doc.words, 1), 1), rep.items


# ---------------------------------------------------------------- typography fixer
TYPO_RULES = [
    (re.compile(r"(?<=\d)\s*[\u2013\u2014]\s*(?=\d)"), "-"),
    (re.compile(r"(?<=\d{4})\s*[\u2013\u2014]\s*(?=(?:Present|Current|Now|Ongoing)\b|[A-Z][a-z]+ \d{4})"), " to "),
    (re.compile(r"\s*(?:→|(?<![-<])->(?!>))\s*"), " to "),
    (re.compile(r"\s+[\u2013\u2014]\s+"), ", "),
    (re.compile(r"[\u2013\u2014]"), "-"),
    (re.compile(r"[‘’‚‛]"), "'"),
    (re.compile(r"[“”„‟]"), '"'),
    (re.compile(r"…"), "..."),
]


def fix_typography(text):
    for pat, repl in TYPO_RULES:
        text = pat.sub(repl, text)
    return text


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="Structure and wording checks for documents other people read.")
    ap.add_argument("file")
    ap.add_argument("--type", default="doc", choices=TYPES)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any WARN as well")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--notes-marker", default=None, help="regex for headings whose sections are speaker notes")
    ap.add_argument("--fix-typography", metavar="OUT", default=None,
                    help="write a copy with dashes, curly quotes, arrows and ellipses fixed to OUT (never in place)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        raw, notes, original = load(a.file)
    except (OSError, UnicodeDecodeError) as e:
        print(f"lint_doc: cannot read {a.file}: {e}", file=sys.stderr)
        return 2

    if a.fix_typography:
        out = Path(a.fix_typography).resolve()
        if Path(a.file).is_dir() or out == Path(a.file).resolve():
            print("lint_doc: --fix-typography needs a single input file and a different output path", file=sys.stderr)
            return 2
        out.write_text(fix_typography(original), encoding="utf-8")
        print(f"wrote {out}")
        raw, notes, _ = load(out)

    doc = Doc(raw, notes, a.notes_marker)
    rep = Report()
    stats = lint(doc, a.type, rep)
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    rep.items.sort(key=lambda i: order[i["level"]])
    fails = sum(i["level"] == "FAIL" for i in rep.items)
    warns = sum(i["level"] == "WARN" for i in rep.items)
    code = 1 if fails or (a.strict and warns) else 0

    if a.json:
        print(json.dumps({"file": a.file, "type": a.type, "exit": code, "fails": fails, "warns": warns,
                          "stats": stats, "results": rep.items}, indent=1))
        return code
    print(f"lint_doc  {a.file}  type={a.type}  body words={stats['body_words']}  sources={stats['sources_entries']}")
    for i in rep.items:
        print(f"{i['level']:<5} {i['rule']:<24} {i['count']:>4}  {i['message']}")
        for ex in i["examples"]:
            print(f"{'':36}{ex}")
    print(f"INFO  shares prose {stats['prose_share']:.0%} / bullets {stats['bullet_share']:.0%} / tables {stats['table_share']:.0%}; "
          f"sentence mean {stats['sentence_mean']}; burstiness {stats['burstiness_cv']}; "
          f"participle clauses {stats['participle_per_1k']}/1k; reading grade {stats['reading_grade']}")
    print(f"Result: {'FAIL' if code else 'PASS'}  ({fails} FAIL, {warns} WARN)")
    return code


if __name__ == "__main__":
    sys.exit(main())
