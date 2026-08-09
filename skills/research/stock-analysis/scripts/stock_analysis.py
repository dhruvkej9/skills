#!/usr/bin/env python3
"""Stock analysis -> beautiful PDF report (WeasyPrint + yfinance).

Focus: guidance, growth rate & acceleration (racing-car), and sector peer
comparison to find the fastest-growing company.

Usage:
    python3 stock_analysis.py "RELIANCE.NS" [--out report.pdf] [--days 365] \
        [--peers TATAMOTORS.NS,ASHOKLEY.NS,...]
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


def _growth(series):
    """YoY growth of a pandas Series (latest vs prior year). Returns (pct, accel)."""
    try:
        s = series.dropna()
        if len(s) < 2:
            return None, None
        cur, prev = float(s.iloc[-1]), float(s.iloc[-2])
        if prev == 0:
            return None, None
        g = (cur - prev) / prev * 100
        # acceleration: compare the most recent growth to the prior period's growth
        if len(s) >= 3:
            prev2 = float(s.iloc[-3])
            g_prior = (prev - prev2) / prev2 * 100 if prev2 else 0
            accel = g - g_prior
        else:
            accel = None
        return g, accel
    except Exception:
        return None, None


def _car_status(g, accel):
    """Racing-car analogy: is the car speeding up or slowing down?"""
    if g is None:
        return "No growth data", "—"
    if accel is None:
        return f"Growing {g:+.1f}%/yr", "unknown"
    if accel > 0:
        return f"Growing {g:+.1f}%/yr", f"SPEEDING UP (+{accel:.1f}pt vs prior)"
    return f"Growing {g:+.1f}%/yr", f"SLOWING DOWN ({accel:+.1f}pt vs prior)"


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
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = float((100 - 100 / (1 + rs)).iloc[-1]) if not rs.isna().all() else None

    # ---- Growth (racing car) ----
    rev_g, rev_acc = _growth(t.income_stmt.loc["Total Revenue"]) if "Total Revenue" in t.income_stmt.index else (None, None)
    ni_g, ni_acc = _growth(t.income_stmt.loc["Net Income"]) if "Net Income" in t.income_stmt.index else (None, None)
    rev_car = _car_status(rev_g, rev_acc)
    ni_car = _car_status(ni_g, ni_acc)
    # Margins
    gross_m = info.get("grossMargins")
    op_m = info.get("operatingMargins")
    net_m = info.get("profitMargins")

    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector", "—"),
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
        # Future / guidance (analyst estimates)
        "fwd_pe": info.get("forwardPE"),
        "fwd_eps": info.get("forwardEps"),
        "target": info.get("targetMeanPrice"),
        "rec": info.get("recommendationKey"),
        "n_analyst": info.get("numberOfAnalystOpinions"),
        "sma50": sma50, "sma200": sma200, "rsi": rsi,
        "ret1y": (price / float(close.iloc[0]) - 1) * 100 if len(close) > 1 else 0,
        "rev_growth": rev_g, "rev_accel": rev_acc, "rev_car": rev_car,
        "ni_growth": ni_g, "ni_accel": ni_acc, "ni_car": ni_car,
        "gross_m": gross_m, "op_m": op_m, "net_m": net_m,
        "hist": hist,
    }


def fetch_peers(tickers):
    """Return list of {ticker,name,rev_growth,ni_growth,car} for peers."""
    peers = []
    for tk in tickers:
        try:
            t = yf.Ticker(tk.strip())
            info = t.info or {}
            rev_g, _ = _growth(t.income_stmt.loc["Total Revenue"]) if "Total Revenue" in t.income_stmt.index else (None, None)
            ni_g, _ = _growth(t.income_stmt.loc["Net Income"]) if "Net Income" in t.income_stmt.index else (None, None)
            peers.append({
                "ticker": tk.strip(),
                "name": info.get("shortName") or tk.strip(),
                "rev_growth": rev_g, "ni_growth": ni_g,
            })
        except Exception:
            continue
    # rank by revenue growth desc
    peers.sort(key=lambda p: (p["rev_growth"] if p["rev_growth"] is not None else -1e9), reverse=True)
    return peers


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
    # growth tilt
    if d["rev_growth"] is not None and d["rev_growth"] > 15:
        score += 1; reasons.append(f"Revenue growing {d['rev_growth']:.0f}%/yr — strong")
    if d["rev_accel"] is not None and d["rev_accel"] > 0:
        score += 1; reasons.append("Growth is ACCELERATING (racing car speeding up)")
    elif d["rev_accel"] is not None:
        score -= 1; reasons.append("Growth is DECELERATING (racing car slowing)")
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


def render(d, out, peers=None):
    v, reasons = verdict(d)
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "chart.png")
        chart(d, png)
        chart_abs = os.path.abspath(png)
        html = open(TEMPLATE).read()
        html = html.replace("{{CHART}}", f"file://{chart_abs}")
        html = (html.replace("{{TICKER}}", d["ticker"])
                    .replace("{{NAME}}", d["name"])
                    .replace("{{SECTOR}}", d["sector"])
                    .replace("{{CURRENCY}}", d["currency"])
                    .replace("{{DATE}}", datetime.now().strftime("%d %b %Y"))
                    .replace("{{PRICE}}", _fmt(d["price"]))
                    .replace("{{DAYCHG}}", f"{_fmt(d['day_change'])} ({_pct(d['day_pct'])})")
                    .replace("{{HIGH52}}", _fmt(d["high52"]))
                    .replace("{{LOW52}}", _fmt(d["low52"]))
                    .replace("{{MKTCAP}}", _fmt(d["mktcap"] / 1e7, " Cr") if d["mktcap"] else "—")
                    .replace("{{PE}}", _fmt(d["pe"]))
                    .replace("{{FWDPE}}", _fmt(d["fwd_pe"]))
                    .replace("{{FWDEPS}}", _fmt(d["fwd_eps"]))
                    .replace("{{TARGET}}", _fmt(d["target"]))
                    .replace("{{UPSIDE}}", _pct((d["target"] / d["price"] - 1) * 100) if (d["target"] and d["price"]) else "—")
                    .replace("{{RECO}}", {"strong_buy": "Strong Buy", "buy": "Buy", "hold": "Hold", "sell": "Sell", "strong_sell": "Strong Sell"}.get(d["rec"], (d["rec"] or "—").title()))
                    .replace("{{NANALYST}}", str(d["n_analyst"]) if d["n_analyst"] else "—")
                    .replace("{{EPS}}", _fmt(d["eps"]))
                    .replace("{{BOOK}}", _fmt(d["book"]))
                    .replace("{{DIV}}", _pct(d["div_yield"] * 100) if (d["div_yield"] and d["div_yield"] < 0.1) else (_pct(d["div_yield"]) if d["div_yield"] else "—"))
                    .replace("{{ROE}}", _pct(d["roe"] * 100) if d["roe"] else "—")
                    .replace("{{SMA50}}", _fmt(d["sma50"]))
                    .replace("{{SMA200}}", _fmt(d["sma200"]))
                    .replace("{{RSI}}", _fmt(d["rsi"]))
                    .replace("{{RET1Y}}", _pct(d["ret1y"]))
                    .replace("{{REVGROWTH}}", _pct(d["rev_growth"]))
                    .replace("{{REVCAR}}", d["rev_car"][1])
                    .replace("{{NIGROWTH}}", _pct(d["ni_growth"]))
                    .replace("{{NICAR}}", d["ni_car"][1])
                    .replace("{{GROSSM}}", _pct(d["gross_m"] * 100) if d["gross_m"] else "—")
                    .replace("{{OPM}}", _pct(d["op_m"] * 100) if d["op_m"] else "—")
                    .replace("{{NETM}}", _pct(d["net_m"] * 100) if d["net_m"] else "—")
                    .replace("{{VERDICT}}", v))
        reasons_html = "".join(f"<li>{r}</li>" for r in reasons)
        html = html.replace("{{REASONS}}", reasons_html)

        # ---- Research sections (concall / PPT / results) ----
        research = d.get("research") or {}
        # Growth override: yfinance trailing growth is often stale/wrong vs reported.
        # If research provides real reported growth, use it everywhere.
        g = research.get("growth")
        if g:
            if g.get("revenue") is not None:
                d["rev_growth"] = g["revenue"]
            if g.get("net_income") is not None:
                d["ni_growth"] = g["net_income"]
            if g.get("rev_car"):
                d["rev_car"] = g["rev_car"]
            if g.get("ni_car"):
                d["ni_car"] = g["ni_car"]
        # Fundamentals override: yfinance price/valuation is often stale/wrong.
        # If research provides real figures (e.g. from Screener), use them.
        f = research.get("fundamentals")
        if f:
            for k in ("price", "day_pct", "high52", "low52", "mktcap", "pe",
                      "eps", "book", "div_yield", "roe", "roce", "sma50", "sma200", "rsi", "ret1y"):
                if f.get(k) is not None:
                    d[k] = f[k]
        # Concalls
        concalls = research.get("concalls") or []
        if concalls:
            rows = ""
            for c in concalls:
                hl = "".join(f"<li>{h}</li>" for h in c.get("highlights", []))
                rows += (f"<div class='call'><div class='call-h'>{c.get('quarter','')} "
                         f"<span class='call-d'>({c.get('date','')})</span></div>"
                         f"<div class='call-s'>{c.get('summary','')}</div>"
                         f"<ul class='call-hl'>{hl}</ul></div>")
            html = html.replace("{{CONCALLS}}", rows)
        else:
            html = html.replace("{{CONCALLS}}", "<p class='na'>No concall data provided. Pass --research research.json.</p>")
        # Latest results
        res = research.get("results")
        if res:
            rows = (f"<tr><td class='k'>Quarter</td><td class='v'>{res.get('quarter','—')}</td></tr>"
                    f"<tr><td class='k'>Revenue</td><td class='v'>{res.get('revenue','—')}</td></tr>"
                    f"<tr><td class='k'>Profit</td><td class='v'>{res.get('profit','—')}</td></tr>"
                    f"<tr><td class='k'>Margin</td><td class='v'>{res.get('margin','—')}</td></tr>")
            html = html.replace("{{RESULTS}}", rows)
        else:
            html = html.replace("{{RESULTS}}", "<tr><td colspan=2 class='na'>No results provided. Pass --research research.json.</td></tr>")
        # Presentation
        pres = research.get("presentation")
        if pres:
            hl = "".join(f"<li>{h}</li>" for h in pres.get("highlights", []))
            html = html.replace("{{PRES_TITLE}}", pres.get("title", "Investor Presentation"))
            html = html.replace("{{PRES_HL}}", hl)
        else:
            html = html.replace("{{PRES_TITLE}}", "Investor Presentation")
            html = html.replace("{{PRES_HL}}", "<li>No presentation data provided.</li>")

        # Brutal honesty: explicit points from research + auto-generated data-driven ones
        brutal = list(research.get("brutal") or [])
        # Auto: flag data discrepancy between yfinance trailing growth and reported guidance
        if d["rev_growth"] is not None and d["rev_growth"] < 0:
            brutal.append(f"DATA WARNING: trailing revenue growth from financials is {d['rev_growth']:.1f}% (negative) — this conflicts with management-reported growth. Verify the reporting period before trusting either number.")
        if d["rsi"] is not None and d["rsi"] > 70:
            brutal.append(f"RSI {d['rsi']:.0f} — overbought; short-term pullback risk is real.")
        if d["pe"] is not None and d["pe"] > 40:
            brutal.append(f"P/E {d['pe']:.1f} — expensive vs sector; you're paying a premium for the growth story.")
        if not brutal:
            brutal.append("No explicit risk flags from research. This is NOT a clean bill of health — it means the data provided was thin. Dig into guidance, capex, and competitive moat before acting.")
        html = html.replace("{{BRUTAL}}", "".join(f"<li>{b}</li>" for b in brutal))

        # Peer table — always include the TARGET as row 0 so it's in the "cars" list
        target_row = (f"<tr class='target'><td>★</td><td>{d['name']} ({d['ticker']}) <span class='tag'>TARGET</span></td>"
                      f"<td>{_pct(d['rev_growth'])}</td><td>{_pct(d['ni_growth'])}</td></tr>")
        if peers:
            rows = target_row
            for i, p in enumerate(peers, 1):
                cls = ' class="fastest"' if i == 1 and p["rev_growth"] is not None else ""
                rows += (f"<tr{cls}><td>{i}</td><td>{p['name']} ({p['ticker']})</td>"
                         f"<td>{_pct(p['rev_growth'])}</td><td>{_pct(p['ni_growth'])}</td></tr>")
            html = html.replace("{{PEERS}}", rows)
        else:
            html = html.replace("{{PEERS}", target_row)

        # ---- Thesis (Momentum & Growth framework) ----
        thesis = research.get("thesis") or []
        # Auto: Gaadi-ka-Speed verdict from growth acceleration
        rev_car_txt = d["rev_car"][1].upper()
        speed = "ACCELERATING (speeding up)" if "SPEEDING" in rev_car_txt else ("DECELERATING (slowing)" if "SLOWING" in rev_car_txt else "FLAT / UNCLEAR")
        auto = [f"Gaadi-ka-Speed (sales growth pace): {speed} — {d['rev_car'][0]}"]
        if d["rev_growth"] is not None and d["rev_growth"] >= 15:
            auto.append("Growth velocity strong (≥15% YoY) — passes the momentum bar.")
        elif d["rev_growth"] is not None and d["rev_growth"] < 0:
            auto.append("Growth velocity NEGATIVE — fails the momentum bar. Stock unlikely to reward under this framework.")
        else:
            auto.append("Growth velocity modest (<15%) — below the framework's preferred pace.")
        thesis_html = "".join(f"<li>{t}</li>" for t in auto + list(thesis))
        html = html.replace("{{THESIS}}", thesis_html)
        html = html.replace("{{THESIS_NOTE}}", research.get("thesis_note", ""))

        HTML(string=html, base_url=td).write_pdf(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--out", default=None)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--peers", default="", help="Comma-separated peer tickers, e.g. TATAMOTORS.NS,ASHOKLEY.NS")
    ap.add_argument("--research", default=None, help="Path to research.json with concalls/results/presentation data")
    a = ap.parse_args()
    out = a.out or f"stock_report_{a.ticker.replace('.', '_')}.pdf"
    d = fetch(a.ticker, a.days)
    if a.research:
        import json
        with open(a.research) as f:
            d["research"] = json.load(f)
    peers = fetch_peers([p for p in a.peers.split(",") if p.strip()]) if a.peers else None
    render(d, out, peers)
    print(f"OK: {out} ({os.path.getsize(out)} bytes)")
    print(f"Verdict: {verdict(d)[0]} @ {d['currency']} {d['price']:.2f}")
    if d["rev_car"][1] != "—":
        print(f"Growth: {d['rev_car'][0]} — {d['rev_car'][1]}")


if __name__ == "__main__":
    main()
