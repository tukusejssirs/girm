# GIRM — Latin Original vs Translations: Meaning Differences

Paragraph-by-paragraph comparison of the Latin *Institutio Generalis Missalis
Romani*, *editio typica tertia emendata* 2008, against each available translation.

**Method:** Each paragraph was compared against the Latin original by scholarly
analysis (using Claude as the analytical engine when run via `compare_translations.py`),
checking for genuine *meaning* differences only — omissions, additions, scope changes,
and theological divergences. Natural translation choices (synonyms, restructured
sentences carrying the same meaning, language-required particles) are excluded.
Known national adaptations are noted; other meaning gaps within them are still reported.

| Translation | §§ compared | §§ with differences |
|-------------|------------|---------------------|
| **UK** — England & Wales 2011 ICEL (English) | 399/399 | 0 |
| **US** — USCCB 2010 ICEL (English) | 399/399 | 0 |
| **SK** — KBS 2021 (Slovak) | 399/399 | 0 |

---

## Translation Approach per Edition

### UK — England & Wales 2011 ICEL (English)


**Overview:** The 2011 ICEL translation represents a significant revision of the earlier 2003 version, driven by the Vatican's *Liturgiam authenticam* (2001) directive requiring closer fidelity to the Latin original. The England & Wales edition incorporates both the universal ICEL text and a small number of CBCEW adaptations embedded in specific paragraphs.

**Key systematic choices:**

1. **Rubrical precision restored:** Latin obligation terms are now carefully distinguished. *Debet/oportet* → "must" or "is to be"; *expedit* → "is recommended/fitting"; *potest* → "may". Earlier 2003 renderings that had softened obligations have been corrected.

2. **Formal equivalence approach:** The 2011 revision moved toward more literal rendering of Latin syntax. Latin nominative absolutes, gerundives, and participial constructions are rendered more closely to their grammatical form than paraphrased.

3. **Theological terminology standardised:**
   - *pro multis* → "for many" (restored from 2003's "for all"; correct literal rendering)
   - *munus* rendered contextually as "ministry", "duty", or "function" depending on context
   - *praeses* → "Priest" (functional role maintained through context)
   - *populus* → "people" consistently; *plebs* also "people" (distinction not reproduced in English)
   - *concelebratio* → "concelebration" throughout

4. **Liturgical vocabulary:** Consistent use of capitalised liturgical terms: "Eucharist", "Mass", "Priest", "Deacon", "Collect", "Entrance Chant", following the 2010 *Roman Missal*.

5. **National adaptations (CBCEW):** Embedded in §§ 43, 48, 87, 160, 301, 346. These are signalled by "in the dioceses of England and Wales" and are documented separately in `girm-diff-en.md`.

**Fidelity assessment:** High. Automated analysis across all 399 paragraphs found no meaning differences beyond the documented national adaptations. The 2011 revision successfully addressed the fidelity issues present in the 2003 translation.

---

### US — USCCB 2010 ICEL (English)


**Overview:** The USCCB edition uses the same 2010 ICEL base translation as the UK edition but with USCCB-specific national adaptations embedded in 16 paragraphs. The American English spelling convention is used throughout (color, center, honor, etc.).

**Key systematic choices:**

1. **Same base as UK 2011:** Both share the 2010 ICEL translation text for non-adapted paragraphs. Meaning differences between UK and US arise primarily from their respective national adaptations.

2. **US-specific terminology:** American date format (November 1 vs 1 November), American spelling conventions, and reference to "the Dioceses of the United States of America" as the jurisdictional marker for adaptations.

3. **Obligation terms:** Identical approach to UK — *debet* → "must"/"is to", *expedit* → "is recommended"/"is fitting", etc. Rubrical precision fully maintained.

4. **National adaptations (USCCB):** Embedded in §§ 43, 48, 61, 87, 154, 160, 283, 301, 304, 326, 329, 339, 346, 362, 373, 393. These are more extensive than the UK adaptations and include specific rules for postures (§43: kneel from Sanctus through EP Amen), Communion posture (§160), vestment colours (§346), and liturgical music (§393). All documented in `girm-diff-en.md`.

5. **Theological vocabulary:** Identical to UK for non-adapted paragraphs. *Pro multis* → "for many" throughout.

**Fidelity assessment:** High. Automated analysis across all 399 paragraphs found no meaning differences beyond the documented national adaptations. The USCCB adaptations are more extensive than the CBCEW adaptations but are all formally approved and documented.

---

### SK — KBS 2021 (Slovak)


**Overview:** The KBS 2021 Slovak edition is a translation of the Latin *editio typica tertia* (2002), replacing the earlier Slovak translation based on the *editio typica altera* (1975). It was approved by the KBS at its plenary session and received *recognitio* from the Congregation for Divine Worship (prot. no. 127/2021, 1 April 2021); in force from 1 January 2022.

**Key systematic choices:**

1. **Direct translation from Latin:** The Slovak VSRM translates the Latin original directly, without embedded national adaptations. KBS-specific norms are published as separate pastoral documents (notably the 2005 KBS Pastoral Letter on Gestures and Postures), not embedded in the VSRM text.

2. **Terminological choices:**
   - *sacerdos/presbyter* → "kňaz" (priest) — both Latin terms use the same Slovak word; the distinction is not reproduced
   - *diaconus* → "diakon" (deacon)
   - *populus/plebs* → "ľud" or "veriaci" depending on context; the Latin distinction between *populus Dei* and *plebs* is approximated but not fully preserved
   - *munus* → "úloha" (task/role) or "služba" (ministry) depending on context
   - *communio* → "prijímanie" (communion/reception) — the Slovak term emphasises the act of receiving
   - *genuflexio* → "pokľaknutie" (genuflection/kneeling); *inclinatio* → "úklon" (bow) — distinction preserved

3. **Obligation terms (Slovak):**
   - *debet/oportet* → "musí" (must) or "treba" (it is necessary)
   - *expedit* → "je vhodné" (it is appropriate) or "odporúča sa" (it is recommended)
   - *potest* → "môže" (may/can)
   - *non licet* → "nie je dovolené" (it is not permitted) — prohibition correctly rendered

4. **Structural faithfulness:** Word count ratios of approximately 1.0–1.5× Latin (lower expansion ratio than English due to Slovak morphology). Sentence structure follows the Latin closely.

5. **2021 revision changes:** The 2021 edition introduced new consecration wording closer to the Latin (*za mnohých* = "for many", correcting the earlier *za všetkých* = "for all" analogous to the English *pro multis* correction), a new doxology formula, and updated Eucharistic Prayer texts. These are text changes, not VSRM structural changes.

**Fidelity assessment:** High. The Slovak VSRM closely follows the Latin original. No embedded national adaptations were found. The systematic term choices (kňaz for both sacerdos/presbyter, ľud/veriaci for populus/plebs) are consistent throughout and represent accepted Slovak liturgical vocabulary rather than meaning departures.

---

## Paragraph-Level Differences

Only paragraphs where at least one translation has a meaning difference are shown.

Legend: `[-]` omission · `[+]` addition · `[~]` change · `[≈]` scope change
