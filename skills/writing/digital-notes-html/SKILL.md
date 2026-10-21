---
name: digital-notes-html
description: "Write a review, analysis or report as one aesthetic HTML page that reads like handwritten digital notes: dotted paper, handwritten headings, sticky notes, grades, charts. Use when asked for notes-style HTML, an aesthetic or human-looking review page, or more pages in the same notes format. Content is a JSON file; render.py builds the page and shoot.sh screenshots it for a layout check."
---

# Digital notes HTML

One self-contained page that looks like a careful person's notebook, not a
report. The author writes JSON (words and numbers only); `scripts/render.py`
owns the look. A new page costs one JSON file and two commands.

## Workflow

1. **Collect facts first.** Every number, file name and quote on the page is
   something you measured, read or fetched. Nothing estimated is shown as
   measured; say "est." when it is an estimate.
2. **Write `notes.json`** next to where the page goes. Start from
   `templates/example.json`, which uses every block once.
3. **Render:** `python3 scripts/render.py notes.json out/index.html`
4. **Look at it:** `bash scripts/shoot.sh out/index.html` writes
   `out/shots/part0.png`, `part1.png`, ... Read every part. Fix label collisions,
   clipped SVG, grids that wrap 4 + 1, text overflowing a card.
5. **Hand over the path.** On WSL give `wslpath -w out/index.html` so it opens
   from Windows.

`python3 scripts/render.py --selftest` checks the renderer after any edit to it.
Needs Python 3.9+; `shoot.sh` also needs Pillow and `agent-browser`.

## Writing style

- **Fragments, not sentences.** "handbook retold, 90 lines" beats "This file
  mostly restates the official handbook."
- **Headings are lowercase and handwritten:** "the verdict", "what changes".
  No emoji or symbols in section headings.
- **Flow tells a story:** cover (what this is, one diagram) -> verdict (grades,
  stickies, stats) -> details -> plan (todo). The reader should know the answer
  after the first screen.
- **Colour has a job.** Section heading colours cycle yellow, pink, green, blue
  unless set. Green = good or kept, red/pink = wrong or cut, amber = minor.
  Never colour alone: the word says it too.
- **Margin notes** (`"margin"` on a `p`) for the aside a person would scribble.
- **Link sources** with `[text](https://...)`, and only URLs you checked.
- **Charts:** one hue, value labels on the bars, the table view stays (`bars`
  adds it). No dual axes. A single number is a `stats` tile, not a chart.

## Document

```json
{
  "title": "browser tab title",
  "date": "small handwritten line above the heading",
  "heading": "Big heading\nsecond line",
  "subtitle": "one plain line under it",
  "cover": [blocks],
  "sections": [{"heading": "the verdict", "color": "yellow|pink|green|blue", "blocks": [blocks]}],
  "footer": "handwritten sign-off"
}
```

## Blocks

Every block is `{"type": "<name>", ...}`. Text fields take inline markup unless
marked *plain*.

| type | fields |
|---|---|
| `p` | `text`, `margin` (plain, optional scribble in the margin) |
| `h3` | `text`: small caps label |
| `list` | `items`: string or `{text, state: good\|bad\|meh, sub: [strings]}` |
| `grades` | `items`: `{letter, file (plain), why, tone: a\|b\|c\|d}` |
| `stickies` | `items`: `{title, small, color}` |
| `stats` | `items`: `{num (plain), label, tone: good\|bad\|info}` |
| `cards` | `items`: `{title, pen: green\|red\|blue, tape: pink\|yellow\|green\|blue, items: [list items]}` |
| `diff` | `lines`: strings starting `+`, `-` or a space |
| `conflict` | `left`, `right`: `{src (plain), text}`; `vs` (plain, default "vs") |
| `table` | `headers`, `rows` (arrays of strings) |
| `bars` | `title`, `sub`, `rows`: `{label, value (number), display, tip, soft}`, `label_header`, `value_header` |
| `hub` | `center`: `{title, sub}`, `spokes`: `{label, note}`, `aside` (`\n` breaks), `caption`, `aria` |
| `figure` | `svg` (raw, trusted), `caption` |
| `html` | `html`: raw escape hatch, trusted |

`bars` adds a hover tooltip and a "the numbers as a table" fold. `soft: true`
draws a lighter bar for a projected or estimated value.

## Inline markup

| write | get |
|---|---|
| `` `code` `` | code chip |
| `**bold**` | bold |
| `==text==` | yellow highlighter |
| `!!text!!` | pink highlighter (warning) |
| `++text++` | green highlighter (good) |
| `~~text~~` | red strike |
| `[text](https://...)` | link |
| `->` | → |
| a newline (`\n`) | line break |

## Changing the look

All styling is `templates/base.css`, inlined into each page. Fonts are Caveat,
Inter and JetBrains Mono from Google Fonts; offline, the page falls back to
system fonts. A new block type is one `b_<name>(b)` function in `render.py`
plus one use in `example.json`; the selftest fails until both exist.
