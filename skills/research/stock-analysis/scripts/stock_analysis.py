#!/usr/bin/env python3
"""Stock analysis -> beautiful PDF report (WeasyPrint).

All data comes from a research.json file (real data gathered by the agent
from Screener.in / BSE / company filings). NO yfinance dependency.

Usage:
    python3 stock_analysis.py "RELIANCE.NS" --research research.json [--out report.pdf]
"""
import argparse, os, sys, tempfile, json
from datetime import datetime

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


def _div(v):
    """Render dividend yield: research gives it in % (e.g. 0.37)."""
    if v is None:
        return "—"
    return f"{v:+.2f}%"


def load(research_path):
    """Build the data dict entirely from research.json."""
    with open(research_path) as f:
        r = json.load(f)
    fund = r.get("fundamentals") or {}
    growth = r.get("growth") or {}
    d = {
        "ticker": fund.get("ticker") or r.get("ticker", "—"),
        "name": fund.get("name") or r.get("name", "—"),
        "sector": fund.get("sector", "—"),
        "currency": fund.get("currency", "INR"),
        "price": fund.get("price"),
        "day_change": fund.get("day_change"),
        "day_pct": fund.get("day_pct"),
        "high52": fund.get("high52"),
        "low52": fund.get("low52"),
        "mktcap": fund.get("mktcap"),
        "pe": fund.get("pe"),
        "eps": fund.get("eps"),
        "book": fund.get("book"),
        "div_yield": fund.get("div_yield"),
        "roe": fund.get("roe"),
        "roce": fund.get("roce"),
        "sma50": fund.get("sma50"),
        "sma200": fund.get("sma200"),
        "rsi": fund.get("rsi"),
        "ret1y": fund.get("ret1y"),
        "rev_growth": growth.get("revenue"),
        "ni_growth": growth.get("net_income"),
        "rev_car": growth.get("rev_car") or ["No growth data", "—"],
        "ni_car": growth.get("ni_car") or ["No growth data", "—"],
        "gross_m": fund.get("gross_m"),
        "op_m": fund.get("op_m"),
        "net_m": fund.get("net_m"),
        "research": r,
    }
    return d


def render(d, out, peers=None):
    with tempfile.TemporaryDirectory() as td:
        html = open(TEMPLATE).read()
        html = (html.replace("{{TICKER}}", d["ticker"])
                    .replace("{{NAME}}", d["name"])
                    .replace("{{SECTOR}}", d["sector"])
                    .replace("{{CURRENCY}}", d["currency"])
                    .replace("{{DATE}}", datetime.now().strftime("%d %b %Y"))
                    .replace("{{PRICE}}", _fmt(d["price"]))
                    .replace("{{DAYCHG}}", f"{_fmt(d['day_change'])} ({_pct(d['day_pct'])})")
                    .replace("{{HIGH52}}", _fmt(d["high52"]))
                    .replace("{{LOW52}}", _fmt(d["low52"]))
                    .replace("{{MKTCAP}}", _fmt(d["mktcap"], " Cr") if d["mktcap"] else "—")
                    .replace("{{PE}}", _fmt(d["pe"]))
                    .replace("{{EPS}}", _fmt(d["eps"]))
                    .replace("{{BOOK}}", _fmt(d["book"]))
                    .replace("{{DIV}}", _div(d["div_yield"]))
                    .replace("{{ROE}}", _pct(d["roe"]) if d["roe"] is not None else "—")
                    .replace("{{ROCE}}", _pct(d["roce"]) if d["roce"] is not None else "—")
                    .replace("{{SMA50}}", _fmt(d["sma50"]))
                    .replace("{{SMA200}}", _fmt(d["sma200"]))
                    .replace("{{RSI}}", _fmt(d["rsi"]))
                    .replace("{{RET1Y}}", _pct(d["ret1y"]))
                    .replace("{{REVGROWTH}}", _pct(d["rev_growth"]))
                    .replace("{{REVCAR}}", d["rev_car"][1])
                    .replace("{{NIGROWTH}}", _pct(d["ni_growth"]))
                    .replace("{{NICAR}}", d["ni_car"][1])
                    .replace("{{GROSSM}}", _pct(d["gross_m"]) if d["gross_m"] is not None else "—")
                    .replace("{{OPM}}", _pct(d["op_m"]) if d["op_m"] is not None else "—")
                    .replace("{{NETM}}", _pct(d["net_m"]) if d["net_m"] is not None else "—"))

        research = d["research"]

        # Future & Guidance — detailed guidance points from research
        guidance = research.get("guidance") or {}
        g_rows = ""
        for k, v in guidance.items():
            g_rows += f"<tr><td class='k'>{k}</td><td class='v'>{v}</td></tr>"
        html = html.replace("{{GUIDANCE_ROWS}}", g_rows)

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
            html = html.replace("{{CONCALLS}}", "<p class='na'>No concall data provided in research.json.</p>")

        # Exact quotes from concalls (verbatim, highlighted)
        quotes = research.get("quotes") or []
        if quotes:
            q_html = ""
            for q in quotes:
                q_html += (f"<div class='quote'><div class='quote-q'>{q.get('speaker','')} "
                           f"— {q.get('context','')}</div><div class='quote-t'>“{q.get('text','')}”</div></div>")
            html = html.replace("{{CONCALL_QUOTES}}", q_html)
        else:
            html = html.replace("{{CONCALL_QUOTES}}", "<p class='na'>No verbatim quotes provided.</p>")

        # Latest results
        res = research.get("results")
        if res:
            rows = (f"<tr><td class='k'>Quarter</td><td class='v'>{res.get('quarter','—')}</td></tr>"
                    f"<tr><td class='k'>Revenue</td><td class='v'>{res.get('revenue','—')}</td></tr>"
                    f"<tr><td class='k'>Profit</td><td class='v'>{res.get('profit','—')}</td></tr>"
                    f"<tr><td class='k'>Margin</td><td class='v'>{res.get('margin','—')}</td></tr>")
            html = html.replace("{{RESULTS}}", rows)
        else:
            html = html.replace("{{RESULTS}}", "<tr><td colspan=2 class='na'>No results provided in research.json.</td></tr>")

        # Presentation
        pres = research.get("presentation")
        if pres:
            hl = "".join(f"<li>{h}</li>" for h in pres.get("highlights", []))
            html = html.replace("{{PRES_TITLE}}", pres.get("title", "Investor Presentation"))
            html = html.replace("{{PRES_HL}}", hl)
        else:
            html = html.replace("{{PRES_TITLE}}", "Investor Presentation")
            html = html.replace("{{PRES_HL}}", "<li>No presentation data provided.</li>")

        # Brutal honesty
        brutal = list(research.get("brutal") or [])
        if d["rsi"] is not None and d["rsi"] > 70:
            brutal.append(f"RSI {d['rsi']:.0f} — overbought; short-term pullback risk is real.")
        if d["pe"] is not None and d["pe"] > 40:
            brutal.append(f"P/E {d['pe']:.1f} — expensive vs sector; you're paying a premium for the growth story.")
        if not brutal:
            brutal.append("No explicit risk flags from research. This is NOT a clean bill of health — it means the data provided was thin. Dig into guidance, capex, and competitive moat before acting.")
        html = html.replace("{{BRUTAL}}", "".join(f"<li>{b}</li>" for b in brutal))

        # Peer table — rank target + peers TOGETHER by real revenue growth.
        # Only the single fastest gets green; target gets a "Target" tag on the right.
        rows = ""
        all_ = [{"ticker": d["ticker"], "name": d["name"], "rev_growth": d["rev_growth"],
                 "ni_growth": d["ni_growth"], "is_target": True}]
        for p in (research.get("peers") or peers or []):
            all_.append({"ticker": p["ticker"], "name": p["name"],
                         "rev_growth": p.get("rev_growth"), "ni_growth": p.get("ni_growth"),
                         "is_target": False})
        all_.sort(key=lambda x: (x["rev_growth"] if x["rev_growth"] is not None else -1e9), reverse=True)
        fastest = next((x["rev_growth"] for x in all_ if x["rev_growth"] is not None), None)
        for i, x in enumerate(all_, 1):
            cls = ' class="fastest"' if (x["rev_growth"] is not None and x["rev_growth"] == fastest) else ""
            tag = " <span class='tag'>Target</span>" if x["is_target"] else ""
            rows += (f"<tr{cls}><td>{i}</td><td>{x['name']} ({x['ticker']}){tag}</td>"
                     f"<td>{_pct(x['rev_growth'])}</td><td>{_pct(x['ni_growth'])}</td></tr>")
        html = html.replace("{{PEERS}}", rows)

        # Thesis
        thesis = research.get("thesis") or []
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

        # Sources & reference reports (links to PDFs used) — make URLs clickable
        sources = research.get("sources") or []
        if sources:
            import re as _re
            def _linkify(s):
                return _re.sub(r'(https?://\S+)', r'<a href="\1">\1</a>', s)
            s_html = "".join(f"<li>{_linkify(s)}</li>" for s in sources)
        else:
            s_html = "<li>No source links provided.</li>"
        html = html.replace("{{SOURCES}}", s_html)

        # Chart: only if research provides a price-history image path
        chart_path = research.get("chart_path")
        if chart_path and os.path.exists(chart_path):
            html = html.replace("{{CHART}}", f"file://{os.path.abspath(chart_path)}")
        else:
            html = html.replace(
                '<div class="section">\n      <div class="title"><span class="bar"></span>Price Chart (1Y)</div><hr class="rule">\n      <div class="chart"><img src="{{CHART}}"></div>\n    </div>',
                "")

        HTML(string=html, base_url=td).write_pdf(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", help="Ticker symbol (used for the report header)")
    ap.add_argument("--research", required=True, help="Path to research.json (all real data from Screener/BSE/filings)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"stock_report_{a.ticker.replace('.', '_')}.pdf"
    d = load(a.research)
    render(d, out)
    print(f"OK: {out} ({os.path.getsize(out)} bytes)")
    print(f"Price: {d['currency']} {d['price']:.2f}")
    print(f"Growth: {d['rev_car'][0]} — {d['rev_car'][1]}")


if __name__ == "__main__":
    main()
