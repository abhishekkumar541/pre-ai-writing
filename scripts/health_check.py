#!/usr/bin/env python3
"""Health check for the pre-ai-writing skill. Run: python3 -I scripts/health_check.py

Run it after any rule change, before promoting a learning, and once a month.
Checks:
  1. the test suite passes (FAIL if not)
  2. every rule in references/rules.md names a lint_doc.py check that exists, or says [manual]
  3. learnings.md Open entries, and any older than 30 days
  4. uncommitted changes in the skill's git repo
  5. optional: which files changed since a cleaned public copy was last synced (PRE_AI_PUBLIC_COPY)
     (--mark-synced records the current commit after a push)
Exit codes: 0 no FAIL, 1 at least one FAIL.
"""
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
# Optional: if you keep a private copy of this skill and publish a cleaned one, set PRE_AI_PUBLIC_COPY
# to the public folder. Unset, the sync check is skipped.
PUBLIC = Path(os.environ["PRE_AI_PUBLIC_COPY"]) if os.environ.get("PRE_AI_PUBLIC_COPY") else None
fails, warns = [], []


def git(*args, cwd=SKILL):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


# 1. tests
r = subprocess.run([sys.executable, "-I", str(SKILL / "tests/test_lint_doc.py")], capture_output=True, text=True)
last = (r.stderr.strip().splitlines() or ["no output"])[-1]
ran = re.search(r"Ran (\d+) tests", r.stderr)
(fails if r.returncode else []).append(f"tests: {last}")
print(f"tests      {'OK' if r.returncode == 0 else 'FAILED'} ({ran.group(1) if ran else '?'} tests)")

# 2. rules map to lint checks
lint_src = (SKILL / "scripts/lint_doc.py").read_text()
known = set(re.findall(r'rep\.add\(\s*"([a-z_]+)"', lint_src))
rules = re.findall(r"^## (\d+)\. (.*)$", (SKILL / "references/rules.md").read_text(), re.M)
manual = []
for num, title in rules:
    tag = re.search(r"\[([^\]]+)\]\s*$", title)
    if not tag:
        warns.append(f"rule {num} has no lint id and no [manual] tag")
        continue
    ids = [i.strip() for i in tag.group(1).split(",")]
    if ids == ["manual"]:
        manual.append(num)
        continue
    missing = [i for i in ids if i not in known]
    if missing:
        fails.append(f"rule {num} names lint ids that don't exist: {', '.join(missing)}")
print(f"rules      {len(rules)} rules, {len(rules) - len(manual)} with lint checks, manual: {', '.join(manual) or 'none'}")

# 3. learnings
text = (SKILL / "learnings.md").read_text() if (SKILL / "learnings.md").exists() else ""
open_part = text.split("## Open", 1)[-1].split("## Promoted", 1)[0] if text else ""
entries = re.findall(r"^- (\d{4}-\d{2}-\d{2}) \|.*$", open_part, re.M)
stale = [d for d in entries if (dt.date.today() - dt.date.fromisoformat(d)).days > 30]
if not text:
    warns.append("learnings.md is missing")
if stale:
    warns.append(f"{len(stale)} Open learnings older than 30 days: promote or drop them")
print(f"learnings  {len(entries)} open, {len(stale)} older than 30 days")

# 4. git state
dirty = git("status", "--porcelain")
if dirty:
    warns.append(f"uncommitted changes: {len(dirty.splitlines())} files")
print(f"git        last commit {git('log', '-1', '--format=%cs %s') or 'none'}; {'uncommitted changes' if dirty else 'clean'}")

# 5. public copy drift. The public files are cleaned of personal details, so comparing bytes says
# nothing. Instead .public_sync holds the live commit the public copy last matched.
MARK = SKILL / ".public_sync"
if "--mark-synced" in sys.argv:
    MARK.write_text(git("rev-parse", "HEAD") + "\n")
    print(f"public     marked as synced at {git('rev-parse', '--short', 'HEAD')}")
elif PUBLIC is None or not PUBLIC.exists():
    print("public     no PRE_AI_PUBLIC_COPY set, skipped")
elif not MARK.exists():
    warns.append("public sync point unknown: review every file against the public copy, clean personal details, "
                 "push, then run health_check.py --mark-synced")
    print(f"public     sync point unknown (public last commit {git('log', '-1', '--format=%cs', cwd=PUBLIC)})")
else:
    since = MARK.read_text().strip()
    changed = sorted(set(git("diff", "--name-only", since, "HEAD").splitlines()) - {".public_sync", "learnings.md"})
    if changed:
        warns.append("changed since the last public sync (clean, then copy): " + ", ".join(changed))
    print(f"public     {len(changed)} files changed since last sync at {since[:7]}")

for w in warns:
    print("WARN ", w)
for f in fails:
    print("FAIL ", f)
sys.exit(1 if fails else 0)
