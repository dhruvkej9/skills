---
name: stock-analysis
description: "Analyze a stock and generate a beautiful PDF report (WeasyPrint + Screener.in authenticated data + web research). NO yfinance."
version: 2.6.0
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

## Output filename convention
The generated PDF is named `<TICKER>_<QUARTER>.pdf` — e.g. `RRKABEL_Q1FY27.pdf`. The script derives this automatically from the ticker argument and the `results.quarter` field in `research.json` (format `Q1 FY27 (Jun 2026)` → `Q1FY27`). Do not use `stock_report_*.pdf` or any other naming. `--out` still overrides if explicitly passed.

## Trusted data sources (ONLY these, in order)
1. **NSE** — always use NSE data first (current price, 52-week high/low, market cap, P/E). RRKABEL etc. are NSE-listed.
2. **BSE** — ONLY if the stock is NOT listed on NSE.
3. **Screener.in** — mirrors NSE/BSE data; its **key-points box** (Current Price, High/Low, Market Cap, P/E, ROCE, ROE) is the authoritative source for these figures.
4. **Company IR page** — investor decks, results, guidance.

> **⚠️ FINANCIAL DATA RULE — STRICTLY NO FABRICATION.** This is financial data. If you CANNOT find a value from NSE/BSE/Screener, **SAY SO to the user** — do NOT invent, estimate, or carry forward a stale number. Wrong/stale price, 52-week range, or market cap is unacceptable.

> **NEVER hardcode** price, 52-week high/low, market cap, or P/E. Always pull them fresh from the Screener key-points box on each run.

Do NOT trust Yahoo Finance / generic aggregators for the core numbers.

---

## Concall transcript sourcing — STRICT ORDER (no silent 3rd-party fallback)

For **concall transcripts / quotes**, follow this order and **STOP to ask the user** if a step fails:

1. **Screener.in** — the company's Screener page has a **"Concalls" section** (`<ul class="list-links">`) with a dated list of earnings calls. Each entry has:
   - **Transcript** link → `https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=<uuid>.pdf` (official BSE Regulation 30 filing)
   - **REC** link → company IR audio (`.mp3` on the company website)
   - Parse these with regex: `<div class="ink-600...">Jul 2026</div>...href="(https://www.bseindia.com/...)" title="Raw Transcript"`. Pick the **latest** date. **This is how you get the real transcript — the data IS there.**
2. **BSE / NSE** — official filings & announcements (Regulation 30 filings) link the earnings-call audio/transcript.
3. **Company IR page** — investor events / transcripts section.
4. **THEN STOP — ASK THE USER.** Do NOT silently jump to a 3rd-party aggregator (AlphaStreet, TipRanks, stockanalysis.com, etc.). If you need a 3rd-party source, **ask the user first**.

> **Why:** the user explicitly wants primary sources (Screener/BSE/NSE) first. Silently pulling quotes from AlphaStreet is NOT acceptable. If the primary sources fail, ask — don't guess.

> **⚠️ EXTRACTION PITFALL:** Screener/BSE/NSE **DO have the transcripts** — if you "can't find" them, your extraction is broken, not the data. The Screener page's Concalls section is the key: it links every BSE transcript. Always parse it before concluding the transcript is unavailable.

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
- **Key points box** (Current Price, High/Low, Market Cap, P/E, ROCE, ROE, Book Value, Dividend Yield) is an HTML `<ul id="top-ratios">` — parse with BeautifulSoup/regex, NOT `pd.read_html`. This is the **authoritative source** for price, 52-week high/low, market cap, and P/E. Parse it fresh every run — never reuse a stale value.
- **Peers**: fetch each peer the same way (Screener API), compute YoY growth the same way.
- **Price / DMA50 / DMA200 / 1Y return** — fetch from the chart API (numeric company id from search, e.g. `1284488`):
  ```bash
  curl -s "https://www.screener.in/api/company/<NUMERIC_ID>/chart/?q=Price-DMA50-DMA200&days=365&consolidated=true" \
    -H "Cookie: csrftoken=<CSRF>; sessionid=<SID>"
  ```
  Latest price = last value of the `Price` series. **Never hardcode a stale price** — always pull fresh from the chart API on each run.
- **RSI(14)** — compute from the daily `Price` series (last 14 closes: `100 - 100/(1+avg_gain/avg_loss)`). Screener does not expose RSI directly.
- **Chart image** — render the Price/DMA50/DMA200 series with matplotlib (`matplotlib.use('Agg')`), save PNG, set `chart_path` in research.json. This keeps the report's chart fresh too.

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
  "guidance": {
    "Volume growth guidance": "~18% YoY",
    "Margin guidance": "+100bps YoY; W&C 10.5% by FY28",
    "Capex plan": "₹1,200 cr (~80% cable); ₹600-650 cr deployed FY27",
    "FMEG": "Yearly breakeven expected this year"
  },
  "quotes": [
    {
      "speaker": "Management",
      "context": "Q1 FY27 — Growth outlook",
      "text": "Verbatim management quote from the concall transcript (exact wording)"
    }
  ],
  "sources": [
    "Investor Presentation Q1 FY27 — https://www.rrkabel.com/investor-presentation/",
    "Q1 FY27 Earnings Call Transcript — https://alphastreet.com/india/r-r-kabel-ltd-rrkabel-q1-2027-earnings-call-transcript/",
    "Earnings Call Intimation (BSE) — https://www.bseindia.com/xml-data/corpfiling/AttachLive/0995bfda-62a9-4190-b87c-d507a0686828.pdf",
    "Screener RRKABEL — https://www.screener.in/company/RRKABEL/consolidated/"
  ],
  "presentation": {
    "title": "Investor Presentation — Q1 FY27 (Jul 2026)",
    "highlights": ["key deck takeaway 1", "key deck takeaway 2"]
  },
  "brutal": ["honest risk flag — do not sugarcoat"],
  "thesis": ["framework point 1", "framework point 2"],
  "thesis_note": "optional: one-line thesis context",
  "chart_path": "/path/to/price_chart.png"
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
4. **Future & Guidance** — ROCE/ROE + **detailed guidance rows** from `guidance` dict (volume, margin, capex, FMEG, industry, retail, exports, data center). NO analyst target / forward P/E / consensus (removed)
5. **Brutal Honesty & Risks** — researched risk flags + auto data-driven warnings
6. **Latest Results** — latest quarter revenue/profit/margins
7. **Concall Analysis (Past 2+)** — per-call summary + management highlights
8. **Exact Quotes from Concalls** — verbatim management quotes from `quotes` array, rendered as **highlighted amber cards** (speaker + context header + exact wording)
9. **Investor Presentation** — latest deck takeaways
10. **Margins** — gross, operating, net margin
11. **Fundamentals** — P/E, EPS, book value, dividend yield, ROE
12. **Technicals** — 50/200-day SMA, RSI(14) (if provided in research.json)
13. **Sector Peer Comparison (Fastest Car)** — ranks target + peers TOGETHER by revenue growth; ONLY the single fastest is green; target gets a "Target" tag on the right
14. **Thesis** — Momentum & Growth framework check
15. **Price chart** — 1-year close with 50/200-day SMA overlay (only if `research.json` provides a `chart_path`)
16. **Sources & Reference Reports** — every PDF/report used, as **clickable links** (URLs auto-linkified in the script)

> **COMPETITOR CONCALLS MUST BE ANALYZED TOO.** The report must analyze the **latest concall of EVERY competitor peer** (not just the target), sourced from BSE/Screener the same way. Add a **"Competitor Concall Analysis"** section listing each peer's latest concall summary + highlights + verbatim quotes. Use subagents (parallel) to fetch each peer's transcript from BSE — but verify the numbers yourself before they enter the report.
>
> **PEERS ARE AUTO-DETERMINED — DO NOT ASK THE USER.** The agent picks the peer set itself: same-sector, same-subsegment listed competitors (e.g. for a wires & cables company: Polycab, Havells, KEI, Finolex Cables). Resolve tickers correctly (Finolex **Cables** = FINCABLES; Finolex **Industries** = FINPIPE, pipes — NOT a cable peer). If a chosen ticker turns out to be the wrong company/segment, silently swap to the correct one and analyze it — do not ask the user which peers to use. The user decides nothing about peers; the agent decides and reports.

> **LIST EVERYTHING ANALYZED.** The report must explicitly list **every single thing analyzed**: each concall (target + all peers), each investor presentation, each results filing, each Screener data pull. Nothing analyzed should be silently omitted — the user wants full transparency of what went into the report.

> **NO verdict / buy-sell / analyst consensus / target price.** This is a pure data report. The user does not want investment opinions.

---

## Procedure (end-to-end)
1. **Identify the ticker.** Indian → `.NS`/`.BO`. Ask the user if unclear.
2. **Fetch real data from Screener.in** (authenticated session) — fundamentals, quarterly YoY growth, ratios, price. Do the same for each peer.
3. **Research phase (web):**
   a. BSE/NSE filings + company IR → latest results, concalls, investor presentation.
   b. **Source the concall transcript in STRICT order: Screener → BSE/NSE → IR. If all fail, ASK the user** (never silently use AlphaStreet/3rd party).
   c. Extract revenue/PAT/margins, concall summary + highlights, **verbatim management quotes** (exact wording for the `quotes` array), **detailed guidance** (volume, margin, capex, FMEG, etc. for the `guidance` dict).
   d. Write the `brutal` risk list + `thesis` framework points.
   e. Collect **source links** — company IR, AlphaStreet transcript, BSE filing PDFs, Screener peer pages — into the `sources` array (real URLs, not labels).
   f. Save everything to `research.json`.
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
- **Sources must be real links** — put actual URLs in the `sources` array, not labels like "company IR". The script auto-linkifies any `http(s)://` in the list.
- **Quotes must be verbatim** — copy the exact wording from the transcript, don't paraphrase. If you can't get the exact text, omit the quote rather than invent it.
- **NEVER silently use 3rd-party transcripts** — source concall from Screener → BSE/NSE → IR first. If none have it, ASK the user before using AlphaStreet/TipRanks/stockanalysis.

---

## Verification
- Confirm the PDF exists and is non-empty (`ls -la <out>`).
- Open/parse it to confirm all sections rendered.
- Cross-check the current price and peer growth against Screener.in live.
- Verify concall quarters are the actual latest 2.
- Confirm NO leftover `{{PLACEHOLDER}}` in the PDF text.
