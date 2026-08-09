---
name: stock-analysis
description: "Analyze a stock and generate a beautiful PDF report (WeasyPrint + Screener.in authenticated data + web research). NO yfinance."
version: 2.0.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [stock, finance, analysis, pdf, report, weasyprint, screener, concall, earnings, investor-presentation, momentum]
    category: research
    related_skills: [equity-research, pdf-creation, online-shopping-research]
---

# Stock Analysis + PDF Report

Analyze any stock (NSE/BSE) and produce a **beautiful PDF report** covering price action, fundamentals, technicals, growth (Momentum & Growth thesis), **past 2+ earnings concalls**, **latest results**, **investor presentation**, and **brutally honest** risks.

> ⚠️ **yfinance is REMOVED.** Its trailing data was stale/wrong end-to-end. All data comes from **Screener.in (authenticated session)** + **BSE/NSE filings** + **company IR**. The script is 100% `research.json`-driven — it does NOT fetch anything itself.

## Trusted data sources (ONLY these)
- **Screener.in** — fundamentals, quarterly results, ratios, price, technicals (authenticated via session tokens)
- **BSE / NSE** — official filings, results, concall transcript PDFs, investor presentations
- **Company IR page** — investor decks, results, guidance

Do NOT trust Yahoo Finance / generic aggregators for the core numbers.

---

## Phase 1 — Fetch real data from Screener.in (authenticated)

Screener session tokens are configured in the **trading profile** MCP server (`screener`):
- `SCREENER_CSRF_TOKEN`, `SCREENER_SESSION_ID`, `SCREENER_CSRF_MIDDLEWARE_TOKEN` in `~/.hermes/profiles/trading/config.yaml`
- MCP server code: `/home/ubuntu/screener.in-MCP-server/server.py`

> **If the Screener session tokens are MISSING** (no MCP server configured, no cookies available), the AI should **ASK the user for them** during initial setup — do NOT fall back to yfinance or unauthenticated scraping. The user logs into screener.in, opens DevTools → Application → Cookies, and shares `csrftoken` + `sessionid` (and optionally `csrfmiddlewaretoken`). Store them in the trading profile's `config.yaml` under `mcp_servers.screener.args`.

Use these cookies to hit Screener's API directly for exact numbers:

```bash
# company id lookup
curl -s "https://www.screener.in/api/company/search/?q=RRKABEL" \
  -H "Cookie: csrftoken=<CSRF>; sessionid=<SID>"
# company page (parse tables with pandas.read_html)
curl -s "https://www.screener.in/company/RRKABEL/consolidated/" \
  -H "Cookie: csrftoken=<CSRF>; sessionid=<SID>"
# price/DMA/RSI chart data
curl -s "https://www.screener.in/api/company/<ID>/chart/?q=Price-DMA50-DMA200-Volume&days=365&consolidated=true" \
  -H "Cookie: csrftoken=<CSRF>; sessionid=<SID>"
```

### Key parsing rules (get these RIGHT)
- **Quarterly YoY growth** = compare the **LAST column** to the **SAME QUARTER PRIOR YEAR** (4 columns back), NOT the previous quarter. Example: `Jun 2026` vs `Jun 2025`.
- **Key points box** (price, P/E, ROE, ROCE, market cap) is an HTML `<div>`, not a `<table>` — parse with BeautifulSoup/regex, not `pd.read_html`.
- **Peers**: fetch each peer the same way (Screener API), compute YoY growth the same way.

### Build `research.json` (single source of truth for the script)

```json
{
  "ticker": "RRKABEL.NS",
  "name": "R R Kabel Limited",
  "fundamentals": {
    "ticker": "RRKABEL.NS", "name": "R R Kabel Limited",
    "sector": "Wires & Cables / FMEG", "currency": "INR",
    "price": 2562.0, "day_change": null, "day_pct": null,
    "high52": 2775.0, "low52": 1165.0, "mktcap": 28881.0,
    "pe": 47.2, "eps": 43.52, "book": 228.0, "div_yield": 0.37,
    "roe": 21.3, "roce": 28.1,
    "gross_m": 18.4, "op_m": 8.0, "net_m": 5.1,
    "sma50": null, "sma200": null, "rsi": null, "ret1y": 81.0
  },
  "growth": {
    "revenue": 54.0, "net_income": 127.8,
    "rev_car": ["Growing +54%/yr", "ACCELERATING (speeding up)"],
    "ni_car": ["Growing +128%/yr", "ACCELERATING (speeding up)"]
  },
  "peers": [
    {"ticker": "POLYCAB.NS", "name": "Polycab India", "rev_growth": 39.0, "ni_growth": 32.8},
    {"ticker": "HAVELLS.NS", "name": "Havells India", "rev_growth": 19.5, "ni_growth": -16.7},
    {"ticker": "KEI.NS", "name": "KEI Industries", "rev_growth": 23.0, "ni_growth": 39.8}
  ],
  "results": {
    "quarter": "Q1 FY27 (Jun 2026)",
    "revenue": "₹3,168 cr (+54% YoY)",
    "profit": "PAT ₹205 cr (+129% YoY)",
    "margin": "EBITDA 9.0% (+205bps) · PAT 6.5% (+212bps)",
    "note": "optional one-line context"
  },
  "concalls": [
    {
      "quarter": "Q1 FY27", "date": "Jul 27, 2026",
      "summary": "2-3 sentence management summary",
      "highlights": ["guidance", "capex", "segment performance"]
    }
  ],
  "presentation": {
    "title": "Investor Presentation — Q1 FY27 (Jul 2026)",
    "highlights": ["key deck takeaway 1", "key deck takeaway 2"]
  },
  "brutal": ["honest risk flag — do not sugarcoat"],
  "thesis": ["framework point 1", "framework point 2"],
  "thesis_note": "optional: one-line thesis context"
}
```

### `brutal` list (CRITICAL — what makes the report trustworthy)
- **Growth quality** — is revenue growth real volume or price inflation? (e.g. "volume +17% but revenue +54% — a chunk is copper price pass-through")
- **Margin weakness** — thin EBITDA margin vs peers
- **Loss-making segments** — any segment still losing money
- **Capex risk** — big capex bets with execution risk
- **Valuation** — expensive P/E, premium multiple
- **Data conflicts** — surface any discrepancy, don't hide it

### `thesis` list (Momentum & Growth framework)
- Framework: Momentum & Growth (Rajarshi Shome) — track the **PACE of sales growth** (Gaadi-ka-Speed): accelerating = reward, decelerating = avoid
- Rank peers by **revenue growth velocity**, NOT net income
- Assess growth quality (volume vs price), margin expansion (operating leverage), corroborating signals (retail footprint, capacity, exports), circle of competence

---

## Phase 2 — Generate the PDF

```bash
python3 scripts/stock_analysis.py "RRKABEL.NS" \
  --research research.json \
  --out /path/to/report.pdf
```

### Arguments
| Arg | Required | Description |
|-----|----------|-------------|
| `TICKER` | ✅ | Ticker symbol (report header). Indian: `RRKABEL.NS` |
| `--research` | ✅ | Path to `research.json` — ALL data comes from here |
| `--out` | optional | Output path (default `stock_report_<TICKER>.pdf`) |

> `--peers` and `--days` are GONE. Peers come from `research.json`'s `peers` array. The script fetches nothing from the network.

---

## What the report contains (all sections)
1. **Header** — ticker, company name, sector, currency, report date
2. **Price card** — current price, day change, 52-week high/low, market cap, 1Y return
3. **Growth (Racing Car)** — YoY revenue & net-income growth, speeding up / slowing down
4. **Future & Guidance** — ROCE (no analyst target / forward P/E / consensus — removed)
5. **Brutal Honesty & Risks** — researched risk flags + auto data-driven warnings
6. **Latest Results** — latest quarter revenue/profit/margins
7. **Concall Analysis (Past 2+)** — per-call summary + management highlights
8. **Investor Presentation** — latest deck takeaways
9. **Margins** — gross, operating, net margin
10. **Fundamentals** — P/E, EPS, book value, dividend yield, ROE
11. **Technicals** — 50/200-day SMA, RSI(14) (if provided in research.json)
12. **Sector Peer Comparison (Fastest Car)** — ranks target + peers TOGETHER by revenue growth; ONLY the single fastest is green; target gets a "Target" tag on the right
13. **Thesis** — Momentum & Growth framework check
14. **Price chart** — 1-year close with 50/200-day SMA overlay (only if `research.json` provides a `chart_path`)

> **NO verdict / buy-sell / analyst consensus / target price.** This is a pure data report. The user does not want investment opinions.

---

## Procedure (end-to-end)
1. **Identify the ticker.** Indian → `.NS`/`.BO`. Ask the user if unclear.
2. **Fetch real data from Screener.in** (authenticated session) — fundamentals, quarterly YoY growth, ratios, price. Do the same for each peer.
3. **Research phase (web):**
   a. BSE/NSE filings + company IR → latest results, concalls, investor presentation.
   b. Extract revenue/PAT/margins, concall summary + highlights, deck takeaways.
   c. Write the `brutal` risk list + `thesis` framework points.
   d. Save everything to `research.json`.
4. **Generate:** run the script with ticker + `--research research.json`.
5. **Deliver:** send the PDF via `MEDIA:/path/to/report.pdf` on WhatsApp.
6. **Summarize:** 2-3 lines — key data points + top brutal risk + one highlight.

---

## Pitfalls
- **yfinance is gone** — do NOT fall back to it. All numbers come from research.json (Screener/BSE/filings).
- **YoY, not sequential** — quarterly growth must compare same quarter last year (4 cols back), not the previous quarter.
- **Key points box is a div, not a table** — parse with BeautifulSoup, not pd.read_html.
- **Concall/PPT NOT in Screener** — always web-research those (BSE filings, AlphaStreet, company IR).
- **Wrong ticker suffix** — Indian stocks need `.NS`/`.BO`.
- **Stale transcripts** — verify the concall quarter/date is actually the latest.
- **WeasyPrint missing** — install with `pip install weasyprint` (+ `apt install libpango` on Linux).
- **html5lib missing** — `pip install html5lib` (needed for `pd.read_html`).

---

## Verification
- Confirm the PDF exists and is non-empty (`ls -la <out>`).
- Open/parse it to confirm all sections rendered.
- Cross-check the current price and peer growth against Screener.in live.
- Verify concall quarters are the actual latest 2.
- Confirm NO leftover `{{PLACEHOLDER}}` in the PDF text.
