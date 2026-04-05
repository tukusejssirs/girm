#!/usr/bin/env python3
"""
extract_uk_pdf_fns.py — extract all UK PDF footnotes using spatial layout.

Structure A: left col (x<100) = fn numbers, right col (x 100-130) = fn texts,
             separated by citation-start patterns.
Structure B: "NNN Citation text..." on a single line (two-column PDF artefact).
"""

import re
from pathlib import Path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LTAnno

PDF = Path(__file__).parent / "src/girm-uk/girm-uk-2011.pdf"

# Patterns that reliably start a new footnote entry within a combined text block
CITE_START_RE = re.compile(
    r'\n\s*(?='
    r'Ecumenical Council|Second Ecumenical|Cf\.|cf\. ibidem|'
    r'Sacred Congregation|Pontifical Commission|'
    r'Ibidem|ibidem|Code of Canon|'
    r'Paul [Vv]I|John Paul II|Pius XII|Pius X[I ]|'
    r'John XXIII|Benedict [Xx][Vv]|'
    r'Evening Mass|Decree on|Solemn Profession|'
    r'Caeremoniale|Pontificale Romanum|Rituale Romanum|'
    r'Ordo |Missale Romanum|Institutio Generalis|Graduale|'
    r'Interdicasterial|Congregation for Divine|'
    r'Apostolic Letter|Apostolic Constitution|'
    r'St\. Augustine|Universal Norms|'
    r'Denzinger)'
)

# Structure B: fn number embedded with text on same line
STRUCT_B_RE = re.compile(
    r'^(\d{1,3})\s+'
    r'(Cf\.|Second |Sacred |Pontifical |Ibidem|ibidem|'
    r'Code |Paul [Vv]|John Paul|Pius |St\. |Caeremoniale|Pontificale|'
    r'Rituale|Ordo |Missale|Institutio|Graduale|Interdicasterial|'
    r'Congregation for|Evening Mass|Apostolic |'
    r'cf\. ibidem|Universal Norms|Denzinger)'
)


def _box_text(el):
    t = ""
    for line in el:
        if not isinstance(line, LTTextLine): continue
        for ch in line:
            t += ch.get_text() if isinstance(ch, (LTChar, LTAnno)) else ""
    return t


def _clean(text):
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)  # rejoin hyphens
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract():
    fn_map = {}

    for page_num, page in enumerate(extract_pages(PDF), 1):
        boxes = []
        for el in page:
            if not isinstance(el, LTTextBox): continue
            t = _box_text(el)
            if t.strip():
                x0, y0, x1, y1 = el.bbox
                boxes.append((float(x0), float(y0), float(y1), t))

        # ── Structure B (whole page) ──────────────────────────────────────────
        for x0, y0, y1, text in boxes:
            for line in text.split('\n'):
                m = STRUCT_B_RE.match(line.strip())
                if m:
                    fn_n = int(m.group(1))
                    if 1 <= fn_n <= 165 and fn_n not in fn_map:
                        rest = _clean(line.strip()[len(m.group(1))+1:])
                        if rest:
                            fn_map[fn_n] = rest

        # ── Structure A ───────────────────────────────────────────────────────
        # Num column: x < 100, y_top < 230 (raised from 200 to catch fn22, fn32 etc.)
        num_boxes = [(float(y1), float(y0), text)
                     for x0, y0, y1, text in boxes
                     if x0 < 100 and y1 < 230]
        if not num_boxes: continue

        num_y_max = max(e[0] for e in num_boxes)
        num_y_min = min(e[1] for e in num_boxes)

        # Text column: x in [100, 130], y_top ≤ num_y_max + 20
        # (no lower-bound on y0 — text boxes can extend to page bottom margin)
        text_boxes = [(float(y1), float(y0), text)
                      for x0, y0, y1, text in boxes
                      if 100 <= x0 <= 130
                      and y1 <= num_y_max + 20]
        if not text_boxes: continue

        # Extract fn numbers top→bottom
        num_boxes.sort(key=lambda e: -e[0])
        fn_nums = []
        for y1, y0, text in num_boxes:
            for n_str in re.findall(r'\b(\d{1,3})\b', text):
                n = int(n_str)
                if 1 <= n <= 165:
                    fn_nums.append(n)
        if not fn_nums: continue

        # Merge text boxes top→bottom
        text_boxes.sort(key=lambda e: -e[0])
        combined = "".join(t for _, _, t in text_boxes)

        # Split into per-fn texts
        parts = CITE_START_RE.split(combined)
        clean_parts = [_clean(p) for p in parts if p.strip()]

        # Assign in order to fn_nums
        for i, fn_n in enumerate(fn_nums):
            if fn_n not in fn_map and i < len(clean_parts):
                fn_map[fn_n] = clean_parts[i]

    return fn_map


if __name__ == "__main__":
    fm = extract()
    missing = sorted(set(range(1, 166)) - set(fm))
    print(f"Extracted: {len(fm)}/165  Missing: {missing or 'none'}")
    print()
    for n in [1, 2, 3, 7, 22, 32, 33, 48, 49, 50, 51, 52,
              63, 64, 71, 72, 96, 101, 107, 123, 126, 136, 145, 152, 153, 165]:
        print(f"  fn{n:3d}: {fm.get(n, 'MISSING')[:100]}")
