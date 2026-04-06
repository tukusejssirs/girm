#!/usr/bin/env python3
"""build_master_annotated.py
Generates out/girm-master.md — annotated master GIRM with universal text + national adaptations.

Legend:
  🌐  Universal (whole Latin Church)
  🇬🇧  England & Wales adaptation (embedded in GIRM text, CBCEW 2011)
  🇺🇸  US adaptation (embedded in GIRM text, USCCB 2011)
  🇸🇰  Slovakia — separate KBS directive, NOT embedded in GIRM text
  [+]  Addition
  [~]  Replacement of universal text
  [-]  Omission
  [*]  Pastoral guidance / note (not a binding adaptation)
"""

import json, re, textwrap
from pathlib import Path

ROOT = Path(__file__).parent
OUT  = ROOT / "out"

uk_data = json.loads((ROOT/"extracted/uk.json").read_text())
us_data = json.loads((ROOT/"extracted/us.json").read_text())
va_data = json.loads((ROOT/"extracted/va.json").read_text())
adaptations = json.loads((ROOT/"meta/adaptations.json").read_text())

uk_map = {p["num"]: p for p in uk_data["paragraphs"]}
us_map = {p["num"]: p for p in us_data["paragraphs"]}
va_map = {p["num"]: p for p in va_data["paragraphs"]}
uk_gfn = uk_data["footnotes"]
us_gfn = us_data["footnotes"]

US_ADAPTED = set(adaptations["us_adapted_paras"])
UK_ADAPTED = set(adaptations["uk_adapted_paras"])
SK_ADDITIONS = {int(k): v for k,v in adaptations["sk_additions"].items()}

def wrap(text, width=100):
    out = []
    for line in text.split("\n"):
        if line.startswith((">", "#", "-", "[", " ")):
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(out)

def blockquote(text, prefix=""):
    lines = []
    for line in (prefix + text).split("\n"):
        lines.append(f"> {line}")
    return "\n".join(lines)

UK_PHRASE = re.compile(
    r"[Ii]n the [Dd]ioceses? of England and Wales|[Ii]n England and Wales"
)

def get_universal_text(n):
    """Return universal text for a paragraph.
    For US-only adapted paras: UK text is universal.
    For UK-adapted paras: UK text up to the E&W-specific phrase.
    For non-adapted: UK text.
    """
    uk_t = uk_map.get(n, {}).get("text", "")
    if n in UK_ADAPTED:
        m = UK_PHRASE.search(uk_t)
        if m:
            return uk_t[:m.start()].strip()
    return uk_t

def get_us_extra(n):
    """Return the text added by the US edition for paragraph n."""
    uk_t = uk_map.get(n, {}).get("text", "")
    us_t = us_map.get(n, {}).get("text", "")
    if not us_t or us_t == uk_t:
        return None, None
    min_l = min(len(uk_t), len(us_t))
    cp = 0
    for i in range(min_l):
        if uk_t[i] == us_t[i]: cp = i + 1
        else: break
    uk_tail = uk_t[cp:].strip()
    us_tail = us_t[cp:].strip()
    return us_tail or None, uk_tail or None

def get_uk_extra(n):
    """Return E&W-specific text for paragraph n."""
    uk_t = uk_map.get(n, {}).get("text", "")
    m = UK_PHRASE.search(uk_t)
    if m:
        return uk_t[m.start():].strip()
    return None

# Section headings (from existing generate.py logic)
SECTION_HEADINGS = {
    1:   ("Preamble / Introduction",                     None),
    16:  ("Chapter I",   "The Importance and Dignity of the Celebration of the Eucharist"),
    27:  ("Chapter II",  "The Structure of the Mass, Its Elements and Its Parts"),
    91:  ("Chapter III", "The Duties and Ministries in the Mass"),
    112: ("Chapter IV",  "The Different Forms of Celebrating Mass"),
    288: ("Chapter V",   "The Arrangement and Ornamentation of Churches for the Celebration of the Eucharist"),
    319: ("Chapter VI",  "The Requirements for the Celebration of Mass"),
    352: ("Chapter VII", "The Choice of the Mass and Its Parts"),
    368: ("Chapter VIII","Masses and Prayers for Various Circumstances and Masses for the Dead"),
    386: ("Chapter IX",  "Adaptations within the Competence of Bishops and Bishops' Conferences"),
}

lines = []
def L(*args):
    for a in args: lines.append(a)
def blank(): lines.append("")

# ── Header ────────────────────────────────────────────────────────────────────
L(
"# General Instruction of the Roman Missal (GIRM) — Annotated Master",
"",
"<!-- Annotation legend",
"  🌐  Universal — valid for the whole Latin Church",
"  🇬🇧  England & Wales adaptation (embedded in UK GIRM text, CBCEW 2011)",
"  🇺🇸  United States adaptation (embedded in US GIRM text, USCCB 2011)",
"  🇸🇰  Slovakia — separate KBS directive; NOT embedded in VSRM text",
"  [+]  Addition (not present in universal text / Latin original)",
"  [~]  Replacement (replaces universal text in that region)",
"  [-]  Omission (universal text not applicable or dropped in that region)",
"  [*]  Pastoral guidance or note (not a binding canon law adaptation)",
"-->",
"",
"> **Base text:** England & Wales 2011 (ICEL), with Universal text identified by",
"> comparison with the Vatican 2003 ICEL translation and USCCB 2010.",
"> All paragraph numbers (§§1–399) follow the *editio typica tertia* (2002).",
"> See `meta/` directory for full bibliographical metadata per source.",
"",
"---",
""
)

used_fns = {}
current_chapter = None

for p in uk_data["paragraphs"]:
    n = p["num"]
    text = p["text"]

    # Chapter heading
    if n in SECTION_HEADINGS:
        ch_label, ch_title = SECTION_HEADINGS[n]
        if ch_title:
            L(f"## {ch_label}: {ch_title}")
        else:
            L(f"## {ch_label}")
        blank()

    # Headings from headings_before
    for h in p.get("headings_before", []):
        if h.strip():
            L(f"### {h.strip()}")
            blank()

    L(f"#### §{n}")
    blank()

    # Universal text — with 🌐 marker if it has adaptations
    has_us = n in US_ADAPTED
    has_uk = n in UK_ADAPTED
    has_sk = n in SK_ADDITIONS
    marker = " 🌐" if (has_us or has_uk or has_sk) else ""
    
    if has_us or has_uk or has_sk:
        L(f"🌐 **Universal:**")
        blank()

    # Universal text: UK base, stripped of any E&W-specific phrases
    universal_text = get_universal_text(n)
    # Edge case: if universal_text is empty (whole UK para is E&W-specific),
    # find the common prefix between UK and US as the universal base
    if not universal_text and n in US_ADAPTED:
        uk_t = uk_map.get(n, {}).get("text", "")
        us_t = us_map.get(n, {}).get("text", "")
        min_l = min(len(uk_t), len(us_t))
        cp = 0
        for i in range(min_l):
            if uk_t[i] == us_t[i]: cp = i + 1
            else: break
        universal_text = uk_t[:cp].strip()
        # If still empty, use a note
        if not universal_text or len(universal_text) < 10:
            universal_text = (f"*Text governed entirely by national adaptations; "
                              f"see Conference of Bishops' norms below.*")

    L(wrap(universal_text))
    blank()

    # Collect footnotes
    for k, v in p.get("footnotes", {}).items():
        used_fns[int(k)] = v

    # US adaptation
    if has_us:
        us_extra, uk_only = get_us_extra(n)
        if us_extra:
            # Determine type: [+] if only in US, [~] if replacing UK text
            marker_type = "[~]" if uk_only else "[+]"
            us_fn_refs = ""
            for k, v in us_map.get(n, {}).get("footnotes", {}).items():
                if k not in uk_map.get(n, {}).get("footnotes", {}):
                    us_fn_refs += f"[^us-{k}]"
                    used_fns[f"us-{k}"] = v
            L(f"> 🇺🇸 {marker_type} **US adaptation (embedded in §{n} — USCCB, in force 2011-11-27):**")
            for line in wrap(us_extra, 94).split("\n"):
                L(f"> {line}")
            blank()

    # UK (E&W) adaptation  
    if has_uk:
        uk_extra = get_uk_extra(n)
        if uk_extra:
            L(f"> 🇬🇧 [+] **England & Wales adaptation (embedded in §{n} — CBCEW, in force 2011-11-27):**")
            for line in wrap(uk_extra, 94).split("\n"):
                L(f"> {line}")
            blank()

    # SK non-embedded addition
    if has_sk:
        sk = SK_ADDITIONS[n]
        marker_type = sk.get("type", "+")
        label = {"+" : "[+]", "~": "[~]", "-": "[-]", "*": "[*]"}.get(marker_type, "[+]")
        src = sk.get("source", "KBS")
        url = sk.get("url", "")
        L(f"> 🇸🇰 {label} **Slovak note (separate directive — {src};**")
        L(f"> **NOT embedded in VSRM text):**")
        L(f">")
        if "text_sk" in sk:
            L(f"> *{sk['text_sk']}*")
            L(f">")
        for line in wrap(sk.get("text_en",""), 94).split("\n"):
            L(f"> {line}")
        if "pastoral_guidance" in sk:
            L(f">")
            for line in wrap(sk["pastoral_guidance"], 92).split("\n"):
                L(f"> {line}")
        if url:
            L(f">")
            L(f"> Source: {url}")
        blank()

# Footnotes
L("---", "")
L("## Footnotes", "")
for fn_n, fn_text in sorted(used_fns.items(), key=lambda x: (str(x[0]).replace("us-",""), str(x[0]))):
    if isinstance(fn_n, int):
        L(f"[^{fn_n}]: {fn_text}")
    else:
        L(f"[^{fn_n}]: [US §{fn_n.replace('us-','')}] {fn_text}")
    blank()

OUT.mkdir(exist_ok=True)
output = re.sub(r"§§(\d)", r"§\1", "\n".join(lines))
(OUT/"girm-master.md").write_text(output, encoding="utf-8")
print(f"Written: out/girm-master.md ({output.count(chr(10))} lines)")
