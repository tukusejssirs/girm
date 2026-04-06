#!/usr/bin/env python3
"""extract_la_html.py
Extract Latin IGMR paragraphs, section headings, and footnotes
from src/girm-la/girm-la.html (iglesiaactualidad.wordpress.com).

Structure found in the HTML:
- Paragraph body: <p> starting with "N. text…"
- Section headings: standalone <p> that are short and don't start with a number
- Inline footnote refs: [N] within body text
- Footnote definitions: <p> after §399 with "(N) text…" format
"""

import re, json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "extracted"

with open(ROOT / "src/girm-la/girm-la.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

content = soup.find("article") or soup.find("div", class_="entry-content")
paras   = content.find_all("p")

# ── 1. Find §399 boundary ────────────────────────────────────────────────────
PARA_NUM_RE = re.compile(r"^(\d{1,3})\.\s*(.*)", re.DOTALL)
FN_DEF_RE   = re.compile(r"^\((\d+)\)\s*(.+)", re.DOTALL)
INLINE_FN   = re.compile(r"\[(\d+)\]")

para_399_idx = None
for i, p in enumerate(paras):
    t = p.get_text(strip=True)
    if re.match(r"^399\.", t):
        para_399_idx = i
        break

if para_399_idx is None:
    raise RuntimeError("§399 not found in HTML")

body_paras = paras[:para_399_idx + 1]
fn_paras   = paras[para_399_idx + 1:]

# ── 2. Extract footnote definitions ─────────────────────────────────────────
footnote_defs = {}
for p in fn_paras:
    text = p.get_text(" ", strip=True)
    m = FN_DEF_RE.match(text)
    if m:
        n   = int(m.group(1))
        val = re.sub(r"\s+", " ", m.group(2)).strip()
        footnote_defs[n] = val

print(f"Footnote definitions: {len(footnote_defs)}")

# ── 3. Classify body <p>s: headings vs paragraph text ───────────────────────
# A <p> is a heading if:
#   - It does NOT start with a paragraph number (digits + period)
#   - It is reasonably short (< 120 chars after stripping)
#   - It is not clearly mid-sentence continuation

KNOWN_HEADING_PREFIXES = re.compile(
    r"^(INSTITUTIO|PROEMIUM|Caput|I\.|II\.|III\.|IV\.|V\.|VI\.|VII\.|VIII\.|IX\.|"
    r"[A-Z]\)|\d+°|A\.|B\.|C\.|D\.|E\.|De |Ad |Ritus|Ordo|Lectio|Acclam|Psalm|"
    r"Sanctus|Agnus|Pater|Communio|Conclus|Silentium|Cantus|Gestus|Homo)",
    re.IGNORECASE
)

classified = []  # list of ("heading", text) or ("para", text)
for p in body_paras:
    raw  = p.get_text(" ", strip=True)
    if not raw:
        continue
    pm = PARA_NUM_RE.match(raw)
    if pm:
        classified.append(("para", raw))
    elif (len(raw) < 120
          and not raw.rstrip()[-1] in ".,:;?"
          and not re.search(r'\[\d+\]\s*$', raw)):
        # Short line, no trailing sentence punctuation, no trailing footnote ref = heading
        classified.append(("heading", raw))
    else:
        # Long line, or ends with sentence punctuation = continuation of previous para
        classified.append(("cont", raw))

# ── 4. Parse paragraphs with headings_before ─────────────────────────────────
paragraphs   = {}
pending_hdgs = []
cur_num      = None
cur_lines    = []

def flush():
    global cur_num, cur_lines
    if cur_num is None: return
    body = re.sub(r"\s+", " ", " ".join(cur_lines)).strip()
    # Strip any trailing heading text that leaked in
    # (happens when a heading <p> immediately follows the para text in the HTML
    #  without being on a separate line — the get_text() merges them)
    # We detect this by looking for a known heading pattern at the end
    body = strip_trailing_heading(body)
    # Strip inline footnote refs from display text and record which fns are referenced
    fn_refs = sorted(set(int(n) for n in INLINE_FN.findall(body)))
    body_clean = re.sub(r"\s*\[\d+\]", "", body).strip()
    fns = {str(n): footnote_defs.get(n, "") for n in fn_refs}
    paragraphs[cur_num] = {
        "num": cur_num,
        "text": body_clean,
        "footnotes": fns,
        "source": "la",
        "headings_before": pending_hdgs.copy(),
    }
    pending_hdgs.clear()
    cur_num = None
    cur_lines = []

# Heading patterns that may appear at the end of a paragraph body
HEADING_TAIL_RE = re.compile(
    r"\s+((?:Caput\s+[IVXLC]+|[A-Z][A-Z\s]{4,}(?:\s+[IVXLC]+)?|"
    r"De \w[\w\s]{3,60}|Ad \w[\w\s]{3,50}|"
    r"Ritus\s+\w[\w\s]{2,40}|Lectio\s+\w[\w\s]{2,40}|"
    r"Acclam\w+[\w\s]{0,50}|Psalm\w+[\w\s]{0,50}|"
    r"Ordo\s+\w[\w\s]{2,40}|Cantus\s+\w[\w\s]{2,40}|"
    r"Gestus[\w\s]{0,50}|Communio\w*[\w\s]{0,40}|"
    r"[A-Z]{2,}\s+[A-Z]{2,}[\w\s]{0,60}))$"
)

def strip_trailing_heading(body: str) -> str:
    """Remove section heading text that leaked into the end of a paragraph."""
    m = HEADING_TAIL_RE.search(body)
    if m:
        tail = m.group(1)
        # Only strip if the tail looks like a real heading (all-caps or starts with De/Ad/Ritus…)
        if (tail == tail.upper() and len(tail) > 5) or \
           re.match(r"^(De |Ad |Ritus |Acclam|Psalm|Caput|Lectio|Ordo |Cantus|Gestus|Communio)", tail):
            pending_hdgs.append(tail.strip())
            return body[:m.start()].strip()
    return body

for kind, text in classified:
    if kind == "heading":
        # Store heading; will be attached to next paragraph
        flush()
        pending_hdgs.append(text)
    elif kind == "para":
        pm = PARA_NUM_RE.match(text)
        n  = int(pm.group(1))
        flush()
        cur_num = n
        cur_lines = [pm.group(2).strip()] if pm.group(2).strip() else []
    else:  # continuation
        if cur_num is not None:
            cur_lines.append(text)

flush()  # final paragraph

# ── 5. Report ────────────────────────────────────────────────────────────────
nums    = sorted(paragraphs.keys())
missing = sorted(set(range(1, 400)) - set(paragraphs.keys()))
print(f"Paragraphs: {len(paragraphs)}; range §{min(nums)}–§{max(nums)}")
print(f"Missing: {missing[:10] if missing else 'none'}")
total_hdg = sum(len(p["headings_before"]) for p in paragraphs.values())
total_fns = sum(len(p["footnotes"]) for p in paragraphs.values())
print(f"Section headings assigned: {total_hdg}")
print(f"Inline footnotes resolved: {total_fns}")
print(f"Global footnote defs: {len(footnote_defs)}")

# Spot-check §61
p61 = paragraphs.get(61, {})
print(f"\n§61 tail: {p61.get('text','')[-80:]!r}")
print(f"§62 headings_before: {paragraphs.get(62,{}).get('headings_before',[])}")

# ── 6. Write output ──────────────────────────────────────────────────────────
result = {
    "paragraphs": sorted(paragraphs.values(), key=lambda p: p["num"]),
    "footnotes":  {str(k): v for k, v in sorted(footnote_defs.items())},
}
OUT.mkdir(exist_ok=True)
(OUT / "la.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWritten: extracted/la.json")
