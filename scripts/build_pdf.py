#!/usr/bin/env python3
"""build_pdf.py: Markdown to a clean, print-ready PDF (pre-ai-writing skill).

Use only when the user asks for a PDF or the deliverable is a PDF. It uses Inter, real tables, bare URLs turned into links, a footer with page numbers,
printed by headless Chrome. After printing it checks the PDF is not empty and has no dashes.

Usage (no -I: it imports the third-party `markdown` package):
  python3 build_pdf.py in.md out.pdf [--title T] [--footer-left TEXT] [--html out.html]
                       [--paper Letter|A4] [--overwrite]
Exit 0 = built and checked, 1 = built but a check failed, 2 = usage or build error.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

def find_chrome():
    """CHROME_PATH wins; then the usual macOS app; then chrome or chromium on PATH."""
    import os
    cands = [os.environ.get("CHROME_PATH", ""), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    cands += [shutil.which(n) or "" for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")]
    return next((c for c in cands if c and Path(c).exists()), "")


CHROME = find_chrome()


def css_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def autolink(m):
    url, trail = m.group(0), ""
    while url and url[-1] in ".,;:":
        trail, url = url[-1] + trail, url[:-1]
    return f"<{url}>{trail}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown to PDF via headless Chrome.")
    ap.add_argument("src")
    ap.add_argument("out_pdf")
    ap.add_argument("--title", default=None, help="HTML title; defaults to the first heading")
    ap.add_argument("--footer-left", default="", help="footer text on every page; page number sits bottom right")
    ap.add_argument("--html", default=None, help="where to keep the HTML; default next to the PDF")
    ap.add_argument("--paper", default="Letter", choices=["Letter", "A4"])
    ap.add_argument("--overwrite", action="store_true", help="replace an existing PDF (revisions should be new versions)")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        import markdown
    except ImportError:
        print("build_pdf: the 'markdown' package is missing. Run without -I, or: python3 -m pip install --user markdown",
              file=sys.stderr)
        return 2
    src, out_pdf = Path(a.src).resolve(), Path(a.out_pdf).resolve()
    out_html = Path(a.html).resolve() if a.html else out_pdf.with_suffix(".html")
    if not src.is_file():
        print(f"build_pdf: no such file {src}", file=sys.stderr)
        return 2
    if out_pdf.exists() and not a.overwrite:
        print(f"build_pdf: {out_pdf} exists. Write a new version, or pass --overwrite.", file=sys.stderr)
        return 2
    if not CHROME:
        print("build_pdf: Chrome or Chromium not found; set CHROME_PATH", file=sys.stderr)
        return 2

    text = src.read_text(encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = a.title or (m.group(1).strip() if m else src.stem)
    text = re.sub(r"(?<![<(\[])https?://[^\s)<>|]+", autolink, text)
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    footer = f"@bottom-left {{ content: {css_string(a.footer_left)}; font-family: Inter, Arial, sans-serif; font-size: 8.5pt; color: #6B7180 }}" if a.footer_left else ""
    css = f"""
@page {{ size: {a.paper}; margin: 0.7in 0.75in 0.8in;
  @bottom-right {{ content: counter(page); font-family: Inter, Arial, sans-serif; font-size: 8.5pt; color: #6B7180 }}
  {footer} }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact }}
body {{ font-family: Inter, Arial, Helvetica, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #17191F; margin: 0 }}
h1 {{ font-size: 16pt; line-height: 1.25; margin: 0 0 10px; letter-spacing: -0.2px; break-before: page }}
h1:first-of-type {{ font-size: 22pt; break-before: auto; margin-bottom: 14px }}
h2 {{ font-size: 12.5pt; margin: 18px 0 6px; break-after: avoid }}
h3 {{ font-size: 11pt; margin: 14px 0 4px; break-after: avoid }}
p {{ margin: 0 0 8px }}
ul {{ margin: 0 0 8px; padding-left: 20px }}
ol {{ margin: 0 0 8px; padding-left: 2.2em }}
.page-break {{ break-before: page }}
li {{ margin: 0 0 3px }}
table {{ border-collapse: collapse; width: 100%; margin: 6px 0 12px; font-size: 9pt; line-height: 1.4 }}
th, td {{ border: 1px solid #CFCBC0; padding: 5px 7px; vertical-align: top; text-align: left }}
th {{ background: #F3F1EA; font-weight: 600 }}
tr {{ break-inside: avoid }}
blockquote {{ margin: 8px 0 12px; padding: 10px 16px; background: #FFFDF2; border-left: 3px solid #FDE047; break-inside: avoid }}
blockquote p {{ margin: 0 0 6px }}
a {{ color: #1a5fb4; text-decoration: none; overflow-wrap: anywhere }}
strong {{ font-weight: 600 }}
"""
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;")
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>{safe_title}</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap">'
            f"<style>{css}</style></head><body>{body}</body></html>")
    out_html.write_text(html, encoding="utf-8")
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=9000", "--no-pdf-header-footer",
                        f"--print-to-pdf={out_pdf}", f"file://{out_html}"], capture_output=True)
    if not out_pdf.exists() or out_pdf.stat().st_size < 2000:
        print(f"build_pdf: Chrome did not write a usable PDF (exit {r.returncode})", file=sys.stderr)
        return 2

    problems = []
    pages = "?"
    if shutil.which("pdfinfo"):
        info = subprocess.run(["pdfinfo", str(out_pdf)], capture_output=True, text=True).stdout
        mm = re.search(r"^Pages:\s+(\d+)", info, re.M)
        pages = mm.group(1) if mm else "?"
    if shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", "-layout", str(out_pdf), "-"], capture_output=True, text=True).stdout
        if len(txt.split()) < 20:
            problems.append("almost no text in the PDF")
        d = len(re.findall("[\u2014\u2013]", txt))
        if d:
            problems.append(f"{d} em or en dashes in the PDF text")
    else:
        problems.append("pdftotext not found, text checks skipped")
    if shutil.which("pdffonts"):
        fonts = subprocess.run(["pdffonts", str(out_pdf)], capture_output=True, text=True).stdout
        if "Inter" not in fonts:
            problems.append("Inter not embedded (check the network; Arial fallback used)")
    print(f"build_pdf: {out_pdf} ({pages} pages); HTML at {out_html}")
    for p in problems:
        print(f"build_pdf: check: {p}")
    print("build_pdf: now look at the page images before handing it over.")
    return 1 if any("dash" in p or "no text" in p for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main())
