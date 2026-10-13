# Skills

A collection of reusable skills. Each skill lives under `skills/<category>/<name>/` with a `SKILL.md` and any supporting scripts.

## Skills

| Skill | Category | What it does |
|---|---|---|
| [`adversarial-review`](skills/software-development/adversarial-review/) | software-development | Reviewer–critic loop that gates every commit. Verbatim SKILL.md from [arXiv:2608.18167v1](https://arxiv.org/abs/2608.18167) (Qiu & Gill, ICML 2026). |
| [`improve-codebase-architecture`](skills/software-development/improve-codebase-architecture/) | software-development | Survey a codebase for shallow→deep module opportunities and produce a visual HTML report of refactor candidates. |
| [`writing-pr-body-title`](skills/software-development/writing-pr-body-title/) | software-development | Write or edit a PR title/body: concise, bullets, mermaid diagrams, before/after tables, no "I ran tests" filler. |
| [`stock-analysis`](skills/research/stock-analysis/) | research | Analyze a stock and generate a PDF report (WeasyPrint + Screener.in data + web research). No yfinance. |
| [`xtweet`](skills/social-media/xtweet/) | social-media | Read any X/Twitter post by ID/URL **free** via fxtwitter — no API key, no login, no OAuth. Full text, metrics, media. |

## Usage

Skills are loaded by the agent when relevant. For `xtweet`, the core command is:

```bash
curl -s "https://api.fxtwitter.com/i/status/<TWEET_ID>"
```

or the bundled helper:

```bash
python3 skills/social-media/xtweet/scripts/xtweet.py <TWEET_ID_or_URL>
```

## Adding a skill

Drop a folder under `skills/<category>/<name>/` containing a `SKILL.md` (YAML frontmatter + markdown body) and any `scripts/` or `references/` files.

## Credits

`adversarial-review` is reproduced verbatim from the authors' appendix:

> Eric S. Qiu and Joyce Gill, *"Adversarial Review: Structured Disagreement for Grounded Agentic Code Review"*, arXiv:2608.18167v1, ICML 2026.
> https://arxiv.org/abs/2608.18167

## License

MIT
