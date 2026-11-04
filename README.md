# pre-ai-writing

A Claude Code skill for writing documents other people will read, so they don't read as if a chatbot wrote them.

Most "humanizer" tools fix words: "delve", "robust", em dashes. The bigger giveaway is often structure. One take-home answer drafted with Claude had 27 bold run-in labels such as "The answer in one line.", 56 "Confirmed" tags, 50 links in the middle of paragraphs, a "How to read it" paragraph and a counterargument section at the end of every part. A word-level checker passed it. The person submitting it rejected it as an obvious AI giveaway.

This skill makes Claude write the way people wrote before ChatGPT arrived in November 2022: the objective first, then assumptions, plain topic headings, the point in each section's first sentence, mostly prose, and a numbered source list at the end. It then hands the sentences to the [humanizer](https://github.com/blader/humanizer) skill.

## What's in it

- `SKILL.md` is the ten-step workflow Claude follows, from framing the reader to handover.
- `scripts/lint_doc.py` is the linter. It uses only the standard library and reports FAIL and WARN with line numbers.
- `references/` has the rules with before and after examples, a template per document type, where evidence goes, a voice template and the high-stakes tier.
- `scripts/sameness_check.py` compares a draft with ChatGPT, Gemini and Claude answers to the same brief, and `scripts/blind_pack.py` shuffles and anonymises them for a blind odd-one-out review.
- `scripts/build_pdf.py` turns Markdown into a PDF through headless Chrome. It needs the `markdown` package.
- `scripts/prompt_trigger.py` is an optional hook that reminds Claude to use the skill.

## Install

```
git clone https://github.com/abhishekkumar541/pre-ai-writing ~/.claude/skills/pre-ai-writing
```

Install [humanizer](https://github.com/blader/humanizer) as well, since step 6 calls it.

Claude tends to skip skills on short tasks. In fresh-session tests on Opus, it used this one for 2 of 4 drafting requests on the description alone. With the hook below, every test session that got as far as drafting used it. Add this to `hooks.UserPromptSubmit` in `~/.claude/settings.json`:

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "python3 -I ~/.claude/skills/pre-ai-writing/scripts/prompt_trigger.py 2>/dev/null || true",
      "timeout": 5
    }
  ]
}
```

The hook is a local keyword match with no network calls. It only adds a reminder when a message asks to draft or review an email, post, letter, memo, deck, resume or landing page.

## Using the linter on its own

```
python3 scripts/lint_doc.py --type takehome answer.md
python3 scripts/lint_doc.py --type email note.txt --json
python3 scripts/lint_doc.py --type deck slides/
python3 scripts/lint_doc.py draft.md --fix-typography draft_fixed.md
```

Types are takehome, memo, email, cover, post, resume, deck, landing and doc. The exit code is 0 with no FAIL, 1 with at least one FAIL, and 2 if the file can't be read. `--strict` also fails on WARN.

The main FAIL rules:

| Rule | Catches |
|---|---|
| `meta_labels` | "The answer in one line.", "Why.", "Reasoning:", "TL;DR" |
| `repeated_labels` | Three or more labels stamped on every section |
| `reading_guide`, `coverage_table` | "How to read this", a table mapping the brief to sections |
| `status_words`, `date_stamps` | "Confirmed", "(read 2 Nov 2026)" on facts in the body |
| `counter_sections` | A counterargument section in every part |
| `colon_headings`, `decimal_numbering` | "01.2 Channels: search wins" |
| `urls_in_body`, `ref_without_source` | Inline links, or [n] with no Sources entry |
| `table_share`, `prose_share` | Reasoning written as tables or bullets |
| `stock_words`, `staged_or_residue` | "delve", "tapestry", "Here's the thing", "I hope this helps" |
| `dash` | Em and en dashes (a house rule; delete it if you use them) |

## How the thresholds were set

The FAIL thresholds come from a small set of real documents:
- one rejected take-home draft and its accepted rewrite
- ten answers to the same brief from ChatGPT, Gemini and Claude (Haiku, Sonnet and Opus, with a plain prompt and an "act as a CMO" prompt)
- two take-home answers written in 2021, from the Wayback Machine

The rejected draft fails 12 rules, the rewrite passes, all ten LLM answers fail, and both 2021 answers pass. That is a small sample, so anything with weaker evidence is only a WARN. "Leverage" and "showcase", for example, are WARNs because the 2021 writers used them too.

## Limits

- A clean lint doesn't make a document good, or human. The read-through in step 8 and the blind review matter more.
- It uses no AI detector. They are unreliable, and the aim is a document only someone who did the work could write.
- Tested on macOS with Python 3.14. `build_pdf.py` looks for Chrome or Chromium, or uses `CHROME_PATH`.

Run the tests with `python3 -I tests/test_lint_doc.py`.

## Licence

MIT. See `LICENSE`.
