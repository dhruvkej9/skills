#!/usr/bin/env bash
# Print a rendered page to an A4 PDF with headless Chrome.
#
#   pdf.sh <page.html> [out.pdf]     -> out.pdf, plus out-pages/page-N.png previews
#
# Page size, colours and page breaks come from the `@media print` rules in
# base.css, so the PDF matches the page without printer options. The previews
# (needs pdftoppm) are for checking breaks: a card cut in half, an orphan heading.
set -euo pipefail

page=$(realpath "$1")
pdf=$(realpath -m "${2:-${page%.html}.pdf}")

ab="$HOME/.local/share/agent-browser-shim/agent-browser"
[ -x "$ab" ] || ab=agent-browser

port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
python3 -m http.server "$port" --bind 127.0.0.1 --directory "$(dirname "$page")" >/dev/null 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null' EXIT
sleep 1

"$ab" open "http://localhost:$port/$(basename "$page")" >/dev/null
# Web fonts load after the page does; printing before them falls back to system fonts.
"$ab" eval "document.fonts.ready.then(() => document.fonts.size)" >/dev/null
"$ab" wait 500 >/dev/null
"$ab" pdf "$pdf" >/dev/null

if command -v pdfinfo >/dev/null; then
  pdfinfo "$pdf" | awk '/^Pages|^Page size/'
fi
if command -v pdftoppm >/dev/null; then
  prev="${pdf%.pdf}-pages"
  rm -rf "$prev" && mkdir -p "$prev"
  pdftoppm -r 50 -png "$pdf" "$prev/page"
  echo "previews in $prev"
fi
echo "wrote $pdf"
