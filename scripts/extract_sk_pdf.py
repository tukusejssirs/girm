#!/usr/bin/env python3
"""extract_sk_pdf.py — extract Slovak VSRM from the two-column PDF."""
import re, json
from pathlib import Path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTChar

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "extracted"

PDF = ROOT / "src/girm-sk/girm-sk-2021.pdf"

PARA_START = re.compile(r"^(\d{1,3})\.\s{1,3}(.+)", re.DOTALL)
FN_START   = re.compile(r"^(\d{1,3})\s+(.+)", re.DOTALL)
PAGE_NUM   = re.compile(r"^\d{1,3}$")
HEADER_RE  = re.compile(r"^(VŠEOBECNÉ SMERNICE|Kapitola|I\.\s+|II\.\s+|III\.\s+|IV\.\s+|"
                         r"Záver|ZÁVER|Ritus|PRÍLOHA)", re.IGNORECASE)

# ── Collect all text boxes across all pages ───────────────────────────────────
all_boxes = []
for page_num, page_layout in enumerate(extract_pages(str(PDF)), 1):
    page_h = page_layout.height
    for box in page_layout:
        if not isinstance(box, LTTextBoxHorizontal):
            continue
        text = box.get_text().strip()
        if not text:
            continue
        # Estimate font size from first char
        font_size = 10
        for element in box:
            for char in element:
                if isinstance(char, LTChar):
                    font_size = char.size
                    break
            break
        all_boxes.append({
            "page":      page_num,
            "x0":        box.x0,
            "y1":        box.y1,
            "text":      text,
            "font_size": font_size,
        })

# Sort: page asc, y1 desc (top-to-bottom), x0 asc (left-to-right)
all_boxes.sort(key=lambda b: (b["page"], -b["y1"], b["x0"]))

# ── Classify boxes ────────────────────────────────────────────────────────────
# Footnote boxes: small font (< 8pt) OR very low on page (y1 < 160) AND contain digits
def is_footnote_box(b):
    # Small font size OR very low on page AND looks like a footnote number
    return b["font_size"] < 8.5 or (b["y1"] < 160 and re.match(r"^\d{1,3}\s+\S", b["text"]))

def is_page_number(b):
    t = b["text"].strip()
    return (PAGE_NUM.match(t) and b["font_size"] < 12) or \
           re.match(r"^\d{1,3}\s+VŠEOBECNÉ", t) or \
           re.match(r"^VŠEOBECNÉ.*\d{1,3}$", t)

def is_heading(b):
    t = b["text"].strip()
    return bool(HEADER_RE.match(t)) and len(t) < 120

# ── Parse paragraphs ──────────────────────────────────────────────────────────
paragraphs   = {}
footnotes    = {}
headings     = {}   # num → list of heading texts before it
pending_hdgs = []
cur_num      = None
cur_parts    = []

def flush():
    global cur_num, cur_parts
    if cur_num is None: return
    text = re.sub(r"\s+", " ", " ".join(cur_parts)).strip()
    # Strip trailing stray footnote numbers
    text = re.sub(r"(\w)\s*\d{1,3}\s*$", r"\1", text).strip()
    paragraphs[cur_num] = {
        "num": cur_num, "text": text,
        "footnotes": {}, "source": "sk",
        "headings_before": pending_hdgs.copy(),
    }
    pending_hdgs.clear()
    cur_num = None; cur_parts = []

fn_cur_num  = None
fn_cur_text = []

def flush_fn():
    global fn_cur_num, fn_cur_text
    if fn_cur_num is None: return
    footnotes[fn_cur_num] = re.sub(r"\s+", " ", " ".join(fn_cur_text)).strip()
    fn_cur_num = None; fn_cur_text = []

for b in all_boxes:
    t = b["text"].strip()
    if not t: continue
    if is_page_number(b): continue

    if is_footnote_box(b):
        # Try to parse as footnote definition
        m = FN_START.match(t)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 200:
                flush_fn()
                fn_cur_num = n
                fn_cur_text = [m.group(2)]
                continue
        if fn_cur_num is not None:
            fn_cur_text.append(t)
        continue

    if is_heading(b):
        flush()
        pending_hdgs.append(t)
        continue

    m = PARA_START.match(t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 399:
            flush()
            cur_num = n
            cur_parts = [re.sub(r"\s+", " ", m.group(2))]
            continue

    if cur_num is not None:
        cur_parts.append(re.sub(r"\s+", " ", t))

flush()
flush_fn()

# ── Report ────────────────────────────────────────────────────────────────────
nums    = sorted(paragraphs.keys())
missing = sorted(set(range(1, 400)) - set(paragraphs.keys()))
print(f"Paragraphs: {len(paragraphs)}; §{min(nums)}–§{max(nums) if nums else '?'}")
print(f"Missing: {missing[:15] if missing else 'none'}")
print(f"Footnotes: {len(footnotes)}")
total_hdg = sum(len(p["headings_before"]) for p in paragraphs.values())
print(f"Headings: {total_hdg}")

result = {
    "paragraphs": sorted(paragraphs.values(), key=lambda p: p["num"]),
    "footnotes":  {str(k): v for k, v in sorted(footnotes.items())},
}
OUT.mkdir(exist_ok=True)
(OUT / "sk.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
print("Written: extracted/sk.json")

for n in [1, 43, 133, 287, 399]:
    p = paragraphs.get(n, {})
    print(f"§{n}: {p.get('text','MISSING')[:90]}")
