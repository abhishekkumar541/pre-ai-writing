# Rules, with the before and after

Each rule says what to do, then gives a pair. The pairs use a made-up take-home for Acme, a B2B marketplace. They copy the shape of a real rejected draft and its accepted rewrite. The id in brackets is the `lint_doc.py` rule that catches it.

Sentence-level tells (not-X-but-Y, one-line closers, triads, stock words, chatbot residue) belong to Humanizer. Run it at SKILL.md step 6 instead of re-listing its patterns here.

## 1. The first sentence of a section is the answer. No label announces it. [meta_labels]

Before:
> **The answer in one line.** I'd judge every channel by activated teams, and use trial starts as the early read.

After:
> Acme asked how to grow paid teams this year. Every answer below is judged by one number, activated teams: teams that finish setup and invite a colleague within a week.

These labels do the same job and fail the same way:
- "Why."
- "What I'd do."
- "Reasoning:"
- "TL;DR"
- "Bottom line"
- "My recommendation:"

## 2. Write each option as paragraphs, not a stamped template. [repeated_labels, label_density, bullet_bold_leads]

Before (repeated for all three options):
> **What I'd do.** Keep search as the engine and change what it aims at...
> **Why.** Most trials already start from a search...
> **Resources.** Today's budget, re-pointed...
> **How I'd judge it.**

After:
> **Search ads.** Most trials already start from a search, so this stays the main channel. What I'd change is what the bidding aims at...
>
> It needs no new budget at first, only about two weeks of engineering to pass activations back to the ad platform.

One short bold name per option is fine; a 2021 human take-home did exactly that. A stack of four labels under every option is not. Turn bullets that each open with a bold label and a colon into prose (Humanizer 19).

## 3. Headings name the topic and follow the brief's numbering. [colon_headings, decimal_numbering]

Before:
> # 01. Channels: keep search as the engine, add partners, and judge all three on activated teams
> ## 01.3 What I wouldn't fund now

After:
> ## 1. Channels to bring in new teams
> ### What I'd leave for now

The claim moves into the section's first sentence: "I'd put money into three channels: search ads, partner referrals and the template gallery."

## 4. No reading guide and no coverage map. Number the sections to the brief. [reading_guide, coverage_table, self_narration]

Before:
> **How to read this.** Every heading is a conclusion and every section starts with a one-line answer, so you can read the headings alone.

The same draft also had a table headed "The brief asks | Section".

After: neither exists. Sections 1 to 4 match the brief's four prompts, so the reader needs no map. Still make the coverage table, but keep it in chat or `<name>_notes.md`.

The same rule covers any sentence about the document itself:
- "The table below compares..."
- "This section is organised by..."
- "The point is the formula..."

## 5. Name the source in the sentence and cite it as [n]. No status tags, no dates per claim, no URLs in the body. [status_words, date_stamps, urls_in_body, ref_without_source, source_without_raw_url]

Before:
> Customers pay Acme $500 to $5,000 a month, about $1,200 on average (CEO interview in TechCrunch, 3 Mar 2021, Confirmed: https://example.com/acme-interview).

After:
> Customers pay Acme $500 to $5,000 a month, about $1,200 on average [1].

The Sources list then reads:
> 1. TechCrunch, 3 March 2021, interview with Acme's CEO: https://example.com/acme-interview

Still make the status labels (Confirmed, Supported, Unconfirmed, Disputed) and any number tables, but keep them in `<name>_notes.md` or chat, never in the document. See `evidence.md`.

## 6. Assumptions come first. What you couldn't see is an assumption, not an ending. [late_assumptions, no_assumptions]

Before (the last section):
> **What I couldn't see.** No internal data: no spend, conversion rates or funnel numbers. Every fact comes from public pages I checked on 2 to 4 March...

After (straight after the opening):
> ## Assumptions
> - Everything about Acme comes from its public pages as they stood between 2 and 4 March, and from interviews its founders have given. I had no internal data.

## 7. One "What could go wrong", near the end, only where the risk is real. [counter_sections, counter_position]

Before: "1.6 The strongest argument against these picks", then the same section again at 2.7, 3.5 and 4.6.

After: one `## What could go wrong` after the answers, covering in one paragraph the two or three decisions where the risk is real.

## 8. Tables only for scoring, KPIs, maths and sample sizes. Reasoning goes in prose. [table_share, prose_share, bullet_share]

The calibration documents put these shares of their words in tables:

| Document | In tables |
|---|---|
| Rejected draft | 32% |
| Accepted rewrite | 14% |
| Two pre-2022 human take-homes | about 10% |

Ten LLM answers to the same brief ran 22 to 43% prose. If a table's cells are sentences, the content should be paragraphs.

## 9. End on the next step or the ask, never a recap. [recap_ending, takeaways_block, summary_section_last, no_next_step]

After:
> ## In the first week
> Before changing any spend I'd want three answers: which channels bring teams that activate, how long activation takes, and where today's paid teams first found Acme...

No "In summary", no "Key takeaways" block, no closing restatement.

## 10. Process and method stay off the page. [process_slide, self_narration]

A "Limits, and how I made this" slide in an interview deck reads as padding, because every slide should answer a prompt the reader set. Method and AI use get one line on the sources slide or in the speaker notes, for example "AI tools helped with research and drafting."

## 11. Use the reader's words, not your working shorthand.

Before: "workspaces", the internal name, in an email to buyers.

After: "teams", the word buyers use. If you need a working term, explain it once in Assumptions, or not at all.

## 12. No compliment-then-"but" opener in emails and letters.

Before:
> Loved your recent post on retention, but I noticed...

After: give the reason you're writing and the ask in the first two lines. If a detail about the reader matters, use it as the reason, not as flattery.

## 13. Nothing unfinished goes out. [placeholders]

Remove these before handover:
- "To confirm"
- "TBD"
- "[link]"
- "[Name]"
- "XX"

A placeholder that is part of the deliverable, such as an email template's `[postal address]`, is fine; say so in the notes.

## 14. No dashes, anywhere (house rule). [dash]

Never use U+2014 (em dash) or U+2013 (en dash), and that includes quotes, sources and speaker notes. Use a hyphen for ranges ("2022 - 2024"); otherwise use a comma, colon or full stop. `lint_doc.py --fix-typography OUT` writes a fixed copy and never edits in place.
