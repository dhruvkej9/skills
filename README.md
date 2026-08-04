# Skills

A collection of reusable skills. Each skill lives under `skills/<category>/<name>/` with a `SKILL.md` and any supporting scripts.

## Skills

| Skill | Category | What it does |
|---|---|---|
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

## License

MIT
