#!/usr/bin/env python3
"""build_server_doc.py — generates out/girm-altar-servers.md"""

import json, re, textwrap
from pathlib import Path

ROOT = Path(__file__).parent
OUT  = ROOT / "out"

uk_data = json.loads((ROOT/"extracted/uk.json").read_text(encoding="utf-8"))
us_data = json.loads((ROOT/"extracted/us.json").read_text(encoding="utf-8"))
va_data = json.loads((ROOT/"extracted/va.json").read_text(encoding="utf-8"))
uk_map  = {p["num"]: p for p in uk_data["paragraphs"]}
us_map  = {p["num"]: p for p in us_data["paragraphs"]}
va_map  = {p["num"]: p for p in va_data["paragraphs"]}
uk_gfn  = uk_data["footnotes"]

used_fns = {}

def to_uq(text):
    if not text: return text
    text = re.sub(r"[\u0027\u0060\u02BC\u2018]", "\u2019", text)
    text = re.sub(r'[\u0022\u201A\u201B\u201E]',  "\u201C", text)
    return text

def wrap(text, width=100):
    text = re.sub(r"  +", " ", text)
    out = []
    for line in text.split("\n"):
        if line.startswith(("-","#","[",">"," ")):
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(out)

def collect_fns(num):
    p = uk_map.get(num, {})
    for k, v in p.get("footnotes", {}).items():
        used_fns[int(k)] = v

def gfn(*nums):
    s = ""
    for n in nums:
        v = uk_gfn.get(str(n), "")
        if v: used_fns[n] = v
        s += f"[^{n}]"
    return s

def pcite(*nums):
    for n in nums: collect_fns(n)
    return ", ".join(f"§{n}" for n in nums)

def blockquote(num, start=None, end=None):
    collect_fns(num)
    p = uk_map.get(num)
    if not p: return ""
    text = p["text"]
    if start:
        idx = text.find(start)
        if idx >= 0: text = text[idx:]
    if end:
        idx = text.find(end)
        if idx >= 0: text = text[:idx+len(end)]
    lines = []
    for line in wrap(text, 96).split("\n"):
        lines.append(f"> {line}")
    lines.append(f">")
    lines.append(f"> — §{num}")
    return "\n".join(lines)

lines = []
def L(*args):
    for a in args: lines.append(a)
def blank(): lines.append("")
def h2(t):  lines.append(f"## {t}"); blank()
def h3(t):  lines.append(f"### {t}"); blank()
def h4(t):  lines.append(f"#### {t}"); blank()
def BQ(num, start=None, end=None):
    lines.append(blockquote(num, start, end)); blank()
def rule(text, *paras, fns=()):
    for n in paras: collect_fns(n)
    for n in fns:
        v = uk_gfn.get(str(n),""); 
        if v: used_fns[n] = v
    cites = " *(" + ", ".join(f"§{n}" for n in paras) + ")*" if paras else ""
    fn_str = "".join(f"[^{n}]" for n in fns)
    lines.append(f"- {text}{cites}{fn_str}")
def note(text): lines.append(f"> **Note:** {text}"); blank()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
L(
"# Altar Servers and Ministers at the Altar",
"## Rules, Instructions, and Norms from the General Instruction of the Roman Missal",
"",
"> **Source:** *General Instruction of the Roman Missal* (GIRM), Third Typical Edition.",
"> Base text: England & Wales 2011 (ICEL translation). All paragraph references (§) are to the GIRM",
"> unless otherwise stated. Footnotes follow the UK 2011 edition.",
"> Where the USCCB 2010 (US) or Vatican 2003 (VA) text differs materially, this is noted.",
"",
"---",
""
)

# ── 1. Theological Basis ─────────────────────────────────────────────────────
h2("1. Theological Basis and General Principle")
L(wrap(
    f"In the Church, as the Body of Christ, not all members have the same function. "
    f"The diversity of offices is made outwardly visible in the Eucharistic celebration by "
    f"the diversity of sacred vestments and the distinct roles each minister fulfils. *({pcite(335)})*"
), "")
BQ(17)
L(wrap(
    f"The celebration of Mass should be ordered so that each participant — sacred minister "
    f"and faithful alike — carries out their proper part, no more and no less. *({pcite(17)})*"
), "")

# ── 2. Categories of Ministers ────────────────────────────────────────────────
h2("2. Categories of Ministers at the Altar")
h3("2.1 The Instituted Acolyte")
BQ(98)
L(wrap(
    f"The instituted acolyte is the proper, ordinary minister for service at the altar. "
    f"His functions (§§187–193) are proper to him and he must carry them out in person. *({pcite(98)})*"
), "")

h3("2.2 Non-Instituted (Deputed) Altar Servers")
BQ(100)
L(wrap(
    f"In the absence of an instituted acolyte, the pastor or rector may depute suitable lay persons "
    f"by liturgical blessing or temporary deputation for the functions listed in §§100–106. *({pcite(107)})*"
), "")
note(
    "**The norms of the Diocesan Bishop govern the function of serving the Priest at the altar** "
    f"*(§107)*. Servers must observe the bishop's particular norms alongside universal law."
)

h3("2.3 Substitution When a Minister Is Absent")
L(wrap(
    f"*({pcite(116)})* It is desirable that an acolyte, a reader, and a cantor should usually "
    f"be present. When a Deacon is present he should exercise his function; likewise any "
    f"instituted acolyte present should exercise his."
), "")
L(wrap(
    f"*({pcite(208)})* If a Deacon is not present, his functions are carried out by some of the "
    f"concelebrants, or, if ministers are absent, by other suitable faithful laypeople; "
    f"otherwise they are not done by anyone."
), "")
rule(
    "**Deacon present, no acolyte:** A deputed server may assist the Deacon in preparing "
    "the altar and carrying items. However, §178 is explicit: *the Deacon himself takes care "
    "of the sacred vessels* — a server does not handle the chalice or vessels in the Deacon's presence.",
    178, 208
)
rule(
    "**Deacon absent, acolyte present, additional servers present:** The acolyte is responsible "
    "for the sacred vessels and altar preparation (§190). Deputed servers may carry items "
    "from the credence table to the altar and assist the acolyte, but the acolyte handles "
    "the actual placement and preparation of the chalice.",
    178, 190
)
rule(
    "**Deacon absent, no acolyte:** An 'other lay minister' may place the corporal, purificator, "
    "chalice, pall, and Missal on the altar (§139). Any deputed server may perform this.",
    139
)
blank()

h3("2.4 Other Lay Ministers")
rule(
    "In the absence of an instituted lector, suitably prepared lay people may be deputed "
    "to proclaim the readings from Sacred Scripture.",
    101
)
rule(
    "A person fulfilling the reader role (whether instituted or deputed) may, in the "
    "absence of a Deacon, carry the *Book of the Gospels* slightly elevated in procession. "
    "They may not proclaim the Gospel — that belongs to the Deacon or Priest.",
    194, 59
)
blank()

# ── 3. Vestments ─────────────────────────────────────────────────────────────
h2("3. Vestments and Attire")
L(
f"*({pcite(336)})* The **alb**, tied at the waist with a cincture unless made to fit without, "
"is the sacred garment common to all ordained and instituted ministers of any rank. "
"Before the alb, an amice may be put on.",
""
)
L(wrap(
    f"*({pcite(339)})* Acolytes, readers, and other lay ministers may wear the alb "
    "or **other suitable attire legitimately approved by the Bishops' Conference** (cf. §390). "
    "The alb is the universal norm; cassock and surplice (or similar local attire) are an "
    "approved alternative only where the relevant Bishops' Conference has specifically authorised them. "
    "They are not the universal default for servers."
), "")
note(
    "§339 concerns the attire of **lay ministers and servers**. "
    "Priests wear alb, stole, and chasuble (§337); the Deacon wears alb, stole, and dalmatic "
    f"(§338). A stole or dalmatic is never worn by a non-ordained minister."
)

# ── 4. The Altar Before Mass ──────────────────────────────────────────────────
h2("4. The Altar Before Mass and the Rule on What May Be Placed on It")
BQ(306)
L(wrap(
    f"*({pcite(306)})* The altar table must remain bare at the start of Mass "
    "(apart from candles and the altar cross, which stand beside or on the altar at all times — §307–308). "
    "The *Book of the Gospels* may be placed on the altar from the beginning of the celebration "
    "until after the Gospel. The chalice, corporal, pall, purificator, and Missal are brought to "
    "the altar only from the Presentation of the Gifts onward."
), "")
note(
    "**Candles and the altar cross are always present** regardless of the phase of Mass (§307–308). "
    "Everything else must wait until Offertory."
)
blank()

# ── 5. Preparation Before Mass ────────────────────────────────────────────────
h2("5. Preparation Before Mass")
h3("5.1 The Sacristy")
L(
f"*({pcite(119)})* The following should be prepared in the sacristy:",
"",
f"- **For the Priest:** the alb, stole, and chasuble *(§119)*",
f"- **For the Deacon:** the alb, stole, and dalmatic; the dalmatic may be omitted for lesser "
  "solemnity or necessity *(§119, §338)*",
f"- **For other ministers:** albs or other lawfully approved attire *(§119, §339)*",
""
)

h3("5.2 What Must Be Prepared and Where")
L(
f"*({pcite(118)})* The following should be prepared:",
"",
"- **Next to the Priest's chair:** the Missal and, if appropriate, a hymnal *(§118a)*",
"- **At the ambo:** the Lectionary *(§118b)*",
"- **On the credence table:** the chalice, corporal, purificator, pall; paten and ciborium; "
  "cruets with wine and water; communion plate; book of the prayers of the faithful; "
  "if incense is used: thurible and boat *(§118c)*",
"- **At the altar:** the Book of the Gospels if it is to be placed there at the start, and nothing else *(§118d, §306)*",
""
)

# ── 6. Procession and Introductory Rites ─────────────────────────────────────
h2("6. The Procession to the Altar and Introductory Rites")
h3("6.1 Order of the Entrance Procession")
BQ(120)
L(
f"*({pcite(120, 172, 188)})* The order is:",
"",
"1. **Thurifer** carrying the smoking thurible (if incense is used) *(§120a)*",
"2. **Ministers with lighted candles**, with the **cross-bearer** (acolyte or other minister) "
   "between them *(§120b)*",
"3. **Acolytes and other ministers** *(§120c)*",
"4. **Reader** carrying the *Book of the Gospels* slightly elevated, if no Deacon is present *(§120d, §194)*",
"5. **Deacon**, if present, carrying the *Book of the Gospels* slightly elevated, "
   "preceding or walking alongside the Priest *(§172)*",
"6. **Priest Celebrant** *(§120e)*",
"",
"The **recessional** follows the same order. *({pcite(193)})*",
""
)

h3("6.2 Arrival at the Altar")
rule("All ministers reverence the altar with a profound bow upon arrival. "
     "Those carrying the processional cross or candles bow the head instead of a profound bow.", 49, 122, 274)
rule("The Priest and Deacon venerate the altar with a kiss; "
     "other ministers do not kiss the altar.", 49, 273)
rule("The acolyte places the cross upright near the altar as the altar cross, "
     "or puts it in a dignified place, then takes his place in the sanctuary.", 188)
blank()

h3("6.3 Presenting the Book at the Chair — Introductory Rites")
rule(
    "Throughout the celebration, the acolyte (or server) approaches the Priest or Deacon "
    "whenever necessary to present the Missal. This is most needed **at the chair**: "
    "for the Greeting, Penitential Act, Gloria, Collect, Creed, Universal Prayer, "
    "Prayer over the Offerings (if said at the chair), and Prayer after Communion. "
    "**At the Eucharistic Prayer the Missal is on the altar** (§306) and does not need to be held.",
    189, 306
)
blank()

h3("6.4 The Profession of Faith (Creed)")
L(wrap(
    f"*({pcite(67, 68)})* The Creed is sung or said by the Priest together with the people "
    f"on **Sundays and Solemnities**, after the Homily. It may also be used at other more "
    f"solemn celebrations. At the words *et incarnatus est* (and by the Holy Spirit… and became man), "
    f"all make a profound bow of the body; on the Nativity of the Lord and the Annunciation, "
    f"all genuflect."
), "")
rule("All — Priest, ministers, and faithful — make a profound bow of the body at *et incarnatus est*. "
     "On Christmas and the Annunciation, all genuflect instead.", 137)
blank()

# ── 7. Liturgy of the Word ────────────────────────────────────────────────────
h2("7. Liturgy of the Word")
h3("7.1 The Readings")
rule("The readings are proclaimed by a reader; the Gospel by the Deacon or, "
     "in his absence, another Priest. If neither is present, the Priest Celebrant reads the Gospel.", 59)
rule("The reader takes his place and reads the readings that precede the Gospel. "
     "In the absence of a psalmist, the reader may also proclaim the Responsorial Psalm.", 196)
blank()

h3("7.2 Incensation Before the Gospel")
rule("If incense is used, during the *Alleluia* or other chant the Deacon ministers to "
     "the Priest as he puts incense in the thurible. "
     "If no Deacon is present, the server (thurifer) presents the thurible and assists.", 175, 276)
rule("Before and after incensing the *Book of the Gospels*, a profound bow is made to it.", 277)
blank()

h3("7.3 The Homily")
L(wrap(
    f"*({pcite(66)})* The Homily is given by the Priest Celebrant or entrusted to a "
    f"concelebrating Priest, or from time to time to the Deacon, "
    f"**but never to a lay person.**{gfn(65, 66)}"
), "")

h3("7.4 The Profession of Faith — see §6.4 above")

h3("7.5 The Universal Prayer (Prayer of the Faithful)")
L(wrap(
    f"*({pcite(69, 70, 71)})* The Universal Prayer follows the Creed (or, when the Creed "
    f"is not said, the Homily). The intentions may be announced from the ambo or another "
    f"suitable place by a cantor, reader, or other person."
), "")
blank()

# ── 8. Liturgy of the Eucharist ───────────────────────────────────────────────
h2("8. Liturgy of the Eucharist")
h3("8.1 Preparation of the Altar and the Gifts (Offertory)")
BQ(139)
L(wrap(
    f"*({pcite(178)})* When the Deacon is present, he prepares the altar assisted by the "
    f"acolyte, but it is **the Deacon's place to take care of the sacred vessels himself**. "
    f"When no Deacon is present, the acolyte performs these duties (§190)."
), "")
rule("Any deputed server may place the corporal, purificator, chalice, pall, and Missal "
     "on the altar when no instituted acolyte is present. *({pcite(139)})*")
rule("Any deputed server may carry the bread, wine, and water to the altar, "
     "and assist the Priest in receiving the gifts of the people.", 100, 190)
rule("When acolyte is present but Deacon absent: deputed servers may carry items "
     "from the credence table; the acolyte handles the actual placement and pours the wine and water.", 178, 190)
rule("A server does not place the consecrated hosts on the altar — the server carries "
     "the paten or ciborium to the Priest (or Deacon or acolyte), who then places it "
     "on the altar with the prescribed formula.", 73, 100, 190)
blank()

h3("8.2 Incensation of the Gifts, Cross, and Altar")
rule("If incense is used, the Priest puts incense in the thurible, blesses it, and "
     "incenses the offerings, cross, and altar. "
     "A minister (the thurifer) stands at the side of the altar and incenses the Priest and people.", 75, 144, 276)
rule("Before and after incensing any person or object, a profound bow is made to them, "
     "**except for the altar and the offerings**.", 277)
blank()

h3("8.3 The Eucharistic Prayer and Consecration")
rule("The server holds the Missal for the Priest at the chair whenever needed during the "
     "celebration. **During the Eucharistic Prayer itself, the Missal is on the altar** and "
     "does not need to be held.", 189, 306)
rule("**The bell (optional):** A little before the Consecration, *if appropriate*, a minister may ring "
     "a small bell as a signal to the faithful. At each elevation the bell may also be rung "
     "*according to local custom*. Both usages are optional, not obligatory.", 150)
rule("**Incensation at the Consecration (optional):** If incense is used, a minister incenses "
     "the host and the chalice when each is shown to the people after the Consecration, "
     "with three swings of the thurible.", 150, 276, 277)
blank()

# ── 9. Communion Rite ─────────────────────────────────────────────────────────
h2("9. Communion Rite")
h3("9.1 Lord's Prayer, Rite of Peace")
rule("During the Lord's Prayer and Rite of Peace, servers observe the same postures as "
     "the faithful. They do not exchange the peace before the faithful unless directed.", 82, 83)
blank()

h3("9.2 Who Distributes Holy Communion")
L(wrap(
    f"*({pcite(162)})* The Priest may be assisted by other Priests who happen to be present. "
    f"If no Priest is available and there is **a truly large number of communicants**, the Priest may "
    f"call upon extraordinary ministers: duly instituted acolytes or **other faithful who have been "
    f"duly deputed** for this purpose.{gfn(97, 98)}"
), "")
note(
    "**A regular (non-instituted) server may distribute Holy Communion** if deputed by the Priest "
    f"when necessity requires, even on a single occasion *(§162)*{gfn(97, 98)}. "
    "Such deputation follows the rite in *Roman Missal*, Appendix III. "
    "They must not approach the altar before the Priest has received Communion, and must receive "
    "the vessel from the Priest Celebrant's hands."
)
blank()

h3("9.3 The Chalice at Communion under Both Kinds")
L(wrap(
    f"*({pcite(284)})* The chalice is administered by: the Deacon; in his absence, a Priest; "
    f"or a duly instituted acolyte; **or another extraordinary minister of Holy Communion, "
    f"whether instituted or deputed**."
), "")
note(
    "A server who has been deputed as an extraordinary minister (even for a single occasion) "
    "may administer the chalice. A server who has **not** been deputed as an EMHC "
    "may **not** hold or administer the chalice at Communion."
)
rule("If Communion from the chalice is by intinction, the minister holds the chalice "
     "while the Priest or EMHC intincts the host and distributes it.", 287)
blank()

h3("9.4 'Preparing the Chalice' Before Distribution")
L(wrap(
    f"*({pcite(285)})* When Communion is distributed under both kinds, the chalice(s) must "
    f"be prepared in advance: one large chalice or several chalices of sufficient size are needed. "
    f"'Preparing the chalice' means making it available for distribution (uncovering the pall, "
    f"positioning it for the EMHC). There is no special liturgical action required beyond "
    f"what the Deacon or acolyte would perform in the course of normal altar preparation."
), "")
blank()

h3("9.5 Purification of the Sacred Vessels")
BQ(279)
L(wrap(
    f"*({pcite(279)})* The order of those authorised to purify: "
    f"**(1) the Priest; (2) the Deacon; (3) a duly instituted acolyte.** "
    f"A non-instituted (deputed) server may **not** purify the sacred vessels."
), "")
rule("A duly instituted acolyte, in the absence of a Deacon, carries the sacred vessels "
     "to the credence table and purifies, wipes, and arranges them.", 192)
rule("Deputed (non-instituted) servers may carry **unconsecrated vessels** (empty cruets, "
     "purificator, etc.) but **not vessels that have contained the Blessed Sacrament** — "
     "those remain the acolyte's responsibility.", 192, 279)
blank()

# ── 10. Concluding Rites ─────────────────────────────────────────────────────
h2("10. Concluding Rites and Recessional")
rule("The Priest venerates the altar with a kiss after the Concluding Rites, then makes "
     "a profound bow with the lay ministers and withdraws.", 169)
rule("All make a profound bow to the altar before withdrawing.", 169)
rule("The recessional procession follows the same order as the entrance. *(§193)*")
blank()

# ── 11. Genuflections, Bows, and Reverence ───────────────────────────────────
h2("11. Genuflections, Bows, and Reverence")

h3("11.1 The Two Kinds of Bow")
L(
f"*({pcite(275)})* The GIRM distinguishes two kinds of bow:",
"",
"| Bow | When made |",
"|-----|-----------|",
"| **Bow of the head** | At the names of the three Divine Persons named *together* (e.g. *Father, Son, and Holy Spirit*; *the Holy Trinity*); at the name of Jesus; at the name of the Blessed Virgin Mary; at the name of the Saint in whose honour Mass is celebrated |",
"| **Bow of the body (= profound bow)** | To the altar; at *et incarnatus est* in the Creed; by the Priest at *Munda cor meum* and *In spiritu humilitatis*; by the Priest in the Roman Canon at *Supplices te rogamus*; by the Deacon before asking for the blessing before the Gospel |",
""
)
note(
    '"Bow of the body", "profound bow", and "deep bow" are all the same gesture in the GIRM '
    '*(§275)*. They are distinct from the bow of the head.'
)

h3("11.2 Head Bow — Who, When, and Where")
L(wrap(
    f"*({pcite(275)})* The head bow is made by all present (not only the Priest or ministers) "
    f"whenever the three Divine Persons are explicitly named together (e.g. *In the name of the "
    f"Father, and of the Son, and of the Holy Spirit*; the doxologies *Glory be to the Father…*), "
    f"and at the name of Jesus, the Blessed Virgin Mary, or the day's saint. "
    f"This applies throughout the Mass and, by the same logic of liturgical reverence, "
    f"during the Liturgy of the Hours and other liturgical rites."
), "")

h3("11.3 Profound Bow — Servers Specifically")
L(
f"*({pcite(275)})* For altar servers, the profound bow is made:",
"",
"- To the altar whenever approaching or departing from it *(§275b)*",
"- At *et incarnatus est* in the Creed, together with all the faithful *(§137)* — "
  "on the Nativity and Annunciation, a **genuflection** replaces the bow",
"- **Not** the private preparatory prayers (*Munda cor meum*, *In spiritu humilitatis*) — said by the Priest alone *(§275b)*",
"- **Not** the *Supplices te rogamus* in the Roman Canon — said by the Priest alone *(§275b)*",
"- **Not** the Deacon's pre-Gospel blessing bow — that is the Deacon's bow to the Priest *(§275b)*",
""
)

h3("11.4 Genuflection")
BQ(274)
L(
f"*({pcite(274)})* The rules for servers:",
"",
"- **If the tabernacle is in the sanctuary:** genuflect when approaching and departing the altar "
  "(before and after Mass). During Mass itself: no genuflections to the tabernacle; bow to the altar instead *(§274)*.",
"- **If the tabernacle is not in the sanctuary:** profound bow to the altar at approach and departure *(§274)*.",
"- **Passing before the Blessed Sacrament** (when not in procession): single genuflection *(§274)*.",
"- **Carrying the processional cross or candles:** bow the head instead of genuflecting *(§274)*. "
  "By extension, carrying any liturgical object (thurible, navicula, Book of the Gospels) "
  "warrants a head bow; the GIRM names only the cross and candles explicitly.",
""
)

h3("11.5 Passing Before or Behind the Altar")
L(wrap(
    f"*({pcite(274)})* The GIRM does not specify whether servers should pass in front of or "
    f"behind the altar. In practice: passing **behind** the altar (between altar and east wall "
    f"or tabernacle wall) avoids the need to genuflect or bow before the Blessed Sacrament "
    f"mid-action, and is the customary norm in many churches. Local practice and the layout "
    f"of the particular church govern this."
), "")

h3("11.6 Double Genuflection Before the Blessed Sacrament Exposed")
L(wrap(
    f"*({pcite(274)})* The GIRM prescribes only a **single genuflection** (right knee to the ground) "
    f"for the Blessed Sacrament reserved in the tabernacle. "
    f"A **double genuflection** (both knees, brief pause) is traditionally prescribed when "
    f"the Blessed Sacrament is **solemnly exposed** (e.g. during Benediction or Exposition) — "
    f"this comes from the *Caeremoniale Episcoporum* and eucharistic rites, not from the GIRM itself. "
    f"During Mass, when the Sacrament is in the tabernacle, a single genuflection suffices."
), "")

h3("11.7 Blessing at the End of Mass")
L(wrap(
    f"*({pcite(167, 168)})* At the final blessing, the faithful bow their heads. "
    f"*({pcite(275)})* §275 provides that a bow of the body is made when asking for a blessing; "
    f"at the final blessing of Mass the faithful bow the head as the Priest imparts it. "
    f"Servers bow the head with the rest of the assembly."
), "")
blank()

# ── 12. Incensation — Full Reference ─────────────────────────────────────────
h2("12. Incensation — All Occasions and Thurifer's Duties")
BQ(276)
L(wrap(
    f"*({pcite(276)})* **All uses of incense are optional** at every form of Mass. "
    f"When used, the thurifer prepares the thurible, maintains the coals, "
    f"and carries the thurible and incense boat throughout the celebration."
), "")
L(
"**Occasions when incense may be used** *(§276)*:",
"",
"| Occasion | Who incenses |",
"|----------|-------------|",
"| Entrance procession | Thurifer carries smoking thurible *(§120a)* |",
"| Beginning of Mass — cross and altar | Priest incenses the cross and altar *(§276b)* |",
"| Before the Gospel — *Book of the Gospels* | Deacon (or Priest) incenses the Book *(§175, §276c)* |",
"| Offertory — offerings, cross, altar, Priest, people | Priest (with server's assistance) *(§75, §144, §276d)* |",
"| Consecration — elevation of host and chalice | Server incenses host then chalice with three swings *(§150, §276e)* |",
""
)
L(wrap(
    f"*({pcite(277)})* **Three swings** of the thurible are used for: the Most Blessed Sacrament, "
    f"a relic of the Holy Cross or image of the Lord exposed, the offerings, the altar cross, "
    f"the *Book of the Gospels*, the paschal candle, the Priest, and the people. "
    f"**Two swings** for relics and images of Saints. **Single swings** are used to incense the altar "
    f"(the Priest walks around it if freestanding, or from right to left if against a wall)."
), "")
rule("Before and after incensing any person or object, a profound bow is made — "
     "**except for the altar and the offerings for the Sacrifice of the Mass** (§277).", 277)
blank()

# ── 13. Permitted and Prohibited ─────────────────────────────────────────────
h2("13. Summary: Permitted and Prohibited")

h3("13.1 Permitted for All Deputed Servers")
L(
"- Carry the processional cross *(§100, §188)*",
"- Carry lighted candles in procession *(§120b)*",
"- Carry the thurible as thurifer *(§100)*",
"- Present the Missal to the Priest or Deacon during the celebration *(§189)*",
"- Place the corporal, purificator, chalice, pall, and Missal on the altar when no "
  "instituted acolyte is present *(§139)*",
"- Carry the bread, wine, and water to the altar *(§100)*",
"- Hand the paten or ciborium to the Priest, Deacon, or acolyte at the Offertory *(§73, §100)*",
"- Ring the small bell before the Consecration and at the elevations, where customary *(§150)*",
"- Incense the host and chalice at the elevations (as thurifer) *(§150, §276e)*",
"- Carry unconsecrated vessels and liturgical items to and from the credence table *(§100)*",
"- Return in recessional procession to the sacristy *(§193)*",
""
)

h3("13.2 Permitted for Deputed Lay Persons — Including Single-Occasion Deputation")
L(
f"- Distribute Holy Communion as an extraordinary minister when necessity requires *(§162)*{gfn(97, 98)} — "
  "deputation by the Priest, even for a single occasion, suffices",
f"- Administer the chalice at Communion under both kinds, if deputed as an EMHC *(§284)*",
"- Proclaim the readings from Sacred Scripture when no instituted lector is present *(§101)*",
"- Carry the *Book of the Gospels* in procession when fulfilling the reader role, "
  "in the absence of a Deacon *(§194)*",
""
)

h3("13.3 Restricted to Instituted Acolytes")
L(
f"- Distribute Holy Communion as an extraordinary minister *in the ordinary/stable sense*, "
  f"apart from the single-occasion deputation available to any lay person *(§191)*{gfn(100)}",
"- Purify and arrange the sacred vessels at the credence table in the Deacon's absence *(§192, §279)*",
"- Carry sacred vessels that have contained the Blessed Sacrament to the credence table *(§192)*",
""
)

h3("13.4 Prohibited for Any Server or Lay Minister")
L(
"- Preach the Homily *(§66)*",
f"- Perform any act reserved to the **Priest or Bishop**: "
  "the Eucharistic Prayer, the words of Consecration, the words of absolution, "
  "or any presidential prayer *(§4, §93)*. "
  "**Note:** The Deacon does *not* pronounce the Eucharistic Prayer or consecrate — "
  "these are reserved to ordained Priests and Bishops.",
"- Purify the sacred vessels unless duly instituted as an acolyte *(§279)*",
"- Handle vessels containing or having contained the Blessed Sacrament unless authorised *(§192, §279)*",
"- Stand at or near the altar in a manner that implies ordination or clerical rank *(§335)*",
""
)

h3("13.5 Governed by the Diocesan Bishop's Norms *(§107)*")
L(
"The function of serving the Priest at the altar is specifically subject to "
f"norms established by the Diocesan Bishop *(§107)*{gfn(89)}. These may include:",
"",
f"- Whether women and girls may serve as altar servers *(§107)*{gfn(89)}",
"- The suitability and formation required before deputation *(§107)*",
"- The attire to be worn when the alb is not used *(§339)*",
"- Any particular ceremonies or gestures specific to the diocese *(§107)*",
""
)
L(
f"> **§107 (UK 2011):** *\u201cAs to the function of serving the Priest at the altar, "
f"the norms established by the Bishop for his diocese should be observed.\u201d*",
""
)

# ── 14. Vestments Quick Reference ─────────────────────────────────────────────
h2("14. Vestments for Servers — Quick Reference")
L(
"| Vestment | Who wears it | Notes |",
"|----------|-------------|-------|",
f"| **Alb** with cincture | All lay ministers and servers | Universal norm *(§336, §339)* |",
f"| **Alb** without cincture | Where alb is shaped to fit without | *(§336)* |",
f"| **Approved attire** (e.g. cassock and surplice) | Lay ministers and servers | Only where legitimately approved by the Bishops' Conference *(§339)*; not the universal default |",
""
)
L(wrap(
    f"*({pcite(336)})* The alb is to be tied at the waist with a cincture unless it is made "
    f"in such a way as to fit without one. A stole or dalmatic is **never** worn by a "
    f"non-ordained minister."
), "")
blank()

# ── 15. Bibliography ──────────────────────────────────────────────────────────
h2("15. Bibliography and Sources Referenced")
L(
"### Primary Liturgical Sources",
"",
"- **General Instruction of the Roman Missal** (*Institutio Generalis Missalis Romani*), "
  "Third Typical Edition. Vatican City: Libreria Editrice Vaticana, 2002. "
  "English translation: Catholic Bishops' Conference of England and Wales / ICEL, 2011.",
"- **General Instruction of the Roman Missal**, USCCB translation. "
  "Washington, D.C.: United States Conference of Catholic Bishops, 2010.",
"- **General Instruction of the Roman Missal**, Vatican (earlier ICEL translation), 2003.",
"",
"### Documents Cited in GIRM Footnotes",
"",
"- **Paul VI**, Apostolic Letter *Ministeria quaedam*, 15 August 1972: "
  "*AAS* 64 (1972), p. 532. [On instituted ministries, including the acolyte.]",
"- **Sacred Congregation for the Discipline of the Sacraments**, Instruction "
  "*Immensae caritatis*, 29 January 1973: *AAS* 65 (1973), pp. 265–266. "
  "[On extraordinary ministers of Holy Communion.]",
"- **Sacred Congregation for the Sacraments and Divine Worship**, Instruction "
  "*Inaestimabile donum*, 3 April 1980, no. 10: *AAS* 72 (1980), p. 336. "
  "[On extraordinary ministers and single-occasion deputation.]",
"- **Interdicasterial Instruction** *Ecclesiae de mysterio*, 15 August 1997, "
  "arts. 6, 8: *AAS* 89 (1997), pp. 864–871. "
  "[On collaboration of non-ordained faithful; service at the altar and EMHC.]",
"- **Pontifical Commission for the Interpretation of Legal Texts**, "
  "response to *dubium* regarding CIC can. 230 §2, 11 July 1992: "
  "*AAS* 86 (1994), p. 541. [Female altar servers: permissive, not obligatory.]",
"- **Code of Canon Law** (*Codex Iuris Canonici*), 1983: "
  "can. 230 §2–3 (deputation of lay persons); can. 910 §2 (EMHC); can. 767 §1 (Homily).",
"- **Roman Missal**, Appendix III: *Rite of Deputing a Minister to Distribute Holy Communion "
  "on a Single Occasion*.",
"",
"### Other Authoritative Documents",
"",
"- **Caeremoniale Episcoporum**, editio typica, 1984. "
  "[Governing ceremonies for Pontifical Masses and the role of ministers.]",
"- **Second Ecumenical Council of the Vatican** (Vatican II): "
  "Constitution on the Sacred Liturgy *Sacrosanctum Concilium*, 1963; "
  "Dogmatic Constitution on the Church *Lumen gentium*, 1964; "
  "Decree on the Ministry and Life of Priests *Presbyterorum ordinis*, 1965.",
""
)

# ── Footnotes ─────────────────────────────────────────────────────────────────
L("---", "")
L("## Footnotes", "")
for fn_n, fn_text in sorted(used_fns.items()):
    L(f"[^{fn_n}]: {fn_text}")
    blank()

OUT.mkdir(exist_ok=True)
output = re.sub(r"§§(\d)", r"§\1", "\n".join(lines))
(OUT/"girm-altar-servers.md").write_text(output, encoding="utf-8")
print(f"Written: out/girm-altar-servers.md ({output.count(chr(10))} lines)")
print(f"Footnotes: {sorted(used_fns.keys())}")
