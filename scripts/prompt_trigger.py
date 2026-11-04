#!/usr/bin/env python3
"""UserPromptSubmit hook for the pre-ai-writing skill.

Reads the hook JSON on stdin. If the prompt asks to draft, rewrite or review a document someone else
will read (email, post, cover letter, memo, deck, resume, landing page...), it adds a one-line reminder
to use the skill. Otherwise it prints nothing. Local keyword match only: no network, no model call.
Never blocks the prompt; any error exits 0 silently.
"""
import json
import re
import sys

DOC = re.compile(
    r"\b(?:e-?mails?|cold email|follow[- ]?up|linkedin|(?:social|blog) post|post (?:for|on|about)|a post\b|tweet|thread|"
    r"cover letter|letter|memo|brief|one[- ]pager|report|proposal|deck|slides?|presentation|resume|cv|bio|"
    r"take[- ]home|case study|assignment|landing page|website copy|web copy|copy for|newsletter|press release|"
    r"message (?:to|for)|reply to|response to|doc(?:ument)?|write[- ]?up|summary for)\b", re.I)
VERB = re.compile(
    r"\b(?:write|draft|re-?write|redo|edit|polish|review|improve|tighten|proofread|humani[sz]e|prepare|create|make|"
    r"compose|turn .{1,60} into|reply|respond|send|fix|shorten|refine|finali[sz]e)\b", re.I)
# Reading or searching mail is not drafting.
NOT_DRAFTING = re.compile(r"\b(?:inbox|unread|search (?:my|for)|find (?:my|the)|look up|read my|summari[sz]e (?:my|these|the) e-?mails?)\b", re.I)
CODE = re.compile(
    r"\b(?:python|javascript|typescript|function|script|regex|code|bug|sql|api|json|yaml|html|css|commit message|"
    r"unit test|stack trace|error message|terminal|shell|cli)\b", re.I)
CONTEXT = ("This request looks like text someone other than the user will read. Invoke the pre-ai-writing skill "
           "before drafting or reviewing it (it calls humanizer itself). Skip it only if this is a chat reply, "
           "research notes, a plan or code.")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = str(data.get("prompt") or "")
    head = prompt[:1500]
    if not head.strip() or head.lstrip().startswith("/") or "pre-ai-writing" in head:
        return 0
    if CODE.search(head) or NOT_DRAFTING.search(head) or not DOC.search(head) or not VERB.search(head):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CONTEXT}}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
