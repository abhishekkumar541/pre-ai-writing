---
name: pre-ai-writing
description: Pre-AI writing standard for anything someone other than the user will read. Make sure to use this skill whenever you draft, rewrite, review or polish such text, even a short one and even if the user does not name the skill - cold, referral or follow-up emails, LinkedIn or social posts, cover letters, resumes, memos, reports, briefs, docs, take-home or case answers, deck or slide text, landing-page copy, or a message the user will send. Also use it after another skill drafts such text, and before handover. It owns structure, format and evidence placement, runs a linter, calls humanizer and checks claims about the user. Not for chat replies, research notes, plans, code or commit messages; a bare "humanize this" passage goes to humanizer.
---

# Pre-AI writing

Documents keep reading as LLM output for structural reasons that a word-level pass cannot fix:
- run-in labels ("The answer in one line.")
- reading guides
- status tags on every fact
- a counterargument in every section
- tables for everything
- URLs in every paragraph

Write the way people wrote before November 2022: the objective first, assumptions next, plain headings, the point in each section's first sentence, mostly prose, and a numbered source list at the end. The humanizer skill (https://github.com/blader/humanizer) then handles the sentences.

`references/rules.md` has every rule with a before and after. `references/structures.md` has one template per document type. Paths below are relative to this skill's folder.

## Workflow

1. **Frame.** In one chat line, name four things:
   - the reader
   - when they read it (inbox, interview panel, feed)
   - the type: takehome, memo, email, cover, post, resume, deck, landing or doc
   - the tier

   High-stakes means a job application or take-home, a client deliverable, anything for an executive, or anything the user calls high-stakes. *Done when the line is written.*
2. **Gather before drafting.** Collect:
   - **The brief's exact words**, including any length or page limit.
   - **A coverage table** mapping everything the brief asks for to the section that will answer it. It stays in chat or notes, never in the document.
   - **First-hand evidence**, each item with its source.
   - **The user's own words** from notes and earlier messages.
   - **For client copy,** 15 to 20 of the client's own lines.

   Mark any planned claim without a source "ask". *Done when every planned claim has a source or an "ask".*
3. **Shape.** Pick the template in `references/structures.md` and give each section a word budget that follows its importance. A limit in the brief beats any default length. *Done when an outline with budgets exists.*
4. **Draft** to `<name>_draft.md`, following `references/rules.md` and `references/evidence.md`. Status labels, access dates and number tables go in `<name>_notes.md`.
5. **Lint.** Run:

   ```
   python3 scripts/lint_doc.py --type <type> <file>
   ```

   For a deck, pass the slides folder; `<aside>` is read as speaker notes. Fix every FAIL. Fix each WARN, or say in chat why it stays. *Done when the exit code is 0.*
6. **Humanizer.** Invoke the `humanizer` skill with the Skill tool, even for a three-line email. A manual "I checked it myself" pass does not count; fresh sessions skipped this step in testing. Run it in embedded mode on the prose only. Tables, quoted copy, code and the Sources list stay as they are. Save the result as a new file and lint it again. *Done when the new file lints clean.*
7. **Claims about the user.** List every sentence that states the user's actions, habits, results, usage or feelings. Trace each to their resume, their notes or memory, or what they said in this conversation. Ask about or cut anything without a source. *Done when a chat table (claim | source | kept, cut or asked) covers every such sentence.*
8. **Read-through as the named reader.** Answer each question yes or no, and fix every wrong answer:
   - Does each section's first sentence carry its point?
   - Would the reader miss each paragraph if it were cut?
   - Does any sentence describe the document itself?
   - Does section length follow importance?
   - What here could only come from first-hand work? (Name it; if nothing, the draft is generic.)
   - Does every number trace to the notes?
   - Does it end with a next step or an ask?
   - Does the format fit where it is going? (Plain text for email and LinkedIn, no markdown.)
   - Does it repeat a mistake listed under Open in `learnings.md`?
9. **High-stakes tier only.** This step is required whenever step 1 says high-stakes, short texts included. A referral or job-application email gets the reader-lens review too. Follow `references/high-stakes.md`:
   - a reader-lens review by a fresh agent
   - for take-homes and pitches, baselines plus `scripts/sameness_check.py` and a blind review via `scripts/blind_pack.py`

   *Done when its pass rule is met, or the failures are reported.*
10. **Hand over** in the destination's format:
    - plain text for email and posts
    - Markdown or a doc for documents
    - slides for decks

    The coverage, claims and status tables go in chat or `<name>_notes.md`. Make a PDF only when the user asks or the deliverable is a PDF:

    ```
    python3 scripts/build_pdf.py in.md out.pdf --title "..." --footer-left "..."
    ```

    Then check the page images, including the sources page. Run it without `-I` because it imports `markdown`.
11. **Log corrections.** If the user corrects the text, at handover or later, add one entry per correction under Open in `learnings.md`. Don't edit `references/rules.md` from a single correction unless the user asks for a rule. *Done when every correction in this session has an entry.*

## Rules that override other skills

- **Dashes.** No U+2014 or U+2013 anywhere, quotes and notes included. This is the author's house rule; delete the `dash` check in `scripts/lint_doc.py` if your style allows dashes.
- **Revisions are new versions.** Never silently edit the original deliverable.
- **Process stays off the page.** Method, process and AI use get one line on the sources slide or in notes, never a section or slide.
- **This skill is the final pass.** Copywriting, email and resume skills draft content; this skill runs after them, not instead of them.

## Keeping the skill current

The skill learns from the user's corrections, but a person approves every new rule:
- **Log first.** Corrections go to `learnings.md` (step 11), never straight into the rules.
- **Promote on repeat or approval.** A correction becomes a rule when it comes up again in a different document, or when the user asks. Promotion steps are in `learnings.md`.
- **Every rule is checked.** Each rule heading names its `scripts/lint_doc.py` check with a firing test and a near-miss test, or says `[manual]` with the reason.
- **Commit each change.** Keep the skill folder in git, one commit per rule change, so a bad rule can be reverted.
- **Health check.** Run `python3 -I scripts/health_check.py` after any change and once a month. It runs the tests, checks rule tags and flags Open learnings older than 30 days.

## Files

- `scripts/lint_doc.py`: the structural and wording linter. Run `--help` for flags; `--fix-typography OUT` writes a fixed copy.
- `scripts/sameness_check.py`, `scripts/blind_pack.py`: the high-stakes kit.
- `scripts/build_pdf.py`: Markdown to PDF, with checks.
- `scripts/prompt_trigger.py`: an optional UserPromptSubmit hook that reminds Claude to use this skill (see README).
- `scripts/health_check.py`: tests, rule tags, learnings age and, if you keep a private and a public copy, what changed since the last sync.
- `learnings.md`: corrections waiting to become rules, and what was promoted or dropped.
- `references/`:
  - `structures.md`
  - `rules.md`
  - `evidence.md`
  - `voice.md`
  - `high-stakes.md`
- `templates/blind_review_prompt.md`
- `tests/test_lint_doc.py`: run it after changing any rule.
