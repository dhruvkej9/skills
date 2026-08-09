---
name: stock-analysis
description: "Analyze a stock and generate a beautiful PDF report (WeasyPrint + yfinance + web research)."
version: 1.1.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [stock, finance, analysis, pdf, report, weasyprint, yfinance, concall, earnings]
    category: research
    related_skills: [equity-research, pdf-creation]
---

# Stock Analysis + PDF Report

Analyze any stock (NSE/BSE or global) and produce a **beautiful PDF report** with price action, fundamentals, technicals, growth, **past 2+ earnings concalls**, **latest results**, **investor presentation**, and a brutally honest verdict.

**Two data sources, two phases:**
- **Script** (`stock_analysis.py`) → pulls price/fundamentals/technicals/forward estimates from **yfinance**.
- **Agent (you)** → does **web research** for concalls, results, and investor PPT (BSE/NSE filings, AlphaStreet, company IR), then passes it to the script via `--research research.json`.

Yahoo Finance does **NOT** have concalls or PPTs — those must come from web research.

## When to Use

Use whenever the user wants a stock analyzed or a formatted PDF report on a ticker. For a **full** report (with concalls/PPT/results), you MUST do the web-research phase — the script alone only produces the quantitative sections.

## Requirements

- `yfinance`, `requests`, `weasyprint` (all present in the Hermes venv)
- Internet access (live market data + web research)

## Phase 1 — Web research (concall / results / PPT)

For the target company, find:
1. **Past 2+ earnings concall transcripts** — search `"<Company> <quarter> earnings call transcript"` (AlphaStreet, BSE filing PDFs, company IR).
2. **Latest quarterly results** — revenue, PAT, margins, YoY growth.
3. **Latest investor presentation / corporate deck** — company IR or BSE filing.

Build a `research.json`:
```json
{
  "results": {
    "quarter": "Q4 FY26 (Apr 2026)",
    "revenue": "₹2,964.1 cr (+33.7% YoY)",
    "profit": "PAT ₹168.0 cr (+30.1% YoY)",
    "margin": "EBITDA 8.9% · PAT 5.7%"
  },
  "concalls": [
    {
      "quarter": "Q1 FY26",
      "date": "1 Aug 2025",
      "summary": "2-3 sentence management summary",
      "highlights": ["guidance / capex / segment points"]
    }
  ],
  "presentation": {
    "title": "Investor Presentation (Apr 2026)",
    "highlights": ["key deck takeaways"]
  },
  "brutal": ["honest risk flags, not sugarcoated"]
}
```

## Phase 2 — Generate the PDF

```bash
python3 scripts/stock_analysis.py "RELIANCE.NS" \
  --research research.json \
  --peers "ONGC.NS,BPCL.NS,IOC.NS,GAIL.NS,OIL.NS" \
  --out /path/to/report.pdf
```

- Ticker format: Indian stocks use `.NS` (NSE) or `.BO` (BSE), e.g. `RELIANCE.NS`, `HDFCBANK.NS`. Global: `AAPL`, `TSLA`.
- `--research` (optional) injects concall/results/PPT/brutal sections. Without it, those sections show "no data provided".
- `--peers` (optional) adds a **sector peer comparison** table, ranked by revenue growth with the fastest company highlighted — the "fastest car".
- `--out` defaults to `stock_report_<TICKER>.pdf`; `--days` (default 365) sets the price-history window.

## What the report contains

- **Header** — ticker, company name, sector, currency, report date
- **Price card** — current price, day change, 52-week high/low, market cap, 1Y return
- **Growth (Racing Car)** — YoY revenue & net-income growth, speeding up / slowing down
- **Future & Guidance** — forward P/E, forward EPS, analyst target, upside, consensus
- **Brutal Honesty & Risks** — honest risk flags (from research + auto data-driven warnings)
- **Latest Results** — latest quarter revenue/profit/margins
- **Concall Analysis (Past 2+)** — summaries + management highlights per call
- **Investor Presentation** — latest deck takeaways
- **Margins** — gross, operating, net margin
- **Fundamentals** — P/E, EPS, book value, dividend yield, ROE
- **Technicals** — 50/200-day SMA, RSI(14)
- **Sector Peer Comparison** — ranks peers by revenue growth, highlights fastest
- **Verdict** — data-driven buy/hold/sell signal with rationale
- **Price chart** — 1-year close with 50/200-day SMA overlay

## Procedure

1. **Research phase:** web-search concall transcripts (past 2+), latest results, and investor PPT. Extract key numbers + management commentary. Build `research.json` with `results`, `concalls`, `presentation`, and `brutal` risk flags.
2. **Generate:** run the script with the ticker, `--research research.json`, and `--peers` if comparing.
3. If the ticker fails (no data), try `.NS`/`.BO` suffix for Indian stocks or the correct global symbol.
4. Present the PDF to the user (send via `MEDIA:/path/to/report.pdf` on WhatsApp).
5. Summarize the verdict + top brutal risk in 2-3 lines alongside the PDF.

## Pitfalls

- **Concall/PPT NOT in yfinance** — always do the web-research phase for those; never claim the script fetched them.
- **Wrong ticker suffix** — Indian stocks need `.NS`/`.BO`. Bare `RELIANCE` fails.
- **Data conflicts** — yfinance trailing growth may disagree with management-reported growth (different periods). Surface the conflict in `brutal`, don't hide it.
- **No internet** — script errors out; report can't be generated offline.
- **Delisted/illiquid** — `yfinance` may return empty; verify the symbol.
- **WeasyPrint missing** — install with `pip install weasyprint`.

## Verification

- Confirm the PDF exists and is non-empty (`ls -la <out>`).
- Open/parse it to confirm all sections rendered (price, fundamentals, concalls, verdict).
- Cross-check the current price against a live source if accuracy matters.
