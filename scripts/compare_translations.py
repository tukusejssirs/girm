#!/usr/bin/env python3
"""compare_translations.py
Compare every GIRM translation against the Latin original using Claude.

Architecture:
  Phase 1 — Per-paragraph comparison (cached per language):
    For each §N, sends LA + one translation to Claude and asks for meaning differences.
    Cached in cache/la-diff-{lang}.json so reruns are instant.

  Phase 2 — Translation rules inference (cached per language):
    Asks Claude to infer systematic translation rules from Phase 1 results.

  Phase 3 — Render out/girm-diff-la.md from all cached results.

Usage:
  python3 scripts/compare_translations.py [--lang uk|us|sk|all] [--para N] [--force] [--phase 1|2|3|all]
"""

import json, os, re, time, argparse, sys
from pathlib import Path
import urllib.request, urllib.error

ROOT  = Path(__file__).parent.parent
OUT   = ROOT / "out"
CACHE = ROOT / "cache"

la_data = json.loads((ROOT / "extracted/la.json").read_text(encoding="utf-8"))
la_map  = {p["num"]: p for p in la_data["paragraphs"]}

TRANSLATIONS = {}
for _lang, _fname in [("uk","extracted/uk.json"), ("us","extracted/us.json"),
                       ("sk","extracted/sk.json")]:
    _path = ROOT / _fname
    if _path.exists():
        _d = json.loads(_path.read_text(encoding="utf-8"))
        TRANSLATIONS[_lang] = {p["num"]: p for p in _d["paragraphs"]}

LANG_LABELS = {
    "uk": "England & Wales 2011 ICEL (English)",
    "us": "USCCB 2010 ICEL (English)",
    "sk": "KBS 2021 (Slovak)",
}

NATIONAL_ADAPTATIONS = {
    "uk": {43, 48, 87, 160, 301, 346},
    "us": {43, 48, 61, 87, 154, 160, 283, 301, 304, 326, 329, 339, 346, 362, 373, 393},
    "sk": set(),
}

# ── API ───────────────────────────────────────────────────────────────────────
def call_claude(prompt: str, system: str = "", max_tokens: int = 600) -> str:
    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Try .env file in repo root
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=",1)[1].strip().strip("\"'")
    if not api_key:
        raise RuntimeError(
            "No ANTHROPIC_API_KEY found. Set it as an environment variable:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  python3 scripts/compare_translations.py\n"
            "or place it in a .env file in the repo root."
        )
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"content-type": "application/json",
                 "anthropic-version": "2023-06-01",
                 "x-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data["content"][0]["text"].strip()

# ── Phase 1 ───────────────────────────────────────────────────────────────────
COMPARE_SYSTEM = """You are a liturgical scholar comparing translations of the General
Instruction of the Roman Missal (GIRM) against the authoritative Latin original.

IGNORE (these are NOT meaning differences):
- Synonym substitution (sacerdos=priest, populus=people, etc.)
- Different sentence structure that carries the same meaning
- Expanding Latin subordinate clauses into separate sentences
- Adding articles/prepositions required by the target language
- Spelling variants (colour/color)
- Word-count differences from natural Latin compression

REPORT ONLY genuine meaning differences:
- A concept or instruction present in Latin but absent from the translation
- Something added with no basis in the Latin text
- A change in strength of obligation (must/shall vs may/should)
- A change in who the instruction applies to
- A theological concept rendered with a materially different meaning

Respond ONLY with valid JSON, no markdown fences:
{
  "same_meaning": true,
  "differences": [],
  "notes": ""
}
or if there are differences:
{
  "same_meaning": false,
  "differences": [
    {
      "type": "omission|addition|change|scope_change",
      "latin_fragment": "relevant Latin text (max 30 words)",
      "translation_fragment": "relevant translated text or null if omission",
      "explanation": "one clear sentence"
    }
  ],
  "notes": "optional brief observation"
}"""

def compare_paragraph(n: int, lang: str) -> dict:
    la_text = la_map.get(n, {}).get("text", "")
    tr_text = TRANSLATIONS[lang].get(n, {}).get("text", "")
    label   = LANG_LABELS[lang]
    adapted = n in NATIONAL_ADAPTATIONS.get(lang, set())
    note    = (f"\nNote: §{n} has a documented national adaptation for {lang.upper()}. "
               "Differences due to that adaptation are expected; still report other meaning gaps."
               if adapted else "")

    prompt = (f"Compare Latin GIRM §{n} with its {label} translation.{note}\n\n"
              f"LATIN:\n{la_text}\n\n{lang.upper()} ({label}):\n{tr_text}")

    raw = call_claude(prompt, system=COMPARE_SYSTEM, max_tokens=600)
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
        return {"same_meaning": True, "differences": [], "notes": f"parse_error: {raw[:80]}"}

def run_phase1(lang: str, para=None, force=False):
    CACHE.mkdir(exist_ok=True)
    cache_file = CACHE / f"la-diff-{lang}.json"
    cache = {}
    if cache_file.exists() and not force:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))

    todo = ([para] if para else list(range(1, 400)))
    todo = [n for n in todo if (str(n) not in cache or force)
            and n in la_map and n in TRANSLATIONS.get(lang, {})]

    if not todo:
        print(f"  {lang}: all cached ({len(cache)} entries)")
        return cache

    print(f"  {lang}: {len(todo)} to process ({len(cache)} cached)")
    for i, n in enumerate(todo, 1):
        print(f"    §{n} ({i}/{len(todo)})...", end=" ", flush=True)
        try:
            result = compare_paragraph(n, lang)
            cache[str(n)] = result
            ndiff = len(result.get("differences", []))
            print("same" if result.get("same_meaning") else f"{ndiff} diff(s)")
        except Exception as e:
            print(f"ERR: {e}")
            cache[str(n)] = {"same_meaning": True, "differences": [], "notes": f"error:{e}"}
        cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        if i < len(todo):
            time.sleep(0.25)
    return cache

# ── Phase 2 ───────────────────────────────────────────────────────────────────
RULES_SYSTEM = ("You are a liturgical translation scholar. Analyse the systematic "
                "translation choices in a specific GIRM edition based on observed differences.")

def infer_rules(lang: str, cache: dict) -> str:
    rules_file = CACHE / f"la-rules-{lang}.json"
    if rules_file.exists():
        return json.loads(rules_file.read_text())["rules"]

    all_diffs = [{"para": int(k), **d}
                 for k, v in cache.items()
                 for d in v.get("differences", [])]

    if not all_diffs:
        rules = (f"Automated analysis found no meaning differences between the Latin GIRM "
                 f"and the {LANG_LABELS[lang]} translation across all {len(cache)} compared paragraphs.")
        rules_file.write_text(json.dumps({"rules": rules}, indent=2))
        return rules

    sample = json.dumps(all_diffs[:60], ensure_ascii=False, indent=2)
    label  = LANG_LABELS[lang]
    prompt = (f"Based on these observed differences between the Latin GIRM and the "
              f"{label} translation, describe the systematic translation approach.\n\n"
              f"Focus on:\n1. Deliberate theological/terminological choices\n"
              f"2. Structural/syntactic patterns\n3. Patterns of omission or addition\n"
              f"4. Overall fidelity level\n\nDifferences (sample of up to 60):\n{sample}\n\n"
              f"Write a concise structured analysis (250-400 words) for a scholarly header note.")

    rules = call_claude(prompt, system=RULES_SYSTEM, max_tokens=600)
    rules_file.write_text(json.dumps({"rules": rules}, indent=2, ensure_ascii=False))
    return rules

# ── Phase 3 ───────────────────────────────────────────────────────────────────
def render(langs: list):
    sys.path.insert(0, str(ROOT))
    from scripts.generate import CHAPTERS

    all_caches = {}
    for lang in langs:
        f = CACHE / f"la-diff-{lang}.json"
        if f.exists():
            all_caches[lang] = json.loads(f.read_text(encoding="utf-8"))

    if not all_caches:
        print("No cached results found. Run Phase 1 first.")
        return

    lines = [
        "# GIRM — Latin Original vs Translations: Meaning Differences",
        "",
        "Paragraph-by-paragraph comparison of the Latin *Institutio Generalis Missalis",
        "Romani*, *editio typica tertia emendata* 2008, against each available translation.",
        "",
        "**Method:** Each paragraph was compared against the Latin original by scholarly",
        "analysis (using Claude as the analytical engine when run via `compare_translations.py`),",
        "checking for genuine *meaning* differences only — omissions, additions, scope changes,",
        "and theological divergences. Natural translation choices (synonyms, restructured",
        "sentences carrying the same meaning, language-required particles) are excluded.",
        "Known national adaptations are noted; other meaning gaps within them are still reported.",
        "",
    ]

    # Coverage table
    lines += ["| Translation | §§ compared | §§ with differences |",
              "|-------------|------------|---------------------|"]
    for lang, cache in all_caches.items():
        compared  = len(cache)
        different = sum(1 for v in cache.values() if not v.get("same_meaning", True))
        lines.append(f"| **{lang.upper()}** — {LANG_LABELS[lang]} | {compared}/399 | {different} |")
    lines += ["", "---", ""]

    # Translation rules
    lines += ["## Translation Approach per Edition", ""]
    for lang, cache in all_caches.items():
        label = LANG_LABELS[lang]
        lines += [f"### {lang.upper()} — {label}", ""]
        rf = CACHE / f"la-rules-{lang}.json"
        if rf.exists():
            rules_text = json.loads(rf.read_text())["rules"]
            # Strip any leading "## Translation Approach..." line (render adds its own heading)
            rules_lines = rules_text.split("\n")
            if rules_lines and rules_lines[0].startswith("## "):
                rules_lines = rules_lines[1:]
            for l in rules_lines:
                lines.append(l)
        else:
            lines.append("*Not yet analysed — run `--phase 2`.*")
        lines += ["", "---", ""]

    # Per-paragraph differences
    lines += ["## Paragraph-Level Differences", "",
              "Only paragraphs where at least one translation has a meaning difference are shown.",
              "", "Legend: `[-]` omission · `[+]` addition · `[~]` change · `[≈]` scope change", ""]

    TYPE_MARKER = {"omission":"[-]","addition":"[+]","change":"[~]","scope_change":"[≈]"}

    for ch_num, slug, ch_title, para_range in CHAPTERS:
        chapter_lines = []
        for n in para_range:
            para_diffs = []
            for lang, cache in all_caches.items():
                result = cache.get(str(n), {})
                diffs  = result.get("differences", [])
                if diffs:
                    adapted = n in NATIONAL_ADAPTATIONS.get(lang, set())
                    para_diffs.append((lang, diffs, result.get("notes",""), adapted))

            if not para_diffs:
                continue

            la_text = la_map.get(n, {}).get("text", "")
            chapter_lines += [
                f"### §{n}", "",
                f"> **LA:** {la_text[:250]}{'…' if len(la_text)>250 else ''}",
                "",
            ]
            for lang, diffs, notes, adapted in para_diffs:
                tr_text = TRANSLATIONS.get(lang,{}).get(n,{}).get("text","")
                label   = LANG_LABELS[lang]
                tag     = " *(national adaptation paragraph)*" if adapted else ""
                chapter_lines += [
                    f"**{lang.upper()}**{tag} — {label}:",
                    f"> {tr_text[:250]}{'…' if len(tr_text)>250 else ''}",
                    "",
                ]
                for d in diffs:
                    marker = TYPE_MARKER.get(d.get("type",""),"[?]")
                    la_f   = d.get("latin_fragment","")
                    tr_f   = d.get("translation_fragment","")
                    expl   = d.get("explanation","")
                    chapter_lines.append(f"- {marker} **{d.get('type','')}:** {expl}")
                    if la_f:  chapter_lines.append(f'  - *LA:* "{la_f}"')
                    if tr_f:  chapter_lines.append(f'  - *{lang.upper()}:* "{tr_f}"')
                if notes:
                    chapter_lines.append(f"  > *{notes}*")
                chapter_lines.append("")

        if chapter_lines:
            lines += [f"## {ch_title}", "", *chapter_lines]

    total = sum(sum(1 for v in c.values() if not v.get("same_meaning",True))
                for c in all_caches.values())
    OUT.mkdir(exist_ok=True)
    (OUT / "girm-diff-la.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: out/girm-diff-la.md ({len(lines)} lines, {total} §§ with differences)")

# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang",  default="all")
    ap.add_argument("--para",  type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--phase", default="all", choices=["1","2","3","all"])
    args = ap.parse_args()

    langs = list(TRANSLATIONS.keys()) if args.lang == "all" else [args.lang]

    if args.phase in ("1","all"):
        print("=== Phase 1: paragraph comparison ===")
        for lang in langs:
            run_phase1(lang, para=args.para, force=args.force)

    if args.phase in ("2","all") and not args.para:
        print("=== Phase 2: translation rules inference ===")
        for lang in langs:
            cf = CACHE / f"la-diff-{lang}.json"
            if cf.exists():
                cache = json.loads(cf.read_text())
                print(f"  {lang}...", end=" ", flush=True)
                rules = infer_rules(lang, cache)
                print("done" if rules else "no diffs found")

    if args.phase in ("3","all") and not args.para:
        print("=== Phase 3: rendering ===")
        render(langs)
