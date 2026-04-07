# GIRM — Latin vs English: Semantic Fidelity Analysis

Comparison of the Latin *Institutio Generalis Missalis Romani*,
*editio typica tertia emendata* 2008, against the England & Wales 2011 ICEL
and USCCB 2010 ICEL translations.

**Scope:** meaning differences only — not word choice, rephrasing, or
natural expansion of Latin syntactic compression.
Known national adaptations (documented in `girm-diff-en.md`) are excluded.

---

## Known ICEL 2011 Translation Choices

These are deliberate translation decisions that differ from the most literal
rendering of the Latin. They are not errors; they are documented here as a
reference for liturgical software that needs to reason about the Latin original.

| Latin term | ICEL 2011 rendering | Alternative/literal | Significance |
|------------|---------------------|---------------------|--------------|
| *pro multis* | 'for many' | older ICEL: 'for all' | Restored literal rendering (2011 correction) |
| *praeses* | 'Priest' (as presider) | 'one who presides' | Functional vs hierarchical emphasis |
| *munus* | 'ministry', 'duty', 'function' | no single English equivalent | Context-dependent rendering throughout |
| *populus* / *plebs* | 'people', 'faithful' | distinct in Latin | Both rendered as 'people' in most contexts |
| *concio* | 'homily' | 'address', 'sermon' | Standardised in ICEL 2011 |
| *deprecatio* | 'prayer of petition' | 'intercession' | Nuanced prayer-type distinction |
| *oboedientia* | 'obedience' | 'submission' | Theological weight retained |

---

## Automated Concept-Gap Analysis

The following liturgically significant Latin concepts were checked against
both translations across all 399 paragraphs:

- **genuflexio — kneeling/genuflection** (*genuflect…* → 'kneel', 'genuflect'): Distinct from inclinatio (bow); must not be conflated.
- **inclinatio — bow** (*inclinatio…* → 'bow', 'inclin'): Shallow or profound bow; distinct from genuflexio.
- **humi prostratus — prostration** (*procumbit…* → 'prostrat'): Full prostration (Good Friday etc.); rare, high significance.
- **incensatio — incensation** (*incensat…* → 'incens'): Ritual use of incense; rubrical requirement in certain Masses.
- **concelebratio — concelebration** (*concelebr…* → 'concelebr'): Distinct form of Mass celebration with multiple priests.
- **tabernaculum — tabernacle** (*tabernacul…* → 'tabernacl'): Reservation of the Blessed Sacrament; canonical location rules.
- **reconciliatio — reconciliation** (*reconciliat…* → 'reconcil'): As distinct from penitential rite.
- **anamnesis — memorial/remembrance** (*anamnesi…* → 'memorial', 'anamnesi', 'remembrance'): Technical eucharistic theology term; distinct from mere 'memory'.
- **fractio panis — breaking of bread** (*fractio…* → 'break', 'fraction'): Distinct rite within the Communion rite.

**Result: 0 concept gaps found.**

The ICEL 2011 translation faithfully renders all checked concepts
across all 399 paragraphs in both the UK and US editions.
The ICEL 2011 revision (which restored *pro multis* → 'for many' and
corrected several earlier translation choices) appears complete and
consistent with the Latin original on the checked concepts.

*Note:* This automated check covers only the curated concept list above.
Subtle theological nuances in non-flagged terms (e.g. *munus*, *plebs*)
are documented in the Known Translation Choices table.