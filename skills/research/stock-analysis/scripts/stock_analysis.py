#!/usr/bin/env python3
"""Stock analysis -> beautiful PDF report (WeasyPrint + yfinance).

Usage:
    python3 stock_analysis.py "RELIANCE.NS" [--out report.pdf] [--days 365]
"""
import argparse, os, sys, tempfile
from datetime import datetime

import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from weasyprint import HTML

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "report.html")


def _fmt(v, suffix=""):
    if v is None:
        return "—"
    try:
        return f"{v:,.2f}{suffix}"
    except (TypeError, ValueError):
        return str(v)


def _pct(v):
    if v is None:
        return "—"
    return f"{v:+.2f}%"


def fetch(ticker, days):
    t = yf.Ticker(ticker)
    hist = t.history(period=f"{days}d")
    if hist.empty:
        sys.exit(f"ERROR: no data for {ticker}. Try .NS/.BO suffix for Indian stocks.")
    info = t.info or {}
    close = hist["Close"]
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    # RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = float((100 - 100 / (1 + rs)).iloc[-1]) if not rs.isna().all() else None
    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "currency": info.get("currency", "INR"),
        "price": price,
        "day_change": price - prev,
        "day_pct": (price - prev) / prev * 100 if prev else 0,
        "high52": info.get("fiftyTwoWeekHigh"),
        "low52": info.get("fiftyTwoWeekLow"),
        "mktcap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
        "book": info.get("bookValue"),
        "div_yield": info.get("dividendYield"),
        "roe": info.get("returnOnEquity"),
        "sma50": sma50,
        "sma200": sma200,
        "rsi": rsi,
        "ret1y": (price / float(close.iloc[0]) - 1) * 100 if len(close) > 1 else 0,
        "hist": hist,
    }


def verdict(d):
    score = 0
    reasons = []
    if d["sma50"] and d["price"] > d["sma50"]:
        score += 1; reasons.append("Price above 50-day SMA (short-term bullish)")
    elif d["sma50"]:
        score -= 1; reasons.append("Price below 50-day SMA (short-term bearish)")
    if d["sma200"] and d["price"] > d["sma200"]:
        score += 1; reasons.append("Price above 200-day SMA (long-term bullish)")
    elif d["sma200"]:
        score -= 1; reasons.append("Price below 200-day SMA (long-term bearish)")
    if d["rsi"] is not None:
        if d["rsi"] < 30:
            score += 1; reasons.append(f"RSI {d['rsi']:.0f} — oversold (potential bounce)")
        elif d["rsi"] > 70:
            score -= 1; reasons.append(f"RSI {d['rsi']:.0f} — overbought (pullback risk)")
        else:
            reasons.append(f"RSI {d['rsi']:.0f} — neutral")
    if d["pe"] is not None:
        if d["pe"] < 20:
            score += 1; reasons.append(f"P/E {d['pe']:.1f} — reasonable valuation")
        elif d["pe"] > 40:
            score -= 1; reasons.append(f"P/E {d['pe']:.1f} — rich valuation")
    if score >= 2:
        return "BUY", reasons
    if score <= -2:
        return "SELL", reasons
    return "HOLD", reasons


def chart(d, out_png):
    h = d["hist"]
    close = h["Close"]
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=130)
    ax.plot(close.index, close, color="#2563eb", lw=1.6, label="Close")
    if len(close) >= 50:
        ax.plot(close.index, close.rolling(50).mean(), color="#f59e0b", lw=1.1, label="SMA 50")
    if len(close) >= 200:
        ax.plot(close.index, close.rolling(200).mean(), color="#ef4444", lw=1.1, label="SMA 200")
    ax.set_title(f"{d['ticker']} — 1Y Price", fontsize=11, color="#1e293b")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def render(d, out):
    v, reasons = verdict(d)
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "chart.png")
        chart(d, png)
        # chart is referenced as file:// relative to template; copy alongside
        chart_abs = os.path.abspath(png)
        html = open(TEMPLATE).read()
        html = html.replace("{{CHART}}", f"file://{chart_abs}")
        html = (html.replace("{{TICKER}}", d["ticker"])
                    .replace("{{NAME}}", d["name"])
                    .replace("{{CURRENCY}}", d["currency"])
                    .replace("{{DATE}}", datetime.now().strftime("%d %b %Y"))
                    .replace("{{PRICE}}", _fmt(d["price"]))
                    .replace("{{DAYCHG}}", f"{_fmt(d['day_change'])} ({_pct(d['day_pct'])})")
                    .replace("{{HIGH52}}", _fmt(d["high52"]))
                    .replace("{{LOW52}}", _fmt(d["low52"]))
                    .replace("{{MKTCAP}}", _fmt(d["mktcap"] / 1e7, " Cr") if d["mktcap"] else "—")
                    .replace("{{PE}}", _fmt(d["pe"]))
                    .replace("{{EPS}}", _fmt(d["eps"]))
                    .replace("{{BOOK}}", _fmt(d["book"]))
                    .replace("{{DIV}}", _pct(d["div_yield"] * 100) if d["div_yield"] else "—")
                    .replace("{{ROE}}", _pct(d["roe"] * 100) if d["roe"] else "—")
                    .replace("{{SMA50}}", _fmt(d["sma50"]))
                    .replace("{{SMA200}}", _fmt(d["sma200"]))
                    .replace("{{RSI}}", _fmt(d["rsi"]))
                    .replace("{{RET1Y}}", _pct(d["ret1y"]))
                    .replace("{{VERDICT}}", v))
        reasons_html = "".join(f"<li>{r}</li>" for r in reasons)
        html = html.replace("{{REASONS}}", reasons_html)
        HTML(string=html, base_url=td).write_pdf(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--out", default=None)
    ap.add_argument("--days", type=int, default=365)
    a = ap.parse_args()
    out = a.out or f"stock_report_{a.ticker.replace('.', '_')}.pdf"
    d = fetch(a.ticker, a.days)
    render(d, out)
    print(f"OK: {out} ({os.path.getsize(out)} bytes)")
    print(f"Verdict: {verdict(d)[0]} @ {d['currency']} {d['price']:.2f}")


if __name__ == "__main__":
    main()
