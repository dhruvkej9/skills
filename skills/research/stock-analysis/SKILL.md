---
name: stock-analysis
description: "Analyze a stock and generate a beautiful PDF report (WeasyPrint + yfinance + web research)."
version: 1.2.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [stock, finance, analysis, pdf, report, weasyprint, yfinance, concall, earnings, investor-presentation]
    category: research
    related_skills: [equity-research, pdf-creation, online-shopping-research]
---

# Stock Analysis + PDF Report

Analyze any stock (NSE/BSE or global) and produce a **beautiful PDF report** covering price action, fundamentals, technicals, growth, **past 2+ earnings concalls**, **latest results**, **investor presentation**, and a **brutally honest** verdict.

## The two data sources (READ THIS FIRST)

The report combines two independent data sources. Do NOT confuse them:

| Source | What it provides | Fetched by |
|--------|-----------------|------------|
| **yfinance** | Price, market cap, P/E, EPS, book value, dividend yield, ROE, forward P/E, forward EPS, analyst target, consensus, RSI, 50/200-day SMA, 1Y return, revenue/profit growth | `stock_analysis.py` (automatic) |
| **Web research** | Earnings concall transcripts (past 2+), latest quarterly results, investor presentation deck, brutal risk flags | **You (the agent)** — web search + extraction |

> ⚠️ **Yahoo Finance does NOT have concalls, PPTs, or detailed results commentary.** Those MUST come from web research. Never claim the script fetched them.

---

## Phase 1 — Web research (REQUIRED for a full report)

This is the part that makes the report valuable. Do it thoroughly.

### 1.1 Find the latest quarterly results

**Search queries:**
- `"<Company Name>" "<latest quarter>" results revenue PAT`
- `"<Company Name>" quarterly results <year>`
- `"<Company Name>" Q4 FY26 results`

**Sources (in priority order):**
1. **Company IR page** — `<company>.com/investors` or `/investor-relations`
2. **BSE/NSE stock exchange filing** — search `site:bseindia.com <Company> results` or `site:nseindia.com`
3. **Screener.in** — `https://www.screener.in/company/<SYMBOL>/` (quarterly results, ratios, shareholding)
4. **Moneycontrol / Investing.com** — quarterly results summary pages

**Extract these numbers:**
- Quarter + year (e.g. "Q4 FY26, Apr 2026")
- Revenue (₹ cr) + YoY growth %
- Net profit / PAT (₹ cr) + YoY growth %
- EBITDA margin %, PAT margin %
- Any one-off items or exceptional charges

### 1.2 Find past 2+ earnings concall transcripts

**Search queries:**
- `"<Company Name>" earnings call transcript <quarter> <year>`
- `"<Company Name>" concall transcript <quarter>`
- `"<Company Name>" Q1 FY26 concall` / `Q4 FY25 concall`

**Sources (in priority order):**
1. **AlphaStreet** — `alphastreet.com` (clean transcripts, most reliable)
2. **BSE filing PDFs** — companies often file concall transcripts as PDFs (search `site:bseindia.com <Company> concall`)
3. **Company IR** — investor presentation + transcript PDFs
4. **Investing.com / TradingView** — earnings call transcripts

**For EACH concall, extract:**
- Quarter + call date
- **Summary** (2-3 sentences): what management said about the quarter — demand, segments, outlook
- **Highlights** (3-6 bullets): guidance, capex plans, segment performance, margin commentary, management quotes

> Get at least the **past 2 concalls** (e.g. Q1 FY26 + Q4 FY25). Add more if the story is complex or recent quarters matter.

### 1.3 Find the latest investor presentation

**Search queries:**
- `"<Company Name>" investor presentation <year> PDF`
- `"<Company Name>" corporate presentation <year>`
- `site:<company-domain> investor presentation`

**Sources:**
1. **Company IR page** — most companies host the latest deck
2. **BSE filing** — presentations are often filed
3. **Google/PDF search** — `filetype:pdf "<Company>" investor presentation`

**Extract 3-6 key takeaways** from the deck: growth strategy, market opportunity, capacity/capex plans, segment roadmap, financial targets.

### 1.4 Build `research.json`

Create a JSON file with this exact structure:

```json
{
  "results": {
    "quarter": "Q4 FY26 (Apr 2026)",
    "revenue": "₹2,964.1 cr (+33.7% YoY)",
    "profit": "PAT ₹168.0 cr (+30.1% YoY)",
    "margin": "EBITDA 8.9% · PAT 5.7%",
    "note": "optional: one-line context (one-offs, exceptional items)"
  },
  "concalls": [
    {
      "quarter": "Q1 FY26",
      "date": "1 Aug 2025",
      "summary": "2-3 sentence management summary of the quarter and outlook",
      "highlights": [
        "Guidance: 18% volume growth, 100bps margin improvement for FY26",
        "CapEx: ₹1,200 cr to double cable capacity, targeting +₹4,500 cr topline",
        "FMEG: EBIT breakeven expected this year"
      ]
    },
    {
      "quarter": "Q4 FY25",
      "date": "May 2025",
      "summary": "2-3 sentence summary",
      "highlights": ["point 1", "point 2"]
    }
  ],
  "presentation": {
    "title": "Investor Presentation (Apr 2026)",
    "highlights": ["key deck takeaway 1", "key deck takeaway 2"]
  },
  "brutal": [
    "honest risk flag 1 — do not sugarcoat",
    "honest risk flag 2"
  ]
}
```

### 1.5 Write the `brutal` list (CRITICAL)

The `brutal` array is the **most important part** — it's what makes this report trustworthy. Include honest, specific concerns. Examples:

- **Growth quality** — is revenue growth real volume or just price inflation? (e.g. "volume grew 6.5% but revenue grew 13.9% — a chunk is copper price inflation, not demand")
- **Margin weakness** — is EBITDA margin thin vs peers?
- **Loss-making segments** — any segment still losing money despite promises?
- **Capex risk** — big capex bets with execution risk
- **Valuation** — is P/E expensive? You're paying a premium for growth.
- **Data conflicts** — if yfinance trailing growth disagrees with management-reported growth, surface it. Don't hide it.

The script ALSO auto-adds data-driven warnings (negative trailing growth, RSI > 70 overbought, P/E > 40 expensive). Combine those with your researched points.

---

## Phase 2 — Generate the PDF

```bash
python3 scripts/stock_analysis.py "RELIANCE.NS" \
  --research research.json \
  --peers "ONGC.NS,BPCL.NS,IOC.NS,GAIL.NS,OIL.NS" \
  --out /path/to/report.pdf
```

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `TICKER` | ✅ | Indian: `.NS` (NSE) or `.BO` (BSE). Global: `AAPL`, `TSLA` |
| `--research` | for full report | Path to `research.json` (concall/results/PPT/brutal) |
| `--peers` | optional | Comma-separated peer tickers → sector comparison table |
| `--out` | optional | Output path (default `stock_report_<TICKER>.pdf`) |
| `--days` | optional | Price-history window in days (default 365) |

---

## What the report contains (all sections)

1. **Header** — ticker, company name, sector, currency, report date
2. **Price card** — current price, day change, 52-week high/low, market cap, 1Y return
3. **Growth (Racing Car)** — YoY revenue & net-income growth, speeding up / slowing down
4. **Future & Guidance** — forward P/E, forward EPS, analyst target, upside %, consensus, # analysts
5. **Brutal Honesty & Risks** — researched risk flags + auto data-driven warnings
6. **Latest Results** — latest quarter revenue/profit/margins
7. **Concall Analysis (Past 2+)** — per-call summary + management highlights
8. **Investor Presentation** — latest deck takeaways
9. **Margins** — gross, operating, net margin
10. **Fundamentals** — P/E, EPS, book value, dividend yield, ROE
11. **Technicals** — 50/200-day SMA, RSI(14)
12. **Sector Peer Comparison** — ranks peers by revenue growth, highlights fastest
13. **Verdict** — data-driven buy/hold/sell signal with rationale
14. **Price chart** — 1-year close with 50/200-day SMA overlay

---

## Procedure (end-to-end)

1. **Identify the ticker.** Indian → `.NS`/`.BO`; global → bare symbol. Ask the user if unclear.
2. **Research phase:**
   a. Web-search latest results → extract revenue/PAT/margins.
   b. Web-search past 2+ concall transcripts → extract summary + highlights per call.
   c. Web-search latest investor presentation → extract key takeaways.
   d. Write the `brutal` risk list (honest, specific, not sugarcoated).
   e. Save all of it to `research.json`.
3. **Generate:** run the script with ticker + `--research research.json` + `--peers` (if comparing).
4. **Handle failures:** if the ticker errors, try `.NS`/`.BO` or the correct global symbol.
5. **Deliver:** send the PDF via `MEDIA:/path/to/report.pdf` on WhatsApp.
6. **Summarize:** 2-3 lines — verdict + top brutal risk + one notable highlight.

---

## Pitfalls

- **Concall/PPT NOT in yfinance** — always do web research for those. Never claim the script fetched them.
- **Wrong ticker suffix** — Indian stocks need `.NS`/`.BO`. Bare `RELIANCE` fails.
- **Data conflicts** — yfinance trailing growth may disagree with management-reported growth (different periods). Surface the conflict in `brutal`, don't hide it.
- **Stale transcripts** — verify the concall quarter/date is actually the latest. Old transcripts give a wrong picture.
- **No internet** — script errors out; report can't be generated offline.
- **Delisted/illiquid** — `yfinance` may return empty; verify the symbol.
- **WeasyPrint missing** — install with `pip install weasyprint`.
- **Peer tickers wrong** — verify peer symbols exist before passing `--peers`.

---

## Verification

- Confirm the PDF exists and is non-empty (`ls -la <out>`).
- Open/parse it to confirm all sections rendered (price, fundamentals, concalls, brutal, verdict).
- Cross-check the current price against a live source if accuracy matters.
- Verify concall quarters are the actual latest 2 (not older ones).
