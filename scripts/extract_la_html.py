#!/usr/bin/env python3
"""extract_la_html.py — extract Latin IGMR paragraphs from src/girm-la/girm-la.html"""

import re, json, textwrap
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "extracted"

with open(ROOT / "src/girm-la/girm-la.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

content = soup.find("article") or soup.find("div", class_="entry-content")
raw = content.get_text("\n", strip=True)

# Parse: paragraphs are numbered "N." at start of line (after stripping)
lines = [l.strip() for l in raw.split("\n") if l.strip()]

PARA_START = re.compile(r"^(\d{1,3})\.\s*$")  # bare number on its own line
PARA_INLINE = re.compile(r"^(\d{1,3})\.\s+(.+)")
FOOTNOTE_RE = re.compile(r"^\[(\d+)\]\s*(.+)")
BARE_FN     = re.compile(r"^\[(\d+)\]\s*$")

paragraphs = {}
footnotes  = {}
cur_num    = None
cur_lines  = []
fn_buf_num = None
fn_buf_txt = ""
state      = "body"

def flush():
    global cur_num, cur_lines, fn_buf_num, fn_buf_txt, state
    if cur_num is None: return
    body = " ".join(cur_lines)
    paragraphs[cur_num] = {"num": cur_num, "text": body,
                           "footnotes": {}, "source": "la",
                           "headings_before": []}
    cur_num = None; cur_lines = []; fn_buf_num = None; fn_buf_txt = ""; state = "body"

def flush_fn():
    global fn_buf_num, fn_buf_txt
    if fn_buf_num is not None and fn_buf_txt:
        footnotes[fn_buf_num] = fn_buf_txt.strip()
    fn_buf_num = None; fn_buf_txt = ""

i = 0
while i < len(lines):
    s = lines[i]
    i += 1

    # Detect footnote blocks (typically appear after paragraph text)
    fn_m = FOOTNOTE_RE.match(s)
    if fn_m:
        flush_fn()
        fn_buf_num = int(fn_m.group(1))
        fn_buf_txt = fn_m.group(2)
        state = "fn"
        continue

    bare_fn_m = BARE_FN.match(s)
    if bare_fn_m:
        flush_fn()
        fn_buf_num = int(bare_fn_m.group(1))
        fn_buf_txt = ""
        state = "fn"
        continue

    # Bare paragraph number on its own line
    pm = PARA_START.match(s)
    if pm:
        flush_fn()
        flush()
        cur_num = int(pm.group(1))
        state = "body"
        # Next line is the body
        continue

    # Inline "N. text..."
    inl = PARA_INLINE.match(s)
    if inl:
        n = int(inl.group(1))
        if 1 <= n <= 399:
            flush_fn()
            flush()
            cur_num = n
            cur_lines = [inl.group(2)]
            state = "body"
            continue

    # continuation
    if state == "fn" and fn_buf_num is not None:
        fn_buf_txt += " " + s
    elif state == "body" and cur_num is not None:
        cur_lines.append(s)

flush_fn()
flush()

nums = sorted(paragraphs.keys())
missing = sorted(set(range(1, 400)) - set(paragraphs.keys()))
print(f"Extracted {len(paragraphs)} paragraphs; range §{min(nums)}–§{max(nums)}")
print(f"Missing: {missing[:10] if missing else 'none'}")
print(f"Footnotes: {len(footnotes)}")

result = {
    "paragraphs": sorted(paragraphs.values(), key=lambda p: p["num"]),
    "footnotes": {str(k): v for k, v in sorted(footnotes.items())}
}
OUT.mkdir(exist_ok=True)
(OUT / "la.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Written: extracted/la.json")

# Sample check
for n in [1, 43, 100, 274, 399]:
    p = paragraphs.get(n)
    if p: print(f"\n§{n}: {p['text'][:120]}")
