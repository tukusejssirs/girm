#!/usr/bin/env python3
"""
generate.py — 5 output Markdown files from extracted JSON

Outputs:
  out/girm-src-uk.md     UK 2011 verbatim
  out/girm-src-us.md     USCCB 2010 verbatim
  out/girm-master.md     Master doc (UK base, full headings, all footnotes)
  out/girm-diff-en.md       Systematic differences
"""

import json, re, textwrap
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).parent.parent
EXT  = ROOT / "extracted"
OUT  = ROOT / "out"
OUT.mkdir(exist_ok=True)

uk_data = json.loads((EXT/"uk.json").read_text(encoding="utf-8"))
# VA source removed (outdated 2003 ICEL HTML, not the authoritative Latin text)
us_data = json.loads((EXT/"us.json").read_text(encoding="utf-8"))

uk_map = {p["num"]: p for p in uk_data["paragraphs"]}
us_map = {p["num"]: p for p in us_data["paragraphs"]}
uk_fn_global = uk_data.get("footnotes", {})
la_data = json.loads((EXT/"la.json").read_text(encoding="utf-8"))
la_map  = {p["num"]: p for p in la_data["paragraphs"]}
sk_data = json.loads((EXT/"sk.json").read_text(encoding="utf-8"))
sk_map  = {p["num"]: p for p in sk_data["paragraphs"]}
us_fn_global = us_data.get("footnotes", {})

CHAPTERS = [
    (0, "introduction",  "Introduction",                                        range(1,16)),
    (1, "ch1",           "Chapter I: The Importance and Dignity of the Celebration of the Eucharist", range(16,27)),
    (2, "ch2",           "Chapter II: The Structure of the Mass, Its Elements and Its Parts", range(27,91)),
    (3, "ch3",           "Chapter III: Duties and Ministries in the Mass",      range(91,112)),
    (4, "ch4",           "Chapter IV: The Different Forms of Celebrating Mass", range(112,288)),
    (5, "ch5",           "Chapter V: The Arrangement and Ornamentation of Churches for the Celebration of the Eucharist", range(288,319)),
    (6, "ch6",           "Chapter VI: The Requisites for the Celebration of Mass", range(319,352)),
    (7, "ch7",           "Chapter VII: The Choice of the Mass and Its Parts",   range(352,368)),
    (8, "ch8",           "Chapter VIII: Masses and Prayers for Various Needs and Occasions and Masses for the Dead", range(368,386)),
    (9, "ch9",           "Chapter IX: Adaptations within the Competence of Bishops and Bishops\u2019 Conferences", range(386,400)),
]

# Section headings from LA source (authoritative structure)
SECTION_HEADINGS = {}  # para_num → [str, ...]
for p in la_data["paragraphs"]:
    hdgs = p.get("headings_before", [])
    if hdgs:
        SECTION_HEADINGS[p["num"]] = hdgs

SKIP_HEADS = {"Breadcrumb","Footnotes","Dive into God\u2019s Word","Dive into God's Word",
              "About USCCB","Topics","Prayer & Worship","Get Involved to Act Now","Quick Links"}

def wrap(text, width=100):
    # Normalise multiple spaces (artefact from HTML italic extraction)
    text = re.sub(r"  +", " ", text)
    out = []
    for line in text.split("\n"):
        if line.startswith(("-","#","["," ")):
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(out)

def fn_block(footnotes_dict):
    """Render footnote definitions block."""
    if not footnotes_dict: return ""
    lines = []
    for k, v in sorted(footnotes_dict.items(), key=lambda x: int(x[0])):
        lines.append(f"[^{k}]: {v}")
    return "\n".join(lines)

def emit_headings(num, skip_set, level_offset=1):
    """Return Markdown heading lines for headings before paragraph num."""
    lines = []
    seen = set()
    for htext in SECTION_HEADINGS.get(num, []):
        if htext in skip_set or htext in SKIP_HEADS:
            continue
        key = htext
        if key not in seen:
            md_level = {1:2,2:2,3:3,4:4}.get(level,4) + level_offset - 1
            md_level = max(2, min(md_level, 5))
            lines.append("#" * md_level + " " + htext)
            lines.append("")
            seen.add(key)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Source document builder (verbatim)
# ─────────────────────────────────────────────────────────────────────────────

def build_source(para_map, fn_global, title, edition, notes):
    lines = [f"# {title}", "",
             f"> **Edition:** {edition}  ", f"> {notes}", "", "---", ""]
    seen_headings = set()
    collected_fns = {}

    for ch_num, slug, ch_title, para_range in CHAPTERS:
        # Chapter heading
        lines.append(f"## {ch_title}")
        lines.append("")
        for num in para_range:
            p = para_map.get(num)
            if not p: continue

            # Section headings before this paragraph
            # 1. Hardcoded chapter/section map (UK/US sources)
            for htext in SECTION_HEADINGS.get(num, []):
                if htext in SKIP_HEADS: continue
                key = htext
                if key not in seen_headings:
                    lines.append("#### " + htext)
                    lines.append("")
                    seen_headings.add(key)
            # 2. Per-paragraph headings_before (for sources not covered by SECTION_HEADINGS)
            for entry in p.get("headings_before", []):
                # Handle both [level, text] tuples and plain strings
                htext = entry[1] if isinstance(entry, (list, tuple)) else entry
                if htext in SKIP_HEADS: continue
                if htext not in seen_headings:
                    lines.append("#### " + htext)
                    lines.append("")
                    seen_headings.add(htext)

            # Paragraph
            lines.append(f"### §{num}")
            lines.append("")
            para_text = wrap(p["text"])
            # For sources without inline markers, append fn refs at paragraph end
            para_fns = p.get("footnotes", {})
            if para_fns and not fn_global:
                fn_refs = " ".join(f"[^{k}]" for k in sorted(para_fns, key=int))
                para_text = para_text.rstrip() + " " + fn_refs
            lines.append(para_text)
            lines.append("")

            # Collect footnotes
            collected_fns.update(para_fns)

        lines.append("")

    # Footnotes section at end
    fns_to_write = fn_global if fn_global else collected_fns
    if fns_to_write:
        lines.append("---")
        lines.append("")
        lines.append("## Footnotes")
        lines.append("")
        for k, v in sorted(fns_to_write.items(), key=lambda x: int(x[0])):
            lines.append(f"[^{k}]: {v}")
            lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Master document builder
# ─────────────────────────────────────────────────────────────────────────────

def build_master():
    lines = [
        "# General Instruction of the Roman Missal",
        "",
        "> **Base text:** England & Wales 2011 (ICEL translation, Third Typical Edition)  ",
        "> **Italic text:** Latin terms and document titles as they appear in the UK edition  ",
        "> **Footnotes:** UK 2011, supplemented from USCCB 2010 where UK is incomplete  ",
        "> **Section structure:** USCCB 2010 headings",
        "",
        "---",
        "",
    ]
    seen_headings = set()
    all_fns = {}   # collect all footnotes for end

    for ch_num, slug, ch_title, para_range in CHAPTERS:
        lines.append(f"## {ch_title}")
        lines.append("")

        for num in para_range:
            uk_p = uk_map.get(num)
            us_p = us_map.get(num)
            if not uk_p and not us_p: continue

            # Section headings
            for htext in SECTION_HEADINGS.get(num, []):
                if htext in SKIP_HEADS: continue
                if htext not in seen_headings:
                    lines.append("#### " + htext)
                    lines.append("")
                    seen_headings.add(htext)

            body = (uk_p or us_p)["text"]
            lines.append(f"### §{num}")
            lines.append("")
            lines.append(wrap(body))
            lines.append("")

            # Footnotes for this paragraph
            para_fns = {}
            if uk_p:
                para_fns.update(uk_p.get("footnotes", {}))
            if us_p:
                for k, v in us_p.get("footnotes", {}).items():
                    if k not in para_fns:
                        para_fns[k] = v
            all_fns.update(para_fns)

        lines.append("")

    # Footnote definitions
    if all_fns:
        lines.append("---")
        lines.append("")
        lines.append("## Footnotes")
        lines.append("")
        for k, v in sorted(all_fns.items(), key=lambda x: int(x[0])):
            lines.append(f"[^{k}]: {v}")
            lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Diff helpers
# ─────────────────────────────────────────────────────────────────────────────

# All quote variants → same canonical char for comparison only
# Quote variants normalised to U+0022 for COMPARISON only — never for display
QUOTE_NORM = re.compile(r'[\u0022\u0027\u0060\u00AB\u00BB\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2039\u203A]')

def _strip_refs_md(text):
    """Strip footnote refs and markdown formatting; preserve original quote chars."""
    t = re.sub(r"\[\^\d+\]", "", text or "")
    t = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def normalise(text):
    """For comparison: strip refs/md AND normalise all quotes to same char."""
    t = _strip_refs_md(text)
    t = QUOTE_NORM.sub("\u0022", t)
    return t

def tokenise(text):
    """Comparison tokens (normalised quotes)."""
    return re.findall(r"\S+", normalise(text))

def tokenise_display(text):
    """Display tokens: same stripping as normalise but quotes preserved."""
    return re.findall(r"\S+", _strip_refs_md(text))

def diff_tokens(a_text, b_text):
    # Compare on normalised tokens (quotes collapsed)
    a_cmp = tokenise(a_text)
    b_cmp = tokenise(b_text)
    if a_cmp == b_cmp: return []

    # Display tokens: same structure but original quote chars
    a_dis = tokenise_display(a_text)
    b_dis = tokenise_display(b_text)

    raw = []
    sm = SequenceMatcher(None, a_cmp, b_cmp, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        # Use display tokens for output; fall back to EM-DASH when span is empty
        a_chunk = " ".join(a_dis[i1:i2]) if i2 > i1 else "\u2014"
        b_chunk = " ".join(b_dis[j1:j2]) if j2 > j1 else "\u2014"
        raw.append((a_chunk, b_chunk))

    # Merge adjacent orphan pairs to eliminate confusing (—, Y)+(X, —) patterns:
    #   (X, "—") + ("—", Y)  →  (X, Y)   [delete then insert]
    #   ("—", Y) + (X, "—")  →  (X, Y)   [insert then delete]
    merged = []
    i = 0
    EM = "\u2014"
    while i < len(raw):
        a, b = raw[i]
        if i + 1 < len(raw):
            na, nb = raw[i + 1]
            if b == EM and na == EM:        # (X, —) + (—, Y)
                merged.append((a, nb))
                i += 2
                continue
            if a == EM and nb == EM:        # (—, Y) + (X, —)
                merged.append((na, b))
                i += 2
                continue
        merged.append((a, b))
        i += 1
    return merged

def is_quote_only_diff(a_tok, b_tok):
    """True if the only difference is quote style (not extra/missing quotes)."""
    a_norm = QUOTE_NORM.sub("", a_tok)
    b_norm = QUOTE_NORM.sub("", b_tok)
    return a_norm == b_norm

UK_SPELLINGS = {
    "honour","colour","favour","labour","neighbour","centre","theatre","litre",
    "fulfil","fulfilling","fulfilment","recognise","emphasise","organise","realise",
    "practise","defence","licence","programme","catalogue","dialogue","analyse",
    "paralyse","authorise","characterise","harmonise","symbolise","harmonise",
    "eucharisticum","formulae","formulas",
}
US_SPELLINGS = {s.replace("ise","ize").replace("ise","ize").replace("our","or")
                .replace("re","er").replace("ful","full").replace("c","se")
                for s in UK_SPELLINGS}

def classify_diff(diffs):
    types = set()
    for a, b in diffs:
        a_l, b_l = a.lower().strip("\"',.:;"), b.lower().strip("\"',.:;")
        # Spelling UK/US
        if (a_l in UK_SPELLINGS and b_l in US_SPELLINGS) or \
           (b_l in UK_SPELLINGS and a_l in US_SPELLINGS):
            types.add("Spelling (UK/US)")
        elif a == "\u2014" or b == "\u2014":
            types.add("Structural")
        else:
            types.add("Wording")
    return sorted(types) or ["Wording"]


# ─────────────────────────────────────────────────────────────────────────────
# Diff document builder
# ─────────────────────────────────────────────────────────────────────────────

def build_diff():
    lines = [
        "# General Instruction of the Roman Missal — Differences",
        "",
        "Comparison of editions against the Latin original and each other.",
        "",
        "| Label | Edition |",
        "|-------|---------|",
        "| **LA** | Latin *Institutio Generalis Missalis Romani*, *editio typica tertia emendata* 2008 |",
        "| **UK** | England & Wales 2011 (ICEL) |",
        "| **US** | USCCB 2010 (ICEL) |",
        "| **SK** | Slovak VSRM — KBS 2021 |",
        "",
        "Diff types: **Wording** · **Spelling** · **Formatting** · **UK-specific** · **US-specific**",
        "",
        "---",
        "",
    ]

    total_diffs = 0

    for ch_num, slug, ch_title, para_range in CHAPTERS:
        chapter_lines = []

        for num in para_range:
            la_p = la_map.get(num)
            uk_p = uk_map.get(num)
            us_p = us_map.get(num)
            sk_p = sk_map.get(num)
            if not (la_p or uk_p or us_p): continue

            la_text = (la_p or {}).get("text", "")
            uk_text = (uk_p or {}).get("text", "")
            us_text = (us_p or {}).get("text", "")
            sk_text = (sk_p or {}).get("text", "")

            para_diffs = []

            # ── UK vs US (English translation differences) ────────────────
            diffs_uk_us = diff_tokens(uk_text, us_text)
            if diffs_uk_us:
                real = [(a,b) for a,b in diffs_uk_us if not is_quote_only_diff(a,b)]
                if real:
                    spelling = [(a,b) for a,b in real
                                if a.lower().rstrip(".,;") in UK_SPELLINGS or
                                   b.lower().rstrip(".,;") in UK_SPELLINGS]
                    wording  = [(a,b) for a,b in real if (a,b) not in spelling]
                    if spelling:
                        block = ["#### Spelling (UK vs US)"]
                        for a,b in spelling:
                            block += [f"- **UK:** {a}", f"- **US:** {b}", ""]
                        para_diffs.append("\n".join(block))
                    if wording:
                        block = ["#### Wording (UK vs US)"]
                        for a,b in wording:
                            block += [f"- **UK:** {a}", f"- **US:** {b}", ""]
                        para_diffs.append("\n".join(block))

            # ── UK-specific / US-specific ─────────────────────────────────
            if us_text and "United States" in us_text and (
                    not uk_text or "United States" not in uk_text):
                para_diffs.append(
                    "#### US-specific adaptation\n"
                    "- US text contains content specific to the Dioceses of the United States")
            if uk_text and ("England" in uk_text or "Wales" in uk_text) and (
                    not us_text or ("England" not in us_text and "Wales" not in us_text)):
                para_diffs.append(
                    "#### UK-specific adaptation\n"
                    "- UK text contains content specific to England and Wales")

            # ── Formatting (italic spans) ─────────────────────────────────
            uk_it = set(re.findall(r"\*([^*]+)\*", uk_text))
            us_it = set(re.findall(r"\*([^*]+)\*", us_text)) if us_text else set()
            only_uk_it = uk_it - us_it
            only_us_it = us_it - uk_it
            if only_uk_it or only_us_it:
                block = ["#### Formatting (italics)"]
                if only_uk_it:
                    block.append("- Italic in UK only: " +
                                 ", ".join(f"*{t}*" for t in sorted(only_uk_it)))
                if only_us_it:
                    block.append("- Italic in US only: " +
                                 ", ".join(f"*{t}*" for t in sorted(only_us_it)))
                para_diffs.append("\n".join(block))

            if para_diffs:
                total_diffs += 1
                chapter_lines.append(f"### §{num}")
                chapter_lines.append("")
                for blk in para_diffs:
                    chapter_lines.append(blk)
                    chapter_lines.append("")

        if chapter_lines:
            lines.append(f"## {ch_title}")
            lines.append("")
            # Section headings
            for num in para_range:
                for htext in SECTION_HEADINGS.get(num, []):
                    if any(f"### §{num}" in cl for cl in chapter_lines):
                        break
            lines.extend(chapter_lines)

    lines.append("")
    lines.append(f"*Total paragraphs with differences: {total_diffs}*")
    return "\n".join(lines)

def visual_compare():
    CHECK_PARAS = [1, 43, 54, 69, 70, 91, 120, 150, 288, 399]
    print("\n" + "="*70, file=__import__("sys").stderr)
    print("VISUAL COMPARISON — key paragraphs across all three sources",
          file=__import__("sys").stderr)
    print("="*70, file=__import__("sys").stderr)

    for num in CHECK_PARAS:
        print(f"\n{'─'*60}", file=__import__("sys").stderr)
        print(f"§{num}", file=__import__("sys").stderr)
        for label, mp in [("UK", uk_map), ("US", us_map)]:
            p = mp.get(num)
            txt = p["text"][:160] if p else "MISSING"
            fn_count = len(p.get("footnotes",{})) if p else 0
            print(f"  {label} (fns={fn_count}): {txt}…",
                  file=__import__("sys").stderr)
    print("="*70 + "\n", file=__import__("sys").stderr)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    visual_compare()

    print("Writing girm-src-la.md…")
    (OUT/"girm-src-la.md").write_text(
        build_source(la_map, {},
                     "Institutio Generalis Missalis Romani",
                     "Editio typica tertia emendata (Latin, 2008)",
                     "Latin original; no inline national adaptations"),
        encoding="utf-8")

    print("Writing girm-src-uk.md…")
    (OUT/"girm-src-uk.md").write_text(
        build_source(uk_map, uk_fn_global,
                     "General Instruction of the Roman Missal",
                     "England & Wales 2011 (ICEL, Third Typical Edition)",
                     "Italic: Latin terms and document titles"),
        encoding="utf-8")


    print("Writing girm-src-sk.md…")
    (OUT/"girm-src-sk.md").write_text(
        build_source(sk_map, {},
                     "Všeobecné smernice Rímskeho misála",
                     "Slovak VSRM — KBS 2021 (editio typica tertia)",
                     "Slovak translation; no inline national adaptations"),
        encoding="utf-8")

    print("Writing girm-src-us.md…")
    (OUT/"girm-src-us.md").write_text(
        build_source(us_map, us_fn_global,
                     "General Instruction of the Roman Missal",
                     "USCCB 2010 (ICEL, Third Typical Edition, US adaptations)",
                     "Footnotes as numbered in the USCCB online edition"),
        encoding="utf-8")

    print("Writing girm-master.md…")
    (OUT/"girm-master.md").write_text(build_master(), encoding="utf-8")

    print("Writing girm-diff-en.md…")
    (OUT/"girm-diff-en.md").write_text(build_diff(), encoding="utf-8")

    print("\nFile sizes:")
    for f in sorted((OUT).glob("*.md")):
        lines = f.read_text(encoding="utf-8").count("\n")
        print(f"  {f.name}: {lines:,} lines")

# ─────────────────────────────────────────────────────────────────────────────
# Latin vs translations comparison
# ─────────────────────────────────────────────────────────────────────────────
