# Structures by document type

Pick the template, give each section a word budget, then draft. If the brief sets a length or page limit, that limit is the target. The lengths below are advice from the sources named, not standards. The linter WARNs outside them and never FAILs on length.

## Take-home answer or case study

The evidence is three real candidate answers dated before November 2022:
- Simply Wall St growth channels (archived January 2022): http://web.archive.org/web/20220119203302/https://coda.io/@anthony-yuan/simply-wall-st-growth-channels
- Edureka growth plan (archived October 2021): http://web.archive.org/web/20211025232400/https://coda.io/@arsh-akhtar-ansari/swag-wala-assignment-1
- BarkShop marketing take-home, 2018: https://www.slideshare.net/changahroo/interviewing-at-barkshop-2018

Practitioner essays from the same period back them up.

Order:

1. Title, then one byline line (name, month and year).
2. **Opening paragraph:** the objective or the problem in the company's terms, and the one idea that runs through every answer. No verdict label and no reader's guide.
3. **Assumptions**, as a short bullet list:
   - what the work is based on
   - the dates the public pages were checked (written "as they stood between 2 and 4 March", not "as of")
   - which numbers are examples
   - any term the reader might misread
4. **One section per prompt,** numbered to the brief: `## 1. Channels to bring in new teams`. The heading names the topic. The first sentence gives the recommendation; the next gives the reason.
5. **Sub-headings** only where the brief asks for a list (essential, optional, unnecessary) or the content changes kind (a metric list, a test plan).
6. **One `## What could go wrong`** after the answers, covering only the one or two decisions where the risk is real.
7. **Next steps:** what you'd ask or do in the first week, in order.
8. **`## Sources`:** a numbered list with full raw URLs. The body cites them as [n].

Form:
- **Length.** Follow the brief: "1-2 pages per prompt" means checking pages per prompt in the PDF. Without a limit, the two archived answers ran about 1,300 and 2,700 words. That's two documents, not a ceiling. Cut repetition before substance.
- **Prose.** Mostly paragraphs of 3 to 6 sentences.
- **Bullets** for assumptions, steps and parallel items.
- **Tables** only for scoring, KPIs, money checks and sample sizes. The human samples were about 75% prose, 15% bullets and 10% tables.
- **Section length follows importance.** The option you are surest of gets three paragraphs; the one you are less sure of gets a few lines.
- **Templates.** A light template repeated across options is fine; the Simply Wall St answer repeats "Description:" and "Experiment Outline:". What reads as AI is stacked meta-layers: an answer label, why, resources, how judged, a status tag and a counterargument on every item.

## Memo, brief or report

The same spine as the take-home, shorter:
- the objective
- the recommendation in the first paragraph
- the context
- the options considered
- the decision and why
- risks
- next steps with owners

Amazon's narrative memos put the author's view in prose with causal links ("because of that", "so now"), and a blog reports a six-page cap, appendix excluded: https://released.so/articles/the-amazon-six-pager/ (not an Amazon source). Headings name topics, not claims.

## Email (cold, referral, follow-up)

- **First two lines:** why you're writing and what you're asking. No compliment followed by "but".
- **One reader-specific detail** (their post, their product, a mutual contact), only when it's true and sourced.
- **Plain text:** no bold, no headings, no labelled bullets. One link at most.
- **Close** with one concrete ask: 15 minutes on a named day, or a reply to one question.
- **Length:** Hunter's study of 34 million cold emails found the highest reply rate at 20 to 39 words: https://hunter.io/blog/cold-email-word-count . Referral and follow-up emails can run longer; stay under about 150 words.
- **Subject:** short, plain, no teaser.

## Cover letter

- **Length:** 3 to 4 short paragraphs, under one page. Source: Monroe Community College career center, https://www.monroecc.edu/depts/careercenter/resume-help/cover-letter-strategies/writing-a-cover-letter/
- **Paragraph 1:** the role, and the single strongest reason you fit, tied to something specific about the company.
- **Paragraphs 2 and 3:** one or two pieces of evidence, each with a number and what it changed. Every claim traces to the resume or the writer's notes (SKILL.md step 7).
- **Last paragraph:** the ask and your availability.
- **Format:** no headings, tables or bold. Match the job post's spelling.

## LinkedIn or social post

- **The first line is the hook and must stand alone.** LinkedIn cuts at roughly 210 characters on desktop and 140 on mobile. These are third-party measurements I couldn't confirm: https://medium.com/@artyom.shimanski/the-linkedin-see-more-cutoff-why-210-characters-decide-your-posts-fate-bc05bf211e0f
- **One idea,** told through one specific thing that happened, with facts the writer has confirmed.
- **Format:** short paragraphs in plain text, no markdown bold, at most one link (often better in the first comment) and 3 to 5 hashtags.
- **Length:** about 1,200 to 1,600 characters is the common advice, also unconfirmed: https://linkedinpreview.com/blog/linkedin-post-length
- **Ending:** a question or a plain statement, not a moral ("The lesson?").

## Deck text (slides and speaker notes)

- **One prompt per slide**, titled in the brief's own words and labelled with the prompt it answers.
- **Titles** are plain topics or the brief's phrase, with no claim after a colon.
- **Process, method and AI use** get one line on the sources slide or in speaker notes, never a slide of their own.
- **Access dates, status labels and URLs** go in speaker notes.
- **Before handover,** put a coverage table in chat that maps each thing the brief asks for to the slide line that answers it.
- **Lint** the slide folder with `--type deck`; it reads `<aside>` as speaker notes.

## Landing page copy

- **Start from the client's own lines:** collect 15 to 20 verbatim strings from their live pages before writing.
- **Headline** in the searcher's or buyer's own words, with one action.
- **Reading level:** Unbounce found pages at a 5th to 7th grade level converted at 11.1%, 56% higher than professional-level pages: https://unbounce.com/conversion-benchmark-report/ . The linter WARNs above grade 9.
- **Words per section:** measure against a page the client already ships, not a generic rule.
- **Brand patterns:** keep the client's own patterns unless the user vetoes one after seeing the evidence.

## Resume

Use your resume skill for content. This skill adds three checks:
- `--type resume` lint
- the dash rule
- the claims table from SKILL.md step 7
