#!/usr/bin/env python3
"""Render a notes JSON file into one self-contained HTML page.

    python3 render.py notes.json out.html
    python3 render.py --selftest

Content is JSON so the author writes only words and numbers; the look lives in
templates/base.css. Block types and inline markup are listed in SKILL.md.
Stdlib only.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "templates" / "base.css").read_text()

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700'
         '&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')

TIP_JS = """<script>
document.querySelectorAll('.chart').forEach(chart => {
  const tip = chart.querySelector('.tip');
  chart.querySelectorAll('.bar').forEach(bar => {
    bar.addEventListener('mousemove', e => {
      const box = chart.getBoundingClientRect();
      tip.textContent = bar.dataset.tip;
      tip.style.left = Math.min(e.clientX - box.left + 14, box.width - tip.offsetWidth - 8) + 'px';
      tip.style.top = (e.clientY - box.top - 38) + 'px';
      tip.classList.add('on');
    });
    bar.addEventListener('mouseleave', () => tip.classList.remove('on'));
  });
});
</script>"""

HEADING_CLASS = {"yellow": "", "pink": "pink", "green": "green", "blue": "blue"}
TAPE_CLASS = {"pink": "", "yellow": "y", "green": "g", "blue": "b"}
STICKY_CLASS = {"yellow": "", "pink": "pink", "green": "green", "blue": "blue"}
PEN_CLASS = {"green": "pen-green", "red": "pen-red", "blue": "pen-blue", "": ""}
GRADE_TONE = {"a": "a", "b": "b", "c": "c", "d": "d"}
CYCLE = ["yellow", "pink", "green", "blue"]


def md(text: str) -> str:
    """Escape, then apply the small inline markup the skill documents."""
    codes: list[str] = []

    def keep(m: re.Match) -> str:
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep, str(text))
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"==(.+?)==", r'<span class="mark-y">\1</span>', s)
    s = re.sub(r"!!(.+?)!!", r'<span class="mark-p">\1</span>', s)
    s = re.sub(r"\+\+(.+?)\+\+", r'<span class="mark-g">\1</span>', s)
    s = re.sub(r"~~(.+?)~~", r'<span class="strike">\1</span>', s)
    s = s.replace("-&gt;", "→").replace("\n", "<br>")
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def esc(text) -> str:
    return html.escape(str(text))


def list_items(items, cls="notes") -> str:
    out = [f'<ul class="{cls}">']
    for it in items:
        if isinstance(it, str):
            it = {"text": it}
        state = it.get("state", "")
        sub = list_items(it["sub"], "") if it.get("sub") else ""
        out.append(f'<li class="{esc(state)}">{md(it["text"])}{sub}</li>')
    out.append("</ul>")
    return "".join(out)


def b_p(b):
    margin = f'<span class="margin">{esc(b["margin"])}</span>' if b.get("margin") else ""
    return f'<p class="rel lead">{margin}{md(b["text"])}</p>'


def b_h3(b):
    return f"<h3>{esc(b['text'])}</h3>"


def b_list(b):
    return list_items(b["items"])


def b_grades(b):
    cells = "".join(
        f'<div class="grade {GRADE_TONE.get(g.get("tone", "b"), "b")}"><div class="letter">{esc(g["letter"])}</div>'
        f'<div class="file">{esc(g["file"])}</div><div class="why">{md(g.get("why", ""))}</div></div>'
        for g in b["items"])
    return f'<div class="verdict">{cells}</div>'


def b_stickies(b):
    cells = "".join(
        f'<div class="sticky {STICKY_CLASS.get(s.get("color", CYCLE[i % 4]), "")}">{md(s["title"])}'
        f'<small>{md(s.get("small", ""))}</small></div>'
        for i, s in enumerate(b["items"]))
    cols = "three" if len(b["items"]) >= 3 else "two"
    return f'<div class="grid {cols}" style="margin-top:22px">{cells}</div>'


def b_cards(b):
    cells = []
    for i, c in enumerate(b["items"]):
        tape = TAPE_CLASS.get(c.get("tape", ["green", "pink", "yellow", "blue"][i % 4]), "")
        pen = PEN_CLASS.get(c.get("pen", ""), "")
        cells.append(f'<div class="card"><span class="tape {tape}"></span><h4 class="{pen}">{md(c["title"])}</h4>'
                     f'{list_items(c.get("items", []))}</div>')
    cols = "three" if len(b["items"]) >= 3 else "two"
    return f'<div class="grid {cols}">{"".join(cells)}</div>'


def b_diff(b):
    rows = []
    for line in b["lines"]:
        cls = {"+": "add", "-": "del"}.get(line[:1], "dim")
        rows.append(f'<span class="{cls}">{esc(line)}</span>')
    return f'<pre class="diff">{chr(10).join(rows)}</pre>'


def b_conflict(b):
    def side(s):
        return f'<div class="side"><span class="src">{esc(s["src"])}</span>{md(s["text"])}</div>'
    return f'<div class="conflict">{side(b["left"])}<div class="vs">{esc(b.get("vs", "vs"))}</div>{side(b["right"])}</div>'


def b_todo(b):
    rows = []
    for t in b["items"]:
        done = "done" if t.get("done") else ""
        eta = f'<span class="eta">{esc(t["eta"])}</span>' if t.get("eta") else ""
        rows.append(f'<li class="{done}">{md(t["text"])}{eta}</li>')
    return f'<ul class="notes todo">{"".join(rows)}</ul>'


def b_stats(b):
    cells = "".join(
        f'<div class="stat {esc(s.get("tone", ""))}"><div class="num">{esc(s["num"])}</div>'
        f'<div class="label">{md(s.get("label", ""))}</div></div>'
        for s in b["items"])
    return f'<div class="stats">{cells}</div>'


def b_table(b):
    head = "".join(f"<th>{esc(h)}</th>" for h in b["headers"])
    body = "".join("<tr>" + "".join(f"<td>{md(c)}</td>" for c in r) + "</tr>" for r in b["rows"])
    return f'<table class="sheet"><tr>{head}</tr>{body}</table>'


def b_bars(b):
    """Single-series horizontal bars, one hue, value labels, hover tips, table fallback."""
    rows = b["rows"]
    label_w = max(150, min(260, 8 * max(len(r["label"]) for r in rows) + 16))
    bar_max = 760 - label_w - 120
    top = max(r["value"] for r in rows) or 1
    h = 46 * len(rows) + 16
    parts = []
    for i, r in enumerate(rows):
        y = 18 + 46 * i
        w = max(4, round(bar_max * r["value"] / top))
        x = label_w + 12
        soft = " soft" if r.get("soft") else ""
        disp = r.get("display", r["value"])
        tip = r.get("tip") or f'{r["label"]}: {disp}'
        parts.append(
            f'<g class="bar" data-tip="{esc(tip)}">'
            f'<text x="{label_w}" y="{y + 16}" text-anchor="end" fill="var(--ink)">{esc(r["label"])}</text>'
            f'<rect class="mark{soft}" x="{x}" y="{y}" width="{w}" height="24" rx="4"/>'
            f'<text x="{x + w + 8}" y="{y + 17}" fill="var(--ink-2)">{esc(disp)}</text>'
            f'<rect class="hit" x="0" y="{y - 6}" width="820" height="36"/></g>')
    aria = "; ".join(f'{r["label"]} {r.get("display", r["value"])}' for r in rows)
    table_rows = "".join(f'<tr><td>{esc(r["label"])}</td><td>{esc(r.get("display", r["value"]))}</td></tr>' for r in rows)
    return (f'<div class="chart"><div class="title">{esc(b["title"])}</div><div class="sub">{md(b.get("sub", ""))}</div>'
            f'<svg viewBox="0 0 820 {h}" width="100%" role="img" aria-label="{esc(b["title"])}: {esc(aria)}">'
            f'<g class="bars" font-size="13">{"".join(parts)}</g>'
            f'<line x1="{label_w + 12}" y1="10" x2="{label_w + 12}" y2="{h - 8}" stroke="var(--rule)"/></svg>'
            f'<div class="tip"></div><details class="table"><summary>the numbers as a table</summary>'
            f'<table><tr><th>{esc(b.get("label_header", "item"))}</th><th>{esc(b.get("value_header", "value"))}</th></tr>{table_rows}</table></details></div>')


def b_hub(b):
    """One box on the left fanning out to labelled boxes, with an optional pen note."""
    spokes = b["spokes"]
    n = len(spokes)
    h = max(150, 46 * n + 30)
    cy = h / 2
    box_w = max(150, 8 * max(len(s["label"]) for s in spokes) + 30)
    sx, nx = 336, 336 + box_w + 14
    parts = [f'<rect x="14" y="{cy - 35}" width="170" height="70" rx="12" fill="var(--hl-yellow)" stroke="var(--ink)" stroke-width="1.6"/>',
             f'<text x="99" y="{cy - 5}" text-anchor="middle" font-size="15" font-weight="600" fill="var(--ink)">{esc(b["center"]["title"])}</text>',
             f'<text x="99" y="{cy + 16}" text-anchor="middle" font-size="12" fill="var(--ink-2)">{esc(b["center"].get("sub", ""))}</text>']
    for i, s in enumerate(spokes):
        y = 14 + i * (h - 60) / (n - 1) if n > 1 else cy - 16
        my = y + 16
        parts.append(f'<path d="M190,{cy} C250,{cy} 260,{my} {sx - 6},{my}" fill="none" stroke="var(--ink-2)" stroke-width="1.6" marker-end="url(#ah)"/>')
        parts.append(f'<rect x="{sx}" y="{y}" width="{box_w}" height="32" rx="8" fill="var(--card)" stroke="var(--rule)"/>')
        parts.append(f'<text x="{sx + 14}" y="{y + 21}" font-size="13" fill="var(--ink)">{esc(s["label"])}</text>')
        if s.get("note"):
            parts.append(f'<text x="{nx}" y="{y + 21}" font-size="12" fill="var(--ink-3)">{esc(s["note"])}</text>')
    if b.get("aside"):
        for j, word in enumerate(b["aside"].split("\n")):
            yy = cy - 10 + j * 24
            parts.append(f'<text x="770" y="{yy}" style="font-family: Caveat, cursive" font-size="22" fill="var(--red-pen)" transform="rotate(-6 770 {yy})">{esc(word)}</text>')
    cap = f'<figcaption>{md(b["caption"])}</figcaption>' if b.get("caption") else ""
    return (f'<figure><svg viewBox="0 0 860 {h}" width="100%" role="img" aria-label="{esc(b.get("aria", b["center"]["title"]))}">'
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="var(--ink-2)"/></marker></defs>'
            f'{"".join(parts)}</svg>{cap}</figure>')


def b_figure(b):
    cap = f'<figcaption>{md(b["caption"])}</figcaption>' if b.get("caption") else ""
    return f'<figure>{b["svg"]}{cap}</figure>'


def b_html(b):
    return b["html"]


BLOCKS = {name[2:]: fn for name, fn in globals().items() if name.startswith("b_")}


def block(b) -> str:
    kind = b.get("type")
    if kind not in BLOCKS:
        raise ValueError(f"unknown block type {kind!r}; known: {', '.join(sorted(BLOCKS))}")
    return BLOCKS[kind](b)


def render(doc: dict) -> str:
    cover = "".join(block(b) for b in doc.get("cover", []))
    heading = "<br>".join(esc(x) for x in doc["heading"].split("\n"))
    sections = []
    for i, s in enumerate(doc["sections"]):
        color = s.get("color", CYCLE[i % 4])
        sections.append(f'<h2 class="{HEADING_CLASS.get(color, "")}">{esc(s["heading"])}</h2>'
                        + "".join(block(b) for b in s.get("blocks", [])))
    footer = f'<p class="divider hand" style="font-size:24px">~ ~ ~</p><footer>{md(doc["footer"])}</footer>' if doc.get("footer") else ""
    uses_bars = any(b.get("type") == "bars" for s in doc["sections"] for b in s.get("blocks", []))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(doc["title"])}</title>
{FONTS}
<style>
{CSS}
</style>
</head>
<body>
<div class="page">
<header class="cover">
  <span class="date">{esc(doc.get("date", ""))}</span>
  <h1>{heading}</h1>
  <p class="subtitle">{md(doc.get("subtitle", ""))}</p>
  {cover}
</header>
{"".join(sections)}
{footer}
</div>
{TIP_JS if uses_bars else ""}
</body>
</html>
"""


def selftest() -> None:
    doc = json.loads((ROOT / "templates" / "example.json").read_text())
    out = render(doc)
    for kind in BLOCKS:
        assert any(b.get("type") == kind for s in doc["sections"] for b in s.get("blocks", [])) or \
            any(b.get("type") == kind for b in doc.get("cover", [])), f"example.json does not exercise {kind}"
    assert md("`a<b>` **x** ==y== !!z!! ++w++ ~~v~~ ->") == (
        '<code>a&lt;b&gt;</code> <strong>x</strong> <span class="mark-y">y</span> '
        '<span class="mark-p">z</span> <span class="mark-g">w</span> <span class="strike">v</span> →')
    assert "<script>" in out and "{" not in out.split("<title>")[1].split("</title>")[0]
    try:
        block({"type": "nope"})
    except ValueError:
        pass
    else:
        raise AssertionError("unknown block type must fail")
    print(f"selftest ok: {len(BLOCKS)} block types, {len(out):,} bytes")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(render(json.loads(Path(sys.argv[1]).read_text())))
        print(f"wrote {sys.argv[2]}")
    else:
        sys.exit(__doc__)
