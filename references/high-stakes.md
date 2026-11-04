# High-stakes tier

Use this tier for a job application or take-home, a client deliverable, anything going to an executive, or anything the user calls high-stakes. It answers one question: would the reader think an AI wrote this from the brief alone?

The tier has three parts. Do the first two on any high-stakes piece. The third is for take-homes and pitch documents, where the user's answer competes with what any chat assistant would produce.

## 1. Reader-lens review (always, in this tier)

Start a fresh agent that has never seen this project. Give it three things:
- the brief, or the email or post it replies to
- the reader's role
- the document text

Do not give it your notes, your reasoning or your conclusion.

Prompt:

> You are {reader_role}. You set or received this: {brief_summary}. Read the document below as you would on the day.
> 1. What would you push back on first? Quote the line.
> 2. Which claims would you doubt, and why?
> 3. What did you expect to see that is missing?
> 4. Which sentences tell you nothing new, or explain your own company to you?
> 5. Does it answer every part of what was asked? List each part and where it is answered, or "missing".
> 6. Would you advance or reply to this person? One sentence.

Fix what is real, and say in chat which findings you rejected and why.

In testing, this review caught problems a similarity check cannot:
- a missing cost check
- a metric that rewarded the wrong thing
- an internal word that read wrong to the buyer
- an example number that had lost its "example" label during a cut

A reviewer reading Markdown can't judge page counts, so check pages in the PDF yourself.

## 2. Baselines and sameness check (take-homes, cases, pitch documents)

1. Save the brief as `brief.md`. Strip anything private first. **Never paste the user's resume, emails or private data into another model.**
2. Collect answers to the same brief from several assistants. Ask each one twice: once with a plain prompt, and once with "Act as a world-class expert in this field. Answer it fully so it stands out." Some ways to collect them:
   - ChatGPT logged out, or Gemini in a temporary chat, through the browser. Never click sponsored results, and skip any model that needs an account you don't have.
   - Claude at several sizes with `claude -p --model haiku`, `--model sonnet` and `--model opus`, with the brief on stdin.
3. Save each answer as `baselines/<model>_<plain|expert>.md`.
   - Strip every line that names the vendor or model.
   - Strip coaching tails ("Why this works", "Want me to...").
   - Set the first heading to "# Answer".
4. Write `ideas.json`: the ideas most baselines share. Each idea looks like this:

   ```json
   [{"id": "sem_top3", "label": "Paid search picked as a top-3 channel",
     "patterns": ["(?m)^\\s*[123]\\.\\s*(?:paid search|sem\\b)"],
     "action": "Keep only if your evidence says search is the engine; say what you'd change in it"}]
   ```

5. Run the check:

```
python3 scripts/sameness_check.py --draft draft.md --baselines baselines --ideas ideas.json [--terms terms.txt] --out sameness_report.md
```

It passes when all three hold:
- the draft's topic overlap and reused wording sit below every baseline's leave-one-out score
- the lint tell rate is under 3 per 1,000 words
- the draft's subject-specific evidence (terms from `terms.txt`, or else numbers and proper names) is at least double the baseline median

Wording overlap is weak evidence on its own. LLM answers share ideas far more than sentences: only about 1% to 5% of 5-word phrases are shared. So the ideas table and the blind review carry more weight.

## 3. Blind odd-one-out review

```
python3 scripts/blind_pack.py --draft draft.md --baselines baselines \
  --out blind --key ../blind_KEY.txt --redact "Your Name" --drop-sources --brief brief.md
```

`blind_pack.py` does five things:
- strips names, vendor names, AI-use lines and coaching tails
- renames every title "# Doc X"
- refuses to write the key file inside the review folder
- writes `BRIEF.md`
- exits 1 if anything that could identify a document remains

Then give a fresh agent `blind/BRIEF.md` and the `Doc_*.md` files, with `{reader_role}` and `{brief_summary}` filled in. Never give it the key.

**Pass rule:** the reviewer names the draft as the odd one out for evidence-based reasons, gives it the lowest "AI from the brief alone" probability, and would advance it. If it fails, the review says why: fix that cause, not the score.

## What this tier does not do

It uses no AI-detector APIs. Their error rates are high, and people who judge by feel do little better than chance. The aim is a document that only someone who did the work could write, not one that beats a detector.
