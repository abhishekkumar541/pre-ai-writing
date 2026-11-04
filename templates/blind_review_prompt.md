# Blind odd-one-out review prompt

Fill in `{reader_role}` and `{brief_summary}`. Give it to a fresh agent with `BRIEF.md` and the `Doc_*.md` files from `blind_pack.py`. Never give it the key.

---
You are {reader_role}. You set or received this: {brief_summary}. The documents below answer it. Some were written by AI chat assistants from the brief alone; at most one was written by a person who studied the subject first-hand.

For each document give:
1. Probability (0-100%) it was produced by an AI assistant from the brief alone, and the three strongest reasons.
2. Claims that could only come from first-hand study (quote them, at most 5).
3. Recommendations that appear in most of the other documents (the consensus), at most 5.
4. Whether it makes clear choices (what to stop, what to do first, what it would not do) or lists options.
5. Would you advance or reply to this person? One sentence.

Then name the odd one out and say why. Rank all documents from most to least distinctive.
---

Pass rule: the draft is named the odd one out for evidence-based reasons, gets the lowest "AI from the brief alone" probability, and is the one the reviewer would advance.
