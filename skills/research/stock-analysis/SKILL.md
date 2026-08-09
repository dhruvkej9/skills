---
name: stock-analysis
description: "Analyze a stock and generate a beautiful PDF report (WeasyPrint)."
version: 1.0.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [stock, finance, analysis, pdf, report, weasyprint, yfinance]
    category: research
    related_skills: [equity-research, pdf-creation]
---

# Stock Analysis + PDF Report

Analyze any stock (NSE/BSE or global) and produce a **beautiful PDF report** with price action, fundamentals, technicals, and a verdict. Uses `yfinance` for data and `WeasyPrint` for the PDF.

## When to Use

Use whenever the user wants a stock analyzed, a company researched for investing, or a formatted PDF report on a ticker. Covers price, valuation, fundamentals, technical indicators, and a buy/hold/sell-style verdict.

## Requirements

- `yfinance`, `requests`, `weasyprint` (all present in the Hermes venv)
- Internet access (live market data)

## The One Command

```bash
python3 scripts/stock_analysis.py "RELIANCE.NS" --out /path/to/report.pdf --peers "ONGC.NS,BPCL.NS,IOC.NS,GAIL.NS,OIL.NS"
```

- Ticker format: Indian stocks use `.NS` (NSE) or `.BO` (BSE), e.g. `RELIANCE.NS`, `HDFCBANK.NS`. Global: `AAPL`, `TSLA`.
- `--out` defaults to `stock_report_<TICKER>.pdf` in the current directory.
- `--days` (default 365) controls the price-history window.
- `--peers` (comma-separated tickers) adds a **sector peer comparison** table, ranked by revenue growth with the fastest company highlighted — the "fastest car" in the sector.

## What the report contains

- **Header** — ticker, company name, sector, exchange, currency, report date
- **Price card** — current price, day change, 52-week high/low, market cap, 1Y return
- **Growth (Racing Car)** — YoY revenue & net-income growth, plus whether growth is *speeding up* or *slowing down* (acceleration)
- **Margins** — gross, operating, net margin
- **Fundamentals** — P/E, EPS, book value, dividend yield, ROE
- **Technicals** — 50/200-day SMA, RSI(14), 1Y return
- **Sector Peer Comparison** — ranks peers by revenue growth, highlights the fastest
- **Verdict** — data-driven buy/hold/sell signal with rationale
- **Price chart** — 1-year close with 50/200-day SMA overlay (matplotlib)

## Procedure

1. Run the script with the ticker (and `--out` path if you want a specific location).
2. If the ticker fails (no data), try `.NS`/`.BO` suffix for Indian stocks or the correct global symbol.
3. Present the PDF to the user (send via `MEDIA:/path/to/report.pdf` on WhatsApp).
4. Optionally summarize the verdict in 2-3 lines alongside the PDF.

## Pitfalls

- **Wrong ticker suffix** — Indian stocks need `.NS`/`.BO`. Bare `RELIANCE` fails.
- **No internet** — script errors out; report can't be generated offline.
- **Delisted/illiquid** — `yfinance` may return empty; verify the symbol.
- **WeasyPrint missing** — install with `pip install weasyprint`.

## Verification

- Confirm the PDF exists and is non-empty (`ls -la <out>`).
- Open/parse it to confirm all sections rendered (price, fundamentals, verdict).
- Cross-check the current price against a live source if accuracy matters.
