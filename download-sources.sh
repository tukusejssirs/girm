#!/usr/bin/env bash
# download-sources.sh
# Downloads all three GIRM source texts and pushes them to the GitHub repo.
# Run this on your own machine (not in the Claude container).
# Requires: curl, git, pdftotext (poppler-utils)
#
# Usage:
#   chmod +x download-sources.sh
#   ./download-sources.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
RAW_DIR="$REPO_ROOT/raw"

mkdir -p "$RAW_DIR/usccb"

echo "==================================================================="
echo " GIRM Source Downloader"
echo "==================================================================="

# -----------------------------------------------------------------------
# 1. VATICAN 2003 (single HTML page)
# -----------------------------------------------------------------------
echo ""
echo ">>> [1/3] Vatican 2003 (HTML)"
VATICAN_URL="https://www.vatican.va/roman_curia/congregations/ccdds/documents/rc_con_ccdds_doc_20030317_ordinamento-messale_en.html"

curl \
	--silent \
	--show-error \
	--fail \
	--compressed \
	--user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0" \
	--output "$RAW_DIR/vatican-2003.html" \
	"$VATICAN_URL"

SIZE=$(wc -c < "$RAW_DIR/vatican-2003.html")
echo "    Saved: raw/vatican-2003.html ($SIZE bytes)"

# -----------------------------------------------------------------------
# 2. UK PDF (Liturgy Office, 2011)
# -----------------------------------------------------------------------
echo ""
echo ">>> [2/3] UK PDF (Liturgy Office 2011)"
UK_URL="https://www.liturgyoffice.org.uk/Resources/GIRM/Documents/GIRM.pdf"

curl \
	--silent \
	--show-error \
	--fail \
	--compressed \
	--user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0" \
	--output "$RAW_DIR/girm-uk-2011.pdf" \
	"$UK_URL"

SIZE=$(wc -c < "$RAW_DIR/girm-uk-2011.pdf")
echo "    Saved: raw/girm-uk-2011.pdf ($SIZE bytes)"

# Extract text from PDF (requires poppler-utils)
if command -v pdftotext &> /dev/null; then
	pdftotext -layout "$RAW_DIR/girm-uk-2011.pdf" "$RAW_DIR/girm-uk-2011.txt"
	echo "    Extracted: raw/girm-uk-2011.txt"
else
	echo "    WARNING: pdftotext not found — skipping text extraction."
	echo "    Install with: sudo apt install poppler-utils  (or brew install poppler)"
fi

# -----------------------------------------------------------------------
# 3. USCCB 2010 (multi-page HTML)
# -----------------------------------------------------------------------
echo ""
echo ">>> [3/3] USCCB 2010 (multi-page HTML)"

BASE_URL="https://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal"

PAGES=(
	"girm-table-of-contents"
	"girm-foreword"
	"girm-introduction"
	"girm-chapter-1"
	"girm-chapter-2"
	"girm-chapter-3"
	"girm-chapter-4"
	"girm-chapter-5"
	"girm-chapter-6"
	"girm-chapter-7"
	"girm-chapter-8"
	"girm-chapter-9"
)

for PAGE in "${PAGES[@]}"; do
	curl \
		--silent \
		--show-error \
		--fail \
		--compressed \
		--user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0" \
		--output "$RAW_DIR/usccb/${PAGE}.html" \
		"${BASE_URL}/${PAGE}"

	SIZE=$(wc -c < "$RAW_DIR/usccb/${PAGE}.html")
	echo "    Saved: raw/usccb/${PAGE}.html ($SIZE bytes)"

	# Be polite — 1s delay between requests
	sleep 1
done

# -----------------------------------------------------------------------
# Verify completeness
# -----------------------------------------------------------------------
echo ""
echo "==================================================================="
echo " Download summary"
echo "==================================================================="
echo ""

check_file() {
	local FILE="$1"
	local MIN_BYTES="$2"
	local LABEL="$3"
	local SIZE
	SIZE=$(wc -c < "$FILE" 2>/dev/null || echo 0)
	if [[ "$SIZE" -ge "$MIN_BYTES" ]]; then
		echo "  ✓  $LABEL ($SIZE bytes)"
	else
		echo "  ✗  $LABEL — SUSPICIOUS: only $SIZE bytes (expected >=$MIN_BYTES)"
	fi
}

# Minimum expected sizes (conservative — actual files are much larger)
check_file "$RAW_DIR/vatican-2003.html"      300000  "Vatican 2003 HTML"
check_file "$RAW_DIR/girm-uk-2011.pdf"       500000  "UK PDF 2011"
check_file "$RAW_DIR/usccb/girm-foreword.html"   5000  "USCCB foreword"
check_file "$RAW_DIR/usccb/girm-introduction.html" 20000 "USCCB introduction"
check_file "$RAW_DIR/usccb/girm-chapter-1.html"   20000 "USCCB chapter 1"
check_file "$RAW_DIR/usccb/girm-chapter-2.html"   80000 "USCCB chapter 2"
check_file "$RAW_DIR/usccb/girm-chapter-3.html"   30000 "USCCB chapter 3"
check_file "$RAW_DIR/usccb/girm-chapter-4.html"  100000 "USCCB chapter 4"
check_file "$RAW_DIR/usccb/girm-chapter-5.html"   40000 "USCCB chapter 5"
check_file "$RAW_DIR/usccb/girm-chapter-6.html"   30000 "USCCB chapter 6"
check_file "$RAW_DIR/usccb/girm-chapter-7.html"   20000 "USCCB chapter 7"
check_file "$RAW_DIR/usccb/girm-chapter-8.html"   20000 "USCCB chapter 8"
check_file "$RAW_DIR/usccb/girm-chapter-9.html"   20000 "USCCB chapter 9"

echo ""
echo "==================================================================="
echo " Pushing to GitHub"
echo "==================================================================="
echo ""

cd "$REPO_ROOT"
git add raw/
git commit -m "feat: add raw source downloads (Vatican 2003, UK PDF 2011, USCCB 2010)"
git push

echo ""
echo "Done. Check the summary above for any ✗ failures before proceeding."
