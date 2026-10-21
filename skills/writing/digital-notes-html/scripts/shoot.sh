#!/usr/bin/env bash
# Screenshot a rendered page headless and split it into readable parts.
#
#   shoot.sh <page.html> [outdir]     -> outdir/part0.png, part1.png, ...
#
# Serves the page's folder on a free local port, because a Windows-side browser
# cannot open a WSL file path directly. Read the parts back to check layout:
# label collisions, overflow, wrapped grids.
set -euo pipefail

page=$(realpath "$1")
out=$(realpath -m "${2:-$(dirname "$page")/shots}")
mkdir -p "$out"

# The shim drives the headless Windows Chrome; fall back to whatever is on PATH.
ab="$HOME/.local/share/agent-browser-shim/agent-browser"
[ -x "$ab" ] || ab=agent-browser

port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
python3 -m http.server "$port" --bind 127.0.0.1 --directory "$(dirname "$page")" >/dev/null 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null' EXIT
sleep 1

"$ab" open "http://localhost:$port/$(basename "$page")" >/dev/null
"$ab" set viewport 1280 900 >/dev/null 2>&1 || true
sleep 1
"$ab" screenshot --full "$out/full.png" >/dev/null

python3 - "$out" <<'EOF'
import sys
from pathlib import Path
from PIL import Image
out = Path(sys.argv[1])
im = Image.open(out / "full.png")
w, h = im.size
for old in out.glob("part*.png"):
    old.unlink()
n = (h + 1799) // 1800
for i in range(n):
    im.crop((0, i * 1800, w, min(h, (i + 1) * 1800))).save(out / f"part{i}.png")
print(f"{w}x{h} -> {n} parts in {out}")
EOF
