# Where evidence goes

Writers who trace every claim and print every URL in full still don't want that bookkeeping in front of the reader. Keep the bookkeeping in notes, and give the document clean citations.

## In the document

- **Name the source in the sentence** when it matters to the reader. For example: "Acme's CEO told TechCrunch in March 2021 that...", or "Google's own help page says Target ROAS needs 15 conversions in 30 days".
- **Cite with [n].** The body never shows a URL. The numbered `## Sources` list at the end gives each entry in this order:
  - publisher or author
  - date, if known
  - what it is
  - the full raw URL

  Number sources in order of first use.
- **One dating line**, in Assumptions, not "as of" (Humanizer 23): "Everything about Acme comes from its public pages as they stood between 2 and 4 March."
- **Assumptions up front.** Say which numbers are examples, then use them as plain numbers.
- **Flag a shaky fact in plain words, once, beside the fact:** "this survey is of software buyers, not CPG founders". Never use a status word.
- **Cite only what changes the decision.** Two or three strong sources per section beat a stack of six.
- **Emails, posts and cover letters** carry at most one link and no Sources list. Name the source in the sentence if one is needed.

## In the notes (`<name>_notes.md`, chat, or speaker notes)

- **Status labels** (Confirmed, Supported, Unconfirmed, Disputed) per claim, with the URL and exact location.
- **A material-number table:** `Claim | Value | Status | Source URL | Page | Location | Verified directly?`
- **The brief-coverage table:** what the brief asks for, and where it is answered.
- **The claims-about-the-writer table** (SKILL.md step 7).
- **Access dates per source**, and anything you couldn't open.

## Checks before handover

- Every [n] in the body has a Sources entry with a full raw URL. The linter FAILs `ref_without_source` and `source_without_raw_url`.
- Every Sources entry is cited at least once (WARN `source_not_cited`).
- Every number in the document matches the notes table.
- **Recheck each cited location before delivery.** If one fails, retract the number and everything built on it.
