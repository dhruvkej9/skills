---
name: xtweet
description: "Read X/Twitter posts free via fxtwitter, no API key."
version: 1.0.0
author: Dhruv Kejriwal
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [X, Twitter, tweet, extraction, fxtwitter]
    category: social-media
    related_skills: [xurl, local-twitter-workspace]
---

# X Post Reader (xtweet)

Read any X/Twitter post by ID or URL **for free** — no API key, no login, no OAuth. Uses X's public **fxtwitter** endpoint, which the official X API blocks but this does not.

## When to Use

Use whenever the user shares an X/Twitter post link or bare tweet ID and wants it read, summarized, analyzed, or quoted. This is the **primary** method — it works where direct X scraping, xurl (no creds), Nitter mirrors, and web search all fail.

## The One Command

```bash
curl -s "https://api.fxtwitter.com/i/status/<TWEET_ID>"
```

- `<TWEET_ID>` = the numeric ID in the URL (`x.com/<user>/status/123456789` → `123456789`), or a bare ID.
- No auth headers, no login, zero dependencies. Works on any OS with curl.

## Parse the JSON

```python
import json, subprocess
r = subprocess.run(["curl","-s","-m15","https://api.fxtwitter.com/i/status/<ID>"],capture_output=True,text=True).stdout
d = json.loads(r)
t = d["tweet"]
print("AUTHOR:", t["author"]["name"], "@"+t["author"]["screen_name"])
print("DATE:", t["created_at"])
print("LIKES:", t["likes"], "| REPLIES:", t["replies"], "| RT:", t["retweets"], "| VIEWS:", t["views"])
print("TEXT:\n", t["text"])
for m in t.get("media",{}).get("all",[]):
    print(m["type"], m["url"])
```

Key fields in `tweet`: `text` (full long-form), `author.{name,screen_name}`, `created_at`, `likes`, `replies`, `retweets`, `views`, `media.all[]` (photo/video/GIF with URLs), `lang`.

## Fallbacks (in order)

1. **fxtwitter** (primary): `https://api.fxtwitter.com/i/status/<ID>` — full text + metrics + media.
2. **X syndication** (no auth, public preview): `https://cdn.syndication.twimg.com/tweet-result?id=<ID>&token=a`
3. **x-tweet-fetcher** (`xtf`): smart routing fxtwitter→Nitter→browser for timelines/search/replies/lists/articles. Needs a Nitter instance for timelines.
4. **x2md** (Python, one file): markdown + top replies via fxtwitter + Nitter.

## Pitfalls

- **Official X API has NO free tier** (discontinued Feb 2026, pay-per-use ~$0.005/read). Never reach for it for reading.
- **Nitter public mirrors are unreliable/dead** — don't depend on them; fxtwitter is the reliable base.
- fxtwitter uses X's **undocumented public endpoints**; if it stops working, the `GQL_QUERY_ID` may have rotated — check the FixTweet/FxTwitter repo for updates.
- **Protected/age-gated/deleted/suspended** tweets return a clean error — can't read those without auth.
- fxtwitter returns the **root post only** (not threads). For threads use x2md or x-tweet-fetcher.
- Media URLs (`pbs.twimg.com`) are directly downloadable with curl.
