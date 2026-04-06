#!/usr/bin/env python3
"""extract.py — three GIRM sources → extracted/*.json"""

import json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "extracted"
OUT.mkdir(exist_ok=True)

PARA_RE     = re.compile(r"^(\d{1,3})\.\s+")
BARE_NUM_RE = re.compile(r"^(\d{1,3})$")

# Only patterns that reliably start a NEW footnote (not continuation lines)
CITE_START = re.compile(
    r"^(Cf\.|Second Ecumenical|Ecumenical Council|Paul VI,? Encyclical|"
    r"Paul VI,? Apostolic (Constitution|Letter) [A-Z]|"
    r"John Paul II|Benedict XVI|Francis,?|"
    r"Congregation for|Sacred Congregation|Pontifical Commission|"
    r"Ibidem|ibidem|Code of Canon|Evening Mass|"
    r"Tertullian|Origen|Statuta|St\. Augustine|"
    r"Caeremoniale Episcoporum|Pontificale Romanum|Rituale Romanum|"
    r"Ordo (coronandi|Exsequiarum|lectionum)|Missale Romanum,? editio|"
    r"Institutio Generalis|Graduale (Romanum|Simplex)|"
    r"Interdicasterial Instruction)"
)

CHAPTER_STARTS = {
    1:   (0, "Introduction"),
    16:  (1, "Chapter I: The Importance and Dignity of the Celebration of the Eucharist"),
    27:  (2, "Chapter II: The Structure of the Mass, Its Elements and Its Parts"),
    91:  (3, "Chapter III: Duties and Ministries in the Mass"),
    112: (4, "Chapter IV: The Different Forms of Celebrating Mass"),
    288: (5, "Chapter V: The Arrangement and Ornamentation of Churches for the Celebration of the Eucharist"),
    319: (6, "Chapter VI: The Requisites for the Celebration of Mass"),
    352: (7, "Chapter VII: The Choice of the Mass and Its Parts"),
    368: (8, "Chapter VIII: Masses and Prayers for Various Needs and Occasions and Masses for the Dead"),
    386: (9, "Chapter IX: Adaptations within the Competence of Bishops and Bishops\u2019 Conferences"),
}

# ── Shared helpers ────────────────────────────────────────────────────────────

def to_unicode_quotes(text):
    if not text: return text
    text = re.sub(r"[\u0027\u0060\u02BC\u2018]", "\u2019", text)  # ' ` ʼ ' → '
    text = re.sub(r'[\u0022\u201A\u201B\u201E]',  "\u201C", text)  # " variants → "
    return text

def convert_inline(node, fn_pat):
    if isinstance(node, NavigableString): return str(node)
    if not isinstance(node, Tag):        return ""
    result = ""
    for child in node.children:
        ct = convert_inline(child, fn_pat)
        if isinstance(child, Tag):
            n = child.name
            if n in ("i","em"):
                s = ct.strip()
                if s and not re.fullmatch(r"[;:.,\-–—()\s\d\[\]]+", s):
                    # Preserve surrounding spaces but not inside the asterisks
                    leading  = ct[:len(ct)-len(ct.lstrip())]
                    trailing = ct[len(ct.rstrip()):]
                    result += f"{leading}*{s}*{trailing}"
                else: result += ct
            elif n in ("b","strong"): result += f"**{ct}**" if ct.strip() else ct
            elif n == "a":
                href = child.get("href","")
                m = fn_pat.search(href)
                result += f"[^{m.group(1)}]" if m else ct
            elif n == "br": result += " "
            else: result += ct
        else: result += ct
    return result

def strip_md(t):
    return re.sub(r"\[\^\d+\]|\*\*?([^*]+)\*\*?", r"\1", t).strip()

def make_para(num, body, source):
    p = {"num": num, "text": body, "footnotes": {}, "source": source}
    if num in CHAPTER_STARTS:
        p["chapter"], p["chapter_title"] = CHAPTER_STARTS[num]
    return p

# ── Section heading exclusion set (populated after US is extracted) ───────────

def load_heading_texts():
    us_path = ROOT / "extracted/us.json"
    if not us_path.exists(): return set()
    _us = json.loads(us_path.read_text(encoding="utf-8"))
    ht = set()
    SKIP = {"Breadcrumb","Footnotes","Dive into God\u2019s Word",
            "About USCCB","Topics","Prayer & Worship",
            "Get Involved to Act Now","Quick Links"}
    for _p in _us["paragraphs"]:
        for _, htext in _p.get("headings_before", []):
            if htext not in SKIP:
                ht.add(htext)
                if htext.startswith("The "): ht.add(htext[4:])
    return ht

# ── Section header pattern (to exit fn_text state cleanly) ───────────────────

SECTION_HDR = re.compile(
    r"^(Chapter (I{1,3}|IV|VI{0,3}|IX)\b|"
    r"(I{1,3}|IV|VI{0,3}|IX)[i.]?\.$|"
    r"(A|B|C|D)\.\s+(Mass (with|without)|The Introductory|The Liturgy)|"
    r"Things to Be Prepared$|"
    r"(The )?(Introductory Rites|Liturgy of the Word|Liturgy of the Eucharist|"
    r"Concluding Rites|Preparation of the Gifts|Eucharistic Prayer|"
    r"Communion Rite|Lord\u2019s Prayer|Rite of Peace|Fraction|"
    r"Introductory Rites|Penitential Act|Gloria|Collect|Homily)$)",
    re.I
)

# Running header from PDF page breaks
RUNNING_HDR = re.compile(
    r"^(Introduction \d+|\d+ General Instruction|"
    r"General Instruction of the Roman Missal \d+|"
    r"The (Importance|Structure|Arrangement|Requisites|Choice|Different Forms|"
    r"Duties|Masses).*\d+|Adaptations.*\d+|"
    r"Contents (iii|iv|v|vi|\d+)|Chapter (I{1,3}|IV|VI{0,3}|IX) \d+)$"
)

# Inline footnote ref at end of word: "Mass.34" → "Mass.[^34]"
INLINE_FN = re.compile(r"([A-Za-z.,:;)\u2019\u201D])(\d{1,3})(?=\s|$|[,.\)])") 

# ── UK extraction ─────────────────────────────────────────────────────────────

def extract_uk():
    print("Extracting UK...", file=sys.stderr)

    # -- Italic phrases from pdfminer --
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LTAnno
    ITALIC = "MinionPro-It"
    raw_italic = {}
    cur_font, cur_text = None, ""
    for page in extract_pages(ROOT / "src/girm-uk/girm-uk-2011.pdf"):
        for el in page:
            if not isinstance(el, LTTextBox): continue
            for line in el:
                if not isinstance(line, LTTextLine): continue
                for ch in line:
                    if isinstance(ch, LTChar):
                        short = ch.fontname.split("+")[-1]
                        if short != cur_font:
                            if cur_font and ITALIC in cur_font:
                                p = cur_text.strip()
                                if p: raw_italic[p] = raw_italic.get(p,0)+1
                            cur_font, cur_text = short, ch.get_text()
                        else: cur_text += ch.get_text()
                    elif isinstance(ch, LTAnno): cur_text += ch.get_text()

    HEADING_TEXTS = load_heading_texts()
    COMMON = {"and","the","or","in","of","to","a","an","be","is","are","was","were",
              "it","its","by","for","at","as","on","not","all","but","from","with",
              "Lk","Mt","etc","etc.","sic"}
    italic_ok = {
        p for p in raw_italic
        if len(p) > 3
        and not re.fullmatch(r"[;:.,\-\u2013\u2014()\s\d\[\]]+", p)
        and p.lower() not in COMMON
        and not all(w.lower() in COMMON for w in p.split())
        and p not in HEADING_TEXTS
    }
    print(f"  UK italic phrases: {len(italic_ok)}", file=sys.stderr)

    def italicise(text):
        for phrase in sorted(italic_ok, key=len, reverse=True):
            if phrase in text:
                text = re.sub(rf"(?<!\w)(?<!\*){re.escape(phrase)}(?!\w)(?!\*)",
                              f"*{phrase}*", text)
        return text

    def strip_trailing_headings(text):
        for htext in sorted(HEADING_TEXTS, key=len, reverse=True):
            for suf in (f" *{htext}*", f" {htext}"):
                if text.endswith(suf):
                    text = text[:-len(suf)].rstrip()
        return text

    # ── Two-pass UK parser ────────────────────────────────────────────────────
    # Pass 1: collect paragraphs + global fn text dict
    # Pass 2: assign fn texts to paragraphs based on inline [^N] refs

    lines = (ROOT / "src/girm-uk/girm-uk-2011-clean.txt").read_text(encoding="utf-8").splitlines()

    paragraphs  = {}   # num → para dict (footnotes empty)
    # ── Use spatial PDF extractor for all footnote texts ────────────────────
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from extract_uk_pdf_fns import extract as _extract_pdf_fns
    global_fns = {fn_n: to_unicode_quotes(text)
                  for fn_n, text in _extract_pdf_fns().items()}
    print(f"  UK spatial fn extraction: {len(global_fns)} footnotes", file=_sys.stderr)

    standalone_fn_owner = {}  # fn_num → para_num (still used for pass-2 assignment)
    cur_num     = None
    cur_text    = []
    fn_queue    = []   # bare fn numbers collected in current batch
    fn_buf_num  = None # fn currently being accumulated
    state       = "body"  # body | fn_queue | fn_text

    def flush():
        nonlocal cur_num, cur_text, fn_queue, fn_buf_num, state
        if cur_num is None: return
        body = " ".join(t.strip() for t in cur_text if t.strip())
        body = INLINE_FN.sub(lambda m: f"{m.group(1)}[^{m.group(2)}]", body)
        body = italicise(body)
        body = strip_trailing_headings(body)
        body = to_unicode_quotes(body)
        paragraphs[cur_num] = make_para(cur_num, body, "uk")
        cur_num = None; cur_text = []; fn_queue = []; fn_buf_num = None; state = "body"

    for raw in lines:
        s = raw.strip()

        # New paragraph
        m = PARA_RE.match(s)
        bare_p = re.match(r"^(\d{1,3})\.$", s) if not m else None
        if bare_p and int(bare_p.group(1)) > 399: bare_p = None
        if m or bare_p:
            flush()
            state = "body"
            cur_num = int((m or bare_p).group(1))
            first = s[len(m.group(0)):] if m else ""
            cur_text = [first] if first else []
            continue

        # Running headers
        if RUNNING_HDR.match(s): continue

        if cur_num is None: continue

        # Blank line
        if not s:
            if state == "fn_text" and fn_buf_num is not None:
                fn_buf_num = None  # end of this fn's text; next will assign to next
            continue

        # Bare footnote number
        bm = BARE_NUM_RE.match(s)
        if bm:
            fn_n = int(bm.group(1))
            if fn_n <= 399 and state in ("body", "fn_queue"):
                # Skip if this fn already has text (duplicate standalone ref)
                if global_fns.get(fn_n):
                    continue
                fn_queue.append(fn_n)
                standalone_fn_owner[fn_n] = cur_num  # default owner = current para
                state = "fn_queue"
                continue
            continue  # page number or out-of-range, ignore

        # Structure B: "NNN citation text" on ONE line (two-column PDF artefact)
        # e.g. "102 Cf. Sacred Congregation..."
        struct_b = re.match(
            r"^(\d{1,3}) (Cf\.|Second |Sacred |Pontifical |Ibidem|ibidem|"
            r"Code |Paul VI|John Paul|St\. |Caeremoniale|Pontificale|Rituale|"
            r"Ordo |Missale|Institutio|Graduale|Interdicasterial|"
            r"Congregation for|Evening Mass|Tertullian|Origen|Apostolic Letter)", s
        )
        if struct_b:
            fn_n = int(struct_b.group(1))
            if fn_n <= 399 and not global_fns.get(fn_n):
                fn_text = s[len(struct_b.group(1))+1:].strip()
                global_fns[fn_n] = fn_text
                standalone_fn_owner[fn_n] = cur_num
                continue

        # Text line
        if state == "fn_queue":
            state = "fn_text"
            fn_buf_num = fn_queue[0] if fn_queue else None

        if state == "fn_text":
            if fn_buf_num is not None:
                # Exit fn_text entirely if this looks like a section header
                if SECTION_HDR.match(s):
                    state = "body"
                    continue
                # Advance fn_buf_num through queue using CITE_START
                # (global_fns already populated by spatial extractor; just tracking position)
                if CITE_START.match(s):
                    idx = fn_queue.index(fn_buf_num) + 1
                    if idx < len(fn_queue):
                        fn_buf_num = fn_queue[idx]
                # Do NOT append to global_fns — text already set by spatial extractor
            else:
                # Blank ended previous fn; assign to next unassigned
                for fn_n in fn_queue:
                    if not global_fns.get(fn_n):
                        fn_buf_num = fn_n
                        global_fns[fn_n] = s
                        break
                else:
                    # All assigned → body continuation or section header
                    state = "body"
                    if not SECTION_HDR.match(s):
                        cur_text.append(s)
            continue

        # Body
        cur_text.append(s)

    flush()

    # Pass 2: assign fn texts to paragraphs by inline [^N] refs + standalone ownership
    for para in paragraphs.values():
        refs = [int(m) for m in re.findall(r"\[\^(\d+)\]", para["text"])]
        for ref in refs:
            if ref in global_fns:
                para["footnotes"][str(ref)] = to_unicode_quotes(global_fns[ref])

    # Also assign standalone fns (no inline ref) to their owner paragraph
    for fn_n, owner_num in standalone_fn_owner.items():
        if fn_n in global_fns and owner_num in paragraphs:
            # Only assign if NOT already assigned via inline ref scan
            if str(fn_n) not in paragraphs[owner_num]["footnotes"]:
                # Check no OTHER paragraph claimed it via inline ref
                already_claimed = any(
                    str(fn_n) in p["footnotes"]
                    for p in paragraphs.values()
                )
                if not already_claimed:
                    paragraphs[owner_num]["footnotes"][str(fn_n)] = to_unicode_quotes(global_fns[fn_n])

    result = {"paragraphs": sorted(paragraphs.values(), key=lambda x: x["num"]),
              "footnotes": {str(k): to_unicode_quotes(v) for k,v in global_fns.items()}}
    print(f"  UK: {len(paragraphs)} paragraphs, {len(global_fns)} fn texts", file=sys.stderr)
    missing = sorted(set(range(1,400)) - set(paragraphs))
    if missing: print(f"  UK missing: {missing[:10]}", file=sys.stderr)
    return result


# ── Vatican 2003 ──────────────────────────────────────────────────────────────

def extract_va():
    print("Extracting Vatican HTML...", file=sys.stderr)
    html = (ROOT / "src/girm-va.html").read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    FN_PAT = re.compile(r"_ftn(\d+)$")

    footnotes = {}
    for a in soup.find_all("a", attrs={"name": re.compile(r"^_ftn\d+$")}):
        fn_m = re.search(r"_ftn(\d+)", a.get("name",""))
        if not fn_m: continue
        parent = a.find_parent(["p","li","div"])
        if parent:
            fn_num = int(fn_m.group(1))
            fn_text = re.sub(r"^\[\d+\]\s*", "", parent.get_text(" ", strip=True))
            footnotes[fn_num] = to_unicode_quotes(fn_text.strip())

    paragraphs = {}
    cur_num, cur_parts = None, []

    def flush():
        nonlocal cur_num, cur_parts
        if cur_num is None: return
        body = to_unicode_quotes(" ".join(cur_parts).strip())
        para = make_para(cur_num, body, "va")
        # Assign footnotes by [^N] refs
        refs = [int(m) for m in re.findall(r"\[\^(\d+)\]", body)]
        for r in refs:
            if r in footnotes:
                para["footnotes"][str(r)] = footnotes[r]
        paragraphs[cur_num] = para
        cur_num, cur_parts = None, []

    for p in soup.find_all(["p","li"]):
        md = convert_inline(p, FN_PAT).strip()
        plain = strip_md(md)
        if not plain: continue
        m = PARA_RE.match(plain)
        if m:
            flush()
            cur_num = int(m.group(1))
            pfx = re.match(r"^\d{1,3}\.\s+", md)
            cur_parts = [md[len(pfx.group(0)):].strip() if pfx else md]
        elif cur_num and not re.match(r"^\[\d+\]", plain):
            cur_parts.append(md)
    flush()

    result = {"paragraphs": sorted(paragraphs.values(), key=lambda x: x["num"]),
              "footnotes": {str(k): v for k,v in footnotes.items()}}
    print(f"  Vatican: {len(paragraphs)} paragraphs, {len(footnotes)} footnotes", file=sys.stderr)
    return result


# ── USCCB 2010 ────────────────────────────────────────────────────────────────

def extract_us():
    print("Extracting USCCB HTML...", file=sys.stderr)
    FILES = ["girm-foreword","girm-introduction",
             "girm-chapter-1","girm-chapter-2","girm-chapter-3",
             "girm-chapter-4","girm-chapter-5","girm-chapter-6",
             "girm-chapter-7","girm-chapter-8","girm-chapter-9"]
    HEADING_CLS = {"h2":2,"h3":3,"h4":4}
    BODY_CLS    = {"parafirst","para","normal","bqsingle"}
    LIST_CLS    = {"list1first","list1middle","list1last"}
    FN_PAT      = re.compile(r"footnote-\d+-(\d+)")
    FN_ID_PAT   = re.compile(r"footnote-\d+-(\d+)$")
    SKIP_HEADS  = {"Breadcrumb","Footnotes",
                   "Dive into God\u2019s Word","Dive into God's Word",
                   "About USCCB","Topics","Prayer & Worship",
                   "Get Involved to Act Now","Quick Links"}

    paragraphs, footnotes, pending_headings, cur_num = {}, {}, [], None

    def add_cont(md):
        if cur_num and cur_num in paragraphs:
            paragraphs[cur_num]["text"] += " " + to_unicode_quotes(md.strip())

    for fname in FILES:
        path = ROOT / f"src/girm-us/{fname}.html"
        if not path.exists(): continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "lxml")
        main = soup.find("main") or soup.find(id=re.compile("main",re.I)) or soup.find("body")

        for el in main.find_all(["p","h1","h2","h3","h4","h5","li"]):
            classes = set(el.get("class",[]))
            tag = el.name

            if tag in ("h1","h2","h3","h4","h5"):
                txt = el.get_text(" ",strip=True)
                if txt not in SKIP_HEADS:
                    pending_headings.append((int(tag[1]), txt))
                continue

            if classes & set(HEADING_CLS):
                plain_test = el.get_text(" ",strip=True)
                if not re.match(r"^\d{1,3}\. ", plain_test):
                    if plain_test not in SKIP_HEADS:
                        for cls in classes:
                            if cls in HEADING_CLS:
                                pending_headings.append((HEADING_CLS[cls], plain_test))
                    continue

            if "notepara" in classes:
                anchor = el.find("a", id=FN_ID_PAT)
                if anchor:
                    fn_m = FN_ID_PAT.search(anchor.get("id",""))
                    if fn_m:
                        fn_num = int(fn_m.group(1))
                        fn_text = ""
                        found = False
                        for child in el.children:
                            if found:
                                fn_text += convert_inline(child,FN_PAT) if isinstance(child,Tag) else str(child)
                            if child == anchor: found = True
                        footnotes[fn_num] = to_unicode_quotes(fn_text.strip().lstrip("] "))
                continue

            if (classes & (BODY_CLS|LIST_CLS) or tag=="li" or
                    (classes & set(HEADING_CLS) and
                     re.match(r"^\d{1,3}\. ", el.get_text(" ",strip=True)))):
                md    = convert_inline(el, FN_PAT).strip()
                plain = strip_md(md)
                if not plain: continue
                num_m = PARA_RE.match(plain)
                if num_m:
                    cur_num = int(num_m.group(1))
                    pfx = re.match(r"^\d{1,3}\.\s+", md)
                    body = to_unicode_quotes(md[len(pfx.group(0)):].strip() if pfx else md)
                    para = make_para(cur_num, body, "us")
                    if pending_headings:
                        para["headings_before"] = pending_headings[:]
                        pending_headings = []
                    paragraphs[cur_num] = para
                elif classes & LIST_CLS:
                    if cur_num and cur_num in paragraphs:
                        paragraphs[cur_num]["text"] += f"\n- {to_unicode_quotes(md)}"
                elif classes & {"para","normal","bqsingle"}:
                    add_cont(md)

    # Assign footnotes by [^N] refs in body
    for para in paragraphs.values():
        refs = [int(m) for m in re.findall(r"\[\^(\d+)\]", para["text"])]
        for r in refs:
            if r in footnotes:
                para["footnotes"][str(r)] = footnotes[r]

    result = {"paragraphs": sorted(paragraphs.values(), key=lambda x: x["num"]),
              "footnotes": {str(k): v for k,v in footnotes.items()}}
    print(f"  USCCB: {len(paragraphs)} paragraphs, {len(footnotes)} footnotes", file=sys.stderr)
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run US first so UK heading exclusion works
    us = extract_us()
    (OUT/"us.json").write_text(json.dumps(us, indent=2, ensure_ascii=False), encoding="utf-8")

    uk = extract_uk()
    (OUT/"uk.json").write_text(json.dumps(uk, indent=2, ensure_ascii=False), encoding="utf-8")

    # VA source removed (outdated 2003 ICEL HTML, not the authoritative Latin text)
    # va = extract_va()

    print("\nCoverage:", file=sys.stderr)
    for name, data in [("UK",uk),("US",us)]:
        nums = [p["num"] for p in data["paragraphs"]]
        print(f"  {name}: {len(nums)} paras {min(nums)}\u2013{max(nums)}", file=sys.stderr)
