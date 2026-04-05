#!/usr/bin/env bash
# download-usccb.sh — standalone USCCB downloader with better headers/redirect handling
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
RAW_DIR="$REPO_ROOT/raw/usccb"
mkdir -p "$RAW_DIR"

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

# Fetch one page to get session cookie first
COOKIE_JAR="$RAW_DIR/.cookies.txt"

echo "Seeding session cookie..."
curl \
	--silent \
	--location \
	--max-redirs 10 \
	--cookie-jar "$COOKIE_JAR" \
	--user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0" \
	--header "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
	--header "Accept-Language: en-GB,en;q=0.5" \
	--header "Accept-Encoding: gzip, deflate, br" \
	--header "Connection: keep-alive" \
	--header "Upgrade-Insecure-Requests: 1" \
	--output /dev/null \
	"https://www.usccb.org/" 2>&1

echo "Downloading USCCB pages..."
for PAGE in "${PAGES[@]}"; do
	OUT="$RAW_DIR/${PAGE}.html"
	URL="${BASE_URL}/${PAGE}"

	HTTP_CODE=$(curl \
		--silent \
		--location \
		--max-redirs 10 \
		--cookie "$COOKIE_JAR" \
		--cookie-jar "$COOKIE_JAR" \
		--user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0" \
		--header "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
		--header "Accept-Language: en-GB,en;q=0.5" \
		--header "Accept-Encoding: gzip, deflate, br" \
		--header "Referer: https://www.usccb.org/prayer-and-worship/the-mass/general-instruction-of-the-roman-missal" \
		--header "Connection: keep-alive" \
		--compressed \
		--write-out "%{http_code}" \
		--output "$OUT" \
		"$URL")

	SIZE=$(wc -c < "$OUT" 2>/dev/null || echo 0)
	echo "  ${PAGE}: HTTP ${HTTP_CODE} | ${SIZE} bytes"

	if [[ "$HTTP_CODE" != "200" ]]; then
		echo "    WARNING: non-200 response for ${PAGE}"
		head -5 "$OUT" 2>/dev/null || true
	fi

	sleep 2
done

echo ""
echo "Done. Committing and pushing..."
cd "$REPO_ROOT"
git add raw/usccb/
git commit -m "feat: add USCCB raw HTML pages"
git push
