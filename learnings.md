# Learnings log

Every correction the user makes to text this skill produced goes here first, not straight into `references/rules.md`. A one-off fix for one client or one brief should not become a rule for every document.

## How an entry moves

1. **Log.** At handover, add one entry under Open for each correction the user made: the date, the document, what was wrong, their words if they gave any, and the general rule it might become.
2. **Promote** an Open entry to a rule only when one of these is true:
   - the same kind of correction has come up a second time, in a different document, or
   - the user says it should be a rule.
3. **When promoting,** in one commit:
   - add the rule to `references/rules.md` with a real before and after,
   - add a `scripts/lint_doc.py` check with a test that fires and a near-miss test that stays quiet, or tag the rule `[manual]` and write in it why the linter can't check it,
   - run `python3 -I scripts/health_check.py` and get exit code 0,
   - move the entry to Promoted with the rule number.
4. **Drop** an entry when it turns out to be specific to one client or brief. Move it to Dropped with the reason.

Entry format:

```
- YYYY-MM-DD | document | what was wrong | the user's words, or "none" | candidate rule
```

Example:

```
- 2026-03-02 | Acme pricing memo | "Fund / Don't fund" labels where the brief said "invest" | "nobody says fund in an assignment" | use the brief's own decision verb
```

## Open

(none yet)

## Promoted

(none yet)

## Dropped

(none yet)
