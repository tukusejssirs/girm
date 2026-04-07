# GIRM — General Instruction of the Roman Missal

Structured Markdown extraction pipeline for the *Institutio Generalis Missalis Romani* (*editio typica tertia emendata*, 2008) and its national translations.

**Repository:** `github.com/tukusejssirs/girm`  
**Intended consumers:** [romcal](https://github.com/romcal/romcal) and an altar server handbook.

---

## Repository Layout

```
src/                        Source documents (committed)
  girm-la/
    girm-la.html            Latin IGMR — full text from iglesiaactualidad.wordpress.com
    girm-la_metadata.json
  girm-uk/
    girm-uk-2011.pdf        England & Wales 2011 ICEL PDF (CBCEW)
    girm-uk_metadata.json
  girm-us/
    girm-chapter-*.html     USCCB 2010 ICEL HTML (one file per chapter)
    girm-us_metadata.json
  girm-sk/
    girm-sk-2021.pdf        Slovak VSRM — KBS 2021 PDF
    girm-sk_metadata.json
  kbs-sk/
    kbs-2005-directives_gestures.txt       KBS 2005 postures directive (Slovak text)
    kbs-2005-directives_gestures_metadata.json
    kbs-2005-pastoral-letter_metadata.json
    kbs-2021-missal-guidance_metadata.json
  girm-adaptations.json     Machine-readable map: US/UK adapted paragraphs, SK additions

extracted/                  Parsed paragraph data (committed, auto-generated)
  la.json                   399 §§ · 165 footnotes · 118 section headings
  uk.json                   399 §§ · 165 footnotes
  us.json                   399 §§
  sk.json                   399 §§ · 63 footnotes

cache/                      LLM comparison results (committed — one-time per source)
  la-diff-{lang}.json       Per-paragraph meaning comparison vs Latin
  la-rules-{lang}.json      Scholarly translation approach analysis per language

out/                        Generated documents (committed, auto-generated)
  girm-src-la.md            Latin IGMR verbatim (with footnotes and section headings)
  girm-src-uk.md            England & Wales 2011 verbatim
  girm-src-us.md            USCCB 2010 verbatim
  girm-src-sk.md            Slovak VSRM 2021 verbatim
  girm-master.md            Annotated master: Latin universal + national annotations
  girm-diff-en.md           UK vs US English differences (spelling, wording, adaptations)
  girm-diff-la.md           Latin vs all translations: meaning fidelity + translation rules
  girm-altar-servers.md     Altar server handbook (GIRM-based, Slovak norms included)

scripts/
  extract_la_html.py        Extract Latin from WordPress HTML
  extract_uk_pdf_fns.py     Extract UK PDF with spatial footnote handling
  extract.py                Extract US HTML chapters
  extract_sk_pdf.py         Extract Slovak PDF (two-column, pdfminer-based)
  clean-uk-pdf.py           Clean raw UK PDF text
  generate.py               Build girm-src-*.md, girm-diff-en.md, girm-master.md (generate only)
  build_master_annotated.py Build annotated girm-master.md (Latin base + national annotations)
  build_server_doc.py       Build girm-altar-servers.md
  compare_translations.py   LLM-based Latin vs translation meaning comparison
```

---

## Sources

| Label | File | Edition | Language | Status |
|-------|------|---------|----------|--------|
| LA | `src/girm-la/girm-la.html` | Latin *editio typica tertia emendata* 2008 | Latin | extracted |
| UK | `src/girm-uk/girm-uk-2011.pdf` | England & Wales 2011 (ICEL/CBCEW) | English | extracted |
| US | `src/girm-us/girm-chapter-*.html` | USCCB 2010 (ICEL) | English | extracted |
| SK | `src/girm-sk/girm-sk-2021.pdf` | Slovak VSRM — KBS 2021 | Slovak | extracted |

The Latin source was downloaded from:  
`https://iglesiaactualidad.wordpress.com/2016/05/19/institutio-generalis-missalis-romani/`

---

## Annotation Legend (`girm-master.md`)

| Marker | Meaning |
|--------|---------|
| 🌐 | Universal — valid for the whole Latin Church |
| 🇬🇧 | England & Wales adaptation (embedded in UK GIRM text, CBCEW 2011) |
| 🇺🇸 | United States adaptation (embedded in US GIRM text, USCCB 2011) |
| 🇸🇰 | Slovakia — separate KBS directive; **not embedded** in VSRM text |
| `[+]` | Addition (not present in universal/Latin text) |
| `[~]` | Replacement (replaces universal text in that region) |
| `[-]` | Omission |
| `[*]` | Pastoral guidance / note (not a binding canonical adaptation) |

---

## How National Adaptations Work

### US (USCCB) and UK (CBCEW) — Embedded in the paragraph text

Signalled by "In the Dioceses of the United States of America…" or "in the dioceses of England and Wales…".

- **UK (CBCEW):** §§ 43, 48, 87, 160, 301, 346
- **US (USCCB):** §§ 43, 48, 61, 87, 154, 160, 283, 301, 304, 326, 329, 339, 346, 362, 373, 393

### Slovakia (KBS) — Separate pastoral documents, not embedded in the VSRM text

The Slovak VSRM is a direct translation of the Latin with no embedded adaptations. KBS-specific norms are published separately. The primary document is:

**KBS 2005 Pastoral Letter + Smernice on Gestures and Postures** (51st KBS Plenary, Donovaly, 7–8 June 2005; in force 7 August 2005):  
<https://www.kbs.sk/obsah/sekcia/c/gesta-a-postoje-pri-svatej-omsi-smernice-k-pastierskemu-listu-kbs>

**Critical interpretive note — two distinct clauses in the KBS 2005 directive:**

**Clause A — "Kde je zvyk"** (VSRM §43 quoted verbatim, NOT a KBS addition):  
Kneeling from *Sanctus* through the end of the Eucharistic Prayer applies **only where that local parish custom already exists**. The KBS did not mandate this universally; it merely confirmed that existing customs may continue.

**Clause B — "Na Slovensku zachováme"** (KBS addition, universal for Slovakia):  
The faithful kneel before Communion when the Priest says *Ecce Agnus Dei* (*Hľa, Baránok Boží*). This kneeling counts as the reverential act before receiving; **no separate kneeling is needed in the Communion procession**. This IS a universal Slovak norm.

Additional Slovak norms (KBS 2005):
- During the Gospel, those standing **turn toward the ambo** (VSRM §133 — Slovakia only)
- The sign of peace is given **soberly to immediately neighbouring persons only** (VSRM §82 — Slovakia only)
- Stand for the *Alleluia* from the **first sung note** of the cantor or schola (Slovakia only)

---

## Running the Pipeline

### Prerequisites

```bash
pip install pdfminer.six beautifulsoup4 --break-system-packages
```

### Full rebuild from extracted JSON (fastest)

```bash
python3 scripts/generate.py
python3 scripts/build_master_annotated.py
python3 scripts/build_server_doc.py
python3 scripts/compare_translations.py --phase 3
```

### Full rebuild including re-extraction

```bash
python3 scripts/extract_la_html.py
python3 scripts/extract.py
python3 scripts/extract_sk_pdf.py
python3 scripts/generate.py
python3 scripts/build_master_annotated.py
python3 scripts/build_server_doc.py
```

### Regenerate Latin vs translation comparison

The `cache/` files are committed and cover all 399 paragraphs for UK, US, and SK.
To re-render `girm-diff-la.md` from the existing cache (no API key needed):

```bash
python3 scripts/compare_translations.py --phase 3
```

To re-run the full LLM comparison (requires API key — **only needed when source files
change or a new translation is added**):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Or place in a .env file in the repo root (gitignored)
python3 scripts/compare_translations.py --lang all
```

---

## Adding a New Translation

1. **Obtain the source file** and place in `src/girm-{lang}/`.

2. **Write an extractor** in `scripts/extract_{lang}_{format}.py`. Output must be
   `extracted/{lang}.json` with this schema:

   ```json
   {
     "paragraphs": [
       {
         "num": 1,
         "text": "Cleaned paragraph text.",
         "footnotes": { "1": "Footnote text." },
         "source": "de",
         "headings_before": ["Section heading before this paragraph"]
       }
     ],
     "footnotes": { "1": "Global footnote text if not per-paragraph." }
   }
   ```

3. **Create `src/girm-{lang}/girm-{lang}_metadata.json`** following the pattern of
   existing metadata files. Include `adaptations_method`: `"embedded"` or
   `"separate_document"`, and `adaptation_paragraphs` listing adapted §§.

4. **Register in `scripts/compare_translations.py`:**

   ```python
   # Add to TRANSLATIONS initialisation loop:
   ("de", "extracted/de.json"),

   # Add to LANG_LABELS:
   LANG_LABELS["de"] = "Deutsche Bischofskonferenz 20XX (German)"

   # Add to NATIONAL_ADAPTATIONS:
   NATIONAL_ADAPTATIONS["de"] = {43, ...}  # embedded adaptation paragraphs
   ```

5. **Run comparison** (one-time, API key required):

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   python3 scripts/compare_translations.py --lang de --phase 1  # compare paragraphs
   python3 scripts/compare_translations.py --lang de --phase 2  # infer translation rules
   python3 scripts/compare_translations.py --phase 3            # re-render diff doc
   ```

6. **Register in `scripts/generate.py`** — add a write block for `girm-src-de.md`
   and load `de_data`/`de_map` at the top alongside the existing sources.

7. **Add national annotations to `girm-master.md`** by extending the main loop in
   `scripts/build_master_annotated.py` with a `has_de` flag and blockquote block,
   following the pattern of the existing UK/US/SK blocks.

8. **Commit** source file, extractor, metadata JSON, `extracted/de.json`, and the
   new `cache/la-diff-de.json` / `cache/la-rules-de.json` files.

---

## Document Descriptions

### `out/girm-master.md`
Each paragraph shows:
1. **Universal text** — the Latin original (*editio typica tertia emendata* 2008)
2. **National adaptations** — country-flagged blockquotes with `[+]`/`[~]`/`[-]`/`[*]` markers
3. **Slovak notes** — from the separate KBS 2005 directive (marked "NOT embedded in VSRM text")

All text is in English. The universal text is Latin; annotations are in English.
No other language appears in prose.

### `out/girm-diff-en.md`
UK vs US English edition comparison: spelling, wording, embedded national adaptations.

### `out/girm-diff-la.md`
Latin vs all translations — meaning fidelity report. Contains:
- Translation approach per edition (systematic terminological and structural choices)
- Paragraph-level differences (omissions, additions, scope changes)

**Current result:** 0 meaning differences found across all 399 paragraphs in UK 2011,
US 2010, and SK 2021. The 2011 ICEL revision corrected the fidelity issues present in
the 2003 translation (notably restoring *pro multis* → "for many").

### `out/girm-altar-servers.md`
Practical handbook for altar servers derived from GIRM. Includes full Slovak-specific
norms at every relevant point. Intended for the altar server handbook project.

---

## Source Metadata Files

| File | Description |
|------|-------------|
| `src/girm-la/girm-la_metadata.json` | Latin IGMR 2008; LEV; promulgated 2002-04-20 |
| `src/girm-uk/girm-uk_metadata.json` | E&W 2011; CBCEW; in force 2011-11-27; 165 footnotes |
| `src/girm-us/girm-us_metadata.json` | USCCB 2010; in force 2011-11-27; 16 adapted §§ |
| `src/girm-sk/girm-sk_metadata.json` | KBS 2021; prot. 127/2021; in force 2022-01-01 |
| `src/kbs-sk/kbs-2005-directives_gestures_metadata.json` | KBS 2005 posture directive |
| `src/kbs-sk/kbs-2005-pastoral-letter_metadata.json` | KBS 2005 Pastoral Letter |
| `src/kbs-sk/kbs-2021-missal-guidance_metadata.json` | KBS 2021 Missal guidance (text changes only) |
| `src/girm-adaptations.json` | Machine-readable adaptation map |

---

## Extraction Notes

### Latin (LA)
- Paragraphs: `<p>N. text…` format in WordPress HTML
- Headings: short `<p>` elements with no trailing sentence punctuation or footnote refs
- Footnotes: 165 definitions in `(N) text` format after §399
- Inline `[N]` refs stripped from body; recorded in `footnotes` dict per paragraph
- **Limitation:** exact inline footnote positions are lost; footnote numbers are
  appended at paragraph end in `girm-src-la.md`

### UK (E&W 2011)
- Two-column A4 PDF (75 pages); footnotes extracted spatially (area < 180 pt from bottom)
- §287 on a two-column page — recovered via pdfminer spatial extraction

### US (USCCB 2010)
- 12 HTML chapter files; hyphenation artefacts fixed post-extraction:
  `cate-chesis`, `concele-brants`, `cele-brant`, `concele-brated`, `cele-brated` (§§ 13, 239, 242, 249, 274, 373)
- Date spacing fixed: `June24` → `June 24` in §346

### Slovak (SK 2021)
- Two-column PDF (54 pages); pdftotext unreliable; pdfminer used throughout
- Soft hyphens removed from 347 paragraphs: `vstupné- ho` → `vstupného`
- Trailing glued footnote numbers removed from 12 paragraphs: `jazykov164` → `jazykov`

---

## Key Design Decisions

1. **Latin is the universal base** — `girm-master.md` uses the Latin text as the
   universal paragraph, not the UK ICEL as a proxy.

2. **Slovak norms are always separate** — the Slovak VSRM contains no embedded
   adaptations. KBS norms appear as blockquotes marked "NOT embedded in VSRM text".

3. **`cache/` is committed** — LLM comparison results represent a one-time scholarly
   analysis. Committing them means the repo is self-contained and reproducible without
   an API key for normal operation.

4. **`out/` is committed** — generated documents are committed so the repository is
   immediately usable without running the pipeline.

5. **Section headings from Latin** — `SECTION_HEADINGS` in `generate.py` is built
   from `extracted/la.json` (118 headings), not US/UK sources, for authoritative structure.

6. **All output is English-only** — `girm-master.md` and `girm-altar-servers.md` are
   entirely in English. Latin terms quoted in context are fine; foreign prose is not.

---

## Known Limitations

- **Latin footnote inline positions** — positions lost during extraction; appended at paragraph end.
- **Latin source quality** — WordPress transcription, not a direct scan of the LEV typeset edition.
- **SK heading count** — only 36 headings recovered from Slovak PDF vs 118 from Latin HTML;
  two-column PDF makes heading detection harder.
- **US heading format** — stored as `[level, text]` pairs (from old HTML extractor); LA/SK
  use plain strings. Normalised at render time.
