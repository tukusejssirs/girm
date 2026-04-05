#!/usr/bin/env python3
"""
clean-uk-pdf.py — cleans girm-uk-2011-simple.txt (pdftotext without -layout)
"""

import re
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src/girm-uk/girm-uk-2011-simple.txt"
DST = Path(__file__).parent / "src/girm-uk/girm-uk-2011-clean.txt"

text = SRC.read_text(encoding="utf-8")

# 1. Strip \b and \f
text = text.replace("\x08", "").replace("\x0c", "")

# 2. Remove running headers/footers
RUNNING_HEADER_PATTERNS = [
    r"^Introduction \d+$",
    r"^\d+ General Instruction of the Roman Missal$",
    r"^General Instruction of the Roman Missal \d+$",
    r"^The Importance and Dignity.*\d+$",
    r"^The Structure of the Mass.*\d+$",
    r"^Duties and Ministries.*\d+$",
    r"^The Different Forms.*\d+$",
    r"^The Arrangement.*\d+$",
    r"^The Requisites.*\d+$",
    r"^The Choice of the Mass.*\d+$",
    r"^Masses.*\d+$",
    r"^Adaptations.*\d+$",
    r"^Contents (iii|iv|v|vi|\d+)$",
    r"^Chapter (I{1,3}|IV|V|VI{1,3}|IX) \d+$",
]
combined = re.compile("|".join(RUNNING_HEADER_PATTERNS), re.MULTILINE)
text = combined.sub("", text)

# 3. Trim everything before "Introduction\n" that immediately precedes §1
#    Find §1 first, then look back for the nearest "Introduction" heading
start_para = re.search(r"(?m)^1\. As Christ the Lord", text)
if not start_para:
    print("ERROR: §1 not found", file=sys.stderr)
    sys.exit(1)

# Look for "Introduction" heading within 500 chars before §1
preamble = text[:start_para.start()]
intro_match = list(re.finditer(r"(?m)^Introduction\s*$", preamble))
if intro_match:
    text = text[intro_match[-1].start():]
else:
    text = text[start_para.start():]

# 4. Normalise blank lines
text = re.sub(r"\n{3,}", "\n\n", text)

# 5. Strip trailing whitespace per line
lines = [l.rstrip() for l in text.splitlines()]
text = "\n".join(lines)

# Strip leading/trailing whitespace on the whole doc
text = text.strip() + "\n"

# 6. Write
DST.write_text(text, encoding="utf-8")

remaining_b  = text.count("\x08")
remaining_ff = text.count("\x0c")
print(f"Written  : {DST}", file=sys.stderr)
print(f"Lines    : {text.count(chr(10)):,}", file=sys.stderr)
print(f"Chars    : {len(text):,}", file=sys.stderr)
print(f"\\b left  : {remaining_b}", file=sys.stderr)
print(f"\\f left  : {remaining_ff}", file=sys.stderr)

for para in ["1.", "43.", "91.", "150.", "288.", "350.", "386.", "399."]:
    m = re.search(rf"(?m)^{re.escape(para)} ", text)
    status = f"line {text[:m.start()].count(chr(10))+1}" if m else "MISSING !!!"
    print(f"  §{para:<5} {status}", file=sys.stderr)
