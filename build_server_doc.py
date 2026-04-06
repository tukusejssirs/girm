#!/usr/bin/env python3
"""
build_server_doc.py
Generates girm-altar-servers.md — rules and instructions for altar servers
from the GIRM, with all source refs as footnotes.
"""

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

used_fns = {}   # fn_num → text  (collected as we reference them)
para_refs = []  # ordered list of §N refs used

def to_unicode_quotes(text):
    if not text: return text
    text = re.sub(r"[\u0027\u0060\u02BC\u2018]", "\u2019", text)
    text = re.sub(r'[\u0022\u201A\u201B\u201E]',  "\u201C", text)
    return text

def wrap(text, width=100):
    text = re.sub(r"  +", " ", text)
    out = []
    for line in text.split("\n"):
        if line.startswith(("-", "#", "[", " ")):
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width) or [""])
    return "\n".join(out)

def para_cite(num, note=None):
    """Collect footnotes from §num and return its number as string (no § prefix)."""
    p = uk_map.get(num)
    if not p: return str(num)
    for k, v in p.get("footnotes", {}).items():
        used_fns[int(k)] = v
    return str(num)

def gfn(fn_num):
    """Reference a global UK footnote by number."""
    v = uk_gfn.get(str(fn_num), "")
    if v:
        used_fns[fn_num] = v
    return f"[^{fn_num}]"

def quote_para(num, start=None, end=None):
    """
    Return a block-quoted excerpt from §num.
    If start/end given, extract that substring.
    Collects all footnotes from that paragraph.
    """
    p = uk_map.get(num)
    if not p: return ""
    text = p["text"]
    # Collect fns
    for k, v in p.get("footnotes", {}).items():
        used_fns[int(k)] = v
    if start:
        idx = text.find(start)
        if idx >= 0:
            text = text[idx:]
    if end:
        idx = text.find(end)
        if idx >= 0:
            text = text[:idx+len(end)]
    return wrap(text, 96)

def us_note(num):
    """Return US-only addition/difference for a paragraph, if meaningful."""
    uk_p = uk_map.get(num, {})
    us_p = us_map.get(num, {})
    if not us_p: return None
    uk_t = uk_p.get("text","")
    us_t = us_p.get("text","")
    # Return US text only if substantially different
    if us_t != uk_t and len(us_t) > 20:
        return us_t
    return None


lines = []
def L(*args): lines.extend(args)
def blank(): lines.append("")
def h2(t): lines.append(f"## {t}"); blank()
def h3(t): lines.append(f"### {t}"); blank()
def h4(t): lines.append(f"#### {t}"); blank()
def blockquote(text, cite):
    for line in text.split("\n"):
        lines.append(f"> {line}")
    lines.append(f">")
    lines.append(f"> — {cite}")
    blank()
def rule(text, cite_para=None, extra_fns=None):
    """A single rule/instruction bullet with citation."""
    fn_refs = ""
    if cite_para:
        p = uk_map.get(cite_para, {})
        for k, v in p.get("footnotes", {}).items():
            used_fns[int(k)] = v
        fn_refs = f" *(§{cite_para})*"
    if extra_fns:
        for fn_n in extra_fns:
            v = uk_gfn.get(str(fn_n), "")
            if v: used_fns[fn_n] = v
            fn_refs += f"[^{fn_n}]"
    lines.append(f"- {text}{fn_refs}")


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

L(
"# Altar Servers and Ministers at the Altar",
"## Rules, Instructions, and Norms from the General Instruction of the Roman Missal",
"",
"> **Source:** *General Instruction of the Roman Missal*, Third Typical Edition.",
"> Base text: England & Wales 2011 (ICEL translation).",
"> All paragraph references are to the GIRM unless otherwise stated.",
"> Footnotes follow the UK 2011 edition; US 2010 differences are noted where significant.",
"",
"---",
"",
)

# ── 1. Theological basis ─────────────────────────────────────────────────────
h2("1. Theological Basis and General Principle")

L(wrap(
    "The Church, as the Body of Christ, has members with differing functions. "
    "This diversity of offices is made outwardly visible in the celebration of the Eucharist "
    "by the diversity of sacred vestments and the distinct roles each minister fulfils. "
    f"*(§{para_cite(335)})*"
), "")

blockquote(quote_para(17), "§17")

L(wrap(
    "It is therefore of the greatest importance that the celebration of Mass be so ordered "
    "that the sacred ministers and the faithful each carry out their proper part — "
    "no more, and no less. "
    f"*(§{para_cite(17)})*"
), "")

# ── 2. Categories of Ministers ────────────────────────────────────────────────
h2("2. Categories of Ministers at the Altar")

h3("2.1 The Instituted Acolyte")

blockquote(quote_para(98), "§98")

L(wrap(
    "The instituted acolyte is the proper, ordinary minister for service at the altar. "
    "His functions enumerated in §§187–193 are proper to him and he must carry them out personally. "
    f"His faculty as extraordinary minister of Holy Communion derives from canon law{gfn(84)} "
    "and from the Apostolic Letter *Ministeria quaedam*. *(§98)*"
), "")

h3("2.2 Non-Instituted (Deputed) Altar Servers")

blockquote(quote_para(100), "§100")

L(wrap(
    "In the absence of an instituted acolyte, the pastor or rector of the church may depute "
    "suitable lay persons by means of a liturgical blessing or temporary deputation "
    "to carry out the functions listed in §§100–106. "
    f"*(§{para_cite(107)})*"
), "")

L(
"> **Note:** The norms established by the Diocesan Bishop for his diocese govern the",
"> function of serving the Priest at the altar (§107). Servers must observe the bishop's",
"> particular norms in addition to the universal law expressed here.",
""
)

h3("2.3 Other Lay Ministers")

L(wrap(
    f"*(§{para_cite(101)})* In the absence of an instituted lector, "
    "suitably prepared lay people may be deputed to proclaim the readings. "
    "Where multiple functions are needed and only one minister is available, "
    "priority should be given to the more important duties (§187)."
), "")

L(wrap(
    "The reader, in the absence of a Deacon, may carry the *Book of the Gospels* slightly elevated "
    f"during the procession to the altar, wearing approved attire. *(§{para_cite(194)})*"
), "")

# ── 3. Vestments ─────────────────────────────────────────────────────────────
h2("3. Vestments and Attire")

L(
f"*(§{para_cite(336)})* The alb, tied at the waist with a cincture unless made otherwise, "
"is the sacred garment common to all ordained and instituted ministers.",
"",
f"*(§{para_cite(339)})* Acolytes, readers, and other lay ministers may wear the alb "
"or other suitable attire that has been legitimately approved by the Conference of Bishops. "
"This attire replaces the cassock and surplice where appropriate.",
""
)

# ── 4. Before Mass ────────────────────────────────────────────────────────────
h2("4. Preparation Before Mass")

h3("4.1 The Sacristy")

# §119 is long — quote just the server-relevant parts
L(
"In the sacristy there should be prepared, according to the form of celebration *(§119)*:",
"",
"- **For the Priest:** the alb, stole, and chasuble *(§119)*",
"- **For the Deacon:** the alb, stole, and dalmatic; dalmatic may be omitted for lesser solemnity or out of necessity *(§119)*",
"- **For other ministers:** albs or other lawfully approved attire *(§119, §339)*",
"",
"The ministers also prepare *(§118–119)*: the chalice, corporal, purificator, pall; paten and ciborium;",
"cruets with wine and water; the communion plate; the Missal; and, if used,",
"the thurible with incense, the processional cross, candles, and the Book of the Gospels.",
f"",
""
)

h3("4.2 What Ministers Must Prepare")

L(f"*(§{para_cite(118)})* The following should be prepared:")
L(
"- Next to the Priest's chair: the Missal and, if appropriate, a hymnal *(§118a)*",
"- At the ambo: the Lectionary *(§118b)*",
"- At the credence table: the chalice, corporal, purificator, and pall; "
  "paten and ciborium; cruets with wine and water; "
  "book of the prayers of the faithful; thurible and boat if incense is used *(§118c)*",
"- At the altar: the chalice, corporal, and Missal if not placed elsewhere *(§118d)*",
""
)

# ── 5. The Procession and Introductory Rites ─────────────────────────────────
h2("5. The Procession to the Altar and Introductory Rites")

h3("5.1 Order of Procession")

blockquote(quote_para(120), "§120")

h3("5.2 Actions on Arrival at the Altar")

rule(
    "Upon reaching the sanctuary, the Priest, Deacon, and ministers reverence the altar "
    "with a profound bow. Ministers carrying the cross or candles reverence the altar by "
    "standing in place.",
    cite_para=49
)
rule(
    "If incense is used, the Priest incenses the cross and altar after kissing the altar; "
    "the cross is carried and placed near the altar or in another dignified place.",
    cite_para=49
)
rule(
    "The acolyte places the cross upright near the altar so it may serve as the altar cross; "
    "otherwise it is put away in a dignified place. The acolyte then takes his place in the sanctuary.",
    cite_para=188
)
blank()

h3("5.3 The Penitential Act and Gloria")

L(wrap(
    f"*(§{para_cite(50)})* When the Entrance Chant is concluded, the Priest stands at the chair "
    "and together with the whole assembly makes the Sign of the Cross. "
    "Ministers make the same gesture as the faithful throughout."
), "")

# ── 6. Liturgy of the Word ────────────────────────────────────────────────────
h2("6. Liturgy of the Word")

h3("6.1 The Readings")

L(wrap(
    f"*(§{para_cite(59)})* The function of proclaiming the readings is by tradition "
    "not presidential but ministerial; the readings are to be read by a reader, "
    "and the Gospel by a Deacon or, in his absence, by another Priest."
), "")

rule(
    "During the Gospel acclamation (*Alleluia* or other chant), if incense is used, "
    "the Deacon or Priest ministers to the other as he prepares for the Gospel. "
    "In a Mass without a Deacon, the server presents the thurible.",
    cite_para=175
)

h3("6.2 The Homily")

L(wrap(
    f"*(§{para_cite(66)})* The Homily should ordinarily be given by the Priest Celebrant or "
    "entrusted to a concelebrating Priest or Deacon. "
    "It is never to be given by a lay person."
    f"{gfn(66)}"
), "")

h3("6.3 Incensation at the Gospel")

L(wrap(
    f"*(§{para_cite(175)})* During the singing of the *Alleluia* or other chant, "
    "if incense is being used, the Deacon ministers to the Priest as he puts incense into the thurible "
    "and blesses it. The server assists by holding the thurible."
), "")

h3("6.4 Universal Prayer")

L(wrap(
    f"*(§{para_cite(66)})* The intentions of the Universal Prayer may be announced "
    "by a cantor, reader, or other person at the ambo or another suitable place."
), "")

# ── 7. Liturgy of the Eucharist ───────────────────────────────────────────────
h2("7. Liturgy of the Eucharist")

h3("7.1 Preparation of the Altar and the Gifts")

blockquote(quote_para(139), "§139")

L(wrap(
    f"*(§{para_cite(178)})* After the Universal Prayer, while the Priest remains at the chair, "
    "the Deacon prepares the altar, assisted by the acolyte. If no Deacon is present, "
    "this falls to the acolyte alone (§190)."
), "")

rule(
    "The acolyte (or, in his absence, another minister) places on the altar: "
    "the corporal, the purificator, the chalice, the pall, and the Missal.",
    cite_para=190
)
rule(
    "If necessary, the acolyte assists the Priest in receiving the gifts of the people "
    "and, if appropriate, brings the bread and wine to the altar and hands them to the Priest.",
    cite_para=190
)
rule(
    "If incense is used, the acolyte presents the thurible to the Priest and assists him "
    "while he incenses the offerings, the cross, and the altar. "
    "The acolyte then incenses the Priest and the people.",
    cite_para=190
)
rule(
    "The faithful may also bring gifts of bread and wine in procession. "
    "The minister receives these and places them in a suitable place.",
    cite_para=140
)
blank()

h3("7.2 The Eucharistic Prayer")

rule(
    "The server holds the Missal for the Priest at the chair whenever needed. "
    "Throughout the celebration, the acolyte approaches the Priest or Deacon, whenever necessary, "
    "to present the book or to assist in any other way required.",
    cite_para=189
)
rule(
    "A little before the Consecration, *if appropriate*, a minister may ring a small bell "
    "as a signal to the faithful. At each elevation the bell may also be rung "
    "*according to local custom*. Both usages are optional, not required.",
    cite_para=150
)
blank()

h3("7.3 Communion Rite")

h4("7.3.1 Lord's Prayer and Rite of Peace")

L(wrap(
    f"*(§{para_cite(165)})* After the Communion of the Priest, "
    "if Communion under both kinds is distributed, "
    "the Deacon or minister prepares the chalice."
), "")

h4("7.3.2 Distribution of Holy Communion")

rule(
    "A duly *instituted* acolyte, as an extraordinary minister, may assist the Priest "
    "in distributing Communion when necessary.",
    cite_para=191, extra_fns=[100]
)
rule(
    "If Communion is given under both kinds and a Deacon is absent, "
    "the instituted acolyte administers the chalice or holds it if Communion is by intinction.",
    cite_para=191
)
rule(
    "A non-instituted server may be deputed as extraordinary minister of Holy Communion "
    "when the number of communicants is great and neither Priest, Deacon, "
    "nor instituted acolyte is available.",
    cite_para=100, extra_fns=[85]
)

L(wrap(
    f"*(§{para_cite(284)})* When Communion is distributed under both kinds: "
    "the chalice is usually administered by a Deacon or, in his absence, a Priest; "
    "or a duly deputed acolyte or other extraordinary minister."
), "")

h4("7.3.3 Purification")

rule(
    "After Communion is complete, the instituted acolyte helps the Priest or Deacon "
    "to purify and arrange the sacred vessels.",
    cite_para=192
)
rule(
    "In the absence of a Deacon, a duly instituted acolyte carries the sacred vessels "
    "to the credence table and there purifies, wipes, and arranges them as usual.",
    cite_para=192
)
rule(
    "Non-instituted servers do not purify the sacred vessels; "
    "this function belongs to the Priest, Deacon, or instituted acolyte.",
    cite_para=279, extra_fns=[84]
)
blank()

# ── 8. Concluding Rites ───────────────────────────────────────────────────────
h2("8. Concluding Rites and Recessional")

L(wrap(
    f"*(§{para_cite(169)})* After the Concluding Rites, the Priest venerates the altar "
    "with a kiss and, after making a profound bow with the lay ministers, withdraws."
), "")

blockquote(quote_para(193), "§193")

# ── 9. Genuflections and Bows ─────────────────────────────────────────────────
h2("9. Genuflections and Bows")

h3("9.1 Genuflection")

blockquote(quote_para(274), "§274")

rule(
    "A server who passes before the Most Blessed Sacrament present in the tabernacle "
    "or exposed for adoration genuflects.",
    cite_para=274
)
rule(
    "If the tabernacle is not in the sanctuary, ministers make a profound bow "
    "to the altar rather than a genuflection at the beginning and end of Mass.",
    cite_para=274
)

h3("9.2 Bows")

blockquote(quote_para(275), "§275")

rule(
    "A deep bow of the body is made: to the altar if the tabernacle is not present; "
    "to the Bishop; to the Priest when asking for a blessing.",
    cite_para=275
)

# ── 10. Incensation ────────────────────────────────────────────────────────────
h2("10. Incensation — Duties of the Thurifer")

rule(
    "The thurifer carries the smoking thurible at the head of the entrance procession, "
    "walking before the ministers with lighted candles.",
    cite_para=120
)
rule(
    "The thurifer presents the thurible to the Priest for blessing, assists with incensing "
    "the altar and offerings, and incenses the Priest and people when directed.",
    cite_para=190
)
rule(
    f"*(§{para_cite(144)})* The Priest puts incense into the thurible, "
    "blesses it without saying anything, and incenses the offerings, the cross, and the altar. "
    "The thurifer holds and swings the thurible as the Priest directs."
, "")

# ── 11. Distribution of Functions ─────────────────────────────────────────────
h2("11. Distribution of Functions among Servers")

blockquote(quote_para(187), "§187")

L(wrap(
    f"*(§{para_cite(116)})* It is desirable that an acolyte, a reader, and a cantor "
    "should usually be there to assist the Priest Celebrant. "
    "The rite foresees an even greater number of ministers."
), "")

L(wrap(
    f"*(§{para_cite(106)})* It is desirable, at least in cathedrals and larger churches, "
    "to have a master of ceremonies to direct the orderly carrying out of the rites."
), "")

# ── 12. Permitted and Prohibited ──────────────────────────────────────────────
h2("12. Summary: Permitted and Prohibited")

h3("12.1 Permitted for All Deputed Servers")

L(
"- Carry the processional cross *(§100, §188)*",
"- Carry lighted candles in procession *(§120)*",
"- Carry the thurible *(§100)*",
"- Present the book to the Priest or Deacon *(§189)*",
"- Place and remove the corporal, purificator, chalice, pall, and Missal *(§190)*",
"- Bring the bread and wine to the altar *(§100, §190)*",
"- Carry water and wine cruets *(§100)*",
"- Ring the bell before the Consecration and at the elevations *(§150)*",
"- Assist with the presentation of the thurible during incensation *(§190)*",
"- Return in procession to the sacristy with the Priest and Deacon *(§193)*",
""
)

h3("12.2 Restricted to Instituted Acolytes")

L(
"- Distribute Holy Communion as an extraordinary minister *(§191)*"
f"[^{sorted(used_fns)[0] if used_fns else 100}]",
)
# overwrite
lines[-1] = (
    f"- Distribute Holy Communion as an extraordinary minister "
    f"*(§191)*{gfn(100)}"
)
L(
"- Administer the chalice at Communion under both kinds in the Deacon's absence *(§191)*",
f"- Purify and arrange sacred vessels at the credence table in the Deacon's absence *(§192)*{gfn(84)}",
""
)

h3("12.3 Permitted for Deputed Lay Persons (Not Reserved to Instituted Ministers)")

L(
f"- Serve as extraordinary minister of Holy Communion when necessity requires *(§100)*{gfn(85)}",
"- Proclaim the readings from Sacred Scripture when no instituted lector is present *(§101)*",
"- Carry the *Book of the Gospels* in procession (reader, in the Deacon's absence) *(§194)*",
""
)

h3("12.4 Prohibited for Any Server or Lay Minister")

L(
"- Preach the Homily *(§66)*",
"- Perform any act reserved to the Priest or Deacon: Eucharistic Prayer, Consecration, "
  "words of absolution, or any presidential prayer *(§4, §5, §24)*",
"- Purify sacred vessels unless duly instituted as an acolyte *(§279)*",
"- Stand within the sanctuary in a manner that implies ordination or higher ministry *(§335)*",
""
)

h3("12.5 Governed by the Diocesan Bishop's Norms")

L(
"The function of serving the Priest at the altar is specifically subject to",
"norms established by the Diocesan Bishop *(§107)*. These may include:",
"",
"- Whether women and girls may serve as altar servers *(§107)*[^89]",
"- The suitability and formation required of candidates before deputation *(§107)*",
"- The attire to be worn when the alb is not used *(§339)*",
"- Any particular ceremonies or gestures specific to the diocese *(§107)*",
""
)

L("> **§107 (UK 2011):** *\u201cAs to the function of serving the Priest at the altar, the norms")
L("> established by the Bishop for his diocese should be observed.\u201d*")
blank()

L(
"> **Pontifical Commission for the Interpretation of Legal Texts (2001):** The permission",
"> for female altar servers in §230 §2 of the Code of Canon Law is permissive, not obligatory.",
f"> Each bishop may permit or not permit female servers in his diocese.{gfn(89)}",
""
)

# ── 13. Vestments quick reference ─────────────────────────────────────────────
h2("13. Vestments for Servers")

L(
"| Vestment | Who wears it | Notes |",
"|----------|--------------|-------|",
"| Alb with cincture | Ordained ministers; instituted acolytes; deputed servers | Standard liturgical garment *(§336)* |",
"| Alb without cincture | Where alb is made to be worn without *(§336)* | |",
"| Approved attire (e.g. cassock + surplice) | Lay ministers and servers | Where legitimately approved by the Bishops' Conference *(§339)* |",
""
)

L(wrap(
    f"*(§{para_cite(336)})* The alb is to be tied at the waist with a cincture unless it is "
    "made in such a way as to fit even without a cincture. A stole or dalmatic is not worn "
    "by non-ordained ministers."
), "")

# ── Footnotes ─────────────────────────────────────────────────────────────────
L("---", "")
L("## Footnotes", "")

for fn_n, fn_text in sorted(used_fns.items()):
    L(f"[^{fn_n}]: {fn_text}")
    blank()

# ─────────────────────────────────────────────────────────────────────────────
OUT.mkdir(exist_ok=True)
output = "\n".join(lines)
(OUT/"girm-altar-servers.md").write_text(output, encoding="utf-8")
print(f"Written: out/girm-altar-servers.md ({output.count(chr(10))} lines)")
print(f"Footnotes used: {sorted(used_fns.keys())}")
